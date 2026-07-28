from __future__ import annotations

import base64
import contextlib
import importlib.util
import io
import json
import os
import stat
import struct
import sys
import tempfile
import unittest
import zlib
from unittest import mock
from pathlib import Path

try:
    from _support import ROOT
except ModuleNotFoundError:
    from tests._support import ROOT

from ip_pic.openai_direct import (
    CredentialError,
    doctor,
    load_api_key,
    render_request,
    write_user_api_key,
)
from ip_pic.errors import ValidationError
import ip_pic.openai_direct as openai_direct


TEST_ERROR_DETAIL = "test-error-detail-must-not-leak"
VALID_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _png_chunk(chunk_type: bytes, contents: bytes) -> bytes:
    checksum = zlib.crc32(chunk_type)
    checksum = zlib.crc32(contents, checksum) & 0xFFFFFFFF
    return (
        struct.pack(">I", len(contents))
        + chunk_type
        + contents
        + struct.pack(">I", checksum)
    )


class OpenAICredentialTests(unittest.TestCase):
    def test_default_config_prefers_new_ip_pic_location(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            current = home / ".ip-pic" / ".env"
            legacy = home / ".custom-ip-illustration" / ".env"
            current.parent.mkdir()
            legacy.parent.mkdir()
            current.write_text("OPENAI_API_KEY=current-key\n", encoding="utf-8")
            legacy.write_text("OPENAI_API_KEY=legacy-key\n", encoding="utf-8")
            with mock.patch.object(Path, "home", return_value=home):
                self.assertEqual(load_api_key(env={}), "current-key")

    def test_default_config_reads_legacy_with_migration_warning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            legacy = home / ".custom-ip-illustration" / ".env"
            legacy.parent.mkdir()
            legacy.write_text("OPENAI_API_KEY=legacy-key\n", encoding="utf-8")
            with mock.patch.object(Path, "home", return_value=home):
                with self.assertWarnsRegex(DeprecationWarning, r"\.ip-pic"):
                    self.assertEqual(load_api_key(env={}), "legacy-key")

    def test_explicit_environment_key_takes_precedence_over_user_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / ".env"
            config_path.write_text("OPENAI_API_KEY=config-key\n", encoding="utf-8")
            environment_name = "OPENAI_API_" + "KEY"
            environment_value = "environment-" + "key"
            self.assertEqual(
                load_api_key(
                    env={environment_name: environment_value},
                    config_path=config_path,
                ),
                environment_value,
            )

    def test_reads_only_exact_key_entry_from_user_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / ".env"
            config_path.write_text(
                " OPENAI_API_KEY=wrong\nOPENAI_API_KEY=accepted\n"
                "OPENAI_API_KEY_EXTRA=wrong\n",
                encoding="utf-8",
            )
            self.assertEqual(load_api_key(env={}, config_path=config_path), "accepted")

    def test_write_user_key_creates_private_parent_and_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "private" / ".env"
            returned = write_user_api_key(config_path, "configured-key")
            self.assertEqual(returned, config_path)
            self.assertEqual(
                stat.S_IMODE(config_path.stat().st_mode),
                0o600,
            )
            self.assertEqual(
                stat.S_IMODE(config_path.parent.stat().st_mode),
                0o700,
            )
            self.assertEqual(
                load_api_key(env={}, config_path=config_path),
                "configured-key",
            )

    def test_missing_credentials_doctor_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / ".env"
            result = doctor(env={}, config_path=config_path)
            self.assertEqual(result, {"status": "missing_credentials"})
            self.assertNotIn(TEST_ERROR_DETAIL, repr(result))

    def test_doctor_reports_unsupported_platform_without_loading_credentials(self) -> None:
        with mock.patch.object(openai_direct, "_secure_output_supported", return_value=False):
            with mock.patch.object(openai_direct, "load_api_key", side_effect=AssertionError("credentials read")) as loader:
                result = doctor(env={}, config_path=Path("unused"))
        self.assertEqual(result, {"status": "unsupported_platform"})
        loader.assert_not_called()

    def test_doctor_ready_status_remains_on_supported_platform(self) -> None:
        with mock.patch.object(openai_direct, "_secure_output_supported", return_value=True):
            result = doctor(env={"OPENAI_API_KEY": "doctor-key"}, config_path=Path("unused"))
        self.assertEqual(result, {"status": "ready"})

    def test_rejects_bad_secret_without_echoing_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / ".env"
            with self.assertRaises(CredentialError) as raised:
                write_user_api_key(config_path, TEST_ERROR_DETAIL + "\ninvalid")
            self.assertNotIn(TEST_ERROR_DETAIL, str(raised.exception))

    def test_doctor_treats_unreadable_or_malformed_config_as_missing_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, contents in (("directory", None), ("bad-utf8", b"\xff\xfe")):
                with self.subTest(name=name):
                    path = root / name
                    if contents is None:
                        path.mkdir()
                    else:
                        path.write_bytes(contents)
                    result = doctor(env={}, config_path=path)
                    self.assertEqual(result, {"status": "missing_credentials"})
                    self.assertNotIn(TEST_ERROR_DETAIL, repr(result))
            with mock.patch.object(Path, "read_text", side_effect=PermissionError("denied")):
                result = doctor(env={}, config_path=root / "unreadable")
            self.assertEqual(result, {"status": "missing_credentials"})
            self.assertNotIn(TEST_ERROR_DETAIL, repr(result))

    def test_write_user_key_handles_short_writes_and_preserves_existing_file_on_replace_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / ".env"
            original_write = os.write

            def short_write(fd: int, data: bytes) -> int:
                piece = data[:2]
                return original_write(fd, piece)

            with mock.patch("ip_pic.openai_direct.os.write", side_effect=short_write):
                write_user_api_key(config_path, "short-write-key")
            self.assertEqual(load_api_key(env={}, config_path=config_path), "short-write-key")
            config_path.write_text("OPENAI_API_KEY=previous-key\n", encoding="utf-8")
            with mock.patch("ip_pic.openai_direct.os.rename", side_effect=OSError("blocked")):
                with self.assertRaises(CredentialError) as raised:
                    write_user_api_key(config_path, TEST_ERROR_DETAIL)
            self.assertEqual(load_api_key(env={}, config_path=config_path), "previous-key")
            self.assertNotIn(TEST_ERROR_DETAIL, str(raised.exception))

    def test_write_user_key_rejects_symlinked_config_parent_without_leaking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            config_parent = root / "config"
            try:
                config_parent.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("symlinks unavailable")
            with self.assertRaises(CredentialError) as raised:
                write_user_api_key(config_parent / ".env", TEST_ERROR_DETAIL)
            self.assertFalse((outside / ".env").exists())
            self.assertNotIn(TEST_ERROR_DETAIL, str(raised.exception))

    def test_write_user_key_detects_parent_path_swap_without_writing_outside(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_parent = root / "config"
            config_parent.mkdir()
            original_parent = root / "config-original"
            outside = root / "outside"
            outside.mkdir()
            original_open = os.open
            swapped = False

            def swapping_open(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                name = os.fspath(path)
                if not swapped and ".env." in Path(name).name and flags & os.O_CREAT:
                    config_parent.rename(original_parent)
                    config_parent.symlink_to(outside, target_is_directory=True)
                    swapped = True
                if dir_fd is None:
                    return original_open(path, flags, mode)
                return original_open(path, flags, mode, dir_fd=dir_fd)

            with mock.patch(
                "ip_pic.openai_direct.os.open",
                side_effect=swapping_open,
            ):
                with self.assertRaises(CredentialError) as raised:
                    write_user_api_key(config_parent / ".env", TEST_ERROR_DETAIL)
            self.assertTrue(swapped)
            self.assertFalse((outside / ".env").exists())
            self.assertFalse((original_parent / ".env").exists())
            self.assertNotIn(TEST_ERROR_DETAIL, str(raised.exception))


class OpenAIRendererTests(unittest.TestCase):
    png_bytes = VALID_PNG

    def _request(self, directory: Path, images: list[dict]) -> Path:
        for image in images:
            prompt = directory / image["prompt_path"]
            prompt.parent.mkdir(parents=True, exist_ok=True)
            prompt.write_text(f"Prompt for {image['id']}", encoding="utf-8")
        request_path = directory / "render-request.json"
        request_path.write_text(
            json.dumps(
                {
                    "schema": "render-request/v1",
                    "title": "Renderer test",
                    "template_id": "test",
                    "images": images,
                }
            ),
            encoding="utf-8",
        )
        return request_path

    def _raw_request(self, directory: Path, images: list[dict]) -> Path:
        request_path = directory / "render-request.json"
        request_path.write_text(
            json.dumps({"schema": "render-request/v1", "title": "Renderer test", "template_id": "test", "images": images}),
            encoding="utf-8",
        )
        return request_path

    def _image(self, image_id: str, canvas: str, references: list[str] | None = None) -> dict:
        dimensions = {
            "16:9": (1536, 864),
            "1:1": (1024, 1024),
            "9:16": (1152, 2048),
        }
        width, height = dimensions[canvas]
        return {
            "id": image_id,
            "prompt_path": f"prompts/{image_id}.md",
            "output_path": f"images/{image_id}.png",
            "canvas": canvas,
            "width": width,
            "height": height,
            "reference_images": references or [],
        }

    def _success_transport(self, calls: list[dict]):
        encoded = base64.b64encode(self.png_bytes).decode("ascii")

        def transport(url: str, method: str, headers: dict[str, str], body: bytes) -> dict:
            calls.append({"url": url, "method": method, "headers": headers, "body": body})
            return {"status": 200, "body": json.dumps({"data": [{"b64_json": encoded}]}).encode()}

        return transport

    def test_generation_uses_gpt_image_2_and_standard_canvas_sizes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = self._request(
                root,
                [
                    self._image("landscape", "16:9"),
                    self._image("square", "1:1"),
                    self._image("portrait", "9:16"),
                ],
            )
            calls: list[dict] = []
            result = render_request(
                request,
                root / "output",
                "render-test-key",
                transport=self._success_transport(calls),
            )
            self.assertEqual(result["status"], "complete")
            self.assertEqual([call["url"] for call in calls], [
                "https://api.openai.com/v1/images/generations",
            ] * 3)
            payloads = [json.loads(call["body"]) for call in calls]
            self.assertEqual([payload["model"] for payload in payloads], ["gpt-image-2"] * 3)
            self.assertEqual(
                [payload["size"] for payload in payloads],
                ["1536x864", "1024x1024", "1152x2048"],
            )
            self.assertTrue(all(payload["quality"] == "medium" for payload in payloads))
            self.assertTrue(all(payload["output_format"] == "png" for payload in payloads))
            self.assertTrue(all("background" not in payload for payload in payloads))
            self.assertTrue(all("input_fidelity" not in payload for payload in payloads))

    def test_invalid_exact_dimensions_are_blocked_before_transport(self) -> None:
        cases = (
            ("boolean", True, 1024),
            ("not-multiple-of-16", 1025, 1024),
            ("edge-over-3840", 3856, 1024),
            ("ratio-over-3-to-1", 3088, 1024),
            ("pixels-below-minimum", 800, 800),
            ("pixels-above-maximum", 3840, 2176),
        )
        for name, width, height in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                image = self._image(name, "1:1")
                image["width"] = width
                image["height"] = height
                request = self._request(root, [image])
                calls: list[dict] = []
                with self.assertRaises(ValidationError):
                    render_request(
                        request,
                        root / "output",
                        "renderer-key",
                        transport=self._success_transport(calls),
                    )
                self.assertEqual(calls, [])

    def test_canvas_must_match_the_exact_compiler_dimension_pair(self) -> None:
        for width, height in ((1024, 1024), (2048, 1152)):
            with self.subTest(width=width, height=height), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                image = self._image("mismatch", "16:9")
                image["width"] = width
                image["height"] = height
                request = self._request(root, [image])
                calls: list[dict] = []
                with self.assertRaises(ValidationError):
                    render_request(
                        request,
                        root / "output",
                        "renderer-key",
                        transport=self._success_transport(calls),
                    )
                self.assertEqual(calls, [])

    def test_reference_images_use_edits_multipart_and_write_decoded_png(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "authorized-reference.png"
            reference.write_bytes(b"\x89PNG\r\n\x1a\nreference-image-bytes")
            request = self._request(root, [self._image("edit", "1:1", [str(reference)])])
            calls: list[dict] = []
            result = render_request(
                request,
                root / "output",
                "render-test-key",
                transport=self._success_transport(calls),
            )
            self.assertEqual(result["status"], "complete")
            self.assertEqual(calls[0]["url"], "https://api.openai.com/v1/images/edits")
            self.assertTrue(calls[0]["headers"]["Content-Type"].startswith("multipart/form-data; boundary="))
            self.assertIn(b'name="image[]"; filename="authorized-reference.png"', calls[0]["body"])
            self.assertIn(b"reference-image-bytes", calls[0]["body"])
            self.assertIn(b'name="quality"\r\n\r\nmedium', calls[0]["body"])
            self.assertIn(b'name="output_format"\r\n\r\npng', calls[0]["body"])
            self.assertNotIn(b'name="background"', calls[0]["body"])
            self.assertNotIn(b'name="input_fidelity"', calls[0]["body"])
            self.assertEqual((root / "output" / "images" / "edit.png").read_bytes(), self.png_bytes)

    def test_prompt_paths_that_escape_the_request_root_are_blocked_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root.parent / "outside-prompt.md"
            outside.write_text("outside", encoding="utf-8")
            variants = ["../outside-prompt.md", str(outside)]
            prompts = root / "prompts"
            prompts.mkdir()
            link = prompts / "escape.md"
            try:
                link.symlink_to(outside)
                variants.append("prompts/escape.md")
            except OSError:
                pass
            for index, prompt_path in enumerate(variants):
                with self.subTest(prompt_path=prompt_path):
                    image = self._image(f"escape-{index}", "1:1")
                    image["prompt_path"] = prompt_path
                    request = self._raw_request(root, [image])
                    calls: list[dict] = []
                    with self.assertRaises(ValidationError):
                        render_request(request, root / "output", "render-test-key", transport=self._success_transport(calls))
                    self.assertEqual(calls, [])

    def test_all_output_paths_are_preflighted_before_any_transport_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = [self._image("safe", "1:1"), self._image("escape", "1:1")]
            images[1]["output_path"] = "../outside.png"
            request = self._request(root, images)
            calls: list[dict] = []
            with self.assertRaises(ValidationError):
                render_request(request, root / "output", "render-test-key", transport=self._success_transport(calls))
            self.assertEqual(calls, [])

    def test_duplicate_output_paths_are_blocked_before_any_transport_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = [self._image("first", "1:1"), self._image("second", "1:1")]
            images[1]["output_path"] = images[0]["output_path"]
            request = self._request(root, images)
            calls: list[dict] = []
            with self.assertRaises(ValidationError):
                render_request(
                    request,
                    root / "output",
                    "render-test-key",
                    transport=self._success_transport(calls),
                )
            self.assertEqual(calls, [])

    def test_render_output_inside_skill_root_is_blocked_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = self._request(root, [self._image("blocked", "1:1")])
            common_root = Path(os.path.commonpath((root, ROOT)))

            def forbidden_transport(*_args, **_kwargs):
                raise AssertionError("transport called")

            with self.assertRaises(ValidationError):
                render_request(
                    request,
                    ROOT / "tests",
                    "render-test-key",
                    transport=forbidden_transport,
                    project_root=common_root,
                )

    def test_reference_outside_project_root_is_blocked_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            outside = root / "outside.png"
            outside.write_bytes(b"\x89PNG\r\n\x1a\noutside")
            request = self._request(
                project,
                [self._image("outside-reference", "1:1", [str(outside)])],
            )
            calls: list[dict] = []
            with self.assertRaises(ValidationError):
                render_request(
                    request,
                    project / "output",
                    "render-test-key",
                    transport=self._success_transport(calls),
                    project_root=project,
                )
            self.assertEqual(calls, [])

    def test_reference_symlink_that_escapes_project_is_blocked_before_transport(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            outside = root / "outside.png"
            outside.write_bytes(b"\x89PNG\r\n\x1a\noutside")
            reference = project / "reference.png"
            try:
                reference.symlink_to(outside)
            except OSError:
                self.skipTest("symlinks unavailable")
            request = self._request(
                project,
                [self._image("symlink-reference", "1:1", [str(reference)])],
            )
            calls: list[dict] = []
            with self.assertRaises(ValidationError):
                render_request(
                    request,
                    project / "output",
                    "render-test-key",
                    transport=self._success_transport(calls),
                    project_root=project,
                )
            self.assertEqual(calls, [])

    def test_reference_parent_swap_cannot_read_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sandbox = Path(directory)
            project = sandbox / "project"
            reference_parent = project / "references"
            reference_parent.mkdir(parents=True)
            reference = reference_parent / "owner.png"
            reference.write_bytes(b"\x89PNG\r\n\x1a\ninside")
            outside = sandbox / "outside"
            outside.mkdir()
            (outside / "owner.png").write_bytes(b"\x89PNG\r\n\x1a\noutside")
            parked = project / "parked-references"
            request = self._request(
                project,
                [self._image("reference-parent-swap", "1:1", [str(reference)])],
            )
            calls: list[dict] = []
            original_require = openai_direct._require_project_path
            swapped = False

            def swapping_require(path: Path, project_root: Path, *, field: str) -> Path:
                nonlocal swapped
                result = original_require(path, project_root, field=field)
                if field == "reference image" and not swapped:
                    reference_parent.rename(parked)
                    reference_parent.symlink_to(outside, target_is_directory=True)
                    swapped = True
                return result

            with mock.patch.object(
                openai_direct,
                "_require_project_path",
                side_effect=swapping_require,
            ):
                with self.assertRaises(ValidationError):
                    render_request(
                        request,
                        project / "output",
                        "render-test-key",
                        transport=self._success_transport(calls),
                        project_root=project,
                    )
            self.assertTrue(swapped)
            self.assertEqual(calls, [])

    def test_reference_count_is_limited_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            references = []
            for index in range(5):
                reference = root / f"reference-{index}.png"
                reference.write_bytes(b"\x89PNG\r\n\x1a\nreference")
                references.append(str(reference))
            request = self._request(
                root,
                [self._image("too-many-references", "1:1", references)],
            )
            calls: list[dict] = []
            with self.assertRaises(ValidationError):
                render_request(
                    request,
                    root / "output",
                    "render-test-key",
                    transport=self._success_transport(calls),
                    project_root=root,
                )
            self.assertEqual(calls, [])

    def test_output_parent_symlink_is_blocked_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = self._request(root, [self._image("symlink-output", "1:1")])
            output = root / "output"
            output.mkdir()
            outside = root / "outside"
            outside.mkdir()
            try:
                (output / "images").symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("symlinks unavailable")
            calls: list[dict] = []
            with self.assertRaises(ValidationError):
                render_request(request, output, "render-test-key", transport=self._success_transport(calls))
            self.assertEqual(calls, [])

    def test_existing_output_symlink_is_blocked_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = self._request(root, [self._image("symlink-target", "1:1")])
            output = root / "output"
            target = root / "outside.png"
            output_images = output / "images"
            output_images.mkdir(parents=True)
            try:
                (output_images / "symlink-target.png").symlink_to(target)
            except OSError:
                self.skipTest("symlinks unavailable")
            calls: list[dict] = []
            with self.assertRaises(ValidationError):
                render_request(request, output, "render-test-key", transport=self._success_transport(calls))
            self.assertEqual(calls, [])

    def test_existing_regular_render_output_is_preserved_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = self._request(root, [self._image("existing", "1:1")])
            output = root / "output"
            destination = output / "images" / "existing.png"
            destination.parent.mkdir(parents=True)
            original = b"existing-render-output"
            destination.write_bytes(original)
            calls: list[dict] = []
            with self.assertRaises(ValidationError):
                render_request(
                    request,
                    output,
                    "render-test-key",
                    transport=self._success_transport(calls),
                )
            self.assertEqual(destination.read_bytes(), original)
            self.assertEqual(calls, [])

    def test_transport_time_output_race_preserves_the_competing_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = self._request(root, [self._image("race", "1:1")])
            output = root / "output"
            destination = output / "images" / "race.png"
            competing = b"created-while-request-was-in-flight"
            encoded = base64.b64encode(self.png_bytes).decode("ascii")

            def racing_transport(
                _url: str,
                _method: str,
                _headers: dict[str, str],
                _body: bytes,
            ) -> dict:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(competing)
                return {
                    "status": 200,
                    "body": json.dumps(
                        {"data": [{"b64_json": encoded}]}
                    ).encode(),
                }

            result = render_request(
                request,
                output,
                "render-test-key",
                transport=racing_transport,
            )
            self.assertEqual(result["status"], "partial_failure")
            self.assertEqual(destination.read_bytes(), competing)

    def test_truncated_png_response_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = self._request(root, [self._image("truncated", "1:1")])
            encoded = base64.b64encode(
                b"\x89PNG\r\n\x1a\nnot-a-complete-png"
            ).decode("ascii")

            def truncated_transport(
                _url: str,
                _method: str,
                _headers: dict[str, str],
                _body: bytes,
            ) -> dict:
                return {
                    "status": 200,
                    "body": json.dumps(
                        {"data": [{"b64_json": encoded}]}
                    ).encode(),
                }

            result = render_request(
                request,
                root / "output",
                "render-test-key",
                transport=truncated_transport,
            )
            self.assertEqual(result["status"], "partial_failure")
            self.assertFalse(
                (root / "output" / "images" / "truncated.png").exists()
            )

    def test_png_with_invalid_idat_stream_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = self._request(root, [self._image("invalid-idat", "1:1")])
            invalid_png = (
                b"\x89PNG\r\n\x1a\n"
                + _png_chunk(
                    b"IHDR",
                    struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0),
                )
                + _png_chunk(b"IDAT", b"not-a-zlib-stream")
                + _png_chunk(b"IEND", b"")
            )
            encoded = base64.b64encode(invalid_png).decode("ascii")

            def invalid_transport(
                _url: str,
                _method: str,
                _headers: dict[str, str],
                _body: bytes,
            ) -> dict:
                return {
                    "status": 200,
                    "body": json.dumps(
                        {"data": [{"b64_json": encoded}]}
                    ).encode(),
                }

            result = render_request(
                request,
                root / "output",
                "render-test-key",
                transport=invalid_transport,
            )
            self.assertEqual(result["status"], "partial_failure")
            self.assertFalse(
                (root / "output" / "images" / "invalid-idat.png").exists()
            )

    def test_png_validation_never_uses_unbounded_decompress_flush(self) -> None:
        flush_limits: list[int] = []

        class ProbeDecompressor:
            eof = False
            unused_data = b""
            unconsumed_tail = b""

            def decompress(self, _contents: bytes, _limit: int) -> bytes:
                return b""

            def flush(self, limit: int = 0) -> bytes:
                flush_limits.append(limit)
                raise AssertionError("PNG validation must not use unbounded flush")

        with mock.patch.object(
            openai_direct.zlib,
            "decompressobj",
            return_value=ProbeDecompressor(),
        ):
            self.assertFalse(openai_direct._valid_png(self.png_bytes))
        self.assertEqual(flush_limits, [])

    def test_indexed_png_without_required_palette_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = self._request(root, [self._image("missing-palette", "1:1")])
            invalid_png = (
                b"\x89PNG\r\n\x1a\n"
                + _png_chunk(
                    b"IHDR",
                    struct.pack(">IIBBBBB", 1, 1, 8, 3, 0, 0, 0),
                )
                + _png_chunk(b"IDAT", zlib.compress(b"\x00\x00"))
                + _png_chunk(b"IEND", b"")
            )
            encoded = base64.b64encode(invalid_png).decode("ascii")

            def invalid_transport(
                _url: str,
                _method: str,
                _headers: dict[str, str],
                _body: bytes,
            ) -> dict:
                return {
                    "status": 200,
                    "body": json.dumps(
                        {"data": [{"b64_json": encoded}]}
                    ).encode(),
                }

            result = render_request(
                request,
                root / "output",
                "render-test-key",
                transport=invalid_transport,
            )
            self.assertEqual(result["status"], "partial_failure")
            self.assertFalse(
                (root / "output" / "images" / "missing-palette.png").exists()
            )

    def test_posix_writer_uses_dir_fd_branch_without_fallback(self) -> None:
        if os.name != "posix":
            self.skipTest("POSIX-specific safety branch")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = self._request(root, [self._image("posix", "1:1")])
            calls: list[dict] = []
            with mock.patch.object(openai_direct, "_write_output_fallback", side_effect=AssertionError("fallback used")) as fallback:
                result = render_request(request, root / "output", "render-test-key", transport=self._success_transport(calls))
            self.assertEqual(result["status"], "complete")
            fallback.assert_not_called()

    def test_transport_time_output_symlink_swap_never_writes_outside_root(self) -> None:
        if os.name != "posix":
            self.skipTest("POSIX-specific safety branch")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            encoded = base64.b64encode(self.png_bytes).decode("ascii")
            for replacement in ("root", "parent"):
                with self.subTest(replacement=replacement):
                    request = self._request(root, [self._image(f"swap-{replacement}", "1:1")])
                    output = root / f"output-{replacement}"
                    output.mkdir()
                    if replacement == "parent":
                        (output / "images").mkdir()
                    outside = root / f"outside-{replacement}"
                    outside.mkdir()
                    calls: list[dict] = []

                    def transport(url: str, method: str, headers: dict[str, str], body: bytes) -> dict:
                        calls.append({"url": url})
                        target = output if replacement == "root" else output / "images"
                        target.rmdir()
                        target.symlink_to(outside, target_is_directory=True)
                        return {"status": 200, "body": json.dumps({"data": [{"b64_json": encoded}]}).encode()}

                    result = render_request(request, output, "render-test-key", transport=transport)
                    self.assertEqual(result["images"][0]["status"], "failed")
                    self.assertEqual(len(calls), 1)
                    self.assertFalse((outside / f"swap-{replacement}.png").exists())

    def test_transport_time_output_ancestor_symlink_swap_never_writes_outside_project(
        self,
    ) -> None:
        if os.name != "posix":
            self.skipTest("POSIX-specific safety branch")
        with tempfile.TemporaryDirectory() as directory:
            sandbox = Path(directory)
            root = sandbox / "project"
            root.mkdir()
            request = self._request(root, [self._image("ancestor-swap", "1:1")])
            route = root / "route"
            output = route / "output"
            output.mkdir(parents=True)
            parked_route = root / "parked-route"
            outside = sandbox / "outside"
            (outside / "output").mkdir(parents=True)
            encoded = base64.b64encode(self.png_bytes).decode("ascii")

            def transport(
                _url: str,
                _method: str,
                _headers: dict[str, str],
                _body: bytes,
            ) -> dict:
                route.rename(parked_route)
                route.symlink_to(outside, target_is_directory=True)
                return {
                    "status": 200,
                    "body": json.dumps(
                        {"data": [{"b64_json": encoded}]}
                    ).encode(),
                }

            result = render_request(
                request,
                output,
                "render-test-key",
                transport=transport,
                project_root=root,
            )
            self.assertEqual(result["status"], "partial_failure")
            self.assertFalse(
                (outside / "output" / "images" / "ancestor-swap.png").exists()
            )

    def test_without_dir_fd_safety_support_rendering_fails_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = self._request(root, [self._image("no-secure-output", "1:1")])
            calls: list[dict] = []
            with mock.patch.object(openai_direct, "_secure_output_supported", return_value=False):
                with self.assertRaises(ValidationError):
                    render_request(request, root / "output", "render-test-key", transport=self._success_transport(calls))
            self.assertEqual(calls, [])

    def test_multipart_detects_image_signatures_and_sanitizes_filename(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = [
                ("photo.jpg", b"\xff\xd8\xffjpeg", b"image/jpeg"),
                ("photo.webp", b"RIFF\x04\x00\x00\x00WEBPwebp", b"image/webp"),
                ('evil"\r\nInjected.png', b"\x89PNG\r\n\x1a\npng", b"image/png"),
            ]
            for index, (name, contents, mime) in enumerate(cases):
                with self.subTest(name=name):
                    reference = root / name
                    reference.write_bytes(contents)
                    request = self._request(root, [self._image(f"mime-{index}", "1:1", [str(reference)])])
                    calls: list[dict] = []
                    render_request(request, root / f"output-{index}", "render-test-key", transport=self._success_transport(calls))
                    body = calls[0]["body"]
                    self.assertIn(b"Content-Type: " + mime, body)
                    self.assertIn(b"filename*=UTF-8''", body)
                    self.assertNotIn(b'evil"', body)
                    self.assertNotIn(b"\r\nInjected", body)

    def test_unknown_reference_format_is_blocked_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "unknown.bin"
            reference.write_bytes(b"not-an-image")
            request = self._request(root, [self._image("unknown", "1:1", [str(reference)])])
            calls: list[dict] = []
            with self.assertRaises(ValidationError):
                render_request(request, root / "output", "render-test-key", transport=self._success_transport(calls))
            self.assertEqual(calls, [])

    def test_invalid_success_payloads_are_reported_and_batch_continues(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = self._request(root, [self._image("null", "1:1"), self._image("list", "1:1"), self._image("string", "1:1"), self._image("good", "1:1")])
            encoded = base64.b64encode(self.png_bytes).decode("ascii")
            responses = [b"null", b"[]", b'"text"', json.dumps({"data": [{"b64_json": encoded}]}).encode()]
            calls: list[dict] = []

            def transport(url: str, method: str, headers: dict[str, str], body: bytes) -> dict:
                calls.append({"url": url})
                return {"status": 200, "body": responses.pop(0)}

            result = render_request(request, root / "output", "render-test-key", transport=transport)
            self.assertEqual([item["status"] for item in result["images"]], ["failed", "failed", "failed", "rendered"])
            self.assertTrue(all(item.get("error") == "invalid_response" for item in result["images"][:3]))
            self.assertEqual(len(calls), 4)

    def test_partial_failure_preserves_successful_image_and_reports_safe_classification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = self._request(root, [self._image("first", "1:1"), self._image("second", "1:1")])
            encoded = base64.b64encode(self.png_bytes).decode("ascii")
            responses = [
                {"status": 200, "body": json.dumps({"data": [{"b64_json": encoded}]}).encode()},
                {"status": 429, "body": b'{"error":"do not expose provider payload"}'},
            ]

            def transport(url: str, method: str, headers: dict[str, str], body: bytes) -> dict:
                return responses.pop(0)

            result = render_request(request, root / "output", "render-test-key", transport=transport)
            self.assertEqual(result["status"], "partial_failure")
            self.assertEqual(result["images"][0]["status"], "rendered")
            self.assertEqual(result["images"][1], {"id": "second", "status": "failed", "error": "rate_limited"})
            self.assertTrue((root / "output" / "images" / "first.png").is_file())
            self.assertNotIn("render-test-key", repr(result))

    def test_http_error_codes_are_classified_without_provider_payload(self) -> None:
        expected = {401: "authentication", 403: "authorization", 429: "rate_limited", 500: "server_error"}
        for status, classification in expected.items():
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                request = self._request(root, [self._image("only", "1:1")])

                def transport(url: str, method: str, headers: dict[str, str], body: bytes, code: int = status) -> dict:
                    return {"status": code, "body": b'{"error":"provider secret detail"}'}

                result = render_request(request, root / "output", "render-test-key", transport=transport)
                self.assertEqual(result["images"], [{"id": "only", "status": "failed", "error": classification}])
                self.assertNotIn("provider secret detail", repr(result))


class OpenAICharacterMasterTests(unittest.TestCase):
    png_bytes = VALID_PNG

    def _success_transport(self, calls: list[dict]):
        encoded = base64.b64encode(self.png_bytes).decode("ascii")

        def transport(url: str, method: str, headers: dict[str, str], body: bytes) -> dict:
            calls.append({"url": url, "method": method, "headers": headers, "body": body})
            return {"status": 200, "body": json.dumps({"data": [{"b64_json": encoded}]}).encode()}

        return transport

    def test_master_edit_uses_safe_character_sheet_prompt_and_gpt_image_2_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / 'owner"\r\nPhoto.png'
            reference.write_bytes(b"\x89PNG\r\n\x1a\nreference")
            output = root / "result" / "character-master.png"
            calls: list[dict] = []
            result = openai_direct.render_character_master(
                reference,
                output,
                "master-test-key",
                transport=self._success_transport(calls),
            )
            self.assertEqual(result, {"status": "rendered", "output_path": str(output)})
            self.assertEqual(output.read_bytes(), self.png_bytes)
            self.assertEqual(calls[0]["url"], "https://api.openai.com/v1/images/edits")
            body = calls[0]["body"]
            for required in (
                b"original cartoon",
                b"non-sensitive",
                b"hairstyle",
                b"face shape",
                b"glasses",
                b"sensitive attributes",
                b"full-body",
                b"front, side, and back views",
                b"common facial expressions",
                b"clean neutral background",
                b"text",
                b"watermark",
                b"logo",
                b"third-party character",
            ):
                self.assertIn(required, body)
            for name, value in (
                (b"model", b"gpt-image-2"),
                (b"size", b"1024x1024"),
                (b"quality", b"medium"),
                (b"output_format", b"png"),
            ):
                self.assertIn(b'name="' + name + b'"\r\n\r\n' + value, body)
            self.assertNotIn(b'name="background"', body)
            self.assertNotIn(b'name="input_fidelity"', body)
            self.assertIn(b"Content-Type: image/png", body)
            self.assertIn(b"filename*=UTF-8''", body)
            self.assertNotIn(b'owner"', body)
            self.assertNotIn(b"\r\nPhoto", body)
            self.assertNotIn("master-test-key", repr(result))

    def test_master_accepts_jpeg_and_webp_by_signature(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = [
                ("owner.jpg", b"\xff\xd8\xffreference", b"image/jpeg"),
                ("owner.webp", b"RIFF\x04\x00\x00\x00WEBPreference", b"image/webp"),
            ]
            for index, (name, contents, mime) in enumerate(cases):
                with self.subTest(name=name):
                    reference = root / name
                    reference.write_bytes(contents)
                    calls: list[dict] = []
                    openai_direct.render_character_master(
                        reference,
                        root / f"master-{index}.png",
                        "master-test-key",
                        transport=self._success_transport(calls),
                    )
                    self.assertIn(b"Content-Type: " + mime, calls[0]["body"])

    def test_master_blocks_missing_unknown_and_unsupported_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = root / "missing.png"
            unknown = root / "unknown.bin"
            unknown.write_bytes(b"not-an-image")
            for reference in (missing, unknown):
                with self.subTest(reference=reference):
                    calls: list[dict] = []
                    with self.assertRaises(ValidationError):
                        openai_direct.render_character_master(
                            reference,
                            root / "master.png",
                            "master-test-key",
                            transport=self._success_transport(calls),
                        )
                    self.assertEqual(calls, [])
            valid = root / "valid.png"
            valid.write_bytes(b"\x89PNG\r\n\x1a\nreference")
            calls = []
            with mock.patch.object(openai_direct, "_secure_output_supported", return_value=False):
                with self.assertRaises(ValidationError):
                    openai_direct.render_character_master(
                        valid,
                        root / "master.png",
                        "master-test-key",
                        transport=self._success_transport(calls),
                    )
            self.assertEqual(calls, [])

    def test_master_refuses_existing_regular_output_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "owner.png"
            reference.write_bytes(b"\x89PNG\r\n\x1a\nreference")
            output = root / "character-master.png"
            original = b"existing-character-master"
            output.write_bytes(original)
            calls: list[dict] = []

            with self.assertRaises(ValidationError):
                openai_direct.render_character_master(
                    reference,
                    output,
                    "master-test-key",
                    transport=self._success_transport(calls),
                )

            self.assertEqual(output.read_bytes(), original)
            self.assertEqual(calls, [])

    def test_master_reference_and_output_must_stay_in_user_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            outside = root / "outside.png"
            outside.write_bytes(b"\x89PNG\r\n\x1a\noutside")
            calls: list[dict] = []
            with self.assertRaises(ValidationError):
                openai_direct.render_character_master(
                    outside,
                    project / "character-master.png",
                    "master-test-key",
                    transport=self._success_transport(calls),
                    project_root=project,
                )
            self.assertEqual(calls, [])

            reference = project / "reference.png"
            reference.write_bytes(b"\x89PNG\r\n\x1a\ninside")
            with self.assertRaises(ValidationError):
                openai_direct.render_character_master(
                    reference,
                    root / "outside-master.png",
                    "master-test-key",
                    transport=self._success_transport(calls),
                    project_root=project,
                )
            self.assertEqual(calls, [])

    def test_master_requires_png_output_and_rejects_skill_root_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "owner.png"
            reference.write_bytes(b"\x89PNG\r\n\x1a\nreference")
            outputs = (root / "master.jpg", ROOT / "blocked-character-master.png")
            for output in outputs:
                with self.subTest(output=output):
                    calls: list[dict] = []
                    common_root = Path(os.path.commonpath((root, output)))
                    with self.assertRaises(ValidationError):
                        openai_direct.render_character_master(
                            reference,
                            output,
                            "master-test-key",
                            transport=self._success_transport(calls),
                            project_root=common_root,
                        )
                    self.assertEqual(calls, [])
                    self.assertFalse(output.exists())


class OpenAIBackendCLITests(unittest.TestCase):
    def _module(self):
        script = ROOT / "scripts" / "openai_backend.py"
        specification = importlib.util.spec_from_file_location("openai_backend_test", script)
        self.assertIsNotNone(specification)
        self.assertIsNotNone(specification.loader)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        return module

    def test_doctor_command_prints_only_safe_status(self) -> None:
        module = self._module()
        module.doctor = lambda: {"status": "missing_credentials"}
        stdout = io.StringIO()
        with mock.patch.object(sys, "argv", ["openai_backend.py", "doctor"]), contextlib.redirect_stdout(stdout):
            self.assertEqual(module.main(), 0)
        self.assertEqual(stdout.getvalue(), '{"status": "missing_credentials"}\n')

    def test_master_command_uses_loaded_key_and_structured_result(self) -> None:
        module = self._module()
        captured: dict = {}
        module.load_api_key = lambda: "cli-key"

        def render_master(
            reference: Path,
            output: Path,
            api_key: str,
            *,
            project_root: Path,
        ) -> dict:
            captured.update(
                reference=reference,
                output=output,
                api_key=api_key,
                project_root=project_root,
            )
            return {"status": "rendered", "output_path": str(output)}

        module.render_character_master = render_master
        stdout = io.StringIO()
        argv = ["openai_backend.py", "master", "--reference", "photo.jpg", "--output", "master.png"]
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout):
            self.assertEqual(module.main(), 0)
        self.assertEqual(
            captured,
            {
                "reference": Path("photo.jpg"),
                "output": Path("master.png"),
                "api_key": "cli-key",
                "project_root": Path.cwd(),
            },
        )
        self.assertNotIn("cli-key", stdout.getvalue())
        self.assertEqual(json.loads(stdout.getvalue())["status"], "rendered")

    def test_master_command_returns_safe_structured_error(self) -> None:
        module = self._module()
        module.load_api_key = lambda: TEST_ERROR_DETAIL
        module.render_character_master = mock.Mock(side_effect=ValidationError(TEST_ERROR_DETAIL))
        stdout = io.StringIO()
        argv = ["openai_backend.py", "master", "--reference", "photo.jpg", "--output", "master.png"]
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout):
            self.assertEqual(module.main(), 1)
        self.assertEqual(json.loads(stdout.getvalue()), {"status": "failed", "error": "render_error"})
        self.assertNotIn(TEST_ERROR_DETAIL, stdout.getvalue())

    def test_render_command_passes_current_project_root(self) -> None:
        module = self._module()
        captured: dict = {}
        module.load_api_key = lambda: "cli-key"

        def render(
            request: Path,
            output_dir: Path,
            api_key: str,
            *,
            project_root: Path,
        ) -> dict:
            captured.update(
                request=request,
                output_dir=output_dir,
                api_key=api_key,
                project_root=project_root,
            )
            return {"status": "complete", "images": []}

        module.render_request = render
        stdout = io.StringIO()
        argv = [
            "openai_backend.py",
            "render",
            "--request",
            "render-request.json",
            "--output-dir",
            "output",
        ]
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout):
            self.assertEqual(module.main(), 0)
        self.assertEqual(
            captured,
            {
                "request": Path("render-request.json"),
                "output_dir": Path("output"),
                "api_key": "cli-key",
                "project_root": Path.cwd(),
            },
        )
        self.assertNotIn("cli-key", stdout.getvalue())

    def test_master_and_render_commands_preserve_unsupported_platform_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "owner.png"
            reference.write_bytes(b"\x89PNG\r\n\x1a\nreference")
            prompt = root / "prompts" / "one.md"
            prompt.parent.mkdir()
            prompt.write_text("Prompt", encoding="utf-8")
            request = root / "render-request.json"
            request.write_text(
                json.dumps(
                    {
                        "schema": "render-request/v1",
                        "title": "test",
                        "template_id": "test",
                        "images": [
                            {
                                "id": "one",
                                "prompt_path": "prompts/one.md",
                                "output_path": "images/one.png",
                                "canvas": "1:1",
                                "width": 1024,
                                "height": 1024,
                                "reference_images": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            commands = (
                [
                    "openai_backend.py",
                    "master",
                    "--reference",
                    str(reference),
                    "--output",
                    str(root / "master.png"),
                ],
                [
                    "openai_backend.py",
                    "render",
                    "--request",
                    str(request),
                    "--output-dir",
                    str(root / "output"),
                ],
            )
            for argv in commands:
                with self.subTest(command=argv[1]):
                    module = self._module()
                    module.load_api_key = lambda: TEST_ERROR_DETAIL
                    stdout = io.StringIO()
                    with mock.patch.object(
                        openai_direct,
                        "_secure_output_supported",
                        return_value=False,
                    ), mock.patch.object(
                        sys, "argv", argv
                    ), contextlib.redirect_stdout(stdout):
                        self.assertEqual(module.main(), 2)
                    self.assertEqual(
                        json.loads(stdout.getvalue()),
                        {"status": "unsupported_platform"},
                    )
                    self.assertNotIn(TEST_ERROR_DETAIL, stdout.getvalue())


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import base64
import copy
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.backends import (  # noqa: E402
    finalize_host_render,
    prepare_backend,
    render_openai_direct,
)
from ip_pic.compiler import compile_request  # noqa: E402
from ip_pic.errors import IPPicError  # noqa: E402

from tests.test_selection_and_compiler import article_brief  # noqa: E402


def _image_base64(
    size: tuple[int, int] = (16, 16),
    *,
    image_format: str = "PNG",
) -> str:
    data = io.BytesIO()
    Image.new("RGB", size, "#F7F2E9").save(data, format=image_format)
    return base64.b64encode(data.getvalue()).decode("ascii")


class _FakeImages:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.opened_images: list[object] = []
        self.failures_remaining = 0
        self.failure = RuntimeError("provider failure with private detail")
        self.encoded_image: str | None = None

    def _response_image(self, kwargs: dict) -> str:
        if self.encoded_image is not None:
            return self.encoded_image
        width, height = (
            int(part)
            for part in str(kwargs["size"]).split("x", 1)
        )
        return _image_base64((width, height))

    def _maybe_fail(self) -> None:
        if self.failures_remaining:
            self.failures_remaining -= 1
            raise self.failure

    def generate(self, **kwargs):
        self.calls.append(("generate", kwargs))
        self._maybe_fail()
        return SimpleNamespace(
            data=[SimpleNamespace(b64_json=self._response_image(kwargs))],
            _request_id="req_test_123",
        )

    def edit(self, **kwargs):
        self.opened_images = list(kwargs["image"])
        recorded = dict(kwargs)
        recorded["image"] = [
            {
                "name": item.name,
                "closed_during_call": item.closed,
            }
            for item in kwargs["image"]
        ]
        self.calls.append(("edit", recorded))
        self._maybe_fail()
        return SimpleNamespace(
            data=[SimpleNamespace(b64_json=self._response_image(kwargs))],
            _request_id="req_edit_test_456",
        )


class _FakeClient:
    def __init__(self) -> None:
        self.images = _FakeImages()


class BackendContractTests(unittest.TestCase):
    def _compiled(self, output: Path) -> dict:
        return compile_request(
            ROOT,
            article_brief(),
            output,
            write=True,
        )["manifest"]

    def test_all_backend_preparation_preserves_upstream_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._compiled(root / "compiled")
            baseline = copy.deepcopy(manifest)
            fingerprints = set()
            for backend in (
                "prompt-only",
                "codex-image-tool",
                "host-ai-router",
                "openai-direct",
            ):
                with self.subTest(backend=backend):
                    request = prepare_backend(
                        manifest,
                        backend,
                        root / f"{backend}.json",
                    )
                    self.assertEqual(manifest, baseline)
                    self.assertEqual(
                        request["upstream"]["director_plan"],
                        baseline["director_plan"],
                    )
                    self.assertEqual(
                        request["upstream"]["visual_qa"],
                        baseline["visual_qa"],
                    )
                    fingerprints.add(request["upstream_fingerprint"])
            self.assertEqual(len(fingerprints), 1)

    def test_prompt_only_does_not_claim_render_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._compiled(root / "compiled")
            request = prepare_backend(
                manifest,
                "prompt-only",
                root / "prompt-only.json",
            )
            self.assertEqual(request["status"], "prompt_ready")
            self.assertFalse(request["rendered"])
            self.assertNotIn("credential", json.dumps(request).lower())

    def test_host_backends_require_real_file_before_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._compiled(root / "compiled")
            request_path = root / "codex-request.json"
            request = prepare_backend(
                manifest,
                "codex-image-tool",
                request_path,
            )
            self.assertEqual(request["status"], "awaiting_host")
            self.assertFalse(request["rendered"])
            with self.assertRaisesRegex(IPPicError, "不存在|does not exist"):
                finalize_host_render(
                    request_path,
                    Path(request["expected_output"]),
                    receipt_id="host-001",
                )

            output = Path(request["expected_output"])
            output.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (16, 16), "white").save(output)
            receipt_path = finalize_host_render(
                request_path,
                output,
                receipt_id="host-001",
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"], "ok")
            self.assertTrue(receipt["rendered"])
            self.assertEqual(receipt["backend"], "codex-image-tool")
            self.assertEqual(len(receipt["output_sha256"]), 64)

    def test_openai_direct_uses_official_image_api_and_writes_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._compiled(root / "compiled")
            fake = _FakeClient()
            receipt_path = render_openai_direct(
                manifest,
                root / "openai-request.json",
                client=fake,
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

            method, call = fake.images.calls[0]
            self.assertEqual(method, "generate")
            self.assertEqual(call["model"], "gpt-image-2")
            self.assertEqual(call["size"], manifest["size"])
            self.assertEqual(call["output_format"], "png")
            self.assertIn(
                "一次生成图文融合",
                call["prompt"],
            )
            self.assertEqual(receipt["status"], "ok")
            self.assertTrue(Path(receipt["output_image"]).is_file())
            self.assertEqual(receipt["request_id"], "req_test_123")
            self.assertEqual(receipt["model"], "gpt-image-2")
            self.assertEqual(receipt["quality"], "high")
            self.assertEqual(receipt["operation"], "generate")

    def test_openai_direct_uses_edits_api_for_character_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reference = root / "ato-reference.png"
            style_reference = root / "style-reference.png"
            Image.new("RGB", (32, 32), "#F7F2E9").save(reference)
            Image.new("RGB", (32, 32), "#4B79A6").save(style_reference)
            brief = article_brief()
            brief["visual"]["authorized_assets"] = [
                {
                    "id": "ato-identity",
                    "path": str(reference),
                    "purpose": "identity",
                    "ownership": "project-original-tutorial",
                    "required": True,
                },
                {
                    "id": "approved-style",
                    "path": str(style_reference),
                    "purpose": "style",
                    "ownership": "licensed",
                    "required": False,
                },
            ]
            brief["visual"]["reference_strategy"] = "native_multi_reference"
            manifest = compile_request(
                ROOT,
                brief,
                root / "compiled",
                write=True,
            )["manifest"]
            fake = _FakeClient()

            receipt_path = render_openai_direct(
                manifest,
                root / "openai-edit-request.json",
                client=fake,
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

            method, call = fake.images.calls[0]
            self.assertEqual(method, "edit")
            self.assertEqual(call["model"], "gpt-image-2")
            self.assertEqual(call["size"], manifest["size"])
            self.assertEqual(call["output_format"], "png")
            self.assertEqual(
                call["image"],
                [
                    {
                        "name": str(reference.resolve()),
                        "closed_during_call": False,
                    },
                    {
                        "name": str(style_reference.resolve()),
                        "closed_during_call": False,
                    },
                ],
            )
            self.assertEqual(receipt["request_id"], "req_edit_test_456")
            self.assertTrue(Path(receipt["output_image"]).is_file())
            self.assertEqual(receipt["model"], "gpt-image-2")
            self.assertEqual(receipt["quality"], "high")
            self.assertEqual(receipt["operation"], "edit")
            self.assertEqual(len(receipt["input_assets"]), 2)
            self.assertTrue(
                all(
                    len(item["sha256"]) == 64
                    for item in receipt["input_assets"]
                )
            )
            self.assertTrue(all(item.closed for item in fake.images.opened_images))

    def test_openai_direct_fails_closed_when_selected_reference_disappears(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reference = root / "character-reference.png"
            Image.new("RGB", (32, 32), "#F7F2E9").save(reference)
            brief = article_brief()
            brief["visual"]["authorized_assets"] = [
                {
                    "id": "character",
                    "path": str(reference),
                    "purpose": "identity",
                    "ownership": "user-owned",
                    "required": True,
                }
            ]
            manifest = compile_request(
                ROOT,
                brief,
                root / "compiled",
                write=True,
            )["manifest"]
            reference.unlink()
            fake = _FakeClient()

            with self.assertRaisesRegex(IPPicError, "does not exist"):
                render_openai_direct(
                    manifest,
                    root / "openai-missing-reference-request.json",
                    client=fake,
                )

            self.assertEqual(fake.images.calls, [])
            self.assertFalse(
                (root / "openai-missing-reference-request.receipt.json").exists()
            )

    def test_openai_direct_closes_reference_files_after_provider_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reference = root / "character-reference.png"
            Image.new("RGB", (32, 32), "#F7F2E9").save(reference)
            brief = article_brief()
            brief["visual"]["authorized_assets"] = [
                {
                    "id": "character",
                    "path": str(reference),
                    "purpose": "identity",
                    "ownership": "user-owned",
                    "required": True,
                }
            ]
            manifest = compile_request(
                ROOT,
                brief,
                root / "compiled",
                write=True,
            )["manifest"]
            fake = _FakeClient()
            fake.images.failures_remaining = 1

            with self.assertRaisesRegex(IPPicError, "edit request failed"):
                render_openai_direct(
                    manifest,
                    root / "openai-edit-failure-request.json",
                    client=fake,
                )

            self.assertTrue(fake.images.opened_images)
            self.assertTrue(all(item.closed for item in fake.images.opened_images))

    def test_openai_direct_rejects_tampered_reference_metadata_and_files(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._compiled(root / "compiled")
            valid_image = root / "valid.png"
            Image.new("RGB", (32, 32), "#F7F2E9").save(valid_image)
            symlink = root / "linked.png"
            symlink.symlink_to(valid_image)
            text_file = root / "not-an-image.png"
            text_file.write_text("not an image", encoding="utf-8")

            cases = (
                (
                    "unknown ownership",
                    {
                        "path": str(valid_image),
                        "purpose": "identity",
                        "ownership": "unknown",
                        "required": True,
                    },
                    "ownership",
                ),
                (
                    "symlink",
                    {
                        "path": str(symlink),
                        "purpose": "identity",
                        "ownership": "user-owned",
                        "required": True,
                    },
                    "symbolic link",
                ),
                (
                    "non-image",
                    {
                        "path": str(text_file),
                        "purpose": "identity",
                        "ownership": "user-owned",
                        "required": True,
                    },
                    "valid image",
                ),
            )
            for index, (name, asset, error) in enumerate(cases):
                with self.subTest(case=name):
                    candidate = copy.deepcopy(manifest)
                    candidate["render_handoff"]["assets"] = [asset]
                    fake = _FakeClient()
                    with self.assertRaisesRegex(IPPicError, error):
                        render_openai_direct(
                            candidate,
                            root / f"invalid-{index}.json",
                            client=fake,
                        )
                    self.assertEqual(fake.images.calls, [])

    def test_openai_direct_can_retry_same_request_after_provider_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._compiled(root / "compiled")
            fake = _FakeClient()
            fake.images.failures_remaining = 1
            request_path = root / "openai-retry-request.json"

            with self.assertRaisesRegex(
                IPPicError,
                "no success receipt was written",
            ) as failure:
                render_openai_direct(
                    manifest,
                    request_path,
                    client=fake,
                )

            self.assertNotIn("private detail", str(failure.exception))
            self.assertTrue(request_path.is_file())
            self.assertFalse(
                (root / "openai-retry-request.receipt.json").exists()
            )

            receipt_path = render_openai_direct(
                manifest,
                request_path,
                client=fake,
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"], "ok")
            self.assertEqual(
                [method for method, _ in fake.images.calls],
                ["generate", "generate"],
            )

    def test_openai_direct_preflights_existing_receipt_before_provider_call(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._compiled(root / "compiled")
            fake = _FakeClient()
            request_path = root / "openai-existing-receipt.json"
            receipt_path = root / "openai-existing-receipt.receipt.json"
            receipt_path.write_text("{}\n", encoding="utf-8")

            with self.assertRaisesRegex(IPPicError, "backend receipt"):
                render_openai_direct(
                    manifest,
                    request_path,
                    client=fake,
                )

            self.assertEqual(fake.images.calls, [])
            self.assertFalse(request_path.exists())
            self.assertFalse(
                Path(manifest["expected_outputs"]["raw_image"]).exists()
            )

    def test_openai_direct_rejects_broken_request_and_output_symlinks_before_call(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base_manifest = self._compiled(root / "compiled")

            output_link = root / "broken-output.png"
            output_link.symlink_to(root / "redirected-output.png")
            output_manifest = copy.deepcopy(base_manifest)
            output_manifest["expected_outputs"]["raw_image"] = str(output_link)
            output_manifest["expected_outputs"]["final_image"] = str(output_link)
            fake_output = _FakeClient()
            with self.assertRaisesRegex(IPPicError, "symbolic link"):
                render_openai_direct(
                    output_manifest,
                    root / "output-link-request.json",
                    client=fake_output,
                )
            self.assertEqual(fake_output.images.calls, [])
            self.assertFalse((root / "redirected-output.png").exists())

            request_link = root / "broken-request.json"
            request_link.symlink_to(root / "redirected-request.json")
            fake_request = _FakeClient()
            with self.assertRaisesRegex(IPPicError, "unsafe backend request"):
                render_openai_direct(
                    base_manifest,
                    request_link,
                    client=fake_request,
                )
            self.assertEqual(fake_request.images.calls, [])
            self.assertFalse((root / "redirected-request.json").exists())

    def test_openai_direct_rejects_decoded_non_image_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._compiled(root / "compiled")
            fake = _FakeClient()
            fake.images.encoded_image = base64.b64encode(
                b"decoded but not an image"
            ).decode("ascii")

            with self.assertRaisesRegex(IPPicError, "valid image"):
                render_openai_direct(
                    manifest,
                    root / "openai-invalid-image-request.json",
                    client=fake,
                )

            self.assertFalse(
                Path(manifest["expected_outputs"]["raw_image"]).exists()
            )

    def test_openai_direct_rejects_wrong_output_format_and_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cases = (
                (
                    "wrong format",
                    _image_base64((1536, 864), image_format="JPEG"),
                    "PNG",
                ),
                (
                    "wrong dimensions",
                    _image_base64((16, 16)),
                    "dimensions",
                ),
            )
            for index, (name, encoded, error) in enumerate(cases):
                with self.subTest(case=name):
                    manifest = self._compiled(root / f"compiled-{index}")
                    fake = _FakeClient()
                    fake.images.encoded_image = encoded
                    with self.assertRaisesRegex(IPPicError, error):
                        render_openai_direct(
                            manifest,
                            root / f"invalid-output-{index}.json",
                            client=fake,
                        )
                    self.assertFalse(
                        Path(manifest["expected_outputs"]["raw_image"]).exists()
                    )

    def test_openai_retry_identity_binds_model_quality_and_reference_bytes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reference = root / "character-reference.png"
            Image.new("RGB", (32, 32), "#F7F2E9").save(reference)
            brief = article_brief()
            brief["visual"]["authorized_assets"] = [
                {
                    "id": "character",
                    "path": str(reference),
                    "purpose": "identity",
                    "ownership": "user-owned",
                    "required": True,
                }
            ]
            manifest = compile_request(
                ROOT,
                brief,
                root / "compiled",
                write=True,
            )["manifest"]
            request_path = root / "identity-bound-request.json"
            first = _FakeClient()
            first.images.failures_remaining = 1
            with self.assertRaises(IPPicError):
                render_openai_direct(
                    manifest,
                    request_path,
                    client=first,
                    quality="low",
                )

            changed_runtime = _FakeClient()
            with self.assertRaisesRegex(IPPicError, "handoff has changed"):
                render_openai_direct(
                    manifest,
                    request_path,
                    client=changed_runtime,
                    model="gpt-image-1.5",
                    quality="high",
                )
            self.assertEqual(changed_runtime.images.calls, [])

            Image.new("RGB", (32, 32), "#4B79A6").save(reference)
            changed_asset = _FakeClient()
            with self.assertRaisesRegex(IPPicError, "handoff has changed"):
                render_openai_direct(
                    manifest,
                    request_path,
                    client=changed_asset,
                    quality="low",
                )
            self.assertEqual(changed_asset.images.calls, [])

    def test_openai_optional_dependency_supports_gpt_image_2_contract(
        self,
    ) -> None:
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('openai = ["openai>=2.35.1"]', project)

    def test_openai_direct_fails_closed_without_external_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._compiled(root / "compiled")
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(IPPicError, "OPENAI_API_KEY"):
                    render_openai_direct(
                        manifest,
                        root / "openai-request.json",
                    )

    def test_openai_direct_pins_official_endpoint_and_redacts_secret(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._compiled(root / "compiled")
            created: list[dict] = []
            fake = _FakeClient()

            def create_client(**kwargs):
                created.append(kwargs)
                return fake

            fake_module = SimpleNamespace(OpenAI=create_client)
            test_secret = "test-api-token-for-redaction"
            with (
                patch.dict(os.environ, {"OPENAI_API_KEY": test_secret}, clear=True),
                patch.dict(sys.modules, {"openai": fake_module}),
            ):
                receipt_path = render_openai_direct(
                    manifest,
                    root / "openai-request.json",
                )

            self.assertEqual(
                created,
                [
                    {
                        "api_key": test_secret,
                        "base_url": "https://api.openai.com/v1",
                    }
                ],
            )
            public_artifacts = (
                (root / "openai-request.json").read_text(encoding="utf-8")
                + receipt_path.read_text(encoding="utf-8")
            )
            self.assertNotIn(test_secret, public_artifacts)


if __name__ == "__main__":
    unittest.main()

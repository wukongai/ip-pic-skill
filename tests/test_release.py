from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from _support import ROOT
import ip_pic
from ip_pic.release import validate_release


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
    return (
        struct.pack(">I", len(payload))
        + chunk_type
        + payload
        + struct.pack(">I", checksum)
    )


def _minimal_png(extra_chunk: bytes | None = None) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = _png_chunk(
        b"IHDR",
        struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0),
    )
    middle = b""
    if extra_chunk is not None:
        middle = _png_chunk(extra_chunk, b"metadata")
    idat = _png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
    iend = _png_chunk(b"IEND", b"")
    return signature + ihdr + middle + idat + iend


def _png_from_chunks(chunks: list[tuple[bytes, bytes]]) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"".join(
        _png_chunk(chunk_type, payload)
        for chunk_type, payload in chunks
    )


def _ihdr_payload() -> bytes:
    return struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)


def _idat_payload() -> bytes:
    return zlib.compress(b"\x00\x00\x00\x00")


class ReleaseValidationTests(unittest.TestCase):
    def test_public_package_version_matches_rc5(self) -> None:
        self.assertEqual(ip_pic.__version__, "0.1.0rc5")

    def test_rc5_release_metadata_has_consistent_versions_and_domains(self) -> None:
        manifest = json.loads(
            (ROOT / "public-release-manifest.json").read_text(encoding="utf-8")
        )

        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "0.1.0-rc.5")
        self.assertIn('version = "0.1.0rc5"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertIn("version: 0.1.0-rc.5", (ROOT / "skill.contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "0.1.0-rc.5")
        self.assertEqual(
            set(manifest["allowed_domains"]),
            {
                "api.openai.com",
                "developers.openai.com",
                "github.com",
                "json-schema.org",
                "platform.openai.com",
            },
        )

    def test_manifest_is_the_exact_public_release_tree(self) -> None:
        manifest = json.loads(
            (ROOT / "public-release-manifest.json").read_text(encoding="utf-8")
        )
        actual = {
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file()
            and ".git" not in path.relative_to(ROOT).parts
            and "__pycache__" not in path.relative_to(ROOT).parts
            and path.suffix != ".pyc"
        }

        self.assertEqual(set(manifest["files"]), actual)

    def test_current_release_tree_passes(self) -> None:
        result = validate_release(
            ROOT,
            ROOT / "public-release-manifest.json",
        )
        self.assertEqual(result["status"], "pass", result["findings"])

    def test_ci_compiles_an_existing_tutorial_profile(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertNotIn("examples/ip-profile.example.json", workflow)
        profile = "examples/characters/wukong/profile.json"
        self.assertIn(profile, workflow)
        self.assertTrue((ROOT / profile).is_file())

    def test_unlisted_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "allowed.txt").write_text("clean", encoding="utf-8")
            (root / "extra.txt").write_text("clean", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "public-release-files/v1",
                        "allowed_domains": [],
                        "files": ["allowed.txt", "manifest.json"],
                    }
                ),
                encoding="utf-8",
            )
            result = validate_release(root, manifest)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(
            any("not allowlisted" in item for item in result["findings"])
        )

    def test_git_metadata_is_not_release_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "allowed.txt").write_text("clean", encoding="utf-8")
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text(
                "[core]\nrepositoryformatversion = 0\n",
                encoding="utf-8",
            )
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "public-release-files/v1",
                        "allowed_domains": [],
                        "files": ["allowed.txt", "manifest.json"],
                    }
                ),
                encoding="utf-8",
            )
            result = validate_release(root, manifest)
        self.assertEqual(result["status"], "pass", result["findings"])

    def test_tutorial_pngs_are_exactly_allowlisted_and_hashed(self) -> None:
        manifest = json.loads(
            (ROOT / "public-release-manifest.json").read_text(encoding="utf-8")
        )
        expected = {
            "examples/characters/ato/preview.png",
            "examples/characters/ato/source-synthetic-photo.png",
            "examples/characters/wukong/preview.png",
            "examples/characters/moon-rabbit/preview.png",
        }

        self.assertEqual(set(manifest["binary_assets"]), expected)
        for relative in expected:
            path = ROOT / relative
            payload = path.read_bytes()
            self.assertEqual(payload[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(
                hashlib.sha256(payload).hexdigest(),
                manifest["binary_assets"][relative],
            )

    def test_unlisted_binary_image_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sample.png").write_bytes(_minimal_png())
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "public-release-files/v1",
                        "allowed_domains": [],
                        "files": ["sample.png", "manifest.json"],
                    }
                ),
                encoding="utf-8",
            )
            result = validate_release(root, manifest)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(
            any("binary asset is not allowlisted" in item for item in result["findings"])
        )

    def test_every_unlisted_non_text_file_fails_closed(self) -> None:
        cases = {
            "sample.bmp": b"BM" + b"\x00" * 20,
            "sample.tiff": b"II" + b"\x00" * 20,
            "sample.avif": b"\x00\x00\x00\x18ftypavif",
            "binary-without-extension": b"\x00\xff\x01\x02",
        }
        for filename, payload in cases.items():
            with self.subTest(filename=filename):
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    (root / filename).write_bytes(payload)
                    manifest = root / "manifest.json"
                    manifest.write_text(
                        json.dumps(
                            {
                                "schema": "public-release-files/v1",
                                "allowed_domains": [],
                                "files": [filename, "manifest.json"],
                            }
                        ),
                        encoding="utf-8",
                    )
                    result = validate_release(root, manifest)
                self.assertEqual(result["status"], "fail")
                self.assertTrue(
                    any(
                        "binary asset is not allowlisted" in item
                        for item in result["findings"]
                    ),
                    result["findings"],
                )

    def test_binary_allowlist_accepts_only_png_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = b"BM" + b"\x00" * 20
            (root / "sample.bmp").write_bytes(payload)
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "public-release-files/v1",
                        "allowed_domains": [],
                        "files": ["sample.bmp", "manifest.json"],
                        "binary_assets": {
                            "sample.bmp": hashlib.sha256(payload).hexdigest()
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = validate_release(root, manifest)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(
            any(
                "only exact allowlisted PNG assets are allowed" in item
                for item in result["findings"]
            ),
            result["findings"],
        )

    def test_allowlisted_png_with_matching_hash_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = _minimal_png()
            (root / "sample.png").write_bytes(payload)
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "public-release-files/v1",
                        "allowed_domains": [],
                        "files": ["sample.png", "manifest.json"],
                        "binary_assets": {
                            "sample.png": hashlib.sha256(payload).hexdigest()
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = validate_release(root, manifest)
        self.assertEqual(result["status"], "pass", result["findings"])

    def test_png_hash_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sample.png").write_bytes(_minimal_png())
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "public-release-files/v1",
                        "allowed_domains": [],
                        "files": ["sample.png", "manifest.json"],
                        "binary_assets": {"sample.png": "0" * 64},
                    }
                ),
                encoding="utf-8",
            )
            result = validate_release(root, manifest)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("SHA-256 mismatch" in item for item in result["findings"]))

    def test_png_metadata_and_unknown_ancillary_chunks_fail(self) -> None:
        for chunk_type in (b"eXIf", b"tEXt", b"tIME", b"caBX"):
            with self.subTest(chunk_type=chunk_type.decode("ascii")):
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    payload = _minimal_png(extra_chunk=chunk_type)
                    (root / "sample.png").write_bytes(payload)
                    manifest = root / "manifest.json"
                    manifest.write_text(
                        json.dumps(
                            {
                                "schema": "public-release-files/v1",
                                "allowed_domains": [],
                                "files": ["sample.png", "manifest.json"],
                                "binary_assets": {
                                    "sample.png": hashlib.sha256(payload).hexdigest()
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    result = validate_release(root, manifest)
                self.assertEqual(result["status"], "fail")
                self.assertTrue(
                    any("PNG chunk is not allowed" in item for item in result["findings"]),
                    result["findings"],
                )

    def test_png_structural_lengths_and_chunk_order_fail_closed(self) -> None:
        idat = _idat_payload()
        gamma = struct.pack(">I", 45455)
        cases = {
            "bad-ihdr-length": [
                (b"IHDR", _ihdr_payload()[:-1]),
                (b"IDAT", idat),
                (b"IEND", b""),
            ],
            "bad-iend-length": [
                (b"IHDR", _ihdr_payload()),
                (b"IDAT", idat),
                (b"IEND", b"x"),
            ],
            "duplicate-plte": [
                (b"IHDR", _ihdr_payload()),
                (b"PLTE", b"\x00\x00\x00"),
                (b"PLTE", b"\xff\xff\xff"),
                (b"IDAT", idat),
                (b"IEND", b""),
            ],
            "plte-after-idat": [
                (b"IHDR", _ihdr_payload()),
                (b"IDAT", idat),
                (b"PLTE", b"\x00\x00\x00"),
                (b"IEND", b""),
            ],
            "discontinuous-idat": [
                (b"IHDR", _ihdr_payload()),
                (b"IDAT", idat),
                (b"gAMA", gamma),
                (b"IDAT", idat),
                (b"IEND", b""),
            ],
        }
        for name, chunks in cases.items():
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    payload = _png_from_chunks(chunks)
                    (root / "sample.png").write_bytes(payload)
                    manifest = root / "manifest.json"
                    manifest.write_text(
                        json.dumps(
                            {
                                "schema": "public-release-files/v1",
                                "allowed_domains": [],
                                "files": ["sample.png", "manifest.json"],
                                "binary_assets": {
                                    "sample.png": hashlib.sha256(payload).hexdigest()
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    result = validate_release(root, manifest)
                self.assertEqual(result["status"], "fail", result["findings"])
                self.assertTrue(
                    any("PNG structure is invalid" in item for item in result["findings"]),
                    result["findings"],
                )

    def test_svg_is_scanned_as_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sample.svg").write_text(
                "<svg><text>/" + "Users" + "/private-project</text></svg>",
                encoding="utf-8",
            )
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "public-release-files/v1",
                        "allowed_domains": [],
                        "files": ["sample.svg", "manifest.json"],
                    }
                ),
                encoding="utf-8",
            )
            result = validate_release(root, manifest)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(
            any("private pattern" in item for item in result["findings"])
        )

    def test_source_identifier_assignment_is_not_a_credential(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "safe.py").write_text(
                'api_key = os.environ.get("OPENAI_API_KEY")\n'
                'backend = "ai-router"\n',
                encoding="utf-8",
            )
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "public-release-files/v1",
                        "allowed_domains": [],
                        "files": ["safe.py", "manifest.json"],
                    }
                ),
                encoding="utf-8",
            )
            result = validate_release(root, manifest)
        self.assertEqual(result["status"], "pass", result["findings"])

    def test_literal_credential_value_still_fails(self) -> None:
        field = "api_" + "key"
        value = ("a" * 21) + "1"
        cases = {
            "unsafe.json": json.dumps({field: value}) + "\n",
            "unsafe.py": field + " = " + repr(value) + "\n",
        }
        for filename, text in cases.items():
            with self.subTest(filename=filename):
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    (root / filename).write_text(text, encoding="utf-8")
                    manifest = root / "manifest.json"
                    manifest.write_text(
                        json.dumps(
                            {
                                "schema": "public-release-files/v1",
                                "allowed_domains": [],
                                "files": [filename, "manifest.json"],
                            }
                        ),
                        encoding="utf-8",
                    )
                    result = validate_release(root, manifest)
                self.assertEqual(result["status"], "fail")
                self.assertTrue(
                    any(
                        "credential-like value" in item
                        for item in result["findings"]
                    ),
                    result["findings"],
                )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import ROOT
from custom_ip_illustration.release import validate_release


class ReleaseValidationTests(unittest.TestCase):
    def test_current_release_tree_passes(self) -> None:
        result = validate_release(
            ROOT,
            ROOT / "public-release-manifest.json",
        )
        self.assertEqual(result["status"], "pass", result["findings"])

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

    def test_binary_image_fails_v0_1_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sample.png").write_bytes(b"not-an-image")
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
            any("binary image assets" in item for item in result["findings"])
        )


if __name__ == "__main__":
    unittest.main()

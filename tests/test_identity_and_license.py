from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.profiles import ProfileError, load_character_profile  # noqa: E402


PRIVATE_TOKENS = (
    "艾" + "笑",
    "aix" + "iao",
    "/Users/" + "aim5",
    "/private/tmp/" + "ip-pic-style-parity-20260731",
)
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".toml", ".txt"}


class IdentityAndLicenseTests(unittest.TestCase):
    def test_article_example_uses_the_packaged_ato_profile_exactly(self) -> None:
        example = json.loads(
            (ROOT / "examples" / "article-brief.json").read_text(
                encoding="utf-8"
            )
        )
        packaged = json.loads(
            (
                ROOT
                / "profiles"
                / "characters"
                / "ato"
                / "profile.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(example["visual"]["ip_profile"], packaged)

    def test_tutorial_profiles_are_original_and_complete(self) -> None:
        for character_id in ("ato", "wukong", "moon-rabbit"):
            with self.subTest(character_id=character_id):
                profile = load_character_profile(
                    ROOT / "profiles" / "characters" / character_id / "profile.json"
                )
                self.assertEqual(
                    profile["ownership"]["status"],
                    "project-original-tutorial",
                )
                self.assertTrue(profile["ownership"]["basis"])
                self.assertTrue(profile["identity"]["name"])
                self.assertTrue(profile["identity"]["description"])
                self.assertTrue(profile["appearance"]["description"])
                self.assertTrue(profile["personality"])
                self.assertGreaterEqual(len(profile["continuity_anchors"]), 3)

    def test_profile_without_rights_fails_closed(self) -> None:
        invalid = {
            "schema_version": "ip-character-profile/v1",
            "ownership": {"status": "unknown", "basis": ""},
            "identity": {"name": "Unknown", "description": "Unknown"},
            "appearance": {"description": "Unknown"},
            "personality": ["neutral"],
            "continuity_anchors": ["one", "two", "three"],
        }
        with self.assertRaisesRegex(ProfileError, "ownership"):
            load_character_profile(invalid)

    def test_upstream_mit_attribution_is_preserved(self) -> None:
        license_text = (ROOT / "UPSTREAM-LICENSE.txt").read_text(encoding="utf-8")
        notice = (ROOT / "NOTICE.md").read_text(encoding="utf-8")
        lock = json.loads((ROOT / "upstream.lock.json").read_text(encoding="utf-8"))

        self.assertIn("MIT License", license_text)
        self.assertIn("Copyright (c) 2026 Ian", license_text)
        self.assertIn("Ian Xiaohei Illustrations", notice)
        self.assertIn("does not redistribute", notice)
        self.assertEqual(
            lock["upstream"]["commit"],
            "91b560849e8f883922cc2fa8a358a668caa94105",
        )

    def test_repository_contains_no_private_identity_or_paths(self) -> None:
        findings: list[str] = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in PRIVATE_TOKENS:
                if token.casefold() in text.casefold():
                    findings.append(f"{path.relative_to(ROOT)}:{token}")
        self.assertEqual(findings, [])

    def test_no_character_reference_binaries_are_distributed(self) -> None:
        binary_paths = [
            path.relative_to(ROOT)
            for path in ROOT.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        ]
        self.assertEqual(binary_paths, [])


if __name__ == "__main__":
    unittest.main()

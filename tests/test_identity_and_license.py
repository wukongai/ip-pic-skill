from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.profiles import ProfileError, load_character_profile  # noqa: E402


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

    def test_public_tree_has_no_private_extraction_helper(self) -> None:
        self.assertFalse((ROOT / "scripts" / "extract_public_slice.py").exists())

    def test_python_sources_do_not_obfuscate_literals_with_concatenation(self) -> None:
        findings: list[str] = []
        for path in ROOT.rglob("*.py"):
            if ".git" in path.parts or "build" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Add):
                    continue
                if (
                    isinstance(node.left, ast.Constant)
                    and isinstance(node.left.value, str)
                    and isinstance(node.right, ast.Constant)
                    and isinstance(node.right.value, str)
                ):
                    findings.append(f"{path.relative_to(ROOT)}:{node.lineno}")
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

    def test_public_rules_do_not_hardcode_private_character_traits_or_preferences(
        self,
    ) -> None:
        forbidden_fragments = (
            "扎起的长发",
            "窄矩形眼镜",
            "窄眼镜",
            "品牌服装与饰品",
            "个人推荐",
            "你的个人默认",
            "腰粗",
            "短腿",
            "九分裤",
            "九分通勤裤",
            "收腿裤",
            "小直筒裤",
            "紧身铅笔裤",
            "裤脚露出整个鞋面",
            "夸张蜂腰",
            "腰线自然收窄",
            "腿部修长",
            "裤长基本覆盖鞋面",
        )
        findings: list[str] = []
        for folder in ("references", "templates"):
            for path in (ROOT / folder).rglob("*"):
                if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_fragments:
                    if fragment in text:
                        findings.append(
                            f"{path.relative_to(ROOT)} contains {fragment!r}"
                        )
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from _support import ROOT


class IdentityRenameTests(unittest.TestCase):
    def test_public_skill_uses_ip_pic_identity(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        agent = (ROOT / "agents/openai.yaml").read_text(encoding="utf-8")
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn("name: ip-pic", skill)
        self.assertIn("Use $ip-pic", agent)
        self.assertIn('name = "ip-pic"', project)

    def test_public_docs_use_new_repository(self) -> None:
        for name in ("README.md", "README.en.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("wukongai/ip-pic-skill", text)
            self.assertNotIn(
                "wukongai/custom-ip-illustration-skill",
                text,
            )

    def test_canonical_runtime_paths_use_ip_pic(self) -> None:
        contract = (ROOT / "skill.contract.yaml").read_text(encoding="utf-8")
        preferences = (
            ROOT / "src/ip_pic/preferences.py"
        ).read_text(encoding="utf-8")

        self.assertIn(".ip-pic/EXTEND.md", contract)
        self.assertIn('".ip-pic"', preferences)

    def test_no_unexplained_legacy_brand_in_public_files(self) -> None:
        allowed = {
            "README.md",
            "README.en.md",
            "src/ip_pic/openai_direct.py",
            "src/ip_pic/preferences.py",
            "tests/test_identity_rename.py",
            "tests/test_openai_direct.py",
            "tests/test_preferences.py",
        }
        violations = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            relative = path.relative_to(ROOT).as_posix()
            if relative in allowed or "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if (
                "custom-ip-illustration" in text
                or "custom_ip_illustration" in text
                or "Custom IP Illustration" in text
                or "CustomIPIllustration" in text
            ):
                violations.append(relative)
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()

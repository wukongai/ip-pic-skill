from __future__ import annotations

import json
import unittest

from _support import ROOT


class DocumentationContractTests(unittest.TestCase):
    def test_bilingual_readmes_have_install_and_tutorial_paths(self) -> None:
        chinese = (ROOT / "README.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")

        self.assertIn("[English](README.en.md)", chinese)
        self.assertIn("[简体中文](README.md)", english)
        for text in (chinese, english):
            self.assertIn(
                "npx skills add wukongai/custom-ip-illustration-skill",
                text,
            )
            self.assertIn("examples/ip-profile.example.json", text)
            self.assertIn(".custom-ip-illustration/ip-profile.json", text)
            self.assertIn(".custom-ip-illustration/", text)
            self.assertIn("compile_only", text)
            self.assertIn("Python 3.10+", text)

    def test_demo_is_opt_in_and_is_not_saved_as_user_profile(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        onboarding = (ROOT / "references/ip-onboarding.md").read_text(
            encoding="utf-8"
        )
        profile = json.loads(
            (ROOT / "examples/ip-profile.example.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertIn("用户明确选择教程", skill)
        self.assertIn("不得把示例资料保存为用户资料", skill)
        self.assertIn("不把示例 profile 写入用户项目", onboarding)
        self.assertIn("Git", onboarding)
        self.assertIn("云盘", onboarding)
        self.assertEqual(profile["ownership"]["status"], "licensed")
        self.assertEqual(profile["identity"]["name"], "Mira")
        self.assertIn("Human adult", profile["appearance"]["description"])

    def test_demo_svg_is_human_readable_and_allowlisted(self) -> None:
        svg = (ROOT / "examples/demo-character.svg").read_text(
            encoding="utf-8"
        )
        manifest = json.loads(
            (ROOT / "public-release-manifest.json").read_text(encoding="utf-8")
        )

        self.assertIn("<title", svg)
        self.assertIn("<desc", svg)
        self.assertIn(
            "examples/demo-character.svg",
            manifest["files"],
        )

    def test_installed_script_path_and_output_contract_are_unambiguous(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        interface = (ROOT / "agents/openai.yaml").read_text(encoding="utf-8")
        brief = json.loads(
            (ROOT / "examples/brief.example.json").read_text(encoding="utf-8")
        )
        brief_schema = json.loads(
            (ROOT / "schemas/ip-illustration-brief.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertIn("<skill-root>/scripts/compile_ip_illustration.py", skill)
        self.assertIn('display_name: "Custom IP Illustration"', interface)
        self.assertNotIn("output_dir", brief)
        self.assertNotIn("output_dir", brief_schema["properties"])


if __name__ == "__main__":
    unittest.main()

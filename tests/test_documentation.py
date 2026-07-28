from __future__ import annotations

import json
import subprocess
import sys
import unittest

from _support import ROOT
from ip_pic.models import validate_profile

RETIRED_TUTORIAL_NAME = "Mi" + "ra"


class DocumentationContractTests(unittest.TestCase):
    def test_bilingual_readmes_follow_the_same_four_step_user_journey(self) -> None:
        chinese = (ROOT / "README.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")

        self.assertIn("[English](README.en.md)", chinese)
        self.assertIn("[简体中文](README.md)", english)
        journeys = (
            (
                chinese,
                (
                    "## 1. 安装 Skill",
                    "## 2. 选择出图方式",
                    "## 3. 建立你的卡通 IP",
                    "## 4. 把文章交给 Skill",
                ),
                "## 安装或首次运行失败时",
            ),
            (
                english,
                (
                    "## 1. Install the Skill",
                    "## 2. Choose how to render",
                    "## 3. Create your cartoon IP",
                    "## 4. Give the Skill your article",
                ),
                "## If installation or the first run fails",
            ),
        )
        for text, steps, troubleshooting_heading in journeys:
            self.assertIn(
                "npx skills add wukongai/ip-pic-skill",
                text,
            )
            for step in steps:
                self.assertIn(step, text)
            self.assertIn(troubleshooting_heading, text)
            positions = [text.index(step) for step in steps]
            self.assertEqual(positions, sorted(positions))
            main_path = text[: text.index(troubleshooting_heading)]
            self.assertNotIn("Python 3.10", main_path)
            self.assertNotIn("Node.js", main_path)
            self.assertIn(".ip-pic/ip-profile.json", text)
            self.assertIn("compile_only", text)
            self.assertNotIn("\\\n", text)

    def test_bilingual_readmes_explain_all_rendering_choices_before_api_setup(
        self,
    ) -> None:
        chinese = (ROOT / "README.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")

        expectations = (
            (
                chinese,
                (
                    "Codex Image Tool / 内置 `imagegen`",
                    "直接 OpenAI API",
                    "已有 `ai-router`",
                    "`prompt-only`",
                ),
                "### 直接 OpenAI API 的安全配置",
                "不会生成图片",
            ),
            (
                english,
                (
                    "Codex Image Tool / built-in `imagegen`",
                    "Direct OpenAI API",
                    "Existing `ai-router`",
                    "`prompt-only`",
                ),
                "### Safe direct OpenAI API setup",
                "does not create image files",
            ),
        )
        for text, choices, api_heading, prompt_only_claim in expectations:
            for choice in choices:
                self.assertIn(choice, text)
            self.assertIn(api_heading, text)
            choice_positions = [text.index(choice) for choice in choices]
            self.assertEqual(choice_positions, sorted(choice_positions))
            self.assertLess(max(choice_positions), text.index(api_heading))
            self.assertIn("GPT Image 2", text)
            self.assertIn("OPENAI_API_KEY", text)
            self.assertIn("~/.ip-pic/.env", text)
            self.assertIn(prompt_only_claim, text)
            self.assertNotIn("Nano Banana", text)

    def test_bilingual_readmes_teach_photo_onboarding_and_show_both_tutorials(
        self,
    ) -> None:
        chinese = (ROOT / "README.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")

        for text in (chinese, english):
            self.assertIn(
                "examples/characters/wukong/preview.png",
                text,
            )
            self.assertIn(
                "examples/characters/moon-rabbit/preview.png",
                text,
            )
            self.assertIn(
                "examples/characters/wukong/profile.json",
                text,
            )
            self.assertIn(
                "examples/characters/moon-rabbit/profile.json",
                text,
            )
            self.assertIn(".ip-pic/ip-profile.json", text)
            self.assertNotIn(RETIRED_TUTORIAL_NAME, text)
            self.assertNotIn("examples/ip-profile.example.json", text)
            self.assertNotIn("examples/demo-character.svg", text)

        for required in (
            "本人或已获授权",
            "全身",
            "干净中性背景",
            "多视角",
            "表情",
            "无文字、水印或 logo",
            "第三方角色特征",
            "保存前先让我确认",
        ):
            self.assertIn(required, chinese)
        for required in (
            "yourself or someone you are authorized to depict",
            "full-body",
            "clean neutral background",
            "multiple views",
            "expressions",
            "no text, watermark, or logo",
            "third-party character traits",
            "show it to me before saving",
        ):
            self.assertIn(required, english)

    def test_skill_and_references_enforce_explicit_backend_choice_and_boundaries(
        self,
    ) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        backend = (ROOT / "references/backend-selection.md").read_text(
            encoding="utf-8"
        )
        onboarding = (ROOT / "references/ip-onboarding.md").read_text(
            encoding="utf-8"
        )

        combined = "\n".join((skill, backend, onboarding))
        for backend_id in (
            "codex-image-tool",
            "openai-direct",
            "ai-router",
            "prompt-only",
        ):
            self.assertIn(backend_id, combined)
        self.assertIn("first_run_choice", combined)
        self.assertIn("GPT Image 2", combined)
        self.assertIn("~/.ip-pic/.env", combined)
        self.assertIn("doctor", combined)
        self.assertIn("configure", combined)
        self.assertIn("只有用户明确要求“以后默认", combined)
        self.assertIn("不生成图片", combined)
        self.assertIn("已经安装并注册", combined)
        self.assertIn("不引导下载", combined)
        self.assertNotIn(RETIRED_TUTORIAL_NAME, combined)
        self.assertNotIn("Nano Banana", combined)

    def test_step_three_has_an_executable_branch_for_each_rendering_choice(
        self,
    ) -> None:
        chinese = (ROOT / "README.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        onboarding = (ROOT / "references/ip-onboarding.md").read_text(
            encoding="utf-8"
        )

        direct_command = (
            "python3 <skill-root>/scripts/openai_backend.py master "
            "--reference <project-photo-path> "
            "--output <project-character-master.png>"
        )
        for text in (chinese, english):
            self.assertIn(direct_command, text)
            self.assertIn("unsupported_platform", text)
            self.assertNotIn("from the Skill root", text)
            self.assertNotIn("从 Skill 根目录", text)
        self.assertIn("用户项目目录", chinese)
        self.assertIn("user project directory", english)
        for required in (
            "Codex Image Tool 或已有 `ai-router`",
            "附加真人照片",
            "母版提示词",
            "`prompt-only`",
            "外部图片工具",
            "教程角色",
        ):
            self.assertIn(required, chinese)
        for required in (
            "Codex Image Tool or existing `ai-router`",
            "attach the real photo",
            "character-master prompt",
            "`prompt-only`",
            "external image tool",
            "tutorial character",
        ):
            self.assertIn(required, english)
        combined = "\n".join((skill, onboarding))
        for required in (
            "openai_backend.py master",
            "unsupported_platform",
            "外部图片工具",
            "教程角色",
        ):
            self.assertIn(required, combined)

    def test_direct_master_cli_contract_matches_the_readmes(self) -> None:
        command = [
            sys.executable,
            str(ROOT / "scripts" / "openai_backend.py"),
            "master",
            "--help",
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--reference", completed.stdout)
        self.assertIn("--output", completed.stdout)

    def test_character_master_docs_refuse_overwrite_and_require_new_filename(
        self,
    ) -> None:
        for relative in (
            "README.md",
            "SKILL.md",
            "references/ip-onboarding.md",
            "references/backend-selection.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("输出文件已存在", text, relative)
            self.assertIn("新的输出文件名", text, relative)
            self.assertIn("不会覆盖", text, relative)
            self.assertIn("Skill", text, relative)

        english = (ROOT / "README.en.md").read_text(encoding="utf-8")
        self.assertIn("output file already exists", english)
        self.assertIn("new output filename", english)
        self.assertIn("will not overwrite", english)
        self.assertIn("Skill directory", english)

    def test_direct_api_security_contract_and_contributor_scope_are_current(
        self,
    ) -> None:
        security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        contract = (ROOT / "skill.contract.yaml").read_text(encoding="utf-8")
        contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

        self.assertNotIn("This Skill never needs an API key", security)
        self.assertIn("optional direct OpenAI API", security)
        self.assertIn("~/.ip-pic/.env", security)
        self.assertIn("user-level", security)

        profile_block = contract.split("- name: ip_profile", 1)[1].split(
            "- name: brief", 1
        )[0]
        self.assertIn("required: false", profile_block)
        self.assertNotIn("ip_profile ownership is missing", contract)
        for backend_id in (
            "codex-image-tool",
            "openai-direct",
            "ai-router",
            "prompt-only",
        ):
            self.assertIn(backend_id, contract)
        self.assertIn("scripts/openai_backend.py", contract)
        self.assertIn("suite_id: ip-pic-v0-2", contract)
        self.assertNotIn("image_generation_owned_by_host: true", contract)
        for required in (
            "classification: open_source_byok",
            "credential_sources:",
            "secrets_outside_skill_dir: true",
            "network_allowlist:",
            "api.openai.com",
            "redaction:",
            "apply_requires_explicit_user_approval: true",
            "revoke_rotate_delete: SECURITY.md",
            "security_cases:",
        ):
            self.assertIn(required, contract)
        for lifecycle_action in ("Revoke", "rotate", "delete"):
            self.assertIn(lifecycle_action, security)

        self.assertIn("compiler and render request", contributing)
        self.assertIn("fixed GPT Image 2 direct adapter", contributing)

    def test_skill_declares_untrusted_content_and_metadata_boundary(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        workflow = (ROOT / "references/workflow.md").read_text(encoding="utf-8")
        contract = (ROOT / "skill.contract.yaml").read_text(encoding="utf-8")
        combined = "\n".join((skill, workflow))
        for required in (
            "不可信数据",
            "不得执行",
            "不得读取",
            "不得上传",
            "ownership",
            "backend",
        ):
            self.assertIn(required, combined)
        self.assertIn(
            "instructions_from_untrusted_content_or_metadata",
            contract,
        )

    def test_direct_renderer_docs_use_exact_compiled_dimensions(self) -> None:
        chinese = "\n".join(
            (ROOT / relative).read_text(encoding="utf-8")
            for relative in (
                "README.md",
                "SKILL.md",
                "references/backend-selection.md",
            )
        )
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")
        for dimensions in ("1536x864", "1024x1024", "1152x2048"):
            self.assertIn(dimensions, chinese)
            self.assertIn(dimensions, english)
        self.assertIn("16 的倍数", chinese)
        self.assertIn("multiples of 16", english)

    def test_contract_separates_onboarding_from_article_compilation(self) -> None:
        contract = (ROOT / "skill.contract.yaml").read_text(encoding="utf-8")
        for name, next_name in (
            ("content", "ip_profile"),
            ("brief", "available_image_backends"),
            ("prompts", "render_request"),
            ("render_request", "run_manifest"),
            ("run_manifest", "character_master"),
        ):
            field = contract.split(f"- name: {name}", 1)[1].split(
                f"- name: {next_name}", 1
            )[0]
            self.assertIn("required: false", field)
        onboarding = contract.split("  character_onboarding:", 1)[1].split(
            "  article_illustration:", 1
        )[0]
        article = contract.split("  article_illustration:", 1)[1].split(
            "\ndelegates:", 1
        )[0]
        self.assertIn("compile_artifacts_required: false", onboarding)
        self.assertIn("at_least_one_of:", onboarding)
        for source in (
            "authorized_reference",
            "character_master",
            "tutorial_character",
        ):
            self.assertIn(f"        - {source}", onboarding)
        self.assertIn("minimum_output_count: 1", onboarding)
        for artifact in ("content", "ip_profile", "brief"):
            self.assertIn(f"      - {artifact}", article)
        for artifact in ("prompts", "render_request", "run_manifest"):
            self.assertIn(f"      - {artifact}", article)
        self.assertNotIn("- name: compile_only", contract)
        self.assertIn("valid_outcomes:", contract)
        self.assertIn("status: compile_only", contract)

    def test_troubleshooting_covers_install_and_first_run_failures(self) -> None:
        chinese = (ROOT / "README.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("## 安装或首次运行失败时", chinese)
        self.assertIn("## If installation or the first run fails", english)
        self.assertIn("编译器启动失败", skill)
        self.assertIn("Python 3.10+", skill)
        self.assertIn("Windows 仍可安装", chinese)
        self.assertIn("Windows can still install", english)

    def test_tutorial_profiles_are_original_licensed_examples(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        onboarding = (ROOT / "references/ip-onboarding.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("用户明确选择教程", skill)
        self.assertIn("不得把示例资料保存为用户资料", skill)
        self.assertIn("不把示例 profile 写入用户项目", onboarding)
        self.assertIn("Git", onboarding)
        self.assertIn("云盘", onboarding)

        expected = {
            "wukong": "悟空知识工匠 / Wukong Knowledge Maker",
            "moon-rabbit": "月兔地图师 / Moon Rabbit Mapmaker",
        }
        required_anchors = {
            "wukong": {
                "warm brown fur",
                "cloud-shaped deep-red hair tuft",
                "teal workwear",
                "coral-red scarf",
                "long-handled brass paintbrush staff",
            },
            "moon-rabbit": {
                "ivory-white fur",
                "long ears",
                "crescent-shaped forelock",
                "midnight-blue short jacket",
                "mustard-yellow map satchel",
                "brass moon-phase compass",
            },
        }
        for directory, name in expected.items():
            profile_path = ROOT / "examples" / "characters" / directory / "profile.json"
            profile = validate_profile(
                json.loads(profile_path.read_text(encoding="utf-8"))
            )
            self.assertEqual(profile["ownership"]["status"], "licensed")
            self.assertEqual(profile["identity"]["name"], name)
            self.assertEqual(profile["references"], [])
            appearance = profile["appearance"]["description"]
            signature = set(profile["appearance"]["signature_features"])
            continuity = set(profile["continuity_anchors"])
            for anchor in required_anchors[directory]:
                self.assertIn(anchor, appearance)
                self.assertIn(anchor, signature)
                self.assertIn(anchor, continuity)
            self.assertTrue(
                (profile_path.parent / "preview.png").is_file(),
                f"missing preview for {name}",
            )
        wukong = (
            ROOT / "examples/characters/wukong/profile.json"
        ).read_text(encoding="utf-8")
        self.assertNotIn("red headband", wukong)
        self.assertNotIn("compact golden idea staff", wukong)

    def test_retired_tutorial_assets_are_removed_from_the_full_release(self) -> None:
        self.assertFalse((ROOT / "examples/demo-character.svg").exists())
        self.assertFalse((ROOT / "examples/ip-profile.example.json").exists())
        manifest = json.loads(
            (ROOT / "public-release-manifest.json").read_text(encoding="utf-8")
        )
        for relative in manifest["files"]:
            path = ROOT / relative
            if path.suffix.lower() == ".png":
                continue
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(RETIRED_TUTORIAL_NAME, text, relative)

    def test_notice_limits_license_to_original_expression(self) -> None:
        notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
        self.assertIn("Journey to the West", notice)
        self.assertIn("East Asian Moon Rabbit", notice)
        self.assertIn("public-domain literary and folk archetypes", notice)
        self.assertIn("claims no rights", notice)
        self.assertIn(
            "contributor-created preview artwork and profile text",
            notice,
        )
        for medium in ("film", "animation", "game", "toy", "commercial"):
            self.assertIn(medium, notice)

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
        self.assertIn('display_name: "IP 配图"', interface)
        self.assertNotIn("output_dir", brief)
        self.assertNotIn("output_dir", brief_schema["properties"])


if __name__ == "__main__":
    unittest.main()

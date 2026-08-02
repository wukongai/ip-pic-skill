from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.compiler import compile_request  # noqa: E402
from ip_pic.profiles import ProfileError  # noqa: E402
from ip_pic.publish import FONT_CANDIDATES, compose_publish_layout  # noqa: E402


class DocumentedUserFlowTests(unittest.TestCase):
    def test_beginner_guides_and_customization_reference_exist(self) -> None:
        required = (
            "USER-GUIDE.zh-CN.md",
            "USER-GUIDE.en.md",
            "IMAGE-TOOL-SETUP.zh-CN.md",
            "IMAGE-TOOL-SETUP.en.md",
            "MAINTAINER-GUIDE.zh-CN.md",
            "MAINTAINER-GUIDE.en.md",
            "references/customization.md",
            "examples/article-two-step-brief.json",
            "scripts/compose_publish_layout.py",
        )
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual(missing, [])

    def test_beginner_guide_is_agent_first_and_restores_original_journey(self) -> None:
        guide = (ROOT / "USER-GUIDE.zh-CN.md").read_text(encoding="utf-8")
        required_phrases = (
            "https://github.com/wukongai/ip-pic-skill",
            "帮我安装并使用这个配图工具",
            "带我完成第一次配图",
            "学习向导阿拓",
            "直接运行示例",
            "使用 IP Pic 的学习向导阿拓示例",
            "给下面这段文字配 1 张图",
            "用刚才的阿拓给这篇文章配图",
            "Obsidian",
            "用我的角色",
            "改成毛毡手作",
            "新增自己的风格",
            "保存为我的个人风格",
            "改成 1:1",
            "先无字图再加标题",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, guide)

        user_surfaces = "\n".join(
            (ROOT / relative).read_text(encoding="utf-8")
            for relative in (
                "USER-GUIDE.zh-CN.md",
                "USER-GUIDE.en.md",
                "README.zh-CN.md",
                "README.en.md",
            )
        )
        forbidden_implementation_details = (
            "```bash",
            "终端",
            "Python",
            "JSON",
            "Skill 安装目录",
            "metadata.version",
            "0.3.0-rc.2",
            "临时检查位置",
            "安装名称保持",
            "全局 Skill",
            "不要覆盖或启用",
            "run Python",
            "Skill directory",
            "temporary inspection",
            "global Skill",
            "pip install",
            "json.tool",
            "run-manifest.json",
            "render_handoff",
            "--output-dir",
        )
        for phrase in forbidden_implementation_details:
            with self.subTest(forbidden=phrase):
                self.assertNotIn(phrase, user_surfaces)

        install_section = guide.split("## 第一步：", 1)[1].split(
            "## 第二步：", 1
        )[0]
        self.assertLess(
            len(install_section),
            500,
            "普通用户安装段应是一句交给 Agent 的话，而不是技术操作手册",
        )

    def test_first_example_is_one_short_prompt_and_agent_handles_setup(self) -> None:
        chinese = (ROOT / "USER-GUIDE.zh-CN.md").read_text(encoding="utf-8")
        english = (ROOT / "USER-GUIDE.en.md").read_text(encoding="utf-8")

        chinese_example = chinese.split("## 第二步：直接运行示例", 1)[1].split(
            "## 第三步：", 1
        )[0]
        chinese_prompts = re.findall(
            r"```text\n(.*?)\n```", chinese_example, flags=re.S
        )
        self.assertGreaterEqual(len(chinese_prompts), 1)
        self.assertLessEqual(
            len(chinese_prompts[0]),
            180,
            "第一次示例提示词应短到可以直接复制，不得夹带内部检查流程",
        )
        self.assertIn("使用 IP Pic 的学习向导阿拓示例", chinese_prompts[0])
        self.assertIn("给下面这段文字配 1 张图", chinese_prompts[0])

        english_example = english.split("## 2. Run the example", 1)[1].split(
            "## 3.", 1
        )[0]
        english_prompts = re.findall(
            r"```text\n(.*?)\n```", english_example, flags=re.S
        )
        self.assertGreaterEqual(len(english_prompts), 1)
        self.assertLessEqual(len(english_prompts[0]), 300)
        self.assertIn("Use IP Pic's Learning Guide Ato example", english_prompts[0])
        self.assertIn("give the passage below one illustration", english_prompts[0])

        user_surfaces = "\n".join(
            (ROOT / relative).read_text(encoding="utf-8")
            for relative in (
                "USER-GUIDE.zh-CN.md",
                "USER-GUIDE.en.md",
                "README.zh-CN.md",
                "README.en.md",
            )
        )
        internal_setup_prompts = (
            "请显式调用 `$imagegen`",
            "我没有 Codex。请为 ip-pic 使用 OpenAI 官方图片 API",
            "请把我已有的图片中转站接成当前宿主的图片工具",
            "请检查当前宿主是否已有 `ai_router.generate_image`",
            "图片工具检查结果：",
            "Explicitly invoke `$imagegen`",
            "Connect my existing image relay",
            "Image tool readiness:",
        )
        for phrase in internal_setup_prompts:
            with self.subTest(forbidden=phrase):
                self.assertNotIn(phrase, user_surfaces)

    def test_optional_image_tool_setup_explains_all_real_routes(self) -> None:
        chinese = (ROOT / "IMAGE-TOOL-SETUP.zh-CN.md").read_text(
            encoding="utf-8"
        )
        english = (ROOT / "IMAGE-TOOL-SETUP.en.md").read_text(encoding="utf-8")

        chinese_phrases = (
            "默认推荐使用 GPT Image 2",
            "三种真实出图方式",
            "Codex Image Tool（推荐）",
            "`$imagegen`",
            "不需要配置 API Key",
            "没有 Codex",
            "OpenAI 官方 API",
            "`OPENAI_API_KEY`",
            "`https://api.openai.com/v1`",
            "带有角色参考图时使用图片编辑",
            "中转站",
            "宿主工具或 ai-router 的用户级配置",
            "中转站 Key 也必须由你本人",
            "`ai_router.generate_image`",
            "图片工具检查结果",
            "`prompt-only` 不会生成图片",
        )
        for phrase in chinese_phrases:
            with self.subTest(language="zh-CN", phrase=phrase):
                self.assertIn(phrase, chinese)

        english_phrases = (
            "recommends GPT Image 2 by default",
            "three real rendering methods",
            "Codex Image Tool (recommended)",
            "`$imagegen`",
            "no API key",
            "OpenAI official API",
            "`OPENAI_API_KEY`",
            "`https://api.openai.com/v1`",
            "image editing with every selected authorized reference",
            "relay service",
            "host tool or ai-router user-level configuration",
            "enter a relay key yourself",
            "`ai_router.generate_image`",
            "Image tool readiness",
            "`prompt-only` does not generate an image",
        )
        for phrase in english_phrases:
            with self.subTest(language="en", phrase=phrase):
                self.assertIn(phrase, english)

        chinese_guide = (ROOT / "USER-GUIDE.zh-CN.md").read_text(
            encoding="utf-8"
        )
        english_guide = (ROOT / "USER-GUIDE.en.md").read_text(encoding="utf-8")
        self.assertIn("IMAGE-TOOL-SETUP.zh-CN.md", chinese_guide)
        self.assertIn("IMAGE-TOOL-SETUP.en.md", english_guide)

    def test_technical_manual_is_retained_for_maintainers(self) -> None:
        chinese = (ROOT / "MAINTAINER-GUIDE.zh-CN.md").read_text(
            encoding="utf-8"
        )
        english = (ROOT / "MAINTAINER-GUIDE.en.md").read_text(encoding="utf-8")
        self.assertIn("python3 scripts/compile_ip_pic.py", chinese)
        self.assertIn("python3 scripts/compile_ip_pic.py", english)
        self.assertIn("two-step-publish", chinese)
        self.assertIn("host-ai-router", english)

    def test_readme_routes_writers_to_agent_first_guide(self) -> None:
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("USER-GUIDE.zh-CN.md", chinese)
        self.assertIn("https://github.com/wukongai/ip-pic-skill", chinese)
        self.assertIn("帮我安装并使用这个配图工具", chinese)
        self.assertIn("给这篇文章配图", chinese)
        self.assertNotIn("python3 -m venv", chinese)
        self.assertNotIn("pip install", chinese)

    def test_root_skill_keeps_technical_work_inside_the_agent(self) -> None:
        root_entry = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("普通用户可直接说", root_entry)
        self.assertIn("MAINTAINER-GUIDE.zh-CN.md", root_entry)
        self.assertIn("给这篇文章配图", root_entry)
        self.assertNotIn("```bash", root_entry)

    def test_agent_first_guide_closes_obsidian_and_two_step_journeys(self) -> None:
        guide = (ROOT / "USER-GUIDE.zh-CN.md").read_text(encoding="utf-8")
        required_phrases = (
            "按照当前 Obsidian 项目已有的附件规则",
            "把图片链接插入刚才规划的文章位置",
            "修改前告诉我会改哪篇文章",
            "如果当前已有通过的无字底图",
            "如果当前只有图文融合成品",
            "先生成一个新的无字底图让我确认",
            "如果没有现成附件规则",
            "用“<角色名称>”给这篇文章配图",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, guide)
        self.assertNotIn("默认的原版较粗中文标题样式", guide)

    def test_beginner_guide_closes_project_style_and_asset_version_gaps(
        self,
    ) -> None:
        guide = (ROOT / "USER-GUIDE.zh-CN.md").read_text(encoding="utf-8")
        required_phrases = (
            "安装与自检通过",
            "当前写作项目和图片保存位置",
            "不要把角色参考图、成品或个人风格写进已安装的 IP Pic Skill",
            "以 IP Pic 的“毛毡手作”为基础",
            "柔和毛毡-01",
            "列出“<角色名称>”现有的参考图版本",
            "列出当前项目中的角色、参考图版本和个人风格",
            "个人风格默认保存在当前项目",
            "写作项目只是一个保存文章和图片的文件夹",
            "IP Pic 教程项目",
            "保存为“<角色名称>-参考图-02”",
            "请把当前项目中的个人风格“<名称>”复制到“<新项目>”",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, guide)

        readme = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("首次使用时，Agent 可能先问图片保存到哪个项目", readme)

    def test_beginner_guides_link_only_to_existing_local_files(self) -> None:
        for relative in ("USER-GUIDE.zh-CN.md", "USER-GUIDE.en.md"):
            with self.subTest(guide=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                    if "://" in target or target.startswith("#"):
                        continue
                    clean = target.split("#", 1)[0]
                    self.assertTrue(
                        (ROOT / clean).exists(),
                        f"{relative} links to missing local path: {target}",
                    )

    def test_contract_declares_only_real_cli_paths(self) -> None:
        contract = (ROOT / "skill.contract.yaml").read_text(encoding="utf-8")
        script_paths = re.findall(r"^\s+- path: (scripts/[^\s]+)$", contract, re.M)
        self.assertTrue(script_paths)
        for relative in script_paths:
            self.assertTrue(
                (ROOT / relative).is_file(),
                f"contract declares missing script: {relative}",
            )
        self.assertNotIn("<output-dir>/selection-receipt.json", contract)
        self.assertIn("<output-dir>/image_brief.json#selection_receipt", contract)

    def test_two_step_cli_help_is_executable(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "compose_publish_layout.py"),
                "--help",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--run-manifest", result.stdout)
        self.assertIn("--font-path", result.stdout)

    def test_explicit_font_override_uses_face_zero(self) -> None:
        available = next((path for path in FONT_CANDIDATES if path.is_file()), None)
        if available is None:
            self.skipTest("no bundled test font is available")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root / "raw.png"
            Image.new("RGB", (800, 800), "#F7F2E9").save(raw)
            manifest_path = root / "publish-layout.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": "image-publish-layout/v1",
                        "id": "font-override",
                        "preset": "portrait_3_4",
                        "layout_profile": "title-band-top",
                        "extension_id": "editorial-ink-v2",
                        "source_image": str(raw),
                        "output_image": str(root / "final.png"),
                        "title": {
                            "kicker": "测试",
                            "headline": "用户字体覆盖使用第一个字面",
                            "support": "不继承内置 TTC 索引",
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = json.loads(
                compose_publish_layout(
                    manifest_path=manifest_path,
                    font_path=str(available),
                ).read_text(encoding="utf-8")
            )
            self.assertTrue(result["text"])
            self.assertEqual({item["font_index"] for item in result["text"]}, {0})

    def test_compiler_validates_explicit_character_profile(self) -> None:
        brief = json.loads(
            (ROOT / "examples" / "article-brief.json").read_text(encoding="utf-8")
        )
        brief["visual"]["ip_profile"]["ownership"] = {
            "status": "unknown",
            "basis": "",
        }
        with self.assertRaises(ProfileError):
            compile_request(ROOT, brief, write=False)

    def test_profile_reference_paths_are_not_embedded_in_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            reference = Path(temp) / "private-character-reference.png"
            Image.new("RGB", (32, 32), "white").save(reference)
            brief = json.loads(
                (ROOT / "examples" / "article-brief.json").read_text(
                    encoding="utf-8"
                )
            )
            brief["visual"]["ip_profile"]["references"] = [
                {
                    "path": str(reference),
                    "purpose": "identity",
                    "authorized": True,
                }
            ]
            brief["visual"]["authorized_assets"] = [
                {
                    "id": "identity",
                    "path": str(reference),
                    "purpose": "identity",
                    "ownership": "user-owned",
                    "required": True,
                }
            ]
            result = compile_request(ROOT, brief, write=False)
            self.assertNotIn(str(reference), result["prompt"])
            self.assertIn("identity", result["prompt"])

    def test_two_step_cli_can_write_a_new_retry_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root / "raw.png"
            Image.new("RGB", (800, 800), "#F7F2E9").save(raw)
            run_manifest = root / "run-manifest.json"
            run_manifest.write_text(
                json.dumps(
                    {
                        "publish_layout": {
                            "schema_version": "image-publish-layout/v1",
                            "id": "retryable-layout",
                            "preset": "custom",
                            "width": 640,
                            "height": 853,
                            "layout_profile": "title-band-top",
                            "source_image": str(raw),
                            "output_image": str(root / "first-final.png"),
                            "title": {"headline": "第一次结果不覆盖"},
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            retry_output = root / "retry" / "second-final.png"
            retry_layout = root / "publish-layout-retry-01.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "compose_publish_layout.py"),
                    "--run-manifest",
                    str(run_manifest),
                    "--layout-manifest",
                    str(retry_layout),
                    "--output-image",
                    str(retry_output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(retry_layout.is_file())
            self.assertTrue(retry_output.is_file())
            self.assertTrue(retry_output.with_suffix(".layout-result.json").is_file())


if __name__ == "__main__":
    unittest.main()

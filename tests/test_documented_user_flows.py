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
            "不要让我运行 Python",
            "检查安装并带我完成第一次使用",
            "0.3.0-rc.2",
            "如果版本不符",
            "临时检查位置",
            "不要覆盖或启用现有 ip-pic",
            "只有版本严格等于 0.3.0-rc.2",
            "不要安装、不要启用、不要覆盖现有版本",
            "只有版本确认正确后",
            "你不需要进行本地技术处理",
            "学习向导阿拓",
            "先生成一张阿拓教程参考图",
            "给下面这段文字配 1 张图",
            "给这篇文章配图",
            "Obsidian",
            "用我的角色",
            "改成毛毡手作",
            "改成 1:1",
            "先无字图再加标题",
            "MAINTAINER-GUIDE.zh-CN.md",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, guide)

        forbidden_implementation_details = (
            "```bash",
            "python3 ",
            "pip install",
            "json.tool",
            "run-manifest.json",
            "render_handoff",
            "--output-dir",
        )
        for phrase in forbidden_implementation_details:
            with self.subTest(forbidden=phrase):
                self.assertNotIn(phrase, guide)

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
        self.assertIn("MAINTAINER-GUIDE.zh-CN.md", chinese)
        self.assertIn("https://github.com/wukongai/ip-pic-skill", chinese)
        self.assertIn("0.3.0-rc.2", chinese)
        self.assertIn("给这篇文章配图", chinese)
        self.assertNotIn("python3 -m venv", chinese)
        self.assertNotIn("pip install", chinese)

    def test_root_skill_keeps_technical_work_inside_the_agent(self) -> None:
        root_entry = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("普通用户不运行命令", root_entry)
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

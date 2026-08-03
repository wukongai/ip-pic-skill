from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANAGER = ROOT / "scripts" / "manage_ip_pic_project.py"
COMPILER = ROOT / "scripts" / "compile_ip_pic.py"
EXAMPLES = ROOT / "examples" / "project-customization"


class UserCustomizationJourneyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name).resolve()
        (self.project / "assets").mkdir()
        (self.project / "assets" / "ato-reference.png").write_bytes(
            b"fictional-authorized-reference"
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_script(
        self,
        script: Path,
        *args: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *args],
            cwd=self.project,
            text=True,
            capture_output=True,
            check=False,
        )

    def draft(self, name: str) -> dict:
        return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))

    def plan(
        self,
        kind: str,
        draft: dict,
        *,
        activate: bool = True,
    ) -> dict:
        path = self.project / f"{kind}-draft.json"
        path.write_text(
            json.dumps(draft, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        args = [
            "plan-create",
            "--project-root",
            str(self.project),
            "--kind",
            kind,
            "--draft",
            str(path),
        ]
        if activate:
            args.append("--activate")
        result = self.run_script(MANAGER, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def apply(self, preview: dict, *, confirm: bool = True) -> subprocess.CompletedProcess[str]:
        args = [
            "apply",
            "--project-root",
            str(self.project),
            "--plan",
            preview["plan_path"],
        ]
        if confirm:
            args.append("--confirm")
        return self.run_script(MANAGER, *args)

    def compile_article(self, run_id: str) -> dict:
        brief = {
            "schema_version": "image-asset-brief/v1",
            "id": run_id,
            "scene": "ip_article_illustration",
            "goal": "explain_concept",
            "audience": "中文内容读者",
            "delivery_mode": "direct-integrated",
            "selection_receipt": {
                "status": "confirmed",
                "source": "user-explicit",
                "business_type": "ip_article_illustration",
                "delivery_mode": "direct-integrated",
                "canvas": "16:9",
                "style_variant_id": "warm-learning",
            },
            "content": {
                "headline": "把复杂知识讲清楚",
                "subheadline": "先拆解，再连接",
                "summary": "每一步都对应当前文章内容",
                "points": ["识别问题", "移动卡片", "形成结论"],
            },
            "visual": {},
            "composition": {},
            "project_customization": {
                "character": {"id": "ato-guide", "version": "active"},
                "style": {"id": "warm-learning", "version": "active"},
                "director": {"id": "careful-explain", "version": "active"},
            },
        }
        brief_path = self.project / f"{run_id}.json"
        brief_path.write_text(
            json.dumps(brief, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        output = self.project / "outputs" / run_id
        result = self.run_script(
            COMPILER,
            "--brief",
            str(brief_path),
            "--output-dir",
            str(output),
            "--project-root",
            str(self.project),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return {
            "manifest": json.loads(
                (output / "run-manifest.json").read_text(encoding="utf-8")
            ),
            "prompt": (output / f"{run_id}.prompt.md").read_text(encoding="utf-8"),
        }

    def test_agent_can_create_use_update_and_rollback_private_configuration(self) -> None:
        character_preview = self.plan(
            "character", self.draft("character-draft.json")
        )
        self.assertFalse((self.project / ".ip-pic" / "registry.json").exists())
        denied = self.apply(character_preview, confirm=False)
        self.assertEqual(denied.returncode, 2)
        self.assertFalse((self.project / ".ip-pic" / "registry.json").exists())
        self.assertEqual(self.apply(character_preview).returncode, 0)

        for kind, filename in (
            ("style", "style-draft.json"),
            ("director", "director-draft.json"),
        ):
            self.assertEqual(
                self.apply(self.plan(kind, self.draft(filename))).returncode,
                0,
            )

        first = self.compile_article("first-custom-run")
        self.assertIn("学习向导阿拓", first["prompt"])
        self.assertIn("温暖学习线稿", first["prompt"])
        self.assertIn("把当前步骤卡移到流程板中央", first["prompt"])
        self.assertIn("看向流程板上的当前步骤", first["prompt"])
        self.assertEqual(
            first["manifest"]["project_customization"]["character"]["version"],
            "v0001",
        )

        character_v2 = copy.deepcopy(self.draft("character-draft.json"))
        character_v2["profile"]["appearance"]["description"] += "，外套换成蓝色"
        character_v2["profile"]["continuity_anchors"][2] = "蓝色短外套"
        second_preview = self.plan("character", character_v2)
        second_receipt = json.loads(self.apply(second_preview).stdout)
        self.assertEqual(second_receipt["version"], "v0002")

        activate = self.run_script(
            MANAGER,
            "plan-activate",
            "--project-root",
            str(self.project),
            "--kind",
            "character",
            "--id",
            "ato-guide",
            "--version",
            "v0001",
        )
        self.assertEqual(activate.returncode, 0, activate.stderr)
        self.assertEqual(
            self.apply(json.loads(activate.stdout)).returncode,
            0,
        )

        rollback = self.compile_article("rollback-custom-run")
        self.assertEqual(
            rollback["manifest"]["project_customization"]["character"]["version"],
            "v0001",
        )
        self.assertNotIn("外套换成蓝色", rollback["prompt"])
        self.assertTrue(
            (
                self.project
                / ".ip-pic"
                / "characters"
                / "ato-guide"
                / "v0002.json"
            ).is_file()
        )


if __name__ == "__main__":
    unittest.main()

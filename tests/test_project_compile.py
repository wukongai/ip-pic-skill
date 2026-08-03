from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.compiler import compile_request  # noqa: E402
from ip_pic.errors import IPPicError  # noqa: E402
from ip_pic.project_store import apply_plan, plan_create  # noqa: E402


def article_brief(style: str = "warm-crayon") -> dict:
    return {
        "schema_version": "image-asset-brief/v1",
        "id": "project-custom-article",
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
            "style_variant_id": style,
        },
        "content": {
            "headline": "从信息走向行动",
            "subheadline": "先判断，再执行",
            "summary": "把复杂内容拆成清晰步骤",
            "points": ["识别重点", "形成判断", "开始行动"],
        },
        "visual": {},
        "composition": {},
        "project_customization": {
            "character": {"id": "xiao-he", "version": "active"},
            "style": {"id": "warm-crayon", "version": "active"},
            "director": {"id": "serious-breakdown", "version": "active"},
        },
    }


class ProjectCompileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name).resolve()
        assets = self.project / "assets"
        assets.mkdir()
        self.reference = assets / "xiao-he.png"
        self.reference.write_bytes(b"authorized-project-reference")
        self._create(
            "character",
            {
                "id": "xiao-he",
                "display_name": "小禾",
                "aliases": ["小禾老师"],
                "profile": {
                    "schema_version": "ip-character-profile/v1",
                    "ownership": {
                        "status": "user-owned",
                        "basis": "用户确认拥有角色与参考图权利",
                    },
                    "identity": {
                        "name": "小禾",
                        "description": "成年学习向导",
                    },
                    "appearance": {
                        "description": "短发、圆框眼镜、蓝色外套",
                    },
                    "personality": ["耐心", "清晰"],
                    "continuity_anchors": ["短发", "圆框眼镜", "蓝色外套"],
                    "references": [
                        {
                            "id": "front-v1",
                            "path": "assets/xiao-he.png",
                            "purpose": "identity",
                            "authorized": True,
                        }
                    ],
                },
            },
        )
        self._create(
            "style",
            {
                "id": "warm-crayon",
                "display_name": "温暖蜡笔",
                "aliases": ["暖蜡笔"],
                "base_style_id": "minimal-lineart",
                "overrides": {
                    "line": "略粗、自然、有轻微手绘抖动",
                    "palette": ["暖黄", "砖红", "低饱和青绿"],
                    "material": "干燥蜡笔与纸张颗粒",
                },
            },
        )
        self._create(
            "director",
            {
                "id": "serious-breakdown",
                "display_name": "认真拆解",
                "aliases": ["认真分析"],
                "preset": {
                    "action": "右手移动流程卡片，左手扶住工作台",
                    "character_performance": {
                        "expression_preset": "focused-operate",
                        "expression_description": "认真判断下一步，眉眼克制",
                        "intensity": "balanced",
                        "gaze_target": "流程板上的当前节点",
                        "head_pose": "lean-in",
                        "body_pose": "身体前倾，重心落在工作台一侧",
                    },
                },
            },
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _create(self, kind: str, draft: dict) -> None:
        preview = plan_create(
            ROOT, self.project, kind, draft, activate=True
        )
        apply_plan(
            ROOT,
            self.project,
            Path(preview["plan_path"]),
            confirmed=True,
        )

    def test_selected_character_style_and_director_compile_together(self) -> None:
        result = compile_request(
            ROOT,
            article_brief(),
            write=False,
            project_root=self.project,
        )
        prompt = result["prompt"]
        manifest = result["manifest"]

        self.assertIn("小禾", prompt)
        self.assertIn("温暖蜡笔", prompt)
        self.assertIn("干燥蜡笔与纸张颗粒", prompt)
        self.assertIn("右手移动流程卡片，左手扶住工作台", prompt)
        self.assertIn("认真判断下一步，眉眼克制", prompt)
        self.assertIn("身体前倾，重心落在工作台一侧", prompt)
        self.assertEqual(
            manifest["project_customization"]["character"]["version"],
            "v0001",
        )
        self.assertEqual(
            manifest["project_customization"]["style"]["id"],
            "warm-crayon",
        )
        public_context = json.dumps(
            manifest["project_customization"],
            ensure_ascii=False,
        )
        self.assertNotIn(str(self.project), public_context)
        self.assertNotIn(str(self.project), prompt)

    def test_authorized_reference_reaches_handoff_with_hash(self) -> None:
        result = compile_request(
            ROOT,
            article_brief(),
            write=False,
            project_root=self.project,
        )
        asset = result["manifest"]["render_handoff"]["assets"][0]

        self.assertEqual(Path(asset["path"]), self.reference)
        self.assertEqual(asset["ownership"], "user-owned")
        self.assertEqual(
            asset["sha256"],
            hashlib.sha256(self.reference.read_bytes()).hexdigest(),
        )

    def test_task_action_and_partial_performance_override_project_director(self) -> None:
        brief = article_brief()
        brief["composition"] = {
            "action": "双手举起最终结论卡",
            "character_performance": {
                "gaze_target": "最终结论卡",
                "expression_description": "轻微微笑但保持笃定",
            },
        }

        result = compile_request(
            ROOT,
            brief,
            write=False,
            project_root=self.project,
        )
        performance = result["brief"]["composition"]["character_performance"]

        self.assertEqual(result["brief"]["composition"]["action"], "双手举起最终结论卡")
        self.assertEqual(performance["gaze_target"], "最终结论卡")
        self.assertEqual(performance["expression_description"], "轻微微笑但保持笃定")
        self.assertEqual(performance["body_pose"], "身体前倾，重心落在工作台一侧")

    def test_project_style_must_be_user_explicit(self) -> None:
        brief = article_brief()
        brief["selection_receipt"]["source"] = "user-accepted-recommendation"

        with self.assertRaisesRegex(IPPicError, "project style|个人风格|recommendation"):
            compile_request(
                ROOT,
                brief,
                write=False,
                project_root=self.project,
            )

    def test_unknown_project_asset_fails_without_silent_fallback(self) -> None:
        brief = article_brief()
        brief["project_customization"]["director"]["id"] = "not-found"

        with self.assertRaisesRegex(IPPicError, "不存在|not-found"):
            compile_request(
                ROOT,
                brief,
                write=False,
                project_root=self.project,
            )

    def test_project_customization_requires_project_root(self) -> None:
        with self.assertRaisesRegex(IPPicError, "project-root|project_root"):
            compile_request(ROOT, article_brief(), write=False)

    def test_no_project_call_remains_independent_of_project_state(self) -> None:
        brief = article_brief(style="minimal-lineart")
        brief.pop("project_customization")
        ato = json.loads(
            (ROOT / "profiles" / "characters" / "ato" / "profile.json").read_text(
                encoding="utf-8"
            )
        )
        brief["visual"]["ip_profile"] = ato

        first = compile_request(ROOT, brief, write=False)
        second = compile_request(ROOT, brief, write=False)

        self.assertEqual(first, second)
        self.assertNotIn("project_customization", first["manifest"])
        self.assertNotIn("温暖蜡笔", first["prompt"])


if __name__ == "__main__":
    unittest.main()

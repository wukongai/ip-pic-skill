from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.character_performance import normalize as normalize_performance  # noqa: E402
from ip_pic.errors import PerformanceError  # noqa: E402
from ip_pic.project_assets import (  # noqa: E402
    ProjectAssetError,
    normalize_asset_draft,
)


class ProjectAssetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name).resolve()
        (self.project / "assets").mkdir()
        (self.project / "assets" / "xiao-he.png").write_bytes(b"authorized-image")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def character_draft(self) -> dict:
        return {
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
                        "purpose": "角色正面身份连续性",
                        "authorized": True,
                    }
                ],
            },
        }

    def style_draft(self) -> dict:
        return {
            "id": "warm-crayon",
            "display_name": "温暖蜡笔",
            "aliases": ["暖蜡笔"],
            "base_style_id": "minimal-lineart",
            "overrides": {
                "line": "略粗、自然、有轻微手绘抖动",
                "palette": ["暖黄", "砖红", "低饱和青绿"],
                "material": "干燥蜡笔与纸张颗粒",
            },
        }

    def director_draft(self) -> dict:
        return {
            "id": "serious-breakdown",
            "display_name": "认真拆解",
            "aliases": ["认真分析"],
            "preset": {
                "action": "右手移动流程卡片，左手扶住工作台",
                "character_performance": {
                    "expression_preset": "focused-operate",
                    "expression_description": "认真判断下一步，眉眼克制",
                    "intensity": "balanced",
                    "facial_cues": ["轻收眉", "闭口专注"],
                    "gaze_target": "流程板上的当前节点",
                    "head_pose": "lean-in",
                    "body_pose": "身体前倾，重心落在工作台一侧",
                },
            },
        }

    def test_character_reference_is_normalized_and_authorized(self) -> None:
        result = normalize_asset_draft(
            ROOT, self.project, "character", self.character_draft()
        )

        self.assertEqual(result["schema_version"], "ip-pic-project-character/v1")
        self.assertEqual(result["profile"]["references"][0]["path"], "assets/xiao-he.png")
        self.assertEqual(result["aliases"], ["小禾老师"])

    def test_character_rejects_reference_outside_project(self) -> None:
        draft = self.character_draft()
        draft["profile"]["references"][0]["path"] = "../outside.png"

        with self.assertRaisesRegex(ProjectAssetError, "项目内部"):
            normalize_asset_draft(ROOT, self.project, "character", draft)

    def test_character_rejects_symlink_reference(self) -> None:
        target = self.project / "assets" / "xiao-he.png"
        link = self.project / "assets" / "linked.png"
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable")
        draft = self.character_draft()
        draft["profile"]["references"][0]["path"] = "assets/linked.png"

        with self.assertRaisesRegex(ProjectAssetError, "符号链接"):
            normalize_asset_draft(ROOT, self.project, "character", draft)

    def test_style_is_scoped_and_resolves_official_base(self) -> None:
        result = normalize_asset_draft(
            ROOT, self.project, "style", self.style_draft()
        )

        self.assertEqual(result["schema_version"], "ip-pic-project-style/v1")
        self.assertEqual(result["base_style_id"], "minimal-lineart")
        self.assertEqual(result["scope"], "render-style-only")
        self.assertEqual(result["overrides"]["palette"][0], "暖黄")

    def test_style_rejects_forbidden_nested_identity_or_provider_fields(self) -> None:
        for key in ("identity", "provider", "api_key", "canvas", "delivery_mode"):
            draft = self.style_draft()
            draft["overrides"]["surface_tone"] = {"note": {key: "unsafe"}}
            with self.subTest(key=key), self.assertRaisesRegex(
                ProjectAssetError, "禁止字段"
            ):
                normalize_asset_draft(ROOT, self.project, "style", draft)

    def test_style_rejects_unknown_override_field_and_long_values(self) -> None:
        draft = self.style_draft()
        draft["overrides"]["camera"] = "close-up"
        with self.assertRaisesRegex(ProjectAssetError, "不支持字段"):
            normalize_asset_draft(ROOT, self.project, "style", draft)

        draft = self.style_draft()
        draft["overrides"]["line"] = "粗" * 161
        with self.assertRaisesRegex(ProjectAssetError, "最多 160"):
            normalize_asset_draft(ROOT, self.project, "style", draft)

    def test_director_accepts_action_expression_gaze_and_body_pose(self) -> None:
        result = normalize_asset_draft(
            ROOT, self.project, "director", self.director_draft()
        )
        performance = result["preset"]["character_performance"]

        self.assertEqual(result["schema_version"], "ip-pic-project-director/v1")
        self.assertEqual(performance["expression_description"], "认真判断下一步，眉眼克制")
        self.assertEqual(performance["body_pose"], "身体前倾，重心落在工作台一侧")

    def test_director_rejects_layout_backend_and_unknown_expression(self) -> None:
        for key in ("composition_family", "canvas", "provider"):
            draft = self.director_draft()
            draft["preset"][key] = "unsafe"
            with self.subTest(key=key), self.assertRaisesRegex(
                ProjectAssetError, "未知字段"
            ):
                normalize_asset_draft(ROOT, self.project, "director", draft)

        draft = self.director_draft()
        draft["preset"]["character_performance"]["expression_preset"] = "invented"
        with self.assertRaisesRegex(PerformanceError, "未知 expression_preset"):
            normalize_asset_draft(ROOT, self.project, "director", draft)

    def test_performance_rejects_overlong_custom_description_and_pose(self) -> None:
        for key in ("expression_description", "body_pose"):
            value = {
                "expression_preset": "focused-operate",
                key: "长" * 121,
            }
            with self.subTest(key=key), self.assertRaisesRegex(
                PerformanceError, "最多 120"
            ):
                normalize_performance(value)

    def test_asset_ids_and_unknown_top_level_fields_fail_closed(self) -> None:
        draft = self.style_draft()
        draft["id"] = "../warm"
        with self.assertRaisesRegex(ProjectAssetError, "id"):
            normalize_asset_draft(ROOT, self.project, "style", draft)

        draft = self.style_draft()
        draft["notes"] = "not part of contract"
        with self.assertRaisesRegex(ProjectAssetError, "未知字段"):
            normalize_asset_draft(ROOT, self.project, "style", draft)

    def test_normalized_asset_is_json_serializable(self) -> None:
        value = normalize_asset_draft(
            ROOT, self.project, "director", self.director_draft()
        )
        json.dumps(value, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()

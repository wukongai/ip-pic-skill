from __future__ import annotations

import copy
import importlib
import json
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic import director  # noqa: E402
from ip_pic.character_performance import PerformanceError, normalize  # noqa: E402


def _brief(index: int = 0) -> dict:
    profile = json.loads(
        (ROOT / "profiles" / "characters" / "ato" / "profile.json").read_text(
            encoding="utf-8"
        )
    )
    profile["display_name"] = profile["identity"]["name"]
    return {
        "schema_version": "image-asset-brief/v1",
        "id": f"{index + 1:02d}-architecture-choice",
        "scene": "ip_article_illustration",
        "content": {
            "headline": "如何选择合适的架构",
            "summary": "比较两个方案，保留能完成交付的路径",
            "points": ["先识别判断", "再验证接口", "最后交付版本"],
        },
        "visual": {
            "ip_profile": profile,
            "authorized_assets": [],
        },
        "composition": {},
        "director_context": {"sequence_index": index},
    }


def _normalize_owner(value: dict) -> dict:
    result = copy.deepcopy(value)
    if result.get("owner") in {"image-factory", "ip-pic"}:
        result["owner"] = "public-ip-director"
    return result


class DirectorParityTests(unittest.TestCase):
    def test_public_director_matches_original_for_neutral_character(self) -> None:
        source_root = os.environ.get("IMAGE_FACTORY_SOURCE")
        if not source_root:
            self.skipTest("set IMAGE_FACTORY_SOURCE to run dual-end parity")
        sys.path.insert(0, str(Path(source_root) / "src"))
        try:
            original = importlib.import_module("image_factory.ip_director")
            for index in range(12):
                with self.subTest(index=index):
                    expected = _normalize_owner(original.plan(_brief(index)))
                    actual = _normalize_owner(director.plan(_brief(index)))
                    self.assertEqual(actual, expected)
        finally:
            sys.path.pop(0)

    def test_merge_missing_preserves_explicit_expert_values_and_provenance(self) -> None:
        brief = _brief(2)
        brief["composition"] = {
            "orientation": "left",
            "action": "双手核对已授权的专家动作",
            "character_performance": {
                "expression_preset": "skeptical-check",
                "intensity": "balanced",
                "gaze_target": "decision-dial",
                "head_pose": "slight-tilt",
            },
        }

        result = director.merge_missing(brief)

        self.assertEqual(result["composition"]["orientation"], "left")
        self.assertEqual(
            result["composition"]["action"],
            "双手核对已授权的专家动作",
        )
        self.assertEqual(
            result["director"]["composition"],
            result["composition"],
        )
        self.assertEqual(
            result["director"]["provenance"]["explicit_composition_overrides"],
            ["action", "character_performance", "orientation"],
        )

    def test_sequence_rotates_family_action_orientation_expression_and_gaze(self) -> None:
        plans = [director.plan(_brief(index))["composition"] for index in range(12)]

        self.assertGreaterEqual(len({item["composition_family"] for item in plans}), 4)
        self.assertGreaterEqual(len({item["action"] for item in plans}), 4)
        self.assertEqual(
            {item["orientation"] for item in plans},
            {"front", "left", "right", "back-three-quarter"},
        )
        self.assertGreaterEqual(
            len(
                {
                    item["character_performance"]["expression_preset"]
                    for item in plans
                }
            ),
            3,
        )
        self.assertEqual(
            {
                item["character_performance"]["gaze_target"]
                for item in plans
            },
            {"当前动作对象", "左侧核心物件", "右侧结果出口", "viewer"},
        )

    def test_invalid_character_performance_fails_before_prompt(self) -> None:
        with self.assertRaisesRegex(PerformanceError, "未知字段"):
            normalize(
                {
                    "expression_preset": "focused-operate",
                    "run_arbitrary_tool": True,
                }
            )


if __name__ == "__main__":
    unittest.main()

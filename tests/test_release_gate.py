from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.release import verify_release  # noqa: E402


class ReleaseGateTests(unittest.TestCase):
    def test_public_candidate_passes_static_release_gate(self) -> None:
        report = verify_release(ROOT)
        self.assertEqual(report.errors, ())
        self.assertTrue(report.ok)
        self.assertEqual(report.formal_templates, 13)
        self.assertEqual(report.compatibility_templates, 1)
        self.assertEqual(report.render_styles, 6)

    def test_direct_typography_recipe_is_documented_and_traceable(self) -> None:
        zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        en = (ROOT / "README.en.md").read_text(encoding="utf-8")
        typography_reference = (
            ROOT / "references" / "typography-system.md"
        ).read_text(encoding="utf-8")
        parity = json.loads(
            (ROOT / "parity" / "ip-parity-manifest.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertIn("较粗、端正的黑色中文展示字", zh)
        self.assertIn("单条不规则手绘强调线", zh)
        self.assertIn("two-step-publish`，也不做二次文字叠加", zh)
        self.assertIn("heavy, upright Chinese display type", en)
        self.assertIn("one irregular hand-drawn emphasis line", en)
        self.assertIn(
            "direct-integrated 由生图模型一次生成最终中文",
            typography_reference,
        )
        self.assertIn(
            "two-step-publish 的 raw 阶段禁止模型生成最终中文",
            typography_reference,
        )

        mapping = next(
            item
            for item in parity["entries"]
            if item["source"].endswith("references/typography-system.md")
        )
        self.assertIn(
            "src/ip_pic/typography.py",
            mapping["derived_public_targets"],
        )


if __name__ == "__main__":
    unittest.main()

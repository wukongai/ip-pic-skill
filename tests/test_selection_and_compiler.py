from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.compiler import compile_request  # noqa: E402
from ip_pic.errors import IPPicError  # noqa: E402


def article_brief(
    *,
    delivery_mode: str = "direct-integrated",
    style: str = "minimal-lineart",
    canvas: str = "16:9",
) -> dict:
    profile = json.loads(
        (ROOT / "profiles" / "characters" / "ato" / "profile.json").read_text(
            encoding="utf-8"
        )
    )
    profile["display_name"] = profile["identity"]["name"]
    return {
        "schema_version": "image-asset-brief/v1",
        "id": "ato-intelligence-value-16x9",
        "scene": "ip_article_illustration",
        "goal": "explain_concept",
        "audience": "中文内容读者",
        "delivery_mode": delivery_mode,
        "selection_receipt": {
            "status": "confirmed",
            "source": "user-explicit",
            "business_type": "ip_article_illustration",
            "delivery_mode": delivery_mode,
            "canvas": canvas,
            "style_variant_id": style,
        },
        "content": {
            "headline": "情报不等于价值",
            "subheadline": "真正的价值来自判断与行动",
            "summary": "把散乱信息压成能执行的判断",
            "points": ["过滤噪声", "形成判断", "推动行动"],
            "cta": "",
            "brand": "",
        },
        "visual": {
            "ip_profile": profile,
            "authorized_assets": [],
        },
        "composition": {},
    }


class SelectionAndCompilerTests(unittest.TestCase):
    def test_article_compile_stops_without_selection_receipt(self) -> None:
        brief = article_brief()
        brief.pop("selection_receipt")

        with self.assertRaisesRegex(IPPicError, "selection_receipt|选择确认"):
            compile_request(ROOT, brief, write=False)

    def test_direct_integrated_requires_visible_integrated_text(self) -> None:
        result = compile_request(ROOT, article_brief(), write=False)
        prompt = result["prompt"]
        manifest = result["manifest"]

        self.assertIn("请一次生成一张图文融合的 IP 正文配图", prompt)
        self.assertIn("一次生成图文融合硬约束", prompt)
        self.assertIn("必须组成一个整体画面", prompt)
        self.assertIn("请直接生成一次性图文融合成品", prompt)
        self.assertNotIn("Use no text unless", prompt)
        self.assertEqual(manifest["delivery"]["operation_count"], 1)
        self.assertTrue(manifest["delivery"]["text_integrated"])
        self.assertEqual(
            manifest["expected_outputs"]["final_image"],
            manifest["expected_outputs"]["raw_image"],
        )
        self.assertIn(
            "integrated_text_present",
            manifest["visual_qa"]["required_checks"],
        )
        self.assertIn(
            "integrated_text_legible",
            manifest["visual_qa"]["required_checks"],
        )

    def test_two_step_publish_keeps_raw_text_free_and_unpublishable(self) -> None:
        brief = article_brief(delivery_mode="two-step-publish", canvas="1:1 -> 3:4")
        brief["composition"] = {
            "publish_preset": "portrait_3_4",
            "publish_extension": "warm-paper-title-band-v1",
        }

        result = compile_request(ROOT, brief, write=False)
        prompt = result["prompt"]
        manifest = result["manifest"]

        self.assertIn("无字原始视觉素材", prompt)
        self.assertIn("请直接生成无字原始主视觉图片", prompt)
        self.assertNotIn("一次生成图文融合硬约束", prompt)
        self.assertEqual(manifest["delivery"]["operation_count"], 2)
        self.assertFalse(manifest["delivery"]["raw_publishable"])
        self.assertNotEqual(
            manifest["expected_outputs"]["final_image"],
            manifest["expected_outputs"]["raw_image"],
        )
        self.assertEqual(
            manifest["publish_layout"]["extension_id"],
            "warm-paper-title-band-v1",
        )

    def test_all_six_styles_keep_structure_canvas_delivery_and_director(self) -> None:
        baseline = None
        for style in (
            "minimal-lineart",
            "playful-craft",
            "sticker-collage",
            "expressive-handdrawn",
            "pop-impact",
            "art-print",
        ):
            with self.subTest(style=style):
                result = compile_request(
                    ROOT,
                    article_brief(style=style),
                    write=False,
                )
                contract = {
                    "template": result["manifest"]["template"]["id"],
                    "size": result["manifest"]["size"],
                    "delivery": result["manifest"]["delivery"]["mode"],
                    "director": result["manifest"]["director_plan"],
                }
                if baseline is None:
                    baseline = contract
                else:
                    self.assertEqual(contract, baseline)
                self.assertIn(style, result["prompt"])

    def test_write_mode_creates_new_contract_files_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            result = compile_request(ROOT, article_brief(), output, write=True)

            self.assertTrue(Path(result["paths"]["prompt"]).is_file())
            self.assertTrue(Path(result["paths"]["manifest"]).is_file())
            self.assertTrue(Path(result["paths"]["director"]).is_file())
            with self.assertRaisesRegex(IPPicError, "exists|覆盖"):
                compile_request(ROOT, article_brief(), output, write=True)


if __name__ == "__main__":
    unittest.main()

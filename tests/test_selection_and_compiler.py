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

    def test_direct_integrated_uses_original_heavy_typography_recipe(self) -> None:
        result = compile_request(ROOT, article_brief(), write=False)
        prompt = result["prompt"]

        for expected in (
            "【直出中文字样式】",
            "8–18 个汉字，最多三行",
            "大号、厚重、端正的黑色中文展示字",
            "现代粗黑体或稳重的编辑型宋黑混合",
            "禁止楷体、书法体、儿童体、细宋体、细字重和空心描边字",
            "全图最多一组强调线",
            "55%–82%",
            "#4B79A6",
            "#6E93B7",
            "不得同时使用整词红字、多条红线和红色框",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, prompt)

    def test_two_step_publish_keeps_raw_text_free_and_unpublishable(self) -> None:
        brief = article_brief(delivery_mode="two-step-publish", canvas="1:1 -> 3:4")
        brief["selection_receipt"]["publish_extension_id"] = "editorial-ink-v2"
        brief["composition"] = {
            "publish_preset": "portrait_3_4",
        }

        result = compile_request(ROOT, brief, write=False)
        prompt = result["prompt"]
        manifest = result["manifest"]

        self.assertIn("无字原始视觉素材", prompt)
        self.assertIn("请直接生成无字原始主视觉图片", prompt)
        self.assertNotIn("一次生成图文融合硬约束", prompt)
        self.assertNotIn("【直出中文字样式】", prompt)
        self.assertEqual(manifest["delivery"]["operation_count"], 2)
        self.assertFalse(manifest["delivery"]["raw_publishable"])
        self.assertNotEqual(
            manifest["expected_outputs"]["final_image"],
            manifest["expected_outputs"]["raw_image"],
        )
        self.assertEqual(
            manifest["publish_layout"]["extension_id"],
            "editorial-ink-v2",
        )
        self.assertNotIn("必须是 16:9 横版", prompt)
        self.assertNotIn("不得改变 16:9 画幅", prompt)
        self.assertIn("当前 raw 画布: 1:1", prompt)

    def test_two_step_publish_requires_confirmed_title_band_extension(self) -> None:
        brief = article_brief(
            delivery_mode="two-step-publish",
            canvas="1:1 -> 3:4",
        )

        with self.assertRaisesRegex(IPPicError, "publish_extension_id|标题带"):
            compile_request(ROOT, brief, write=False)

    def test_square_video_compile_emits_overlay_and_visual_qa_contract(self) -> None:
        brief = json.loads(
            (ROOT / "examples" / "video-square-brief.json").read_text(
                encoding="utf-8"
            )
        )
        result = compile_request(ROOT, brief, write=False)
        manifest = result["manifest"]

        self.assertEqual(
            manifest["video_text_overlay"]["schema_version"],
            "video-text-overlay/v1",
        )
        self.assertEqual(
            manifest["video_text_overlay"]["items"][0]["layout_variant"],
            "square-left",
        )
        self.assertEqual(manifest["delivery"]["mode"], "video-two-step-overlay")
        self.assertEqual(
            manifest["visual_qa"]["deliverable_under_review"],
            "final_image",
        )
        self.assertIn(
            "final_text_does_not_overlap_visual",
            manifest["visual_qa"]["required_checks"],
        )
        self.assertIn("无字原始视觉素材", result["prompt"])
        self.assertIn("请直接生成无字视频关键帧 raw", result["prompt"])
        self.assertNotIn("可直接用于内容发布的中文图片素材", result["prompt"])
        self.assertNotIn("请直接生成成品图片", result["prompt"])

        with tempfile.TemporaryDirectory() as temp:
            written = compile_request(
                ROOT,
                brief,
                Path(temp) / "video-run",
                write=True,
            )
            overlay_path = Path(written["paths"]["video_text_overlay"])
            self.assertTrue(overlay_path.is_file())
            self.assertEqual(
                json.loads(overlay_path.read_text(encoding="utf-8")),
                written["manifest"]["video_text_overlay"],
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

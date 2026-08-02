from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.errors import IPPicError  # noqa: E402
from ip_pic.publish import compose_publish_layout  # noqa: E402


VIDEO_SCRIPT = ROOT / "scripts" / "compose_video_keyframe_text.py"


def _video_module():
    spec = importlib.util.spec_from_file_location("public_video_text", VIDEO_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PublishAndVideoTextTests(unittest.TestCase):
    def _publish_manifest(
        self,
        root: Path,
        *,
        same_output: bool = False,
        extension_id: str = "",
    ) -> Path:
        raw = root / "raw.png"
        Image.new("RGB", (800, 800), "#F7F2E9").save(raw)
        output = raw if same_output else root / "final.png"
        path = root / "publish-layout.json"
        manifest = {
            "schema_version": "image-publish-layout/v1",
            "id": "test-publish",
            "preset": "custom",
            "width": 640,
            "height": 853,
            "layout_profile": "title-band-top",
            "source_image": str(raw),
            "output_image": str(output),
            "title": {
                "kicker": "测试 · 固定层次",
                "headline": "原图保留，标题确定性合成",
                "support": "标题带与视觉底色保持一致",
            },
        }
        if extension_id:
            manifest["extension_id"] = extension_id
            manifest["preset"] = "portrait_3_4"
            manifest.pop("width")
            manifest.pop("height")
        path.write_text(
            json.dumps(manifest, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def test_publish_layout_preserves_raw_and_matches_edge_background(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result_path = compose_publish_layout(
                manifest_path=self._publish_manifest(root)
            )
            result = json.loads(result_path.read_text(encoding="utf-8"))

            with Image.open(root / "final.png") as final_image:
                self.assertEqual(final_image.size, (640, 853))
            self.assertEqual(result["background"]["matched_color"], "#F7F2E9")
            self.assertTrue(result["quality_gates"]["title_band_matches_visual"])
            self.assertTrue(result["quality_gates"]["source_preserved"])
            with Image.open(root / "raw.png") as raw_image:
                self.assertEqual(raw_image.size, (800, 800))

    def test_publish_layout_rejects_overwriting_raw(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(IPPicError, "不得覆盖"):
                compose_publish_layout(
                    manifest_path=self._publish_manifest(
                        Path(temp),
                        same_output=True,
                    )
                )

    def test_publish_layout_refuses_to_overwrite_existing_result_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest_path = self._publish_manifest(root)
            result_path = compose_publish_layout(manifest_path=manifest_path)
            (root / "final.png").unlink()
            sentinel = '{"audit":"preserve-me"}\n'
            result_path.write_text(sentinel, encoding="utf-8")

            with self.assertRaisesRegex(IPPicError, "回执"):
                compose_publish_layout(manifest_path=manifest_path)

            self.assertEqual(result_path.read_text(encoding="utf-8"), sentinel)
            self.assertFalse((root / "final.png").exists())

    def test_original_editorial_ink_extension_keeps_heavy_headline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result_path = compose_publish_layout(
                manifest_path=self._publish_manifest(
                    root,
                    extension_id="editorial-ink-v2",
                )
            )
            result = json.loads(result_path.read_text(encoding="utf-8"))
            headline = next(
                item for item in result["text"] if item["zone"] == "headline"
            )

            self.assertEqual(result["extension_id"], "editorial-ink-v2")
            self.assertEqual(headline["font_index"], 2)
            self.assertGreaterEqual(headline["font_size"], 68)

    def test_square_video_overlay_has_exact_typography_hierarchy(self) -> None:
        module = _video_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "square.png"
            Image.new("RGB", module.SQUARE_CANVAS_SIZE, "white").save(source)
            manifest = {
                "schema_version": module.SCHEMA_VERSION,
                "output_dir": "out",
                "items": [
                    {
                        "id": "square-01",
                        "input_image": "square.png",
                        "output_file": "square-final.png",
                        "layout_variant": "square-left",
                        "kicker": "商业模型",
                        "headline": "收入增长，不自动等于利润",
                        "support": "定价 · 成本 · 留存",
                    }
                ],
            }
            manifest_path = root / "overlay.json"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False),
                encoding="utf-8",
            )

            result = json.loads(
                module.run(manifest_path).read_text(encoding="utf-8")
            )["items"][0]

            self.assertEqual(result["headline"]["recipe"], "square-editorial")
            self.assertEqual(result["headline"]["kicker_style"]["color"], "#4B79A6")
            self.assertEqual(
                result["headline"]["underline_style"],
                "single-pressure-curve-brush",
            )
            self.assertEqual(result["headline"]["support"]["color"], "#6E93B7")
            with Image.open(result["output_image"]) as rendered:
                final = rendered.convert("RGB")
                self.assertEqual(final.size, module.SQUARE_CANVAS_SIZE)
                bottom_safe_y = result["protected_safe_zones"]["bottom_y_gte"]
                self.assertEqual(bottom_safe_y, 1740)
                bottom = final.crop((0, bottom_safe_y, 2048, 2048))
                white = Image.new("RGB", bottom.size, "white")
                self.assertIsNone(ImageChops.difference(bottom, white).getbbox())

    def test_video_overlay_rejects_callout_in_platform_safe_zone(self) -> None:
        module = _video_module()
        image = Image.new("RGB", module.CANVAS_SIZE, "white")
        draw = module.ImageDraw.Draw(image)
        with self.assertRaisesRegex(ValueError, "安全区"):
            module._draw_callouts(
                draw,
                [
                    {
                        "text": "错误",
                        "x": module.RIGHT_SAFE_X,
                        "y": 200,
                        "color": "red",
                    }
                ],
                module._font_path(),
            )

    def test_video_overlay_refuses_to_overwrite_existing_final(self) -> None:
        module = _video_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "square.png"
            Image.new("RGB", module.SQUARE_CANVAS_SIZE, "white").save(source)
            output_dir = root / "out"
            output_dir.mkdir()
            existing = output_dir / "square-final.png"
            Image.new("RGB", (32, 32), "red").save(existing)
            manifest = {
                "schema_version": module.SCHEMA_VERSION,
                "output_dir": str(output_dir),
                "items": [
                    {
                        "id": "square-01",
                        "input_image": str(source),
                        "output_file": existing.name,
                        "layout_variant": "square-left",
                        "headline": "不得覆盖旧结果",
                    }
                ],
            }
            path = root / "overlay.json"
            path.write_text(
                json.dumps(manifest, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "覆盖|存在"):
                module.run(path)


if __name__ == "__main__":
    unittest.main()

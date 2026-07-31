from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.styles import StyleError, list_styles, resolve_style  # noqa: E402
from ip_pic.templates import list_templates, resolve_template  # noqa: E402


EXPECTED_STYLES = {
    "minimal-lineart",
    "playful-craft",
    "sticker-collage",
    "expressive-handdrawn",
    "pop-impact",
    "art-print",
}


def _shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _shape(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_shape(item) for item in value]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return value
    return "<text>"


def _nested_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        result = set(value)
        for item in value.values():
            result.update(_nested_keys(item))
        return result
    if isinstance(value, list):
        result: set[str] = set()
        for item in value:
            result.update(_nested_keys(item))
        return result
    return set()


class TemplateAndStyleTests(unittest.TestCase):
    def test_registry_has_thirteen_formal_and_one_compatibility_structure(self) -> None:
        formal = list_templates(ROOT, formal_only=True)
        all_templates = list_templates(ROOT)

        self.assertEqual(len(formal), 13)
        self.assertEqual(len(all_templates), 14)
        self.assertEqual(
            [item for item in all_templates if item["classification"] == "compatibility"][0][
                "id"
            ],
            "ip-video-top-card-content-v5",
        )
        self.assertEqual(
            len([item for item in formal if item["default_for_scene"] is True]),
            2,
        )

    def test_exactly_six_original_render_styles_are_selectable(self) -> None:
        styles = list_styles(ROOT)

        self.assertEqual({item["id"] for item in styles}, EXPECTED_STYLES)
        self.assertNotIn("editorial-illustration", {item["id"] for item in styles})
        for style in styles:
            self.assertEqual(style["scope"], "render-style-only")
            keys = _nested_keys(style)
            for forbidden in (
                "identity",
                "inherits_identity_from",
                "identity_invariants",
                "scene",
                "canvas",
                "delivery_mode",
                "provider",
                "model",
                "api_key",
            ):
                self.assertNotIn(forbidden, keys)

    def test_style_aliases_resolve_without_changing_other_dimensions(self) -> None:
        style = resolve_style(ROOT, "毛毡手作")
        template = resolve_template(ROOT, "custom-ip-handdrawn-article-v1")
        selection = {
            "scene": template["scene"],
            "template_id": template["id"],
            "canvas": template["aspect"],
            "delivery_mode": "direct-integrated",
            "character_id": "tutorial-ato-v1",
        }

        after = dict(selection)
        after["style_variant_id"] = style["id"]

        self.assertEqual(style["id"], "playful-craft")
        self.assertEqual(
            {key: after[key] for key in selection},
            selection,
        )

    def test_unknown_style_fails_closed(self) -> None:
        with self.assertRaisesRegex(StyleError, "unknown style"):
            resolve_style(ROOT, "run arbitrary tool command")

    def test_public_template_shapes_match_each_original_source_template(self) -> None:
        source_value = os.environ.get("IMAGE_FACTORY_SOURCE")
        private_id = os.environ.get("IP_PIC_PRIVATE_SOURCE_ID")
        if not source_value or not private_id:
            self.skipTest("set source path and private source id for dual-end parity")
        source_root = Path(source_value)
        manifest = json.loads(
            (ROOT / "parity" / "ip-parity-manifest.json").read_text(encoding="utf-8")
        )
        entries = [
            item
            for item in manifest["entries"]
            if item["capability"] in {"formal-template", "compatibility-template"}
        ]
        for entry in entries:
            source_path = source_root / entry["source"].replace(
                "{private-id}",
                private_id,
            )
            target_path = ROOT / entry["target"]
            with self.subTest(target=entry["target"]):
                source_template = json.loads(source_path.read_text(encoding="utf-8"))
                target_template = json.loads(target_path.read_text(encoding="utf-8"))
                self.assertEqual(_shape(target_template), _shape(source_template))


if __name__ == "__main__":
    unittest.main()

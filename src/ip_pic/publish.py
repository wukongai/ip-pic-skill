"""Deterministic publishing-layout composition for raw, text-free images."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from statistics import median
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .errors import IPPicError as ImageFactoryError


PRESETS = {
    "portrait_3_4": (1536, 2048),
    "vertical_9_16": (1152, 2048),
    "square_1_1": (2048, 2048),
}

DEFAULT_EXTENSION: dict[str, Any] = {
    "id": "editorial-warm-v1",
    "canvas": {"title_band_ratio": 0.25, "padding_x_ratio": 0.075, "padding_y_ratio": 0.045},
    "colors": {
        "text": "#171717",
        "muted": "#59544D",
        "kicker": "#4B79A6",
        "accent": "#E65345",
        "accent_secondary": "#D89B45",
    },
    "typography": {
        "headline_max_ratio": 0.105,
        "headline_min_px": 42,
        "headline_max_lines": 3,
        "support_max_ratio": 0.044,
        "support_min_px": 24,
        "kicker_max_ratio": 0.032,
        "kicker_min_px": 20,
        "line_gap_ratio": 0.19,
        "zone_kicker_ratio": 0.20,
        "zone_headline_ratio": 0.46,
        "zone_support_ratio": 0.18,
        "zone_footer_ratio": 0.10,
    },
    "fonts": {"base": "", "headline": "", "kicker": "", "support": "", "footer": ""},
    "font_indices": {"base": 0, "headline": 0, "kicker": 0, "support": 0, "footer": 0},
    "decoration": {
        "rule_width_ratio": 0.27,
        "rule_height_px": 8,
        "corner_radius_px": 3,
        "headline_bar": False,
        "headline_bar_width_px": 10,
        "headline_bar_gap_px": 24,
        "bottom_rule": True,
    },
}

FONT_CANDIDATES = (
    Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
)
CANNOT_START_LINE = set("，。！？；：、,.!?;:)]】》」』%％")


def _font_path(explicit: str = "", candidates: tuple[Path, ...] = FONT_CANDIDATES) -> Path:
    if explicit:
        candidate = Path(explicit).expanduser()
        if candidate.is_file():
            return candidate
        raise ImageFactoryError(f"字体不存在：{candidate}")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise ImageFactoryError("未找到可用中文字体")


def _font(path: Path, size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size, index=index)


def _width(draw: ImageDraw.ImageDraw, value: str, font: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), value, font=font)
    return box[2] - box[0]


def _wrap(draw: ImageDraw.ImageDraw, value: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in [part.strip() for part in value.splitlines() if part.strip()]:
        current = ""
        for char in paragraph:
            candidate = current + char
            if current and _width(draw, candidate, font) > max_width:
                if char in CANNOT_START_LINE:
                    lines.append(candidate.rstrip())
                    current = ""
                else:
                    lines.append(current.rstrip())
                    current = char
            else:
                current = candidate
        if current:
            lines.append(current.rstrip())
    return lines


def _fit_text(
    draw: ImageDraw.ImageDraw,
    value: str,
    font_path: Path,
    font_index: int,
    box: dict[str, int],
    *,
    max_size: int,
    min_size: int,
    max_lines: int,
    line_gap_ratio: float,
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    pad_x = max(4, round(box["w"] * 0.01))
    max_width = box["w"] - pad_x * 2
    max_height = box["h"]
    for size in range(max_size, min_size - 1, -2):
        font = _font(font_path, size, font_index)
        lines = _wrap(draw, value, font, max_width)
        gap = max(4, round(size * line_gap_ratio))
        height = len(lines) * size + max(0, len(lines) - 1) * gap
        if (
            lines
            and len(lines) <= max_lines
            and height <= max_height
            and all(_width(draw, line, font) <= max_width for line in lines)
            and all(line and line[0] not in CANNOT_START_LINE for line in lines)
        ):
            return font, lines, gap
    raise ImageFactoryError(f"标题无法在最小字号 {min_size}px 下放入安全区，请缩短文案：{value}")


def _merge_extension(extension: dict[str, Any] | None) -> dict[str, Any]:
    result = json.loads(json.dumps(DEFAULT_EXTENSION))
    if not extension:
        return result
    for section in ("canvas", "colors", "typography", "fonts", "font_indices", "decoration"):
        values = extension.get(section)
        if isinstance(values, dict):
            result[section].update(values)
    if extension.get("id"):
        result["id"] = str(extension["id"])
    return result


def _load_extension(manifest: dict[str, Any], manifest_path: Path) -> dict[str, Any]:
    extension = manifest.get("extension")
    if isinstance(extension, dict):
        return _merge_extension(extension)
    extension_id = str(manifest.get("extension_id") or "").strip()
    if extension_id:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", extension_id):
            raise ImageFactoryError(f"排版 extension_id 非法：{extension_id}")
        built_in = Path(__file__).resolve().parents[2] / "extensions" / "title-bands" / f"{extension_id}.json"
        if not built_in.is_file():
            raise ImageFactoryError(f"排版 extension_id 不存在：{extension_id}")
        return _merge_extension(json.loads(built_in.read_text(encoding="utf-8")))
    extension_path = manifest.get("extension_file")
    if extension_path:
        path = Path(str(extension_path)).expanduser()
        if not path.is_absolute():
            path = (manifest_path.parent / path).resolve()
        if not path.is_file():
            raise ImageFactoryError(f"排版 extension 不存在：{path}")
        return _merge_extension(json.loads(path.read_text(encoding="utf-8")))
    return _merge_extension(None)


def _sample_background(image: Image.Image, sample_px: int = 8) -> tuple[str, dict[str, Any]]:
    """Pick the dominant quantized edge color so the title band matches the raw visual."""

    image = image.convert("RGB")
    w, h = image.size
    points: list[tuple[int, int, int]] = []
    edge_points = [
        (sample_px, sample_px),
        (w - sample_px - 1, sample_px),
        (sample_px, h - sample_px - 1),
        (w - sample_px - 1, h - sample_px - 1),
        (w // 2, sample_px),
    ]
    for cx, cy in edge_points:
        for dx in range(-sample_px, sample_px + 1):
            for dy in range(-sample_px, sample_px + 1):
                x = max(0, min(w - 1, cx + dx))
                y = max(0, min(h - 1, cy + dy))
                points.append(image.getpixel((x, y)))
    buckets: dict[tuple[int, int, int], list[tuple[int, int, int]]] = {}
    for pixel in points:
        bucket = tuple(round(value / 16) * 16 for value in pixel)
        buckets.setdefault(bucket, []).append(pixel)
    dominant = max(buckets.items(), key=lambda item: (len(item[1]), item[0]))
    rgb = tuple(round(median(channel)) for channel in zip(*dominant[1]))
    color = "#" + "".join(f"{value:02X}" for value in rgb)
    return color, {
        "method": "edge-quantized-median",
        "sample_count": len(points),
        "dominant_bucket": list(dominant[0]),
        "dominant_count": len(dominant[1]),
        "rgb": list(rgb),
    }


def _box(x: int, y: int, w: int, h: int) -> dict[str, int]:
    return {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}


def compose_publish_layout(*, manifest_path: Path, font_path: str = "") -> Path:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "image-publish-layout/v1":
        raise ImageFactoryError("manifest.schema_version 必须为 image-publish-layout/v1")
    source_path = Path(str(manifest.get("source_image") or "")).expanduser()
    if not source_path.is_absolute():
        source_path = (manifest_path.parent / source_path).resolve()
    if not source_path.is_file():
        raise ImageFactoryError(f"原图不存在：{source_path}")
    output_path = Path(str(manifest.get("output_image") or "")).expanduser()
    if not output_path.is_absolute():
        output_path = (manifest_path.parent / output_path).resolve()
    if output_path.resolve() == source_path.resolve():
        raise ImageFactoryError("二次合成不得覆盖原始图片")
    if output_path.exists():
        raise ImageFactoryError(f"最终图片已存在，拒绝覆盖：{output_path}")
    result_path = output_path.with_suffix(".layout-result.json")
    if result_path.exists() or result_path.is_symlink():
        raise ImageFactoryError(f"文字层回执已存在，拒绝覆盖：{result_path}")

    preset = str(manifest.get("preset") or "portrait_3_4")
    if preset == "custom":
        width, height = int(manifest["width"]), int(manifest["height"])
    else:
        if preset not in PRESETS:
            raise ImageFactoryError(f"未知发布画布 preset：{preset}")
        width, height = PRESETS[preset]
    profile = str(manifest.get("layout_profile") or "title-band-top")
    if profile != "title-band-top":
        raise ImageFactoryError(f"暂不支持 layout_profile：{profile}")

    extension = _load_extension(manifest, manifest_path)
    source = Image.open(source_path).convert("RGB")
    matched_color, background_provenance = _sample_background(source)
    background = str(manifest.get("background_color") or matched_color)
    canvas_cfg = extension["canvas"]
    title_band_h = round(height * float(canvas_cfg.get("title_band_ratio") or 0.25))
    padding_x = round(width * float(canvas_cfg.get("padding_x_ratio") or 0.075))
    padding_y = round(height * float(canvas_cfg.get("padding_y_ratio") or 0.045))
    visual_box = _box(0, title_band_h, width, height - title_band_h)
    header_box = _box(padding_x, padding_y, width - padding_x * 2, title_band_h - padding_y * 2)
    if header_box["h"] <= 100 or visual_box["h"] <= 0:
        raise ImageFactoryError("标题带比例过小，无法建立安全区")

    canvas = Image.new("RGB", (width, height), background)
    visual = ImageOps.fit(source, (visual_box["w"], visual_box["h"]), method=Image.Resampling.LANCZOS)
    canvas.paste(visual, (visual_box["x"], visual_box["y"]))
    draw = ImageDraw.Draw(canvas)
    font_cfg = extension.get("fonts") if isinstance(extension.get("fonts"), dict) else {}
    font_indices = extension.get("font_indices") if isinstance(extension.get("font_indices"), dict) else {}
    explicit_font_override = bool(str(font_path).strip())

    def font_index(name: str) -> int:
        if explicit_font_override:
            return 0
        return int(font_indices.get(name) or font_indices.get("base") or 0)

    headline_font = _font_path(font_path or str(font_cfg.get("headline") or font_cfg.get("base") or ""))
    kicker_font = _font_path(font_path or str(font_cfg.get("kicker") or font_cfg.get("base") or ""))
    support_font = _font_path(font_path or str(font_cfg.get("support") or font_cfg.get("base") or ""))
    footer_font = _font_path(font_path or str(font_cfg.get("footer") or font_cfg.get("base") or ""))
    title = manifest.get("title") if isinstance(manifest.get("title"), dict) else {}
    kicker = str(title.get("kicker") or "").strip()
    headline = str(title.get("headline") or "").strip()
    support = str(title.get("support") or "").strip()
    footer = str(title.get("footer") or "").strip()
    if not headline:
        raise ImageFactoryError("title.headline 不能为空")

    typo = extension["typography"]
    kicker_h = round(header_box["h"] * float(typo.get("zone_kicker_ratio") or 0.20))
    headline_h = round(header_box["h"] * float(typo.get("zone_headline_ratio") or 0.46))
    support_h = round(header_box["h"] * float(typo.get("zone_support_ratio") or 0.18))
    footer_h = round(header_box["h"] * float(typo.get("zone_footer_ratio") or 0.10))
    if kicker_h + headline_h + support_h + footer_h > header_box["h"]:
        raise ImageFactoryError("extension 的文字区比例总和超过标题安全区")
    zones = {
        "kicker": _box(header_box["x"], header_box["y"], header_box["w"], kicker_h),
        "headline": _box(header_box["x"], header_box["y"] + kicker_h, header_box["w"], headline_h),
        "support": _box(header_box["x"], header_box["y"] + kicker_h + headline_h, header_box["w"], support_h),
        "footer": _box(header_box["x"], header_box["y"] + kicker_h + headline_h + support_h, header_box["w"], footer_h),
        "visual": visual_box,
    }
    colors = extension["colors"]
    text_results: list[dict[str, Any]] = []

    def render_text(
        name: str,
        value: str,
        zone: dict[str, int],
        text_font: Path,
        text_font_index: int,
        max_ratio: float,
        min_px: int,
        max_lines: int,
        fill: str,
        *,
        line_gap_ratio: float | None = None,
    ) -> None:
        if not value:
            return
        fitted_font, lines, line_gap = _fit_text(
            draw,
            value,
            text_font,
            text_font_index,
            zone,
            max_size=max(min_px, round(min(width, height) * max_ratio)),
            min_size=min_px,
            max_lines=max_lines,
            line_gap_ratio=float(line_gap_ratio if line_gap_ratio is not None else (typo.get("line_gap_ratio") or 0.19)),
        )
        total_height = len(lines) * fitted_font.size + max(0, len(lines) - 1) * line_gap
        x = zone["x"]
        y = zone["y"] + max(0, (zone["h"] - total_height) // 2)
        line_boxes: list[list[int]] = []
        for line in lines:
            bbox = draw.textbbox((x, y), line, font=fitted_font)
            draw.text((x, y), line, font=fitted_font, fill=fill)
            line_boxes.append(list(bbox))
            y += fitted_font.size + line_gap
        text_results.append({"zone": name, "text": value, "font_path": str(text_font), "font_index": text_font_index, "font_size": fitted_font.size, "lines": lines, "line_boxes_px": line_boxes, "zone_box_px": [zone["x"], zone["y"], zone["x"] + zone["w"], zone["y"] + zone["h"]]})

    render_text("kicker", kicker, zones["kicker"], kicker_font, font_index("kicker"), float(typo.get("kicker_max_ratio") or 0.032), int(typo.get("kicker_min_px") or 20), 1, str(colors["kicker"]))
    render_text(
        "headline",
        headline,
        zones["headline"],
        headline_font,
        font_index("headline"),
        float(typo.get("headline_max_ratio") or 0.105),
        int(typo.get("headline_min_px") or 42),
        int(typo.get("headline_max_lines") or 3),
        str(colors["text"]),
        line_gap_ratio=float(typo.get("headline_line_gap_ratio") or typo.get("line_gap_ratio") or 0.19),
    )
    render_text("support", support, zones["support"], support_font, font_index("support"), float(typo.get("support_max_ratio") or 0.044), int(typo.get("support_min_px") or 24), int(typo.get("support_max_lines") or 2), str(colors["muted"]))
    render_text("footer", footer, zones["footer"], footer_font, font_index("footer"), float(typo.get("footer_max_ratio") or typo.get("kicker_max_ratio") or 0.032), int(typo.get("footer_min_px") or typo.get("kicker_min_px") or 20), 1, str(colors["muted"]))

    decoration = extension["decoration"]
    if bool(decoration.get("headline_bar")):
        bar_w = int(decoration.get("headline_bar_width_px") or 10)
        bar_gap = int(decoration.get("headline_bar_gap_px") or 24)
        bar_x = max(0, zones["headline"]["x"] - bar_gap - bar_w)
        bar_y = zones["headline"]["y"] + round(zones["headline"]["h"] * 0.08)
        bar_h = round(zones["headline"]["h"] * 0.78)
        draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=max(1, bar_w // 2), fill=str(colors["accent"]))

    if bool(decoration.get("bottom_rule", True)):
        rule_w = round(header_box["w"] * float(decoration.get("rule_width_ratio") or 0.27))
        rule_h = int(decoration.get("rule_height_px") or 8)
        # The bottom rule is optional. When disabled, the reserved whitespace
        # remains as breathing room between the subtitle stack and the visual.
        rule_y = title_band_h - round(padding_y * 0.5) - rule_h
        draw.rounded_rectangle((header_box["x"], rule_y, header_box["x"] + rule_w, rule_y + rule_h), radius=int(decoration.get("corner_radius_px") or 3), fill=str(colors["accent"]))
        draw.rounded_rectangle((header_box["x"] + rule_w + 14, rule_y, header_box["x"] + rule_w + 14 + round(rule_w * 0.18), rule_y + rule_h), radius=int(decoration.get("corner_radius_px") or 3), fill=str(colors["accent_secondary"]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG")
    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    result = {
        "schema_version": "image-publish-layout-result/v1",
        "source_image": str(source_path.resolve()),
        "source_sha256": source_sha256,
        "output_image": str(output_path.resolve()),
        "size": f"{width}x{height}",
        "platform": manifest.get("platform"),
        "layout_profile": profile,
        "extension_id": extension["id"],
        "background": {"mode": "match_visual", "color": background, "matched_color": matched_color, "provenance": background_provenance},
        "zones": zones,
        "text": text_results,
        "quality_gates": {"source_preserved": True, "title_band_matches_visual": background.upper() == matched_color.upper(), "zone_overlap": False, "text_clipped": False},
    }
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result_path

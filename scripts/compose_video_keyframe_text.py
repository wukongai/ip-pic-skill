#!/usr/bin/env python3
"""Deterministically add Chinese key copy to 9:16 or 1:1 IP keyframes."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ModuleNotFoundError as exc:  # pragma: no cover - runtime guard
    raise SystemExit("需要 Pillow：请在 ip-pic Python 环境安装 Pillow>=10.0") from exc


SCHEMA_VERSION = "video-text-overlay/v1"
RESULT_SCHEMA_VERSION = "video-text-overlay-result/v1"
CANVAS_SIZE = (1152, 2048)
SQUARE_CANVAS_SIZE = (2048, 2048)
KEY_COPY_BOX = (96, 1390, 996, 1835)
SUBTITLE_SAFE_KEY_COPY_BOX = (72, 1240, 650, 1535)
SUBTITLE_CORRIDOR_BOX = (80, 1580, 970, 1818)
TOP_HEADER_BOX = (72, 64, 970, 196)
BOTTOM_SAFE_Y = 1840
RIGHT_SAFE_X = 1010
COLORS = {
    "black": "#1D1D1D",
    "orange": "#F28C28",
    "red": "#D94A45",
    "blue": "#3F7FBF",
    "blue_kicker": "#4B79A6",
    "blue_support": "#6E93B7",
}
SQUARE_TEXT_BOXES = {
    "square-left": (110, 180, 920, 800),
    "square-right": (1128, 180, 1938, 800),
}
DEFAULT_FONT_CANDIDATES = (
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)
DEFAULT_HEADLINE_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
)
DEFAULT_BLUE_FONT_PATH = Path("/System/Library/Fonts/Hiragino Sans GB.ttc")
DEFAULT_BLUE_FONT_NAMES = {
    "kicker": "Hiragino Sans GB W6",
    "support": "Hiragino Sans GB W3",
}
CANNOT_START_LINE = set("，。！？；：、）》】」』”’…")
CANNOT_END_LINE = set("《【（「『“‘")


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _resolve(path_text: str, base: Path) -> Path:
    path = Path(path_text).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def _font_path(explicit: str = "") -> Path:
    candidates = (explicit,) if explicit else DEFAULT_FONT_CANDIDATES
    for candidate in candidates:
        if candidate and Path(candidate).expanduser().is_file():
            return Path(candidate).expanduser()
    raise ValueError("找不到可用字体；请在 manifest.font_path 指定支持中文的 TTF/TTC 字体")


def _headline_font_path(explicit: str = "") -> Path:
    candidates = (explicit,) if explicit else DEFAULT_HEADLINE_FONT_CANDIDATES
    for candidate in candidates:
        if candidate and Path(candidate).expanduser().is_file():
            return Path(candidate).expanduser()
    return _font_path()


def _font(path: Path, size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size, index=index)


def _blue_font(
    fallback_path: Path,
    size: int,
    *,
    role: str,
) -> tuple[ImageFont.FreeTypeFont, str]:
    """Use real Chinese font weights instead of synthetic stroke thickening."""
    if DEFAULT_BLUE_FONT_PATH.is_file():
        index = 2 if role == "kicker" else 0
        return _font(DEFAULT_BLUE_FONT_PATH, size, index=index), DEFAULT_BLUE_FONT_NAMES[role]
    return _font(fallback_path, size), fallback_path.stem


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _wrap_two_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    explicit = [part.strip() for part in text.splitlines() if part.strip()]
    if len(explicit) > 1:
        return explicit[:2]
    if _text_width(draw, text, font) <= max_width:
        return [text]

    best: tuple[int, list[str]] | None = None
    for split in range(1, len(text)):
        left, right = text[:split].strip(), text[split:].strip()
        if not left or not right:
            continue
        if right[0] in CANNOT_START_LINE or left[-1] in CANNOT_END_LINE:
            continue
        widest = max(_text_width(draw, left, font), _text_width(draw, right, font))
        if widest <= max_width:
            balance = abs(len(left) - len(right))
            score = balance * 1000 + widest
            if best is None or score < best[0]:
                best = (score, [left, right])
    if best:
        return best[1]
    return [text]


def _fit_headline(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: Path,
    max_width: int,
    max_height: int,
    max_size: int = 92,
    min_size: int = 56,
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    for size in range(max_size, min_size - 1, -2):
        font = _font(font_path, size)
        lines = _wrap_two_lines(draw, text, font, max_width)
        if len(lines) > 2:
            continue
        line_gap = max(16, size // 4)
        height = len(lines) * size + (len(lines) - 1) * line_gap
        if height <= max_height and all(_text_width(draw, line, font) <= max_width for line in lines):
            return font, lines, line_gap
    raise ValueError(f"大字观点无法放入两行安全区，请缩短文案：{text}")


def _draw_editorial_headline(
    draw: ImageDraw.ImageDraw,
    headline: str,
    font_path: Path,
    box: tuple[int, int, int, int] = KEY_COPY_BOX,
) -> dict[str, Any]:
    x1, y1, x2, y2 = box
    font, lines, line_gap = _fit_headline(
        draw,
        headline,
        font_path,
        x2 - x1 - 24,
        y2 - y1 - 92,
        max_size=118,
        min_size=64,
    )
    cursor_y = y1 + 8
    widths: list[int] = []
    for line in lines:
        draw.text((x1, cursor_y), line, font=font, fill="#080808", stroke_width=1, stroke_fill="#080808")
        widths.append(_text_width(draw, line, font))
        cursor_y += font.size + line_gap

    underline_y = min(cursor_y + 12, y2 - 26)
    underline_width = min(max(widths) if widths else 420, x2 - x1 - 36)
    points = [
        (x1 + 8, underline_y),
        (x1 + underline_width // 3, underline_y - 10),
        (x1 + underline_width * 2 // 3, underline_y + 3),
        (x1 + underline_width, underline_y - 5),
    ]
    draw.line(points, fill=COLORS["red"], width=10, joint="curve")
    draw.line(
        [(x1 + 42, underline_y + 16), (x1 + underline_width - 54, underline_y + 8)],
        fill=COLORS["red"],
        width=5,
    )
    return {
        "recipe": "editorial-hero",
        "font_size": font.size,
        "lines": lines,
        "evidence_lines": [],
        "underline_y": underline_y,
        "box_px": [x1, y1, x2, y2],
    }


def _draw_evidence_panel(
    draw: ImageDraw.ImageDraw,
    headline: str,
    font_path: Path,
    evidence_lines: list[Any] | None = None,
) -> dict[str, Any]:
    x1, y1, x2, y2 = KEY_COPY_BOX
    evidence = [_text(line) for line in (evidence_lines or []) if _text(line)]
    if len(evidence) > 3:
        raise ValueError("evidence_lines 最多 3 条")
    for line in evidence:
        if len(line) > 32:
            raise ValueError(f"证据行最多 32 个字符：{line}")
    draw.rounded_rectangle((x1 - 24, y1 - 24, x2 + 24, y2 + 10), radius=28, fill="#FFFFFF")
    draw.rounded_rectangle((x1, y1 + 4, x1 + 14, y2 - 28), radius=7, fill=COLORS["red"])
    headline_height = 170 if evidence else y2 - y1 - 44
    font, lines, line_gap = _fit_headline(
        draw,
        headline,
        font_path,
        x2 - x1 - 52,
        headline_height,
        max_size=70 if evidence else 92,
        min_size=46 if evidence else 56,
    )
    cursor_y = y1 + 18
    for line in lines:
        draw.text((x1 + 42, cursor_y), line, font=font, fill=COLORS["black"])
        cursor_y += font.size + line_gap

    evidence_result: list[dict[str, Any]] = []
    if evidence:
        evidence_y = max(y1 + 190, cursor_y + 4)
        draw.line((x1 + 42, evidence_y - 14, x2 - 24, evidence_y - 14), fill="#D8D8D8", width=2)
        evidence_font = _font(font_path, 28)
        evidence_colors = ("orange", "blue", "red")
        for index, line in enumerate(evidence):
            color_name = evidence_colors[index % len(evidence_colors)]
            color = COLORS[color_name]
            if _text_width(draw, line, evidence_font) > x2 - x1 - 96:
                evidence_font = _font(font_path, 24)
            draw.rounded_rectangle(
                (x1 + 44, evidence_y + 8, x1 + 54, evidence_y + 18),
                radius=3,
                fill=color,
            )
            draw.text((x1 + 68, evidence_y), line, font=evidence_font, fill=COLORS["black"])
            evidence_result.append({"text": line, "color": color_name, "y": evidence_y})
            evidence_y += 42

    return {
        "recipe": "evidence-panel",
        "font_size": font.size,
        "lines": lines,
        "evidence_lines": evidence_result,
        "box_px": [x1, y1, x2, y2],
    }


def _draw_headline(
    draw: ImageDraw.ImageDraw,
    headline: str,
    font_path: Path,
    evidence_lines: list[Any] | None = None,
    recipe: str = "editorial-hero",
    box: tuple[int, int, int, int] = KEY_COPY_BOX,
) -> dict[str, Any]:
    if recipe == "editorial-hero":
        if any(_text(line) for line in (evidence_lines or [])):
            raise ValueError("editorial-hero 不接受底部证据行；请把真实数据放入 data-evidence 镜头，或显式选择 evidence-panel")
        return _draw_editorial_headline(draw, headline, font_path, box)
    if recipe == "evidence-panel":
        return _draw_evidence_panel(draw, headline, font_path, evidence_lines)
    raise ValueError(f"未知 typography_recipe：{recipe}")


def _draw_square_editorial(
    draw: ImageDraw.ImageDraw,
    *,
    kicker: str,
    headline: str,
    support: str,
    headline_font_path: Path,
    auxiliary_font_path: Path,
    box: tuple[int, int, int, int],
) -> dict[str, Any]:
    """Render an editorial hierarchy: Song-style claim, blue navigation and one red brush line."""
    x1, y1, x2, y2 = box

    kicker_font, kicker_font_name = _blue_font(
        auxiliary_font_path,
        48,
        role="kicker",
    )
    if kicker:
        draw.text(
            (x1, y1),
            kicker,
            font=kicker_font,
            fill=COLORS["blue_kicker"],
        )
    headline_y = y1 + (78 if kicker else 8)
    font, lines, line_gap = _fit_headline(
        draw,
        headline,
        headline_font_path,
        x2 - x1,
        y2 - headline_y - 170,
        max_size=142,
        min_size=82,
    )
    cursor_y = headline_y
    widths: list[int] = []
    for line in lines:
        draw.text((x1, cursor_y), line, font=font, fill="#080808", stroke_width=1, stroke_fill="#080808")
        widths.append(_text_width(draw, line, font))
        cursor_y += font.size + line_gap

    underline_y = min(cursor_y + 18, y2 - 116)
    headline_width = min(max(widths) if widths else 520, x2 - x1)
    underline_width = max(360, round(headline_width * 0.82))
    start = (x1 + 8, underline_y + 2)
    control_1 = (x1 + underline_width * 28 // 100, underline_y - 7)
    control_2 = (x1 + underline_width * 68 // 100, underline_y + 5)
    end = (x1 + underline_width, underline_y - 4)
    underline_points: list[tuple[int, int]] = []
    for step in range(25):
        t = step / 24
        one_minus_t = 1 - t
        x = (
            one_minus_t**3 * start[0]
            + 3 * one_minus_t**2 * t * control_1[0]
            + 3 * one_minus_t * t**2 * control_2[0]
            + t**3 * end[0]
        )
        y = (
            one_minus_t**3 * start[1]
            + 3 * one_minus_t**2 * t * control_1[1]
            + 3 * one_minus_t * t**2 * control_2[1]
            + t**3 * end[1]
        )
        underline_points.append((round(x), round(y)))
    # 单笔连续渐细：每一小段只降低极少宽度，避免分叉、双尾和突然变细。
    segment_count = len(underline_points) - 1
    for index, (segment_start, segment_end) in enumerate(
        zip(underline_points, underline_points[1:])
    ):
        progress = index / max(segment_count - 1, 1)
        # 模拟真实落笔压力：细起、厚行、细收，避免起笔圆点或整条等粗。
        pressure = math.sin(math.pi * progress) ** 0.68
        brush_width = 3 + round(11 * pressure)
        draw.line((segment_start, segment_end), fill=COLORS["red"], width=brush_width)

    support_result: dict[str, Any] | None = None
    if support:
        support_font, support_font_name = _blue_font(
            auxiliary_font_path,
            40,
            role="support",
        )
        support_lines = _wrap_two_lines(draw, support, support_font, x2 - x1)
        support_y = underline_y + 42
        for line in support_lines:
            draw.text(
                (x1, support_y),
                line,
                font=support_font,
                fill=COLORS["blue_support"],
            )
            support_y += support_font.size + 12
        support_result = {
            "text": support,
            "lines": support_lines,
            "font_size": support_font.size,
            "font_name": support_font_name,
            "color": COLORS["blue_support"],
            "stroke_width": 0,
        }

    return {
        "recipe": "square-editorial",
        "kicker": kicker,
        "kicker_style": {
            "font_size": kicker_font.size,
            "font_name": kicker_font_name,
            "color": COLORS["blue_kicker"],
            "stroke_width": 0,
        },
        "font_size": font.size,
        "lines": lines,
        "support": support_result,
        "underline_y": underline_y,
        "underline_style": "single-pressure-curve-brush",
        "underline_points": [list(point) for point in underline_points],
        "box_px": [x1, y1, x2, y2],
    }


def _draw_redactions(draw: ImageDraw.ImageDraw, redactions: list[Any]) -> list[dict[str, Any]]:
    rendered: list[dict[str, Any]] = []
    for raw in redactions:
        if not isinstance(raw, dict):
            raise ValueError("redactions 必须是含 box/fill 的对象数组")
        box = raw.get("box")
        if not isinstance(box, list) or len(box) != 4:
            raise ValueError("redactions[].box 必须为 [x1,y1,x2,y2]")
        coords = tuple(int(value) for value in box)
        x1, y1, x2, y2 = coords
        if x1 < 0 or y1 < 0 or x2 > SQUARE_CANVAS_SIZE[0] or y2 > SQUARE_CANVAS_SIZE[1] or x2 <= x1 or y2 <= y1:
            raise ValueError(f"redactions[].box 超出方屏画布: {box}")
        fill = _text(raw.get("fill")) or "#FFFFFF"
        radius = int(raw.get("radius") or 8)
        draw.rounded_rectangle(coords, radius=radius, fill=fill)
        rendered.append({"box": list(coords), "fill": fill, "radius": radius})
    return rendered


def _draw_subtitle_preview(
    draw: ImageDraw.ImageDraw,
    subtitle: str,
    font_path: Path,
    *,
    high_contrast: bool = False,
) -> dict[str, Any]:
    x1, y1, x2, y2 = SUBTITLE_CORRIDOR_BOX
    if high_contrast:
        draw.rounded_rectangle(
            (x1 - 12, y1 + 18, x2 + 12, y2 - 18),
            radius=30,
            fill="#171717",
        )
    font, lines, line_gap = _fit_headline(
        draw,
        subtitle,
        font_path,
        x2 - x1 - 56,
        y2 - y1 - 44,
        max_size=58 if high_contrast else 54,
        min_size=48 if high_contrast else 42,
    )
    total_height = len(lines) * font.size + (len(lines) - 1) * line_gap
    cursor_y = y1 + (y2 - y1 - total_height) // 2
    for line in lines:
        width = _text_width(draw, line, font)
        draw.text(
            (x1 + (x2 - x1 - width) // 2, cursor_y),
            line,
            font=font,
            fill="#FFFFFF" if high_contrast else COLORS["black"],
            stroke_width=0 if high_contrast else 3,
            stroke_fill="#FFFFFF",
        )
        cursor_y += font.size + line_gap
    return {
        "font_size": font.size,
        "lines": lines,
        "box_px": [x1, y1, x2, y2],
        "style": "high-contrast-bar" if high_contrast else "outlined-text",
    }


def _draw_top_header(
    draw: ImageDraw.ImageDraw,
    raw_header: Any,
    font_path: Path,
    *,
    mobile_readable: bool = False,
) -> dict[str, Any] | None:
    if not raw_header:
        return None
    if isinstance(raw_header, str):
        kicker, title, date = "", _text(raw_header), ""
    elif isinstance(raw_header, dict):
        kicker = _text(raw_header.get("kicker"))
        title = _text(raw_header.get("title"))
        date = _text(raw_header.get("date"))
    else:
        raise ValueError("top_header 必须是字符串或含 kicker/title/date 的对象")
    if not title or len(title) > 18:
        raise ValueError("top_header.title 必须为 1–18 个字符")
    if len(kicker) > 8 or len(date) > 10:
        raise ValueError("top_header.kicker 最多 8 个字符，date 最多 10 个字符")

    x1, y1, x2, y2 = TOP_HEADER_BOX
    draw.rounded_rectangle((x1, y1, x2, y2), radius=26, fill="#FCFBF8", outline="#D8D1C8", width=2)
    cursor_x = x1 + 22
    if kicker:
        kicker_font = _font(font_path, 30 if mobile_readable else 28)
        kicker_width = _text_width(draw, kicker, kicker_font) + 34
        draw.rounded_rectangle(
            (cursor_x, y1 + 26, cursor_x + kicker_width, y1 + 78),
            radius=18,
            fill=COLORS["blue"],
        )
        draw.text((cursor_x + 17, y1 + 35), kicker, font=kicker_font, fill="#FFFFFF")
        cursor_x += kicker_width + 22
    title_font = _font(font_path, 52 if mobile_readable else 40)
    title_width = _text_width(draw, title, title_font)
    date_font = _font(font_path, 26)
    date_width = _text_width(draw, date, date_font) if date else 0
    if cursor_x + title_width > x2 - date_width - 44:
        title_font = _font(font_path, 42 if mobile_readable else 34)
        title_width = _text_width(draw, title, title_font)
    draw.text((cursor_x, y1 + 31), title, font=title_font, fill=COLORS["black"])
    if date:
        draw.text((x2 - date_width - 22, y1 + 40), date, font=date_font, fill="#77706A")
    draw.line((x1 + 22, y2 - 20, x2 - 22, y2 - 20), fill="#E5DED6", width=2)
    return {
        "kicker": kicker,
        "title": title,
        "date": date,
        "box_px": [x1, y1, x2, y2],
        "style": "mobile-readable" if mobile_readable else "standard",
    }


def _draw_playback_ui(draw: ImageDraw.ImageDraw) -> dict[str, Any]:
    """Draw a generic, deterministic short-video control rail without platform branding."""
    x = 1060
    centers = [820, 960, 1100]
    for center_y in centers:
        draw.ellipse((x - 34, center_y - 34, x + 34, center_y + 34), fill="#FFFFFF", outline="#D8D8D8", width=2)

    # Heart.
    draw.ellipse((x - 18, centers[0] - 14, x, centers[0] + 5), fill="#D94A45")
    draw.ellipse((x, centers[0] - 14, x + 18, centers[0] + 5), fill="#D94A45")
    draw.polygon([(x - 18, centers[0] - 2), (x + 18, centers[0] - 2), (x, centers[0] + 23)], fill="#D94A45")

    # Comment bubble.
    cy = centers[1]
    draw.rounded_rectangle((x - 19, cy - 15, x + 19, cy + 13), radius=9, outline="#3C3C3C", width=4)
    draw.polygon([(x - 6, cy + 11), (x - 13, cy + 24), (x + 2, cy + 13)], fill="#3C3C3C")

    # Share arrow.
    cy = centers[2]
    draw.line((x - 19, cy + 13, x + 15, cy - 16), fill="#3C3C3C", width=6)
    draw.line((x + 15, cy - 16, x + 7, cy - 16), fill="#3C3C3C", width=6)
    draw.line((x + 15, cy - 16, x + 15, cy - 8), fill="#3C3C3C", width=6)

    # Playback progress.
    draw.rounded_rectangle((72, 1930, 1080, 1938), radius=4, fill="#D9D9D9")
    draw.rounded_rectangle((72, 1930, 425, 1938), radius=4, fill="#D94A45")
    draw.ellipse((416, 1922, 434, 1946), fill="#D94A45")
    return {"control_centers": [[x, value] for value in centers], "progress_box_px": [72, 1930, 1080, 1938]}


def _draw_callouts(
    draw: ImageDraw.ImageDraw,
    callouts: list[Any],
    font_path: Path,
    *,
    max_y: int = 1260,
    badge_style: bool = False,
) -> list[dict[str, Any]]:
    font = _font(font_path, 46 if badge_style else 34)
    rendered: list[dict[str, Any]] = []
    for index, raw in enumerate(callouts):
        if not isinstance(raw, dict):
            raise ValueError("callouts 必须是含 text/x/y/color 的对象数组")
        text_value = _text(raw.get("text"))
        x, y = int(raw.get("x", 0)), int(raw.get("y", 0))
        color_name = _text(raw.get("color")) or ("orange", "red", "blue")[index % 3]
        if not text_value or len(text_value) > 6:
            raise ValueError(f"短批注必须为 1–6 个字符：{text_value!r}")
        if x < 70 or x >= RIGHT_SAFE_X or y < 80 or y >= max_y:
            raise ValueError(f"短批注坐标进入平台或大字安全区：{text_value} @ ({x}, {y})")
        color = COLORS.get(color_name)
        if not color:
            raise ValueError(f"未知批注颜色：{color_name}")
        if badge_style:
            text_width = _text_width(draw, text_value, font)
            badge_box = (x, y, x + text_width + 46, y + 68)
            if badge_box[2] >= RIGHT_SAFE_X:
                raise ValueError(f"大号批注标签进入右侧平台安全区：{text_value}")
            draw.rounded_rectangle(
                (badge_box[0] + 4, badge_box[1] + 5, badge_box[2] + 4, badge_box[3] + 5),
                radius=25,
                fill="#D8D1C8",
            )
            draw.rounded_rectangle(badge_box, radius=25, fill=color)
            draw.text((x + 23, y + 8), text_value, font=font, fill="#FFFFFF")
            rendered.append(
                {
                    "text": text_value,
                    "x": x,
                    "y": y,
                    "color": color_name,
                    "style": "solid-pill",
                    "box_px": list(badge_box),
                }
            )
        else:
            draw.ellipse((x, y + 11, x + 12, y + 23), fill=color)
            draw.text((x + 22, y), text_value, font=font, fill=color)
            rendered.append({"text": text_value, "x": x, "y": y, "color": color_name})
    return rendered


def render_item(
    item: dict[str, Any],
    manifest_dir: Path,
    output_dir: Path,
    font_path: Path,
    headline_font_path: Path,
) -> dict[str, Any]:
    source = _resolve(_text(item.get("input_image")), manifest_dir)
    if not source.is_file():
        raise ValueError(f"输入图片不存在：{source}")
    image = Image.open(source).convert("RGB")
    square_input = image.width == image.height
    if image.size != CANVAS_SIZE and not square_input:
        raise ValueError(
            f"输入图片必须为 {CANVAS_SIZE[0]}x{CANVAS_SIZE[1]} 或正方形，"
            f"实际为 {image.size[0]}x{image.size[1]}"
        )
    if square_input and image.size != SQUARE_CANVAS_SIZE:
        image = image.resize(SQUARE_CANVAS_SIZE, Image.Resampling.LANCZOS)
    headline = _text(item.get("headline"))
    if not headline:
        raise ValueError("每个 item 必须提供 headline")

    draw = ImageDraw.Draw(image)
    typography_recipe = _text(item.get("typography_recipe")) or "editorial-hero"
    layout_variant = _text(item.get("layout_variant")) or "full-frame"
    mobile_readable = _text(item.get("readability_mode")) == "mobile"
    if square_input:
        bottom_safe_y = int(item.get("bottom_safe_y") or 1740)
        if bottom_safe_y < 1500 or bottom_safe_y > SQUARE_CANVAS_SIZE[1]:
            raise ValueError("1:1 bottom_safe_y 必须位于 1500..2048")
        draw.rectangle((0, bottom_safe_y, SQUARE_CANVAS_SIZE[0], SQUARE_CANVAS_SIZE[1]), fill="#FFFFFF")
        redaction_result = _draw_redactions(draw, item.get("redactions") or [])
        if layout_variant not in SQUARE_TEXT_BOXES:
            raise ValueError("1:1 图片的 layout_variant 必须为 square-left 或 square-right")
        headline_result = _draw_square_editorial(
            draw,
            kicker=_text(item.get("kicker")),
            headline=headline,
            support=_text(item.get("support")),
            headline_font_path=headline_font_path,
            auxiliary_font_path=font_path,
            box=SQUARE_TEXT_BOXES[layout_variant],
        )
        if item.get("callouts"):
            raise ValueError("1:1 方屏叠字暂不接受 callouts；请使用 kicker/headline/support")
        callout_result = []
    else:
        redaction_result = []
        key_copy_box = SUBTITLE_SAFE_KEY_COPY_BOX if layout_variant == "subtitle-safe" else KEY_COPY_BOX
        headline_result = _draw_headline(
            draw,
            headline,
            font_path,
            item.get("evidence_lines") or [],
            typography_recipe,
            key_copy_box,
        )
        callout_result = _draw_callouts(
            draw,
            item.get("callouts") or [],
            font_path,
            max_y=1540 if layout_variant == "subtitle-safe" else 1260,
            badge_style=mobile_readable,
        )
    subtitle_text = _text(item.get("subtitle_preview"))
    subtitle_result = None
    if subtitle_text:
        if square_input:
            raise ValueError("1:1 方屏静态图不写入逐字字幕")
        if layout_variant != "subtitle-safe":
            raise ValueError("subtitle_preview 只能用于 layout_variant=subtitle-safe")
        subtitle_result = _draw_subtitle_preview(
            draw,
            subtitle_text,
            font_path,
            high_contrast=mobile_readable,
        )
    top_header_result = None
    playback_ui_result = None
    if not square_input:
        top_header_result = _draw_top_header(
            draw,
            item.get("top_header"),
            font_path,
            mobile_readable=mobile_readable,
        )
        if item.get("playback_ui"):
            playback_ui_result = _draw_playback_ui(draw)

    output_name = _text(item.get("output_file")) or f"{_text(item.get('id')) or source.stem}-text.png"
    output_path = (output_dir / output_name).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")
    return {
        "id": _text(item.get("id")) or source.stem,
        "input_image": str(source),
        "output_image": str(output_path),
        "headline": headline_result,
        "subtitle_preview": subtitle_result,
        "top_header": top_header_result,
        "playback_ui": playback_ui_result,
        "callouts": callout_result,
        "redactions": redaction_result,
        "protected_safe_zones": (
            {"bottom_y_gte": BOTTOM_SAFE_Y, "right_x_gte": RIGHT_SAFE_X}
            if not square_input
            else {"bottom_y_gte": int(item.get("bottom_safe_y") or 1740)}
        ),
    }


def run(manifest_path: Path, output_override: str = "") -> Path:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version 必须是 {SCHEMA_VERSION}")
    manifest_dir = manifest_path.parent
    output_dir = _resolve(output_override or _text(manifest.get("output_dir")) or "video-text-overlay", manifest_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    font_path = _font_path(_text(manifest.get("font_path")))
    headline_font_path = _headline_font_path(_text(manifest.get("headline_font_path")))
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("manifest.items 必须是非空数组")
    results = [render_item(item, manifest_dir, output_dir, font_path, headline_font_path) for item in items]
    result_path = output_dir / "video-text-overlay-result.json"
    result_path.write_text(
        json.dumps(
            {
                "schema_version": RESULT_SCHEMA_VERSION,
                "source_manifest": str(manifest_path.resolve()),
                "font_path": str(font_path),
                "headline_font_path": str(headline_font_path),
                "canvas": "mixed-9:16-or-1:1",
                "items": results,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return result_path


def main() -> int:
    parser = argparse.ArgumentParser(description="为 9:16 或 1:1 IP 视频关键帧确定性叠加中文大字与要点")
    parser.add_argument("--manifest", required=True, help="video-text-overlay/v1 JSON manifest")
    parser.add_argument("--output-dir", default="", help="可选：覆盖 manifest.output_dir")
    args = parser.parse_args()
    try:
        result_path = run(Path(args.manifest).expanduser().resolve(), args.output_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(result_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""IP-only canvas resolution with original ratio tolerance."""

from __future__ import annotations

import re

from .errors import IPPicError


PRESETS = {
    "16:9": ("2048x1152", 16 / 9),
    "1:1": ("2048x2048", 1.0),
    "3:4": ("1536x2048", 3 / 4),
    "9:16": ("1152x2048", 9 / 16),
}
SIZE_PATTERN = re.compile(r"^\s*(\d+)\s*[xX×]\s*(\d+)\s*$")


def parse_size(value: str) -> tuple[int, int]:
    match = SIZE_PATTERN.match(str(value or ""))
    if not match:
        raise IPPicError(f"图片尺寸必须为 宽x高，例如 1152x2048：{value!r}")
    width, height = int(match.group(1)), int(match.group(2))
    if width < 320 or height < 320 or width > 8192 or height > 8192:
        raise IPPicError("图片宽高必须介于 320 与 8192 像素之间")
    return width, height


def raw_canvas(value: str) -> str:
    return str(value or "").split("->", 1)[0].strip()


def resolve_size(canvas: str, fallback_size: str) -> str:
    requested = raw_canvas(canvas)
    fallback_width, fallback_height = parse_size(fallback_size)
    fallback_ratio = fallback_width / fallback_height
    if requested in PRESETS:
        preset_size, expected_ratio = PRESETS[requested]
        if abs(fallback_ratio - expected_ratio) / expected_ratio <= 0.02:
            return f"{fallback_width}x{fallback_height}"
        return preset_size
    width, height = parse_size(requested)
    return f"{width}x{height}"

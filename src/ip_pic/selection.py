"""Confirmed natural-language choices for public IP compilation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import IPPicError
from .styles import resolve_style


DELIVERY_MODES = {"direct-integrated", "two-step-publish"}
SOURCES = {"user-explicit", "user-accepted-recommendation"}
RECOMMENDED = {
    "business_type": "ip_article_illustration",
    "delivery_mode": "direct-integrated",
    "canvas": "16:9",
    "style_variant_id": "minimal-lineart",
}


@dataclass(frozen=True)
class Selection:
    business_type: str
    delivery_mode: str
    canvas: str
    style_variant_id: str
    source: str

    def as_receipt(self) -> dict[str, str]:
        return {
            "status": "confirmed",
            "source": self.source,
            "business_type": self.business_type,
            "delivery_mode": self.delivery_mode,
            "canvas": self.canvas,
            "style_variant_id": self.style_variant_id,
        }


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IPPicError(f"{field} must be a non-empty string")
    return value.strip()


def require_confirmed_selection(root: Path, brief: dict[str, Any]) -> Selection | None:
    scene = str(brief.get("scene") or "").strip()
    if scene != "ip_article_illustration":
        return None
    receipt = brief.get("selection_receipt")
    if not isinstance(receipt, dict) or receipt.get("status") != "confirmed":
        raise IPPicError(
            "IP 正文配图尚未完成 selection_receipt 用户选择确认；"
            "请先确认业务类型、文字策略、画布和 IP 风格。"
        )
    source = _text(receipt.get("source"), "selection_receipt.source")
    if source not in SOURCES:
        raise IPPicError("selection_receipt.source must be user-explicit or user-accepted-recommendation")
    values = {
        key: _text(receipt.get(key), f"selection_receipt.{key}")
        for key in ("business_type", "delivery_mode", "canvas", "style_variant_id")
    }
    if values["business_type"] != scene:
        raise IPPicError("selection_receipt.business_type conflicts with brief.scene")
    if values["delivery_mode"] not in DELIVERY_MODES:
        raise IPPicError("delivery_mode must be direct-integrated or two-step-publish")
    brief_mode = str(brief.get("delivery_mode") or "").strip()
    if brief_mode and brief_mode != values["delivery_mode"]:
        raise IPPicError("selection_receipt.delivery_mode conflicts with brief.delivery_mode")
    style = resolve_style(root, values["style_variant_id"])["id"]
    if source == "user-accepted-recommendation":
        actual = {**values, "style_variant_id": style}
        if actual != RECOMMENDED:
            raise IPPicError("accepted recommendation does not match the published recommendation")
    return Selection(
        business_type=values["business_type"],
        delivery_mode=values["delivery_mode"],
        canvas=values["canvas"],
        style_variant_id=style,
        source=source,
    )

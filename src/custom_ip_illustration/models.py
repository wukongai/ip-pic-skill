from __future__ import annotations

from typing import Any

from .errors import ValidationError


PROFILE_SCHEMA = "ip-profile/v1"
BRIEF_SCHEMA = "ip-illustration-brief/v1"
OWNERSHIP_STATUSES = {"user_owned", "licensed", "authorized"}
CANVASES = {
    "16:9": {"width": 1536, "height": 864, "template": "article-landscape-v1"},
    "1:1": {"width": 1024, "height": 1024, "template": "keyframe-square-v1"},
    "9:16": {"width": 1152, "height": 2048, "template": "story-portrait-v1"},
}


def _require_dict(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{name} must be an object")
    return value


def _require_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{name} must be a non-empty string")
    return value.strip()


def _require_string_list(value: Any, name: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ValidationError(f"{name} must be a non-empty list")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_require_text(item, f"{name}[{index}]"))
    return result


def validate_profile(profile: Any) -> dict[str, Any]:
    data = _require_dict(profile, "profile")
    if data.get("schema") != PROFILE_SCHEMA:
        raise ValidationError(f"profile.schema must equal {PROFILE_SCHEMA}")

    ownership = _require_dict(data.get("ownership"), "profile.ownership")
    status = _require_text(ownership.get("status"), "profile.ownership.status")
    if status not in OWNERSHIP_STATUSES:
        allowed = ", ".join(sorted(OWNERSHIP_STATUSES))
        raise ValidationError(f"profile.ownership.status must be one of: {allowed}")
    _require_text(ownership.get("basis"), "profile.ownership.basis")

    identity = _require_dict(data.get("identity"), "profile.identity")
    _require_text(identity.get("name"), "profile.identity.name")
    _require_text(identity.get("description"), "profile.identity.description")

    appearance = _require_dict(data.get("appearance"), "profile.appearance")
    _require_text(appearance.get("description"), "profile.appearance.description")
    _require_string_list(
        appearance.get("signature_features"),
        "profile.appearance.signature_features",
    )

    personality = _require_dict(data.get("personality"), "profile.personality")
    _require_string_list(personality.get("traits"), "profile.personality.traits")

    _require_string_list(data.get("continuity_anchors"), "profile.continuity_anchors")

    references = data.get("references", [])
    if not isinstance(references, list):
        raise ValidationError("profile.references must be a list")
    for index, reference in enumerate(references):
        item = _require_dict(reference, f"profile.references[{index}]")
        _require_text(item.get("path"), f"profile.references[{index}].path")
        _require_text(item.get("purpose"), f"profile.references[{index}].purpose")
        if item.get("authorized") is not True:
            raise ValidationError(
                f"profile.references[{index}].authorized must be true"
            )
    return data


def validate_brief(brief: Any) -> dict[str, Any]:
    data = _require_dict(brief, "brief")
    if data.get("schema") != BRIEF_SCHEMA:
        raise ValidationError(f"brief.schema must equal {BRIEF_SCHEMA}")
    _require_text(data.get("title"), "brief.title")
    _require_text(data.get("content"), "brief.content")

    canvas = _require_text(data.get("canvas"), "brief.canvas")
    if canvas not in CANVASES:
        raise ValidationError("brief.canvas must be one of: 16:9, 1:1, 9:16")

    image_count = data.get("image_count", 1)
    if not isinstance(image_count, int) or isinstance(image_count, bool):
        raise ValidationError("brief.image_count must be an integer")
    if image_count < 1 or image_count > 12:
        raise ValidationError("brief.image_count must be between 1 and 12")

    points = data.get("content_points", [])
    if not isinstance(points, list):
        raise ValidationError("brief.content_points must be a list")
    for index, point in enumerate(points):
        _require_text(point, f"brief.content_points[{index}]")

    return data


def selected_reference_paths(profile: dict[str, Any], limit: int = 3) -> list[str]:
    selected: list[str] = []
    for reference in profile.get("references", []):
        if reference.get("authorized") is True and reference.get("purpose") in {
            "identity",
            "appearance",
            "style",
        }:
            selected.append(reference["path"])
        if len(selected) == limit:
            break
    return selected

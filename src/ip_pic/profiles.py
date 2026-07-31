"""Identity profiles and ownership validation."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "ip-character-profile/v1"
ALLOWED_OWNERSHIP = {"user-owned", "licensed", "project-original-tutorial"}


class ProfileError(ValueError):
    """A character profile is incomplete, unowned or unsafe."""


def _load(value: Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, Path):
        try:
            raw = json.loads(value.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ProfileError(f"profile not found: {value}") from exc
        except json.JSONDecodeError as exc:
            raise ProfileError(f"profile is invalid JSON: {value}") from exc
    else:
        raw = value
    if not isinstance(raw, dict):
        raise ProfileError("profile must be an object")
    return copy.deepcopy(raw)


def _non_empty_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProfileError(f"{field} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, field: str, minimum: int = 1) -> list[str]:
    if (
        not isinstance(value, list)
        or len(value) < minimum
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise ProfileError(f"{field} must contain at least {minimum} strings")
    return [item.strip() for item in value]


def load_character_profile(value: Path | dict[str, Any]) -> dict[str, Any]:
    profile = _load(value)
    if profile.get("schema_version") != SCHEMA_VERSION:
        raise ProfileError(f"profile schema_version must equal {SCHEMA_VERSION}")
    ownership = profile.get("ownership")
    if not isinstance(ownership, dict):
        raise ProfileError("profile.ownership must be an object")
    status = _non_empty_text(ownership.get("status"), "profile.ownership.status")
    basis = _non_empty_text(ownership.get("basis"), "profile.ownership.basis")
    if status not in ALLOWED_OWNERSHIP:
        raise ProfileError(
            "profile ownership must be user-owned, licensed, or "
            "project-original-tutorial"
        )
    identity = profile.get("identity")
    appearance = profile.get("appearance")
    if not isinstance(identity, dict) or not isinstance(appearance, dict):
        raise ProfileError("profile identity and appearance must be objects")
    _non_empty_text(identity.get("name"), "profile.identity.name")
    _non_empty_text(identity.get("description"), "profile.identity.description")
    _non_empty_text(
        appearance.get("description"),
        "profile.appearance.description",
    )
    profile["personality"] = _string_list(
        profile.get("personality"),
        "profile.personality",
    )
    profile["continuity_anchors"] = _string_list(
        profile.get("continuity_anchors"),
        "profile.continuity_anchors",
        minimum=3,
    )
    profile["ownership"] = {"status": status, "basis": basis}
    references = profile.get("references", [])
    if not isinstance(references, list):
        raise ProfileError("profile.references must be an array")
    for index, item in enumerate(references):
        if not isinstance(item, dict) or item.get("authorized") is not True:
            raise ProfileError(f"profile.references[{index}] must be authorized")
        _non_empty_text(item.get("path"), f"profile.references[{index}].path")
        _non_empty_text(item.get("purpose"), f"profile.references[{index}].purpose")
    return profile

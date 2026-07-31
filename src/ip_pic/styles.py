"""Identity-free, orthogonal render-style registry."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any


FORBIDDEN_KEYS = {
    "identity",
    "identity_invariants",
    "inherits_identity_from",
    "reference_set",
    "character_bible",
    "scene",
    "canvas",
    "delivery_mode",
    "provider",
    "model",
    "api_key",
}


class StyleError(ValueError):
    """A render-style profile is invalid or ambiguous."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StyleError(f"style data not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise StyleError(f"style data is invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise StyleError(f"style data must be an object: {path}")
    return value


def _normalize(value: str) -> str:
    return re.sub(r"[\s_]+", "-", value.strip().casefold())


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


def _entries(root: Path) -> list[dict[str, Any]]:
    registry = _load(root / "profiles" / "render-styles.json")
    if registry.get("schema_version") != "render-style-registry/v1":
        raise StyleError("style registry schema is invalid")
    entries = registry.get("styles")
    if not isinstance(entries, list) or not entries:
        raise StyleError("style registry styles must be a non-empty array")
    return [dict(item) for item in entries]


def _profile(root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    profile = _load(root / "profiles" / "render-styles" / str(entry["profile"]))
    if profile.get("schema_version") != "render-style-profile/v1":
        raise StyleError(f"style profile schema is invalid: {entry['id']}")
    if profile.get("scope") != "render-style-only":
        raise StyleError(f"style profile scope is invalid: {entry['id']}")
    if profile.get("id") != entry.get("id"):
        raise StyleError(f"style profile id does not match registry: {entry['id']}")
    leaked = sorted(_nested_keys(profile).intersection(FORBIDDEN_KEYS))
    if leaked:
        raise StyleError(f"style profile contains forbidden keys: {leaked}")
    return {**copy.deepcopy(profile), **copy.deepcopy(entry)}


def list_styles(root: Path) -> list[dict[str, Any]]:
    return [_profile(root, entry) for entry in _entries(root)]


def resolve_style(root: Path, value: str) -> dict[str, Any]:
    requested = _normalize(str(value or ""))
    if not requested:
        raise StyleError("style id or alias is required")
    for entry in _entries(root):
        candidates = [entry["id"], *entry.get("aliases", [])]
        if requested in {_normalize(str(item)) for item in candidates}:
            return _profile(root, entry)
    raise StyleError(f"unknown style: {value}")

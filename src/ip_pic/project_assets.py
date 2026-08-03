"""Validation for private, project-local IP Pic customization assets."""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from . import character_performance
from .profiles import ProfileError, load_character_profile
from .styles import StyleError, resolve_style


KINDS = {"character", "style", "director"}
ASSET_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
STYLE_OVERRIDE_FIELDS = {
    "line",
    "palette",
    "material",
    "shape_language",
    "surface_tone",
    "background_treatment",
    "typography_tone",
}
FORBIDDEN_STYLE_KEYS = {
    "identity",
    "identity_invariants",
    "inherits_identity_from",
    "reference",
    "references",
    "reference_set",
    "character",
    "character_bible",
    "scene",
    "canvas",
    "delivery_mode",
    "business_type",
    "provider",
    "model",
    "endpoint",
    "token",
    "authorization",
    "api_key",
}
COMMON_FIELDS = {"id", "display_name", "aliases"}


class ProjectAssetError(ValueError):
    """A project customization draft is invalid or unsafe."""


def _text(value: Any, field: str, *, limit: int = 160) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectAssetError(f"{field} 必须是非空字符串")
    result = value.strip()
    if len(result) > limit:
        raise ProjectAssetError(f"{field} 最多 {limit} 个字符")
    return result


def _asset_id(value: Any) -> str:
    result = _text(value, "id", limit=64)
    if not ASSET_ID_RE.fullmatch(result):
        raise ProjectAssetError(
            "id 只允许小写 ASCII 字母、数字和单个连字符，且必须以字母或数字开头结尾"
        )
    if "--" in result:
        raise ProjectAssetError("id 不允许连续连字符")
    return result


def _aliases(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if not isinstance(value, list) or len(value) > 12:
        raise ProjectAssetError("aliases 必须是最多 12 项的字符串数组")
    result: list[str] = []
    for item in value:
        alias = _text(item, "aliases[]", limit=40)
        if alias not in result:
            result.append(alias)
    return result


def _reject_unknown(value: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ProjectAssetError(f"{label} 含未知字段：{unknown}")


def _common(draft: dict[str, Any], allowed: set[str]) -> dict[str, Any]:
    if not isinstance(draft, dict):
        raise ProjectAssetError("资产草稿必须为 object")
    _reject_unknown(draft, COMMON_FIELDS | allowed, "资产草稿")
    return {
        "id": _asset_id(draft.get("id")),
        "display_name": _text(draft.get("display_name"), "display_name", limit=60),
        "aliases": _aliases(draft.get("aliases")),
    }


def _inside_project(project_root: Path, raw_path: Any, field: str) -> str:
    text = _text(raw_path, field, limit=512)
    candidate = Path(text)
    if candidate.is_absolute():
        raise ProjectAssetError(f"{field} 必须是项目内部的相对路径")
    root = project_root.resolve()
    joined = root / candidate
    if joined.is_symlink():
        raise ProjectAssetError(f"{field} 不允许符号链接")
    resolved = joined.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ProjectAssetError(f"{field} 必须位于项目内部") from exc
    if not resolved.is_file():
        raise ProjectAssetError(f"{field} 指向的文件不存在")
    if any((root / Path(*relative.parts[:index])).is_symlink() for index in range(1, len(relative.parts))):
        raise ProjectAssetError(f"{field} 的父路径不允许符号链接")
    return relative.as_posix()


def _normalize_character(project_root: Path, draft: dict[str, Any]) -> dict[str, Any]:
    common = _common(draft, {"profile"})
    profile_value = draft.get("profile")
    if not isinstance(profile_value, dict):
        raise ProjectAssetError("profile 必须为 object")
    profile_copy = copy.deepcopy(profile_value)
    references = profile_copy.get("references", [])
    if not isinstance(references, list):
        raise ProjectAssetError("profile.references 必须为数组")
    for index, item in enumerate(references):
        if not isinstance(item, dict) or item.get("authorized") is not True:
            raise ProjectAssetError(
                f"profile.references[{index}] 必须明确 authorized=true"
            )
        item["path"] = _inside_project(
            project_root,
            item.get("path"),
            f"profile.references[{index}].path",
        )
    try:
        profile = load_character_profile(profile_copy)
    except ProfileError as exc:
        raise ProjectAssetError(str(exc)) from exc
    return {
        "schema_version": "ip-pic-project-character/v1",
        **common,
        "profile": profile,
    }


def _nested_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        result = {str(key) for key in value}
        for item in value.values():
            result.update(_nested_keys(item))
        return result
    if isinstance(value, list):
        result: set[str] = set()
        for item in value:
            result.update(_nested_keys(item))
        return result
    return set()


def _style_value(value: Any, field: str) -> str | list[str]:
    if isinstance(value, str):
        return _text(value, field, limit=160)
    if isinstance(value, list):
        if not value or len(value) > 8:
            raise ProjectAssetError(f"{field} 必须包含 1-8 个字符串")
        return [_text(item, f"{field}[]", limit=40) for item in value]
    raise ProjectAssetError(f"{field} 必须为字符串或字符串数组")


def _normalize_style(
    skill_root: Path,
    draft: dict[str, Any],
) -> dict[str, Any]:
    common = _common(draft, {"base_style_id", "overrides"})
    base_style_id = _text(draft.get("base_style_id"), "base_style_id", limit=64)
    try:
        resolved_base = resolve_style(skill_root, base_style_id)
    except StyleError as exc:
        raise ProjectAssetError(str(exc)) from exc
    overrides = draft.get("overrides")
    if not isinstance(overrides, dict) or not overrides:
        raise ProjectAssetError("overrides 必须是非空 object")
    leaked = sorted(_nested_keys(overrides).intersection(FORBIDDEN_STYLE_KEYS))
    if leaked:
        raise ProjectAssetError(f"个人风格包含禁止字段：{leaked}")
    unknown = sorted(set(overrides) - STYLE_OVERRIDE_FIELDS)
    if unknown:
        raise ProjectAssetError(f"个人风格包含不支持字段：{unknown}")
    normalized = {
        str(key): _style_value(value, f"overrides.{key}")
        for key, value in overrides.items()
    }
    return {
        "schema_version": "ip-pic-project-style/v1",
        **common,
        "base_style_id": str(resolved_base["id"]),
        "scope": "render-style-only",
        "overrides": normalized,
    }


def _normalize_director(draft: dict[str, Any]) -> dict[str, Any]:
    common = _common(draft, {"preset"})
    preset = draft.get("preset")
    if not isinstance(preset, dict) or not preset:
        raise ProjectAssetError("preset 必须是非空 object")
    _reject_unknown(preset, {"action", "character_performance"}, "preset")
    result: dict[str, Any] = {}
    if preset.get("action") not in (None, ""):
        result["action"] = _text(preset.get("action"), "preset.action", limit=160)
    if preset.get("character_performance") not in (None, ""):
        result["character_performance"] = character_performance.normalize(
            preset.get("character_performance")
        )
    if not result:
        raise ProjectAssetError("preset 至少需要 action 或 character_performance")
    return {
        "schema_version": "ip-pic-project-director/v1",
        **common,
        "preset": result,
    }


def normalize_asset_draft(
    skill_root: Path,
    project_root: Path,
    kind: str,
    draft: dict[str, Any],
) -> dict[str, Any]:
    """Return a canonical, JSON-serializable project asset draft."""

    normalized_kind = str(kind or "").strip()
    if normalized_kind not in KINDS:
        raise ProjectAssetError(f"unknown project asset kind: {kind}")
    root = Path(project_root).resolve()
    if normalized_kind == "character":
        return _normalize_character(root, draft)
    if normalized_kind == "style":
        return _normalize_style(Path(skill_root).resolve(), draft)
    return _normalize_director(draft)


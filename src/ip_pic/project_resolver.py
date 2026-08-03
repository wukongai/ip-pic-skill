"""Resolve private project assets before the ordinary IP Pic compiler."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from .errors import IPPicError
from .project_store import ProjectStoreError, resolve_asset


KINDS = ("character", "style", "director")


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _selection(value: Any, kind: str) -> tuple[str | None, str]:
    if value in (None, ""):
        return None, "active"
    if not isinstance(value, dict):
        raise IPPicError(f"project_customization.{kind} 必须为 object")
    unknown = sorted(set(value) - {"id", "version"})
    if unknown:
        raise IPPicError(
            f"project_customization.{kind} 含未知字段：{unknown}"
        )
    asset_id = value.get("id")
    if asset_id is not None and (
        not isinstance(asset_id, str) or not asset_id.strip()
    ):
        raise IPPicError(f"project_customization.{kind}.id 必须为非空字符串")
    version = value.get("version", "active")
    if not isinstance(version, str) or not version.strip():
        raise IPPicError(
            f"project_customization.{kind}.version 必须为非空字符串"
        )
    return str(asset_id).strip() if asset_id is not None else None, version.strip()


def _public_asset(value: dict[str, Any], kind: str) -> dict[str, str]:
    content = copy.deepcopy(value)
    return {
        "kind": kind,
        "id": str(value["id"]),
        "version": str(value["version"]),
        "content_hash": _canonical_hash(content),
    }


def _resolve_optional_active(
    project_root: Path,
    kind: str,
) -> dict[str, Any] | None:
    try:
        return resolve_asset(project_root, kind)
    except ProjectStoreError as exc:
        if "尚未设置活动资产" in str(exc):
            return None
        raise


def _character_values(
    project_root: Path,
    asset: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    profile = copy.deepcopy(asset["profile"])
    profile["display_name"] = asset["display_name"]
    ownership = profile["ownership"]["status"]
    references: list[dict[str, Any]] = []
    for item in profile.get("references", []):
        relative = Path(str(item["path"]))
        source = project_root / relative
        if source.is_symlink():
            raise IPPicError("项目角色参考图不允许是符号链接")
        resolved = source.resolve()
        try:
            resolved.relative_to(project_root)
        except ValueError as exc:
            raise IPPicError("项目角色参考图必须位于 project-root 内") from exc
        if not resolved.is_file():
            raise IPPicError("项目角色参考图不存在")
        digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
        item["path"] = str(resolved)
        references.append(
            {
                "id": str(item.get("id") or relative.stem),
                "path": str(resolved),
                "purpose": str(item["purpose"]),
                "ownership": ownership,
                "required": True,
                "sha256": digest,
            }
        )
    return profile, references


def _merge_director(
    existing: dict[str, Any],
    asset: dict[str, Any],
) -> dict[str, Any]:
    preset = asset["preset"]
    result = copy.deepcopy(existing)
    if not result.get("action") and preset.get("action"):
        result["action"] = preset["action"]
    preset_performance = preset.get("character_performance")
    existing_performance = result.get("character_performance")
    if isinstance(preset_performance, dict):
        result["character_performance"] = {
            **copy.deepcopy(preset_performance),
            **(
                copy.deepcopy(existing_performance)
                if isinstance(existing_performance, dict)
                else {}
            ),
        }
    return result


def apply_project_customization(
    skill_root: Path,
    project_root: Path,
    brief: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Inject selected project defaults without overwriting task-level choices."""

    del skill_root  # Reserved for future project-asset migrations.
    project = Path(project_root).expanduser().resolve()
    if not project.is_dir():
        raise IPPicError("project-root 不存在或不是目录")
    result = copy.deepcopy(brief)
    raw_requested = result.get("project_customization", {})
    if raw_requested in (None, ""):
        raw_requested = {}
    if not isinstance(raw_requested, dict):
        raise IPPicError("project_customization 必须为 object")
    unknown = sorted(set(raw_requested) - set(KINDS))
    if unknown:
        raise IPPicError(f"project_customization 含未知字段：{unknown}")

    resolved: dict[str, dict[str, Any]] = {}
    explicitly_requested = set(raw_requested)
    for kind in KINDS:
        if kind in raw_requested:
            asset_id, version = _selection(raw_requested[kind], kind)
            resolved[kind] = resolve_asset(
                project,
                kind,
                asset_id,
                version=version,
            )
        elif kind in {"character", "director"}:
            active = _resolve_optional_active(project, kind)
            if active is not None:
                resolved[kind] = active

    visual = result.get("visual")
    if not isinstance(visual, dict):
        visual = {}
        result["visual"] = visual
    composition = result.get("composition")
    if not isinstance(composition, dict):
        composition = {}
        result["composition"] = composition

    character = resolved.get("character")
    if character is not None:
        if "character" in explicitly_requested and visual.get("ip_profile") not in (
            None,
            "",
        ):
            raise IPPicError(
                "project character 与本次任务 visual.ip_profile 冲突；请只保留一个明确来源"
            )
        if visual.get("ip_profile") in (None, ""):
            profile, assets = _character_values(project, character)
            visual["ip_profile"] = profile
            current_assets = visual.get("authorized_assets")
            visual["authorized_assets"] = [
                *(
                    copy.deepcopy(current_assets)
                    if isinstance(current_assets, list)
                    else []
                ),
                *assets,
            ]

    director = resolved.get("director")
    if director is not None:
        result["composition"] = _merge_director(composition, director)

    style = resolved.get("style")
    project_style_id = None
    if style is not None:
        project_style_id = f"project:{style['id']}@{style['version']}"
        receipt = result.get("selection_receipt")
        if isinstance(receipt, dict):
            receipt["style_variant_id"] = project_style_id
        visual["style_variant_id"] = project_style_id

    public = {
        kind: _public_asset(value, kind)
        for kind, value in resolved.items()
    }
    context: dict[str, Any] = {
        "public": public,
        "project_style_id": project_style_id,
    }
    if style is not None:
        context["_style_asset"] = style
    return result, context


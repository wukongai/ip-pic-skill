"""Immutable project-local storage for private IP Pic customization."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Iterator

from .errors import IPPicError
from .project_assets import KINDS, normalize_asset_draft


REGISTRY_SCHEMA = "ip-pic-project-registry/v1"
PLAN_SCHEMA = "ip-pic-project-change-plan/v1"
RECEIPT_SCHEMA = "ip-pic-project-change-receipt/v1"
VERSION_RE = re.compile(r"^v[0-9]{4}$")
KIND_DIRS = {
    "character": "characters",
    "style": "styles",
    "director": "directors",
}


class ProjectStoreError(IPPicError):
    """Project customization state is invalid, unsafe or conflicting."""


class ConfirmationRequired(ProjectStoreError):
    """Applying a project customization plan requires explicit confirmation."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _new_registry() -> dict[str, Any]:
    return {
        "schema_version": REGISTRY_SCHEMA,
        "revision": 0,
        "active": {"character": None, "style": None, "director": None},
        "assets": {"character": {}, "style": {}, "director": {}},
    }


def _require_kind(kind: str) -> str:
    result = str(kind or "").strip()
    if result not in KINDS:
        raise ProjectStoreError(f"unknown project asset kind: {kind}")
    return result


def _project_root(value: Path) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise ProjectStoreError("project root 不存在或不是目录")
    return root


def _state_root(project_root: Path, *, create: bool) -> Path:
    root = _project_root(project_root)
    state = root / ".ip-pic"
    if state.is_symlink():
        raise ProjectStoreError(".ip-pic 不允许是符号链接")
    if state.exists() and not state.is_dir():
        raise ProjectStoreError(".ip-pic 必须是目录")
    if create:
        state.mkdir(mode=0o700, exist_ok=True)
    return state


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise ProjectStoreError(f"{label} 不允许是符号链接")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProjectStoreError(f"{label} 不存在") from exc
    except json.JSONDecodeError as exc:
        raise ProjectStoreError(f"{label} 不是有效 JSON") from exc
    if not isinstance(value, dict):
        raise ProjectStoreError(f"{label} 必须为 object")
    return value


def _validate_registry(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("schema_version") != REGISTRY_SCHEMA:
        raise ProjectStoreError("registry schema 无效")
    if not isinstance(value.get("revision"), int) or value["revision"] < 0:
        raise ProjectStoreError("registry revision 无效")
    if set(value.get("active", {})) != KINDS:
        raise ProjectStoreError("registry active 结构无效")
    assets = value.get("assets")
    if not isinstance(assets, dict) or set(assets) != KINDS:
        raise ProjectStoreError("registry assets 结构无效")
    for kind in KINDS:
        if not isinstance(assets[kind], dict):
            raise ProjectStoreError(f"registry assets.{kind} 必须为 object")
    return copy.deepcopy(value)


def _read_registry(project_root: Path) -> dict[str, Any]:
    path = _state_root(project_root, create=False) / "registry.json"
    if not path.exists():
        return _new_registry()
    return _validate_registry(_load_json(path, "registry"))


def _version_path(
    project_root: Path,
    kind: str,
    asset_id: str,
    version: str,
) -> Path:
    if not VERSION_RE.fullmatch(str(version or "")):
        raise ProjectStoreError(f"version 无效：{version}")
    state = _state_root(project_root, create=False)
    return state / KIND_DIRS[kind] / asset_id / f"{version}.json"


def _next_version(registry: dict[str, Any], kind: str, asset_id: str) -> str:
    entry = registry["assets"][kind].get(asset_id, {})
    versions = entry.get("versions", [])
    numbers = [
        int(version[1:])
        for version in versions
        if isinstance(version, str) and VERSION_RE.fullmatch(version)
    ]
    number = max(numbers, default=0) + 1
    if number > 9999:
        raise ProjectStoreError("资产版本数量超过 v9999")
    return f"v{number:04d}"


def _plan_core(
    operation: str,
    registry: dict[str, Any],
    kind: str,
    asset_id: str,
    version: str,
    *,
    content: dict[str, Any] | None,
    activate: bool,
) -> dict[str, Any]:
    core: dict[str, Any] = {
        "schema_version": PLAN_SCHEMA,
        "plan_id": uuid.uuid4().hex,
        "operation": operation,
        "registry_revision": registry["revision"],
        "kind": kind,
        "id": asset_id,
        "version": version,
        "activate": bool(activate),
        "target": f"{KIND_DIRS[kind]}/{asset_id}/{version}.json",
    }
    if content is not None:
        core["content"] = copy.deepcopy(content)
        core["content_hash"] = _hash(content)
    return core


def _write_new_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise ProjectStoreError("目标父目录不允许是符号链接")
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise ProjectStoreError(f"目标已存在，拒绝覆盖：{path.name}") from exc


def _atomic_replace_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    nonce = uuid.uuid4().hex
    temporary = path.with_name(f".{path.name}.{nonce}.tmp")
    try:
        _write_new_json(temporary, value)
        os.replace(temporary, path)
    finally:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()


def _write_plan(project_root: Path, core: dict[str, Any]) -> dict[str, Any]:
    state = _state_root(project_root, create=True)
    plan = {**core, "plan_hash": _hash(core)}
    path = state / "plans" / f"{core['plan_id']}.json"
    _write_new_json(path, plan)
    return {
        "status": "preview",
        "operation": plan["operation"],
        "kind": plan["kind"],
        "id": plan["id"],
        "version": plan["version"],
        "activate": plan["activate"],
        "registry_revision": plan["registry_revision"],
        "content_hash": plan.get("content_hash"),
        "plan_hash": plan["plan_hash"],
        "plan_path": str(path),
    }


def plan_create(
    skill_root: Path,
    project_root: Path,
    kind: str,
    draft: dict[str, Any],
    *,
    activate: bool = False,
) -> dict[str, Any]:
    """Validate a draft and write a preview plan without changing active state."""

    normalized_kind = _require_kind(kind)
    project = _project_root(project_root)
    _state_root(project, create=True)
    content = normalize_asset_draft(
        Path(skill_root).resolve(),
        project,
        normalized_kind,
        draft,
    )
    registry = _read_registry(project)
    version = _next_version(registry, normalized_kind, content["id"])
    core = _plan_core(
        "create",
        registry,
        normalized_kind,
        content["id"],
        version,
        content=content,
        activate=activate,
    )
    return _write_plan(project, core)


def _entry_for(
    registry: dict[str, Any],
    kind: str,
    requested: str,
) -> tuple[str, dict[str, Any]]:
    normalized = str(requested or "").strip()
    entries = registry["assets"][kind]
    if normalized in entries:
        return normalized, entries[normalized]
    matches = [
        (asset_id, entry)
        for asset_id, entry in entries.items()
        if normalized == entry.get("display_name")
        or normalized in entry.get("aliases", [])
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ProjectStoreError(f"资产名称或别名不唯一：{requested}")
    raise ProjectStoreError(f"{kind} 资产不存在：{requested}")


def plan_activate(
    project_root: Path,
    kind: str,
    asset_id: str,
    version: str,
) -> dict[str, Any]:
    """Write a preview that changes only one active pointer."""

    normalized_kind = _require_kind(kind)
    project = _project_root(project_root)
    registry = _read_registry(project)
    canonical_id, entry = _entry_for(registry, normalized_kind, asset_id)
    if version not in entry.get("versions", []):
        raise ProjectStoreError(f"{normalized_kind} 版本不存在：{version}")
    core = _plan_core(
        "activate",
        registry,
        normalized_kind,
        canonical_id,
        version,
        content=None,
        activate=True,
    )
    return _write_plan(project, core)


def _load_plan(project_root: Path, plan_path: Path) -> dict[str, Any]:
    state = _state_root(project_root, create=False)
    plans = state / "plans"
    path = Path(plan_path)
    if path.is_symlink():
        raise ProjectStoreError("plan 不允许是符号链接")
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(plans.resolve())
    except ValueError as exc:
        raise ProjectStoreError("plan 必须位于当前项目 .ip-pic/plans") from exc
    plan = _load_json(resolved, "plan")
    if plan.get("schema_version") != PLAN_SCHEMA:
        raise ProjectStoreError("plan schema 无效")
    supplied_hash = plan.pop("plan_hash", None)
    if not isinstance(supplied_hash, str) or supplied_hash != _hash(plan):
        raise ProjectStoreError("plan hash 校验失败")
    plan["plan_hash"] = supplied_hash
    return plan


def _draft_from_content(kind: str, content: dict[str, Any]) -> dict[str, Any]:
    draft = copy.deepcopy(content)
    draft.pop("schema_version", None)
    if kind == "style":
        draft.pop("scope", None)
    return draft


@contextlib.contextmanager
def _project_lock(project_root: Path) -> Iterator[None]:
    state = _state_root(project_root, create=True)
    lock = state / ".lock"
    nonce = uuid.uuid4().hex
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ProjectStoreError("项目定制正在由另一个任务修改，请稍后重试") from exc
    try:
        os.write(descriptor, nonce.encode("ascii"))
        os.close(descriptor)
        yield
    finally:
        try:
            if not lock.is_symlink() and lock.read_text(encoding="utf-8") == nonce:
                lock.unlink()
        except FileNotFoundError:
            pass


def _validate_plan_shape(plan: dict[str, Any]) -> tuple[str, str, str]:
    allowed = {
        "schema_version",
        "plan_id",
        "operation",
        "registry_revision",
        "kind",
        "id",
        "version",
        "activate",
        "target",
        "content",
        "content_hash",
        "plan_hash",
    }
    unknown = sorted(set(plan) - allowed)
    if unknown:
        raise ProjectStoreError(f"plan 含未知字段：{unknown}")
    operation = str(plan.get("operation") or "")
    if operation not in {"create", "activate"}:
        raise ProjectStoreError("plan operation 无效")
    kind = _require_kind(str(plan.get("kind") or ""))
    asset_id = str(plan.get("id") or "")
    version = str(plan.get("version") or "")
    expected_target = f"{KIND_DIRS[kind]}/{asset_id}/{version}.json"
    if plan.get("target") != expected_target or not VERSION_RE.fullmatch(version):
        raise ProjectStoreError("plan target 或 version 无效")
    return operation, kind, asset_id


def _receipt(
    plan: dict[str, Any],
    registry_revision: int,
) -> dict[str, Any]:
    result = {
        "schema_version": RECEIPT_SCHEMA,
        "status": "applied",
        "change_id": uuid.uuid4().hex,
        "operation": plan["operation"],
        "kind": plan["kind"],
        "id": plan["id"],
        "version": plan["version"],
        "registry_revision": registry_revision,
        "plan_hash": plan["plan_hash"],
    }
    if plan.get("content_hash"):
        result["content_hash"] = plan["content_hash"]
    return result


def apply_plan(
    skill_root: Path,
    project_root: Path,
    plan_path: Path,
    *,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Apply one untampered plan after explicit user confirmation."""

    if not confirmed:
        raise ConfirmationRequired("用户明确确认后才可应用项目定制计划")
    project = _project_root(project_root)
    with _project_lock(project):
        plan = _load_plan(project, plan_path)
        operation, kind, asset_id = _validate_plan_shape(plan)
        registry = _read_registry(project)
        if plan.get("registry_revision") != registry["revision"]:
            raise ProjectStoreError("registry revision 已变化，请重新生成预览")

        version = plan["version"]
        created_version: Path | None = None
        if operation == "create":
            content = plan.get("content")
            if not isinstance(content, dict):
                raise ProjectStoreError("create plan 缺少 content")
            if plan.get("content_hash") != _hash(content):
                raise ProjectStoreError("content hash 校验失败")
            normalized = normalize_asset_draft(
                Path(skill_root).resolve(),
                project,
                kind,
                _draft_from_content(kind, content),
            )
            if _canonical(normalized) != _canonical(content):
                raise ProjectStoreError("plan content 标准化校验失败")
            target = _version_path(project, kind, asset_id, version)
            if target.exists() or target.is_symlink():
                raise ProjectStoreError(f"目标已存在，拒绝覆盖：{target.name}")
            version_document = {**copy.deepcopy(content), "version": version}
            _write_new_json(target, version_document)
            created_version = target
            entry = registry["assets"][kind].setdefault(
                asset_id,
                {
                    "display_name": content["display_name"],
                    "aliases": content.get("aliases", []),
                    "versions": [],
                },
            )
            if version in entry["versions"]:
                raise ProjectStoreError(f"版本已存在，拒绝覆盖：{version}")
            entry["display_name"] = content["display_name"]
            entry["aliases"] = content.get("aliases", [])
            entry["versions"].append(version)
        else:
            _canonical_id, entry = _entry_for(registry, kind, asset_id)
            if version not in entry.get("versions", []):
                raise ProjectStoreError(f"{kind} 版本不存在：{version}")

        if plan.get("activate") is True:
            registry["active"][kind] = {"id": asset_id, "version": version}
        registry["revision"] += 1
        registry_path = _state_root(project, create=True) / "registry.json"
        try:
            _atomic_replace_json(registry_path, registry)
        except Exception:
            if created_version is not None and created_version.is_file():
                stored = _load_json(created_version, "新版本")
                stored.pop("version", None)
                if _hash(stored) == plan.get("content_hash"):
                    created_version.unlink()
            raise

        receipt = _receipt(plan, registry["revision"])
        receipt_path = (
            _state_root(project, create=True)
            / "receipts"
            / f"{receipt['change_id']}.json"
        )
        _write_new_json(receipt_path, receipt)
        return receipt


def list_assets(project_root: Path, kind: str | None = None) -> dict[str, Any]:
    """Return a redacted index of project assets."""

    normalized_kind = _require_kind(kind) if kind is not None else None
    registry = _read_registry(_project_root(project_root))
    kinds = [normalized_kind] if normalized_kind else sorted(KINDS)
    assets: list[dict[str, Any]] = []
    for current_kind in kinds:
        for asset_id, entry in sorted(registry["assets"][current_kind].items()):
            assets.append(
                {
                    "kind": current_kind,
                    "id": asset_id,
                    "display_name": entry["display_name"],
                    "aliases": list(entry.get("aliases", [])),
                    "versions": list(entry.get("versions", [])),
                    "active": registry["active"][current_kind]
                    if registry["active"][current_kind]
                    and registry["active"][current_kind]["id"] == asset_id
                    else None,
                }
            )
    return {
        "schema_version": "ip-pic-project-list/v1",
        "registry_revision": registry["revision"],
        "assets": assets,
    }


def resolve_asset(
    project_root: Path,
    kind: str,
    asset_id: str | None = None,
    *,
    version: str = "active",
) -> dict[str, Any]:
    """Resolve one immutable asset by id/alias and version or active pointer."""

    normalized_kind = _require_kind(kind)
    project = _project_root(project_root)
    registry = _read_registry(project)
    if asset_id in (None, ""):
        active = registry["active"][normalized_kind]
        if not isinstance(active, dict):
            raise ProjectStoreError(f"{normalized_kind} 尚未设置活动资产")
        canonical_id = active["id"]
        entry = registry["assets"][normalized_kind][canonical_id]
        requested_version = active["version"] if version == "active" else version
    else:
        canonical_id, entry = _entry_for(registry, normalized_kind, str(asset_id))
        if version == "active":
            active = registry["active"][normalized_kind]
            if not isinstance(active, dict) or active.get("id") != canonical_id:
                if not entry.get("versions"):
                    raise ProjectStoreError(f"{normalized_kind} 资产没有版本")
                requested_version = entry["versions"][-1]
            else:
                requested_version = active["version"]
        else:
            requested_version = version
    if requested_version not in entry.get("versions", []):
        raise ProjectStoreError(
            f"{normalized_kind} 版本不存在：{canonical_id}@{requested_version}"
        )
    value = _load_json(
        _version_path(
            project,
            normalized_kind,
            canonical_id,
            requested_version,
        ),
        f"{normalized_kind} 版本",
    )
    if value.get("id") != canonical_id or value.get("version") != requested_version:
        raise ProjectStoreError("资产版本内容与 registry 不一致")
    return value

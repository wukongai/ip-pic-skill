"""IP-only batch planning, execution, retry, and full-rebuild contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

from .compiler import compile_request
from .errors import IPPicError


BATCH_SCHEMA_VERSION = "ip-pic-batch/v1"
SHOT_PLAN_SCHEMA_VERSION = "ip-pic-shot-plan/v1"
BATCH_RESULT_SCHEMA_VERSION = "ip-pic-batch-result/v1"

Renderer = Callable[[dict[str, Any], Path], dict[str, Any]]

SQUARE_FAMILIES = (
    "diagonal-cross",
    "top-down-partial",
    "seated-loop",
    "close-hands",
    "object-dominant",
    "contrast-bridge",
)
SQUARE_CROPS = (
    "medium",
    "top-down-partial",
    "full-body-seated",
    "close-hands",
    "object-dominant",
    "medium-wide",
)
SQUARE_ORIENTATIONS = (
    "left",
    "back-three-quarter",
    "right",
    "front",
    "left",
    "right",
)
SQUARE_ACTIONS = (
    "斜向跨画面操作主物件",
    "俯视桌面整理主题物件",
    "坐姿推动圆形闭环",
    "双手近景连接关键部件",
    "从侧后方操作主导装置",
    "跨越并连接左右两种状态",
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IPPicError(f"cannot read batch manifest: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise IPPicError(f"batch manifest must be an object: {path}")
    return value


def _validate_request(request: dict[str, Any]) -> list[dict[str, Any]]:
    if request.get("schema_version") != BATCH_SCHEMA_VERSION:
        raise IPPicError(f"batch schema_version must be {BATCH_SCHEMA_VERSION}")
    raw_items = request.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise IPPicError("batch.items must be a non-empty array")
    if any(not isinstance(item, dict) for item in raw_items):
        raise IPPicError("every batch item must be an object")
    return copy.deepcopy(raw_items)


def _is_square_video(item: dict[str, Any]) -> bool:
    selection = (
        item.get("selection_receipt")
        if isinstance(item.get("selection_receipt"), dict)
        else {}
    )
    return (
        _text(item.get("scene")) == "ip_video_keyframe"
        and _text(selection.get("canvas")) == "1:1"
    )


def build_shot_plan(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the full-rebuild shot manifest required by the original IP SOP."""

    if not items or any(not isinstance(item, dict) for item in items):
        raise IPPicError("shot plan items must be a non-empty object array")
    shots: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        composition = (
            item.get("composition")
            if isinstance(item.get("composition"), dict)
            else {}
        )
        if _is_square_video(item):
            rotation_index = index % len(SQUARE_FAMILIES)
            planned = {
                "composition_family": SQUARE_FAMILIES[rotation_index],
                "crop": SQUARE_CROPS[rotation_index],
                "orientation": SQUARE_ORIENTATIONS[rotation_index],
                "action": SQUARE_ACTIONS[rotation_index],
                "text_layout_variant": (
                    "square-left" if index % 2 == 0 else "square-right"
                ),
                "subtitle_safe_zone": "bottom-12-to-15-percent",
            }
        else:
            planned = {
                key: composition.get(key)
                for key in (
                    "composition_family",
                    "crop",
                    "orientation",
                    "action",
                    "text_layout_variant",
                    "subtitle_safe_zone",
                )
                if composition.get(key) not in (None, "")
            }
        content = item.get("content") if isinstance(item.get("content"), dict) else {}
        shots.append(
            {
                "anchor_id": _text(item.get("id")) or f"shot-{index + 1:02d}",
                "source_excerpt": _text(content.get("summary"))
                or _text(content.get("headline")),
                "duration_hint": _text(item.get("duration_hint")) or "8-12s",
                "kicker": _text(content.get("subheadline")),
                "headline": _text(content.get("headline")),
                "support": _text(content.get("summary")),
                "structure_type": planned.get("composition_family", ""),
                "shot_type": planned.get("composition_family", ""),
                "ip_scale": _text(composition.get("ip_scale")) or "co-lead",
                "body_weight": _text(composition.get("body_weight"))
                or ("seated-shift" if planned.get("composition_family") == "seated-loop" else "active"),
                "physical_metaphor": _text(
                    (item.get("visual") or {}).get("subject")
                    if isinstance(item.get("visual"), dict)
                    else ""
                ),
                "familiar_objects": list(
                    (item.get("visual") or {}).get("metaphors", [])
                    if isinstance(item.get("visual"), dict)
                    and isinstance((item.get("visual") or {}).get("metaphors"), list)
                    else []
                )[:5],
                "orange_motion_path": _text(composition.get("orange_motion_path"))
                or "single-primary-path",
                "visual_anchor_position": _text(
                    composition.get("visual_anchor_position")
                )
                or ("left" if index % 2 == 0 else "right"),
                **planned,
            }
        )
    return {
        "schema_version": SHOT_PLAN_SCHEMA_VERSION,
        "rotation_contract": {
            "adjacent_unique": [
                "composition_family",
                "crop",
                "orientation",
                "action",
            ],
            "recent_six_minimum_families": 4,
            "square_families": list(SQUARE_FAMILIES),
        },
        "shots": shots,
    }


def _apply_shot(item: dict[str, Any], shot: dict[str, Any], index: int) -> dict[str, Any]:
    result = copy.deepcopy(item)
    result["director_context"] = {"sequence_index": index}
    composition = (
        copy.deepcopy(result.get("composition"))
        if isinstance(result.get("composition"), dict)
        else {}
    )
    for key in (
        "composition_family",
        "crop",
        "orientation",
        "action",
        "text_layout_variant",
        "subtitle_safe_zone",
        "ip_scale",
        "body_weight",
        "visual_anchor_position",
    ):
        if shot.get(key) not in (None, ""):
            composition[key] = shot[key]
    result["composition"] = composition
    return result


def _write_manifest(output: Path, manifest: dict[str, Any]) -> Path:
    path = output / "ip-pic-batch-manifest.json"
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _summarize(manifest: dict[str, Any]) -> None:
    items = manifest["items"]
    succeeded = sum(item.get("status") == "ok" for item in items)
    failed = len(items) - succeeded
    manifest["succeeded"] = succeeded
    manifest["failed"] = failed
    manifest["status"] = "ok" if failed == 0 else "partial_failure"


def run_batch(
    root: Path,
    request: dict[str, Any],
    output_dir: Path,
    *,
    renderer: Renderer,
) -> Path:
    """Compile and render each item while preserving per-item failures."""

    items = _validate_request(request)
    output = output_dir.resolve()
    if output.exists():
        raise IPPicError(f"output directory already exists; refusing to overwrite: {output}")
    output.mkdir(parents=True)
    shot_plan = build_shot_plan(items)
    (output / "shot-plan.json").write_text(
        json.dumps(shot_plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    records: list[dict[str, Any]] = []
    for index, (item, shot) in enumerate(zip(items, shot_plan["shots"]), 1):
        item_id = _text(item.get("id")) or f"item-{index:02d}"
        item_dir = output / f"{index:02d}-{item_id}"
        record: dict[str, Any] = {
            "index": index,
            "id": item_id,
            "output_dir": str(item_dir),
            "attempts": 1,
        }
        try:
            compiled = compile_request(
                root,
                _apply_shot(item, shot, index - 1),
                item_dir,
                write=True,
            )
            record["compiled_manifest_path"] = compiled["paths"]["manifest"]
            record["compiled_manifest"] = compiled["manifest"]
            receipt = renderer(compiled["manifest"], item_dir)
            if not isinstance(receipt, dict) or receipt.get("status") != "ok":
                raise IPPicError("renderer did not return an ok receipt")
            record["render_receipt"] = receipt
            record["status"] = "ok"
        except (IPPicError, OSError, ValueError, RuntimeError) as exc:
            record["status"] = "failed"
            record["error"] = str(exc)
        records.append(record)
    manifest: dict[str, Any] = {
        "schema_version": BATCH_RESULT_SCHEMA_VERSION,
        "id": _text(request.get("id")) or "ip-pic-batch",
        "output_dir": str(output),
        "shot_plan": str(output / "shot-plan.json"),
        "items": records,
    }
    _summarize(manifest)
    return _write_manifest(output, manifest)


def retry_failed(manifest_path: Path, *, renderer: Renderer) -> Path:
    """Retry render-stage failures without recompiling or touching successes."""

    path = manifest_path.resolve()
    manifest = _load_json(path)
    items = manifest.get("items")
    if not isinstance(items, list):
        raise IPPicError("batch result items must be an array")
    for record in items:
        if not isinstance(record, dict) or record.get("status") != "failed":
            continue
        compiled_path = Path(_text(record.get("compiled_manifest_path")))
        if not compiled_path.is_file():
            record["error"] = "failed item has no compiled manifest; start a new batch"
            continue
        compiled = _load_json(compiled_path)
        item_dir = Path(_text(record.get("output_dir")))
        record["attempts"] = int(record.get("attempts") or 1) + 1
        try:
            receipt = renderer(compiled, item_dir)
            if not isinstance(receipt, dict) or receipt.get("status") != "ok":
                raise IPPicError("renderer did not return an ok receipt")
            record["render_receipt"] = receipt
            record["status"] = "ok"
            record.pop("error", None)
        except (IPPicError, OSError, ValueError, RuntimeError) as exc:
            record["error"] = str(exc)
    _summarize(manifest)
    return _write_manifest(path.parent, manifest)


def _within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _exclude_old_assets(
    request: dict[str, Any],
    old_output: Path,
) -> tuple[dict[str, Any], list[str]]:
    rebuilt = copy.deepcopy(request)
    excluded: list[str] = []
    for item in rebuilt.get("items", []):
        visual = item.get("visual") if isinstance(item.get("visual"), dict) else {}
        assets = (
            visual.get("authorized_assets")
            if isinstance(visual.get("authorized_assets"), list)
            else []
        )
        kept = []
        for asset in assets:
            raw_path = asset.get("path") if isinstance(asset, dict) else None
            if raw_path and _within(Path(str(raw_path)).expanduser(), old_output):
                excluded.append(str(Path(str(raw_path)).expanduser().resolve()))
            else:
                kept.append(asset)
        visual["authorized_assets"] = kept
        item["visual"] = visual
    return rebuilt, excluded


def rebuild_batch(
    root: Path,
    previous_manifest_path: Path,
    request: dict[str, Any],
    output_dir: Path,
    *,
    renderer: Renderer,
) -> Path:
    """Start a clean batch and prevent rejected old outputs becoming references."""

    previous_path = previous_manifest_path.resolve()
    previous = _load_json(previous_path)
    old_output = Path(_text(previous.get("output_dir"))).resolve()
    new_output = output_dir.resolve()
    if new_output == old_output or _within(new_output, old_output):
        raise IPPicError("整批重建必须使用旧批次之外的新目录 (old batch output is forbidden)")
    sanitized, excluded = _exclude_old_assets(request, old_output)
    result_path = run_batch(root, sanitized, new_output, renderer=renderer)
    result = _load_json(result_path)
    result["rebuild"] = {
        "source_batch": str(previous_path),
        "old_assets_excluded": excluded,
        "old_output_reused": False,
        "new_shot_plan": True,
    }
    return _write_manifest(new_output, result)

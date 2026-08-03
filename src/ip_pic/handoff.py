"""Immutable, provider-neutral render handoff."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable


def build_render_handoff(
    *,
    item_id: str,
    prompt_file: Path,
    size: str,
    output_dir: Path,
    assets: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    normalized = []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        normalized.append(
            {
                "id": str(asset.get("id") or ""),
                "path": str(asset.get("path") or ""),
                "purpose": str(asset.get("purpose") or "content"),
                "ownership": str(asset.get("ownership") or "authorized"),
                "required": bool(asset.get("required", True)),
                "sha256": str(asset.get("sha256") or ""),
            }
        )
    return {
        "schema_version": "image-render-handoff/v1",
        "id": item_id,
        "prompt_file": str(prompt_file),
        "size": size,
        "output_dir": str(output_dir),
        "assets": normalized,
    }

"""Structural IP template discovery."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


class TemplateError(ValueError):
    """A structural template registry or template is invalid."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TemplateError(f"template data not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TemplateError(f"template data is invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise TemplateError(f"template data must be an object: {path}")
    return value


def _entries(root: Path) -> list[dict[str, Any]]:
    registry = _load(root / "templates" / "registry.json")
    if registry.get("schema_version") != "ip-template-registry/v1":
        raise TemplateError("template registry schema is invalid")
    entries = registry.get("templates")
    if not isinstance(entries, list):
        raise TemplateError("template registry templates must be an array")
    ids = [item.get("id") for item in entries if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        raise TemplateError("template registry contains duplicate ids")
    return [dict(item) for item in entries]


def list_templates(root: Path, formal_only: bool = False) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for entry in _entries(root):
        if formal_only and entry.get("classification") != "formal":
            continue
        template = _load(root / "templates" / str(entry["file"]))
        if template.get("id") != entry.get("id"):
            raise TemplateError(f"template id does not match registry: {entry['file']}")
        result.append({**copy.deepcopy(template), **copy.deepcopy(entry)})
    return result


def resolve_template(root: Path, value: str) -> dict[str, Any]:
    requested = str(value or "").strip().casefold()
    if not requested:
        raise TemplateError("template id or alias is required")
    for template in list_templates(root):
        candidates = [template["id"], *template.get("aliases", [])]
        if requested in {str(item).strip().casefold() for item in candidates}:
            return template
    raise TemplateError(f"unknown template: {value}")

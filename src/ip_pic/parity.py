"""Machine-verifiable mapping from the private behavior source to public files."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "ip-pic-parity-manifest/v1"
SKILL_PREFIX = "skills/ip-illustration-factory/"


class ParityError(ValueError):
    """The parity manifest is structurally unsafe or ambiguous."""


@dataclass(frozen=True)
class ParityReport:
    source_file_count: int
    mapped_source_file_count: int
    unmapped_source_files: tuple[str, ...]
    extra_source_entries: tuple[str, ...]
    duplicate_source_files: tuple[str, ...]
    formal_template_count: int
    compatibility_template_count: int
    render_style_count: int

    @property
    def ok(self) -> bool:
        return not (
            self.unmapped_source_files
            or self.extra_source_entries
            or self.duplicate_source_files
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "source_file_count": self.source_file_count,
            "mapped_source_file_count": self.mapped_source_file_count,
            "unmapped_source_files": list(self.unmapped_source_files),
            "extra_source_entries": list(self.extra_source_entries),
            "duplicate_source_files": list(self.duplicate_source_files),
            "formal_template_count": self.formal_template_count,
            "compatibility_template_count": self.compatibility_template_count,
            "render_style_count": self.render_style_count,
        }


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ParityError(f"parity manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ParityError(f"parity manifest is invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ParityError("parity manifest must be a JSON object")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ParityError(f"schema_version must equal {SCHEMA_VERSION}")
    return value


def _validate_entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ParityError("parity manifest entries must be a non-empty array")
    allowed = manifest.get("allowed_decisions")
    if not isinstance(allowed, list) or not allowed:
        raise ParityError("allowed_decisions must be a non-empty array")
    allowed_set = {str(item) for item in allowed}
    result: list[dict[str, Any]] = []
    for index, raw in enumerate(entries):
        if not isinstance(raw, dict):
            raise ParityError(f"entry {index} must be an object")
        source = raw.get("source")
        decision = raw.get("decision")
        capability = raw.get("capability")
        if not isinstance(source, str) or not source.strip():
            raise ParityError(f"entry {index} source must be non-empty")
        if decision not in allowed_set:
            raise ParityError(f"entry {source} has unknown decision {decision!r}")
        if not isinstance(capability, str) or not capability.strip():
            raise ParityError(f"entry {source} capability must be non-empty")
        if decision == "exclude":
            if not str(raw.get("replacement") or raw.get("reason") or "").strip():
                raise ParityError(
                    f"exclude entry {source} requires a replacement or reason"
                )
        else:
            target = raw.get("target")
            if not isinstance(target, str) or not target.strip():
                raise ParityError(f"entry {source} requires a target")
            if Path(target).is_absolute() or ".." in Path(target).parts:
                raise ParityError(f"entry {source} has unsafe target {target!r}")
        result.append(dict(raw))
    return result


def verify_manifest(manifest_path: Path, source_root: Path) -> ParityReport:
    manifest = _load_manifest(manifest_path)
    entries = _validate_entries(manifest)
    skill_root = source_root / "skills" / "ip-illustration-factory"
    if not skill_root.is_dir():
        raise ParityError(f"source skill not found: {skill_root}")
    actual = {
        str(path.relative_to(source_root))
        for path in skill_root.rglob("*")
        if path.is_file()
    }
    private_source_id = os.environ.get("IP_PIC_PRIVATE_SOURCE_ID", "")
    mapped = [
        str(entry["source"]).replace("{private-id}", private_source_id)
        for entry in entries
        if str(entry["source"]).startswith(SKILL_PREFIX)
    ]
    mapped_set = set(mapped)
    duplicates = {source for source in mapped_set if mapped.count(source) > 1}
    return ParityReport(
        source_file_count=len(actual),
        mapped_source_file_count=len(mapped),
        unmapped_source_files=tuple(sorted(actual - mapped_set)),
        extra_source_entries=tuple(sorted(mapped_set - actual)),
        duplicate_source_files=tuple(sorted(duplicates)),
        formal_template_count=sum(
            entry.get("capability") == "formal-template" for entry in entries
        ),
        compatibility_template_count=sum(
            entry.get("capability") == "compatibility-template" for entry in entries
        ),
        render_style_count=sum(
            entry.get("capability") == "render-style" for entry in entries
        ),
    )

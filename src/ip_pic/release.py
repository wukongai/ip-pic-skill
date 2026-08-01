"""Static public-release verification for the standalone candidate."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".toml", ".txt"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
FORBIDDEN_RUNTIME_KEYS = {
    "api_key",
    "access_token",
    "credential",
    "provider",
    "adapter",
    "balance",
    "retry",
    "fallback",
}
REQUIRED_FILES = {
    "SKILL.md",
    "skill.contract.yaml",
    "README.zh-CN.md",
    "README.en.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "UPSTREAM-LICENSE.txt",
    "NOTICE.md",
    "upstream.lock.json",
    "pyproject.toml",
    "parity/ip-parity-manifest.json",
    "release/public-release-manifest.json",
    "extensions/title-bands/editorial-ink-v2.json",
    "extensions/title-bands/editorial-warm-v1.json",
}


@dataclass(frozen=True)
class ReleaseReport:
    errors: tuple[str, ...]
    formal_templates: int
    compatibility_templates: int
    render_styles: int
    scanned_text_files: int

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "formal_templates": self.formal_templates,
            "compatibility_templates": self.compatibility_templates,
            "render_styles": self.render_styles,
            "scanned_text_files": self.scanned_text_files,
        }


def _load(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"JSON root must be an object: {path}")
        return {}
    return value


def _walk_keys(value: Any, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if str(key).casefold() in FORBIDDEN_RUNTIME_KEYS:
                hits.append(path)
            hits.extend(_walk_keys(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(_walk_keys(item, f"{prefix}[{index}]"))
    return hits


def verify_release(root: Path) -> ReleaseReport:
    root = root.resolve()
    errors: list[str] = []
    for relative in sorted(REQUIRED_FILES):
        if not (root / relative).is_file():
            errors.append(f"missing required public file: {relative}")

    template_registry = _load(root / "templates" / "registry.json", errors)
    templates = template_registry.get("templates")
    templates = templates if isinstance(templates, list) else []
    formal = sum(
        isinstance(item, dict) and item.get("classification") == "formal"
        for item in templates
    )
    compatibility = sum(
        isinstance(item, dict) and item.get("classification") == "compatibility"
        for item in templates
    )
    style_registry = _load(root / "profiles" / "render-styles.json", errors)
    styles = style_registry.get("styles")
    styles = styles if isinstance(styles, list) else []
    if formal != 13:
        errors.append(f"formal template count must be 13, got {formal}")
    if compatibility != 1:
        errors.append(f"compatibility template count must be 1, got {compatibility}")
    if len(styles) != 6:
        errors.append(f"render style count must be 6, got {len(styles)}")

    public_manifest = _load(
        root / "release" / "public-release-manifest.json",
        errors,
    )
    if set(public_manifest.get("backends", [])) != {
        "codex-image-tool",
        "openai-direct",
        "host-ai-router",
        "prompt-only",
    }:
        errors.append("public release must declare exactly four supported backends")

    parity = _load(root / "parity" / "ip-parity-manifest.json", errors)
    for entry in parity.get("entries", []):
        if not isinstance(entry, dict) or entry.get("decision") == "exclude":
            continue
        target = root / str(entry.get("target") or "")
        if not target.is_file():
            errors.append(f"missing parity target: {entry.get('target')}")

    private_tokens = (
        "艾" + "笑",
        "aix" + "iao",
        "/Users/" + "aim5",
        "/private/tmp/" + "ip-pic-style-parity-20260731",
    )
    secret_pattern = re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")
    scanned = 0
    for path in root.rglob("*"):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.is_symlink():
            errors.append(f"public candidate contains a symbolic link: {path.relative_to(root)}")
            continue
        if not path.is_file():
            continue
        if path.suffix.casefold() in IMAGE_SUFFIXES:
            errors.append(f"public candidate contains a binary image: {path.relative_to(root)}")
            continue
        if path.name.startswith(".env"):
            errors.append(f"public candidate contains an environment file: {path.relative_to(root)}")
        if path.suffix.casefold() not in TEXT_SUFFIXES:
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in private_tokens:
            if token.casefold() in text.casefold():
                errors.append(f"private token in {path.relative_to(root)}")
        if secret_pattern.search(text):
            errors.append(f"credential-shaped value in {path.relative_to(root)}")

    for directory in (root / "templates", root / "profiles"):
        for path in directory.rglob("*.json"):
            value = _load(path, errors)
            for key in _walk_keys(value):
                errors.append(
                    f"runtime/backend key {key!r} is forbidden in {path.relative_to(root)}"
                )

    upstream = _load(root / "upstream.lock.json", errors)
    upstream_data = (
        upstream.get("upstream")
        if isinstance(upstream.get("upstream"), dict)
        else {}
    )
    if upstream_data.get("license") != "MIT" or not upstream_data.get("commit"):
        errors.append("upstream MIT license and locked commit are required")

    return ReleaseReport(
        errors=tuple(sorted(set(errors))),
        formal_templates=formal,
        compatibility_templates=compatibility,
        render_styles=len(styles),
        scanned_text_files=scanned,
    )

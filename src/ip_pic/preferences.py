from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Any, Mapping

from .errors import SecurityError, ValidationError


DEFAULT_PREFERENCES: dict[str, Any] = {
    "preferred_image_backend": "auto",
    "default_output_dir": "imgs",
    "default_style": "auto",
    "default_canvas": "16:9",
    "generation_batch_size": 4,
    "language": "zh",
}

ALLOWED_KEYS = frozenset(DEFAULT_PREFERENCES)
VALID_CANVASES = {"16:9", "1:1", "9:16"}
VALID_LANGUAGES = {"zh", "en", "auto"}


def _parse_scalar(raw: str) -> Any:
    value = raw.strip().strip('"').strip("'")
    if value.isdigit():
        return int(value)
    return value


def parse_extend(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    inside_yaml = False
    saw_fence = False
    values: dict[str, Any] = {}
    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            if not saw_fence and stripped in {"```yaml", "```yml"}:
                saw_fence = True
                inside_yaml = True
                continue
            if inside_yaml:
                inside_yaml = False
                break
        if saw_fence and not inside_yaml:
            continue
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        if key not in ALLOWED_KEYS:
            raise SecurityError(f"preference key is not allowed: {key}")
        values[key] = _parse_scalar(raw_value)
    merged = dict(DEFAULT_PREFERENCES)
    merged.update(values)
    validate_preferences(merged)
    return merged


def validate_preferences(values: Mapping[str, Any]) -> None:
    extra = set(values) - ALLOWED_KEYS
    if extra:
        raise SecurityError(f"preference keys are not allowed: {sorted(extra)}")
    backend = values["preferred_image_backend"]
    if not isinstance(backend, str) or not backend.strip():
        raise ValidationError("preferred_image_backend must be a non-empty string")
    if values["default_canvas"] not in VALID_CANVASES:
        raise ValidationError("default_canvas must be 16:9, 1:1 or 9:16")
    batch_size = values["generation_batch_size"]
    if not isinstance(batch_size, int) or not 1 <= batch_size <= 8:
        raise ValidationError("generation_batch_size must be between 1 and 8")
    if values["language"] not in VALID_LANGUAGES:
        raise ValidationError("language must be zh, en or auto")
    for key in ("default_output_dir", "default_style"):
        if not isinstance(values[key], str) or not values[key].strip():
            raise ValidationError(f"{key} must be a non-empty string")


def preference_candidates(
    project_root: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> list[Path]:
    env = dict(os.environ if environment is None else environment)
    home = Path(env.get("HOME", str(Path.home()))).expanduser()
    xdg = Path(env.get("XDG_CONFIG_HOME", str(home / ".config"))).expanduser()
    candidates: list[Path] = []
    if project_root is not None:
        candidates.append(project_root.resolve() / ".ip-pic" / "EXTEND.md")
    candidates.append(xdg / "ip-pic" / "EXTEND.md")
    candidates.append(home / ".ip-pic" / "EXTEND.md")
    return candidates


def legacy_preference_candidates(
    project_root: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> list[Path]:
    env = dict(os.environ if environment is None else environment)
    home = Path(env.get("HOME", str(Path.home()))).expanduser()
    xdg = Path(env.get("XDG_CONFIG_HOME", str(home / ".config"))).expanduser()
    candidates: list[Path] = []
    if project_root is not None:
        candidates.append(
            project_root.resolve()
            / ".custom-ip-illustration"
            / "EXTEND.md"
        )
    candidates.append(xdg / "custom-ip-illustration" / "EXTEND.md")
    candidates.append(home / ".custom-ip-illustration" / "EXTEND.md")
    return candidates


def resolve_preferences(
    project_root: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], Path | None]:
    for candidate in preference_candidates(project_root, environment):
        if candidate.is_file():
            return parse_extend(candidate), candidate
    for candidate in legacy_preference_candidates(project_root, environment):
        if candidate.is_file():
            warnings.warn(
                "Legacy custom-ip-illustration preferences are read-only; "
                "move them to the matching .ip-pic or ip-pic config path.",
                DeprecationWarning,
                stacklevel=2,
            )
            return parse_extend(candidate), candidate
    return dict(DEFAULT_PREFERENCES), None

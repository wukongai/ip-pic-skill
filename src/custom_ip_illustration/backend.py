from __future__ import annotations

from typing import Any

from .errors import ValidationError


def _available_backends(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    backends = inventory.get("backends")
    if not isinstance(backends, list):
        raise ValidationError("inventory.backends must be a list")
    available: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, backend in enumerate(backends):
        if not isinstance(backend, dict):
            raise ValidationError(f"inventory.backends[{index}] must be an object")
        backend_id = backend.get("id")
        kind = backend.get("kind")
        if not isinstance(backend_id, str) or not backend_id.strip():
            raise ValidationError(f"inventory.backends[{index}].id is required")
        if backend_id in seen:
            raise ValidationError(f"duplicate backend id: {backend_id}")
        seen.add(backend_id)
        if kind not in {"native", "third_party"}:
            raise ValidationError(
                f"inventory.backends[{index}].kind must be native or third_party"
            )
        if backend.get("available") is True:
            available.append(backend)
    return available


def resolve_backend(
    inventory: dict[str, Any],
    requested: str = "auto",
    preference: str = "auto",
) -> dict[str, Any]:
    available = _available_backends(inventory)
    by_id = {item["id"]: item for item in available}

    if requested != "auto" and requested in by_id:
        return _selected(requested, "request_override")
    if preference != "auto" and preference in by_id:
        return _selected(preference, "saved_preference")

    native = sorted(
        (item for item in available if item["kind"] == "native"),
        key=lambda item: (not bool(item.get("default")), item["id"]),
    )
    if native:
        return _selected(native[0]["id"], "host_native")

    third_party = sorted(
        (item for item in available if item["kind"] == "third_party"),
        key=lambda item: item["id"],
    )
    if len(third_party) == 1:
        return _selected(third_party[0]["id"], "single_third_party")
    if len(third_party) > 1:
        return {
            "status": "needs_user_choice",
            "backend_id": None,
            "reason": "multiple_third_party_backends",
            "choices": [item["id"] for item in third_party],
        }
    return {
        "status": "compile_only",
        "backend_id": None,
        "reason": "no_compatible_backend",
        "choices": [],
    }


def _selected(backend_id: str, reason: str) -> dict[str, Any]:
    return {
        "status": "selected",
        "backend_id": backend_id,
        "reason": reason,
        "choices": [],
    }

from __future__ import annotations

from typing import Any

from .errors import ValidationError


PUBLIC_BACKEND_ORDER = (
    "codex-image-tool",
    "openai-direct",
    "ai-router",
    "prompt-only",
)

PUBLIC_BACKEND_METADATA = {
    "codex-image-tool": {
        "label": "Codex Image Tool",
        "description": "Use Codex's built-in image generation tool.",
        "requires_setup": False,
    },
    "openai-direct": {
        "label": "OpenAI Direct API",
        "description": "Generate with your configured OpenAI API access.",
        "requires_setup": True,
    },
    "ai-router": {
        "label": "Existing ai-router",
        "description": "Use an ai-router installation already connected to this host.",
        "requires_setup": True,
    },
    "prompt-only": {
        "label": "Prompt only",
        "description": "Save the prompt and render request without generating an image.",
        "requires_setup": False,
    },
}


def _inventory_backends(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    backends = inventory.get("backends")
    if not isinstance(backends, list):
        raise ValidationError("inventory.backends must be a list")
    validated: list[dict[str, Any]] = []
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
        validated.append(backend)
    return validated


def _choice_details(backends: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {item["id"]: item for item in backends}
    details: list[dict[str, Any]] = []
    for backend_id in PUBLIC_BACKEND_ORDER:
        metadata = PUBLIC_BACKEND_METADATA[backend_id]
        inventory_item = by_id.get(backend_id)
        if backend_id == "prompt-only":
            available = True
            configured = True
        else:
            available = bool(inventory_item and inventory_item.get("available") is True)
            configured = bool(
                inventory_item.get("configured", available)
                if inventory_item is not None
                else False
            )
        requires_setup = False if available and configured else bool(
            inventory_item.get("requires_setup", metadata["requires_setup"])
            if inventory_item is not None
            else metadata["requires_setup"]
        )
        details.append(
            {
                "id": backend_id,
                "label": (
                    inventory_item.get("label")
                    if inventory_item is not None
                    and isinstance(inventory_item.get("label"), str)
                    and inventory_item["label"].strip()
                    else metadata["label"]
                ),
                "description": metadata["description"],
                "available": available,
                "configured": configured,
                "requires_setup": requires_setup,
            }
        )
    return details


def _needs_user_choice(reason: str, backends: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "needs_user_choice",
        "backend_id": None,
        "reason": reason,
        "choices": list(PUBLIC_BACKEND_ORDER),
        "choice_details": _choice_details(backends),
    }


def _needs_setup(backend_id: str, backends: list[dict[str, Any]]) -> dict[str, Any]:
    detail = next(
        item for item in _choice_details(backends) if item["id"] == backend_id
    )
    return {
        "status": "needs_setup",
        "backend_id": backend_id,
        "reason": "requested_backend_unavailable",
        "choices": [backend_id],
        "choice_details": [detail],
    }


def _backend_is_ready(inventory_item: dict[str, Any] | None) -> bool:
    return bool(
        inventory_item is not None
        and inventory_item.get("available") is True
        and inventory_item.get("configured", True) is True
    )


def resolve_backend(
    inventory: dict[str, Any],
    requested: str = "auto",
    preference: str = "auto",
) -> dict[str, Any]:
    backends = _inventory_backends(inventory)
    available = [item for item in backends if item.get("available") is True]
    by_id = {item["id"]: item for item in available}
    inventory_by_id = {item["id"]: item for item in backends}

    if requested == "prompt-only":
        return _compile_only("prompt-only", "request_override")
    if requested != "auto":
        if requested in PUBLIC_BACKEND_ORDER:
            inventory_item = inventory_by_id.get(requested)
            if _backend_is_ready(inventory_item):
                return _selected(requested, "request_override")
            return _needs_setup(requested, backends)
        if requested in by_id:
            return _selected(requested, "request_override")
        return _needs_user_choice("requested_backend_unavailable", backends)
    if preference == "prompt-only":
        return _compile_only("prompt-only", "saved_preference")
    if preference in PUBLIC_BACKEND_ORDER:
        if _backend_is_ready(inventory_by_id.get(preference)):
            return _selected(preference, "saved_preference")
        return _needs_user_choice("saved_preference_unavailable", backends)
    if preference != "auto" and preference in by_id:
        return _selected(preference, "saved_preference")
    if preference != "auto":
        return _needs_user_choice("saved_preference_unavailable", backends)

    return _needs_user_choice("first_run_choice", backends)


def _selected(backend_id: str, reason: str) -> dict[str, Any]:
    return {
        "status": "selected",
        "backend_id": backend_id,
        "reason": reason,
        "choices": [],
        "choice_details": [],
    }


def _compile_only(backend_id: str | None, reason: str) -> dict[str, Any]:
    return {
        "status": "compile_only",
        "backend_id": backend_id,
        "reason": reason,
        "choices": [],
        "choice_details": [],
    }

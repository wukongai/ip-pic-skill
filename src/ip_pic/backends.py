"""Public render adapters that preserve the provider-neutral upstream contract."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .errors import IPPicError


BACKENDS = {
    "codex-image-tool",
    "openai-direct",
    "host-ai-router",
    "prompt-only",
}

OPENAI_DIRECT_BASE_URL = "https://api.openai.com/v1"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _read_prompt(handoff: dict[str, Any]) -> str:
    prompt_path = Path(_text(handoff.get("prompt_file"))).expanduser()
    if not prompt_path.is_file():
        raise IPPicError(f"prompt file does not exist: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def _upstream(manifest: dict[str, Any]) -> dict[str, Any]:
    handoff = manifest.get("render_handoff")
    if not isinstance(handoff, dict):
        raise IPPicError("manifest has no single render_handoff; resolve selection first")
    if handoff.get("schema_version") != "image-render-handoff/v1":
        raise IPPicError("unsupported render handoff schema")
    return {
        "template": copy.deepcopy(manifest.get("template")),
        "brief": copy.deepcopy(manifest.get("brief")),
        "size": manifest.get("size"),
        "director_plan": copy.deepcopy(manifest.get("director_plan")),
        "visual_qa": copy.deepcopy(manifest.get("visual_qa")),
        "render_handoff": copy.deepcopy(handoff),
        "expected_outputs": copy.deepcopy(manifest.get("expected_outputs")),
        "delivery": copy.deepcopy(manifest.get("delivery")),
    }


def _expected_output(manifest: dict[str, Any]) -> Path:
    expected = (
        manifest.get("expected_outputs")
        if isinstance(manifest.get("expected_outputs"), dict)
        else {}
    )
    path = Path(_text(expected.get("raw_image"))).expanduser()
    if not _text(expected.get("raw_image")):
        raise IPPicError("manifest expected_outputs.raw_image is required")
    return path.resolve()


def _write_new_json(path: Path, value: dict[str, Any]) -> Path:
    target = path.resolve()
    if target.exists() or target.is_symlink():
        raise IPPicError(f"refusing to overwrite backend artifact: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def prepare_backend(
    manifest: dict[str, Any],
    backend: str,
    request_path: Path,
) -> dict[str, Any]:
    """Prepare one backend request without changing the compiled manifest."""

    if backend not in BACKENDS:
        raise IPPicError(f"unknown backend: {backend}")
    upstream = _upstream(manifest)
    handoff = upstream["render_handoff"]
    expected_output = _expected_output(manifest)
    if expected_output.exists() or expected_output.is_symlink():
        raise IPPicError(f"refusing to overwrite render output: {expected_output}")
    request = {
        "schema_version": "ip-pic-backend-request/v1",
        "backend": backend,
        "status": (
            "prompt_ready"
            if backend == "prompt-only"
            else "awaiting_host"
            if backend in {"codex-image-tool", "host-ai-router"}
            else "ready_direct"
        ),
        "rendered": False,
        "upstream_fingerprint": hashlib.sha256(_canonical(upstream)).hexdigest(),
        "upstream": upstream,
        "prompt": _read_prompt(handoff),
        "size": handoff.get("size"),
        "assets": copy.deepcopy(handoff.get("assets", [])),
        "expected_output": str(expected_output),
    }
    _write_new_json(request_path, request)
    return request


def _load_request(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IPPicError(f"cannot read backend request: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise IPPicError("backend request must be an object")
    return value


def _receipt_path(request_path: Path) -> Path:
    return request_path.with_name(f"{request_path.stem}.receipt.json")


def _file_receipt(
    request: dict[str, Any],
    output: Path,
    *,
    receipt_id: str,
    request_id: str = "",
) -> dict[str, Any]:
    if not output.is_file() or output.is_symlink():
        raise IPPicError(f"render output does not exist or is not a regular file: {output}")
    return {
        "schema_version": "ip-pic-render-receipt/v1",
        "backend": request["backend"],
        "status": "ok",
        "rendered": True,
        "receipt_id": receipt_id,
        "request_id": request_id,
        "upstream_fingerprint": request["upstream_fingerprint"],
        "output_image": str(output.resolve()),
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "output_bytes": output.stat().st_size,
    }


def finalize_host_render(
    request_path: Path,
    output_path: Path,
    *,
    receipt_id: str,
) -> Path:
    """Accept a host result only after the expected regular file exists."""

    request_file = request_path.resolve()
    request = _load_request(request_file)
    if request.get("backend") not in {"codex-image-tool", "host-ai-router"}:
        raise IPPicError("only host-mediated requests can be finalized here")
    expected = Path(_text(request.get("expected_output"))).resolve()
    output = output_path.resolve()
    if output != expected:
        raise IPPicError("host output path does not match the prepared request")
    receipt = _file_receipt(
        request,
        output,
        receipt_id=receipt_id,
    )
    return _write_new_json(_receipt_path(request_file), receipt)


def render_openai_direct(
    manifest: dict[str, Any],
    request_path: Path,
    *,
    client: Any | None = None,
    model: str = "gpt-image-2",
    quality: str = "high",
) -> Path:
    """Render with OpenAI's Image API using an external environment secret."""

    request_file = request_path.resolve()
    request = prepare_backend(manifest, "openai-direct", request_file)
    if request["assets"]:
        raise IPPicError(
            "openai-direct reference images require the edits adapter; "
            "use a host backend for this handoff"
        )
    if client is None:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise IPPicError(
                "OPENAI_API_KEY is required for openai-direct; "
                "keep it outside the Skill directory"
            )
        try:
            from openai import OpenAI
        except ModuleNotFoundError as exc:  # pragma: no cover - runtime guard
            raise IPPicError(
                "openai package is required for the openai-direct backend"
            ) from exc
        client = OpenAI(
            api_key=api_key,
            base_url=OPENAI_DIRECT_BASE_URL,
        )
    response = client.images.generate(
        model=model,
        prompt=request["prompt"],
        size=request["size"],
        quality=quality,
    )
    data = getattr(response, "data", None)
    encoded = getattr(data[0], "b64_json", "") if data else ""
    if not encoded:
        raise IPPicError("OpenAI Image API returned no base64 image")
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise IPPicError("OpenAI Image API returned invalid base64") from exc
    output = Path(request["expected_output"]).resolve()
    if output.exists() or output.is_symlink():
        raise IPPicError(f"refusing to overwrite render output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image_bytes)
    request_id = _text(getattr(response, "_request_id", ""))
    receipt = _file_receipt(
        request,
        output,
        receipt_id=request_id or hashlib.sha256(image_bytes).hexdigest()[:16],
        request_id=request_id,
    )
    return _write_new_json(_receipt_path(request_file), receipt)

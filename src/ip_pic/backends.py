"""Public render adapters that preserve the provider-neutral upstream contract."""

from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import os
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from .errors import IPPicError


BACKENDS = {
    "codex-image-tool",
    "openai-direct",
    "host-ai-router",
    "prompt-only",
}

OPENAI_DIRECT_BASE_URL = "https://api.openai.com/v1"
OPENAI_DIRECT_ASSET_OWNERSHIP = {
    "user-owned",
    "licensed",
    "project-original-tutorial",
    "derived_from_authorized_assets",
}
OPENAI_DIRECT_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
OPENAI_DIRECT_IMAGE_SUFFIXES = {".jpeg", ".jpg", ".png", ".webp"}
OPENAI_DIRECT_MAX_REFERENCE_COUNT = 16
OPENAI_DIRECT_MAX_REFERENCE_BYTES = 50 * 1024 * 1024


def _text(value: Any) -> str:
    return str(value or "").strip()


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise IPPicError(f"cannot read file for hashing: {path}") from None
    return digest.hexdigest()


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
    path_text = _text(expected.get("raw_image"))
    if not path_text:
        raise IPPicError("manifest expected_outputs.raw_image is required")
    path = Path(path_text).expanduser()
    if path.is_symlink():
        raise IPPicError(f"render output is a symbolic link: {path}")
    return path.resolve()


def _write_new_json(path: Path, value: dict[str, Any]) -> Path:
    source = path.expanduser()
    if source.exists() or source.is_symlink():
        raise IPPicError(f"refusing to overwrite backend artifact: {source}")
    target = source.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def _build_backend_request(
    manifest: dict[str, Any],
    backend: str,
) -> dict[str, Any]:
    if backend not in BACKENDS:
        raise IPPicError(f"unknown backend: {backend}")
    upstream = _upstream(manifest)
    handoff = upstream["render_handoff"]
    expected_output = _expected_output(manifest)
    if expected_output.exists() or expected_output.is_symlink():
        raise IPPicError(f"refusing to overwrite render output: {expected_output}")
    return {
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


def prepare_backend(
    manifest: dict[str, Any],
    backend: str,
    request_path: Path,
) -> dict[str, Any]:
    """Prepare one backend request without changing the compiled manifest."""

    request = _build_backend_request(manifest, backend)
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


def _prepare_or_reuse_openai_request(
    candidate: dict[str, Any],
    request_path: Path,
) -> dict[str, Any]:
    """Reuse only an identical unfinished request after a provider failure."""

    source = request_path.expanduser()
    if source.is_symlink():
        raise IPPicError(f"refusing to reuse unsafe backend request: {source}")
    request_file = source.resolve()
    receipt_file = _receipt_path(request_file)
    if receipt_file.exists() or receipt_file.is_symlink():
        raise IPPicError(f"refusing to overwrite backend receipt: {receipt_file}")
    if not source.exists():
        _write_new_json(request_file, candidate)
        return candidate
    if not source.is_file():
        raise IPPicError(
            f"refusing to reuse unsafe backend request: {source}"
        )
    existing = _load_request(request_file)
    if existing != candidate:
        raise IPPicError(
            "refusing to reuse openai-direct request because its "
            "compiled handoff has changed"
        )
    return existing


def _validated_openai_reference_paths(assets: Any) -> list[Path]:
    if not isinstance(assets, list):
        raise IPPicError("openai-direct assets must be a list")
    if len(assets) > OPENAI_DIRECT_MAX_REFERENCE_COUNT:
        raise IPPicError(
            "openai-direct accepts at most "
            f"{OPENAI_DIRECT_MAX_REFERENCE_COUNT} reference images"
        )
    paths: list[Path] = []
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            raise IPPicError(f"openai-direct reference asset {index} is invalid")
        ownership = _text(asset.get("ownership"))
        if ownership not in OPENAI_DIRECT_ASSET_OWNERSHIP:
            raise IPPicError(
                f"openai-direct reference asset {index} has invalid ownership"
            )
        if not _text(asset.get("purpose")):
            raise IPPicError(
                f"openai-direct reference asset {index} has no purpose"
            )
        if not isinstance(asset.get("required"), bool):
            raise IPPicError(
                f"openai-direct reference asset {index} has invalid required flag"
            )
        path_text = _text(asset.get("path"))
        if not path_text:
            raise IPPicError(
                f"openai-direct reference asset {index} has no path"
            )
        source = Path(path_text).expanduser()
        if not source.is_absolute():
            raise IPPicError(
                f"openai-direct reference asset {index} must use an absolute path"
            )
        if source.is_symlink():
            raise IPPicError(
                f"openai-direct reference asset is a symbolic link: {source}"
            )
        path = source.resolve()
        if not path.is_file():
            raise IPPicError(
                f"openai-direct reference asset does not exist: {path}"
            )
        if path.suffix.casefold() not in OPENAI_DIRECT_IMAGE_SUFFIXES:
            raise IPPicError(
                "openai-direct reference asset must be PNG, JPEG, or WEBP: "
                f"{path}"
            )
        if path.stat().st_size >= OPENAI_DIRECT_MAX_REFERENCE_BYTES:
            raise IPPicError(
                "openai-direct reference asset must be smaller than 50MB: "
                f"{path}"
            )
        try:
            with Image.open(path) as image:
                if image.format not in OPENAI_DIRECT_IMAGE_FORMATS:
                    raise IPPicError(
                        "openai-direct reference asset must be PNG, JPEG, "
                        f"or WEBP: {path}"
                    )
                image.verify()
        except (OSError, UnidentifiedImageError) as exc:
            raise IPPicError(
                f"openai-direct reference asset is not a valid image: {path}"
            ) from exc
        paths.append(path)
    return paths


def _raise_openai_request_error(operation: str, exc: Exception) -> None:
    request_id = _text(getattr(exc, "request_id", ""))
    request_note = f" Request ID: {request_id}." if request_id else ""
    raise IPPicError(
        f"OpenAI Image API {operation} request failed; no success receipt "
        "was written. Check model access, organization verification, quota, "
        "rate limits, and request safety, then retry the same request path."
        f"{request_note}"
    ) from None


def _validate_rendered_image(image_bytes: bytes, expected_size: str) -> None:
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            actual_format = image.format
            actual_size = image.size
            image.verify()
    except (OSError, UnidentifiedImageError) as exc:
        raise IPPicError(
            "OpenAI Image API returned decoded data that is not a valid image"
        ) from exc
    if actual_format != "PNG":
        raise IPPicError(
            "OpenAI Image API returned a valid image, but the output must be PNG"
        )
    try:
        expected_dimensions = tuple(
            int(part)
            for part in expected_size.casefold().split("x", 1)
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise IPPicError(
            f"openai-direct request has invalid size: {expected_size}"
        ) from exc
    if len(expected_dimensions) != 2:
        raise IPPicError(
            f"openai-direct request has invalid size: {expected_size}"
        )
    if actual_size != expected_dimensions:
        raise IPPicError(
            "OpenAI Image API returned incorrect image dimensions: "
            f"expected {expected_dimensions[0]}x{expected_dimensions[1]}, "
            f"got {actual_size[0]}x{actual_size[1]}"
        )


def _file_receipt(
    request: dict[str, Any],
    output: Path,
    *,
    receipt_id: str,
    request_id: str = "",
) -> dict[str, Any]:
    if not output.is_file() or output.is_symlink():
        raise IPPicError(f"render output does not exist or is not a regular file: {output}")
    receipt = {
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
    runtime = request.get("runtime")
    if isinstance(runtime, dict):
        receipt.update(
            {
                "model": _text(runtime.get("model")),
                "quality": _text(runtime.get("quality")),
                "operation": _text(runtime.get("operation")),
                "request_fingerprint": _text(
                    request.get("request_fingerprint")
                ),
                "input_assets": [
                    {
                        "purpose": _text(asset.get("purpose")),
                        "sha256": _text(asset.get("sha256")),
                    }
                    for asset in request.get("assets", [])
                    if isinstance(asset, dict)
                ],
            }
        )
    return receipt


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

    request_file = request_path.expanduser()
    if request_file.is_symlink():
        raise IPPicError(
            f"refusing to reuse unsafe backend request: {request_file}"
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
    candidate = _build_backend_request(manifest, "openai-direct")
    paths = _validated_openai_reference_paths(candidate["assets"])
    operation = "edit" if paths else "generate"
    candidate["runtime"] = {
        "endpoint": OPENAI_DIRECT_BASE_URL,
        "model": model,
        "quality": quality,
        "operation": operation,
    }
    for asset, path in zip(candidate["assets"], paths):
        asset["sha256"] = _sha256_file(path)
    candidate["request_fingerprint"] = hashlib.sha256(
        _canonical(candidate)
    ).hexdigest()
    request = _prepare_or_reuse_openai_request(candidate, request_file)
    request_file = request_file.resolve()
    if paths:
        try:
            with ExitStack() as stack:
                images = [
                    stack.enter_context(path.open("rb"))
                    for path in paths
                ]
                try:
                    response = client.images.edit(
                        model=model,
                        image=images,
                        prompt=request["prompt"],
                        size=request["size"],
                        quality=quality,
                        output_format="png",
                    )
                except Exception as exc:
                    _raise_openai_request_error("edit", exc)
        except OSError as exc:
            raise IPPicError(
                "cannot read an openai-direct reference asset"
            ) from None
    else:
        try:
            response = client.images.generate(
                model=model,
                prompt=request["prompt"],
                size=request["size"],
                quality=quality,
                output_format="png",
            )
        except Exception as exc:
            _raise_openai_request_error("generation", exc)
    data = getattr(response, "data", None)
    encoded = getattr(data[0], "b64_json", "") if data else ""
    if not encoded:
        raise IPPicError("OpenAI Image API returned no base64 image")
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise IPPicError("OpenAI Image API returned invalid base64") from exc
    _validate_rendered_image(image_bytes, _text(request.get("size")))
    output = Path(request["expected_output"]).resolve()
    if output.exists() or output.is_symlink():
        raise IPPicError(f"refusing to overwrite render output: {output}")
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as handle:
            handle.write(image_bytes)
    except FileExistsError as exc:
        raise IPPicError(f"refusing to overwrite render output: {output}") from exc
    except OSError as exc:
        raise IPPicError(
            f"cannot write OpenAI render output: {output}"
        ) from None
    request_id = _text(getattr(response, "_request_id", ""))
    receipt = _file_receipt(
        request,
        output,
        receipt_id=request_id or hashlib.sha256(image_bytes).hexdigest()[:16],
        request_id=request_id,
    )
    return _write_new_json(_receipt_path(request_file), receipt)

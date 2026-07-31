"""Per-image QA receipts without pretending structural checks are visual approval."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .errors import IPPicError


def _text(value: Any) -> str:
    return str(value or "").strip()


def evaluate_image(
    manifest: dict[str, Any],
    reviewed_image: Path,
    observations: dict[str, bool],
) -> Path:
    """Evaluate explicit visual observations against the compiled QA contract."""

    image = reviewed_image.resolve()
    if not image.is_file() or image.is_symlink():
        raise IPPicError(f"reviewed image does not exist or is not a regular file: {image}")
    qa = manifest.get("visual_qa") if isinstance(manifest.get("visual_qa"), dict) else {}
    required = qa.get("required_checks")
    if not isinstance(required, list) or not required:
        raise IPPicError("manifest.visual_qa.required_checks must be a non-empty array")
    failed = [
        str(check)
        for check in required
        if observations.get(str(check)) is not True
    ]
    expected = (
        manifest.get("expected_outputs")
        if isinstance(manifest.get("expected_outputs"), dict)
        else {}
    )
    final = Path(_text(expected.get("final_image"))).expanduser().resolve()
    mode = _text(
        (manifest.get("delivery") or {}).get("mode")
        if isinstance(manifest.get("delivery"), dict)
        else ""
    )
    if image != final:
        failed.append("reviewed_final_deliverable")
    failed = list(dict.fromkeys(failed))
    if failed:
        if mode == "two-step-publish" and (
            "reviewed_final_deliverable" in failed
            or any(check.startswith("final_") for check in failed)
        ):
            retry_scope = "publish-layout"
        else:
            retry_scope = "render"
        status = "failed"
        visual_acceptance = "failed"
    else:
        retry_scope = "none"
        status = "checks_passed"
        visual_acceptance = "pending_human"
    result = {
        "schema_version": "ip-pic-image-qa/v1",
        "status": status,
        "visual_acceptance": visual_acceptance,
        "approved_for_release": False,
        "delivery_mode": mode,
        "reviewed_image": str(image),
        "reviewed_image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
        "required_checks": [str(check) for check in required],
        "observations": {
            str(check): observations.get(str(check))
            for check in required
        },
        "failed_checks": failed,
        "retry_scope": retry_scope,
        "structural_checks_are_visual_acceptance": False,
    }
    result_path = image.with_suffix(".qa.json")
    if result_path.exists() or result_path.is_symlink():
        raise IPPicError(f"refusing to overwrite QA receipt: {result_path}")
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result_path

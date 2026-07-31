#!/usr/bin/env python3
"""Prepare or execute one public IP Pic render handoff."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.backends import (  # noqa: E402
    finalize_host_render,
    prepare_backend,
    render_openai_direct,
)


def _manifest(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("manifest must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--manifest", type=Path, required=True)
    prepare.add_argument(
        "--backend",
        choices=["codex-image-tool", "host-ai-router", "prompt-only"],
        required=True,
    )
    prepare.add_argument("--request", type=Path, required=True)

    direct = subparsers.add_parser("openai-direct")
    direct.add_argument("--manifest", type=Path, required=True)
    direct.add_argument("--request", type=Path, required=True)
    direct.add_argument("--model", default="gpt-image-2")
    direct.add_argument("--quality", choices=["low", "medium", "high", "auto"], default="high")

    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--request", type=Path, required=True)
    finalize.add_argument("--output", type=Path, required=True)
    finalize.add_argument("--receipt-id", required=True)

    args = parser.parse_args()
    if args.command == "prepare":
        request = prepare_backend(
            _manifest(args.manifest),
            args.backend,
            args.request,
        )
        print(json.dumps(request, ensure_ascii=False, indent=2))
        return 0
    if args.command == "openai-direct":
        receipt = render_openai_direct(
            _manifest(args.manifest),
            args.request,
            model=args.model,
            quality=args.quality,
        )
        print(receipt)
        return 0
    receipt = finalize_host_render(
        args.request,
        args.output,
        receipt_id=args.receipt_id,
    )
    print(receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

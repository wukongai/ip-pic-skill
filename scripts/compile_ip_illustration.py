#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "src"))

from ip_pic.compiler import compile_request, load_json
from ip_pic.errors import IpPicError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile authorized custom IP content into provider-neutral prompts."
    )
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--brief", type=Path, required=True)
    parser.add_argument("--template")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate and preview without writing output files.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = compile_request(
            profile=load_json(args.profile),
            brief=load_json(args.brief),
            output_dir=args.output_dir,
            skill_root=SKILL_ROOT,
            template_id=args.template,
            write=not args.check,
        )
    except IpPicError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(
        json.dumps(
            {
                "status": "validated" if args.check else "compiled",
                "output_dir": result["output_dir"],
                "image_count": result["run_manifest"]["image_count"],
                "rendered": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

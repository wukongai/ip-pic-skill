#!/usr/bin/env python3
"""Compile one public IP illustration request without calling an image API."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.compiler import compile_request  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--template")
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--print-prompt", action="store_true")
    args = parser.parse_args()
    brief = json.loads(args.brief.read_text(encoding="utf-8"))
    result = compile_request(
        ROOT,
        brief,
        args.output_dir,
        template_id=args.template,
        write=True,
        project_root=args.project_root,
    )
    for key, value in result["paths"].items():
        print(f"{key}: {value}")
    print("mode: compile-only; render-handoff: image-render-handoff/v1")
    if args.print_prompt:
        print("")
        print(result["prompt"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

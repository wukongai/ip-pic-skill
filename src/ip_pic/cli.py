"""Installed console entry point for compile-only IP Pic."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .compiler import compile_request
from .errors import IPPicError


def _project_root() -> Path:
    candidates = []
    configured = os.environ.get("IP_PIC_HOME", "").strip()
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.extend((Path(__file__).resolve().parents[2], Path.cwd()))
    for candidate in candidates:
        if (candidate / "templates" / "registry.json").is_file() and (
            candidate / "profiles" / "render-styles.json"
        ).is_file():
            return candidate.resolve()
    raise IPPicError(
        "cannot locate ip-pic templates; run from the complete Skill directory "
        "or set IP_PIC_HOME"
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="ip-pic-compile")
    parser.add_argument("--brief", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--template")
    parser.add_argument("--print-prompt", action="store_true")
    args = parser.parse_args()
    root = _project_root()
    brief = json.loads(args.brief.read_text(encoding="utf-8"))
    result = compile_request(
        root,
        brief,
        args.output_dir,
        template_id=args.template,
        write=True,
    )
    for key, value in result["paths"].items():
        print(f"{key}: {value}")
    print("mode: compile-only; render-handoff: image-render-handoff/v1")
    if args.print_prompt:
        print(result["prompt"])
    return 0

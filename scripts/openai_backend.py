#!/usr/bin/env python3
from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.errors import (
    CredentialError,
    RenderError,
    UnsupportedPlatformError,
    ValidationError,
)
from ip_pic.openai_direct import (
    doctor,
    load_api_key,
    render_character_master,
    render_request,
    write_user_api_key,
)


def _config_path() -> Path:
    return Path.home() / ".ip-pic" / ".env"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Secure direct GPT Image 2 renderer")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="report credential readiness")
    commands.add_parser("configure", help="store a user-level API key securely")
    render = commands.add_parser("render", help="render a compiled request")
    render.add_argument("--request", type=Path, required=True, help="render-request.json path")
    render.add_argument("--output-dir", type=Path, required=True, help="directory for rendered PNGs")
    master = commands.add_parser(
        "master",
        help="create a character consistency master from an authorized photo",
    )
    master.add_argument("--reference", type=Path, required=True, help="authorized photo path")
    master.add_argument("--output", type=Path, required=True, help="character-master PNG path")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "doctor":
        print(json.dumps(doctor(), ensure_ascii=False))
        return 0
    if args.command == "configure":
        try:
            write_user_api_key(_config_path(), getpass.getpass("OpenAI API key: "))
        except CredentialError:
            print(json.dumps({"status": "configuration_error"}))
            return 2
        print(json.dumps({"status": "configured"}))
        return 0

    api_key = load_api_key()
    if api_key is None:
        print(json.dumps({"status": "missing_credentials"}))
        return 2
    try:
        if args.command == "master":
            result = render_character_master(
                args.reference,
                args.output,
                api_key,
                project_root=Path.cwd(),
            )
        else:
            result = render_request(
                args.request,
                args.output_dir,
                api_key,
                project_root=Path.cwd(),
            )
    except UnsupportedPlatformError:
        print(json.dumps({"status": "unsupported_platform"}))
        return 2
    except (CredentialError, RenderError, ValidationError):
        print(json.dumps({"status": "failed", "error": "render_error"}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] in {"complete", "rendered"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

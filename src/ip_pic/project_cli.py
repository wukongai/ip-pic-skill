"""Agent-facing CLI for project-local IP Pic customization."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .errors import IPPicError
from .project_assets import ProjectAssetError
from .project_store import (
    apply_plan,
    list_assets,
    plan_activate,
    plan_create,
    resolve_asset,
)


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _json_object(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise ProjectAssetError("draft 不允许是符号链接")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProjectAssetError("draft 文件不存在") from exc
    except json.JSONDecodeError as exc:
        raise ProjectAssetError("draft 不是有效 JSON") from exc
    except OSError as exc:
        raise ProjectAssetError("draft 文件无法读取") from exc
    if not isinstance(value, dict):
        raise ProjectAssetError("draft 必须是 JSON object")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ip-pic-project")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("plan-create")
    create.add_argument("--project-root", type=Path, required=True)
    create.add_argument(
        "--kind",
        choices=["character", "style", "director"],
        required=True,
    )
    create.add_argument("--draft", type=Path, required=True)
    create.add_argument("--activate", action="store_true")

    activate = subparsers.add_parser("plan-activate")
    activate.add_argument("--project-root", type=Path, required=True)
    activate.add_argument(
        "--kind",
        choices=["character", "style", "director"],
        required=True,
    )
    activate.add_argument("--id", required=True)
    activate.add_argument("--version", required=True)

    apply = subparsers.add_parser("apply")
    apply.add_argument("--project-root", type=Path, required=True)
    apply.add_argument("--plan", type=Path, required=True)
    apply.add_argument("--confirm", action="store_true")

    listing = subparsers.add_parser("list")
    listing.add_argument("--project-root", type=Path, required=True)
    listing.add_argument(
        "--kind",
        choices=["character", "style", "director"],
    )

    show = subparsers.add_parser("show")
    show.add_argument("--project-root", type=Path, required=True)
    show.add_argument(
        "--kind",
        choices=["character", "style", "director"],
        required=True,
    )
    show.add_argument("--id")
    show.add_argument("--version", default="active")
    return parser


def dispatch(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "plan-create":
        return plan_create(
            _skill_root(),
            args.project_root,
            args.kind,
            _json_object(args.draft),
            activate=args.activate,
        )
    if args.command == "plan-activate":
        return plan_activate(
            args.project_root,
            args.kind,
            args.id,
            args.version,
        )
    if args.command == "apply":
        return apply_plan(
            _skill_root(),
            args.project_root,
            args.plan,
            confirmed=args.confirm,
        )
    if args.command == "list":
        return list_assets(args.project_root, args.kind)
    return resolve_asset(
        args.project_root,
        args.kind,
        args.id,
        version=args.version,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = dispatch(args)
    except (IPPicError, ProjectAssetError) as exc:
        print(
            json.dumps(
                {"status": "error", "error": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    except OSError:
        print(
            json.dumps(
                {"status": "error", "error": "项目定制文件操作失败"},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


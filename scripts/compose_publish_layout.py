#!/usr/bin/env python3
"""Compose the deterministic two-step publishing layer from a run manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.errors import IPPicError  # noqa: E402
from ip_pic.publish import compose_publish_layout  # noqa: E402


def _load_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise IPPicError(f"文件不存在：{path}") from exc
    except json.JSONDecodeError as exc:
        raise IPPicError(f"JSON 格式错误：{path}") from exc
    if not isinstance(value, dict):
        raise IPPicError(f"JSON 顶层必须是对象：{path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="从 run-manifest.json 合成 two-step-publish 最终文字层。"
    )
    parser.add_argument(
        "--run-manifest",
        type=Path,
        required=True,
        help="编译器生成的 run-manifest.json。",
    )
    parser.add_argument(
        "--font-path",
        default="",
        help="可选：有合法使用权且支持中文的 TTF/OTF/TTC 字体文件。",
    )
    parser.add_argument(
        "--layout-manifest",
        type=Path,
        help="可选：另存的 publish-layout.json；默认与 run manifest 同目录。",
    )
    parser.add_argument(
        "--output-image",
        type=Path,
        help="可选：为文字层重试指定一个全新的 final 图片路径。",
    )
    args = parser.parse_args()

    run_manifest_path = args.run_manifest.expanduser().resolve()
    run_manifest = _load_object(run_manifest_path)
    publish_layout = run_manifest.get("publish_layout")
    if not isinstance(publish_layout, dict):
        raise IPPicError(
            "run manifest 没有 publish_layout；请确认文章使用 two-step-publish。"
        )

    layout_path = (
        args.layout_manifest.expanduser().resolve()
        if args.layout_manifest
        else run_manifest_path.parent / "publish-layout.json"
    )
    if layout_path.exists():
        raise IPPicError(f"布局 manifest 已存在，拒绝覆盖：{layout_path}")
    if args.output_image:
        publish_layout = dict(publish_layout)
        publish_layout["output_image"] = str(args.output_image.expanduser().resolve())
    layout_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_layout_path = layout_path.with_name(f".{layout_path.name}.tmp")
    if temporary_layout_path.exists():
        raise IPPicError(f"临时布局文件已存在，请先检查上次失败：{temporary_layout_path}")
    temporary_layout_path.write_text(
        json.dumps(publish_layout, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        result_path = compose_publish_layout(
            manifest_path=temporary_layout_path,
            font_path=args.font_path,
        )
    except Exception:
        temporary_layout_path.unlink(missing_ok=True)
        raise
    temporary_layout_path.replace(layout_path)
    print(f"layout_manifest: {layout_path}")
    print(f"layout_result: {result_path}")
    print(
        "final_image: "
        + json.loads(result_path.read_text(encoding="utf-8"))["output_image"]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

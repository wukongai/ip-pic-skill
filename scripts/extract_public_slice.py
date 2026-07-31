#!/usr/bin/env python3
"""Deterministically extract the public-safe IP template and style slice."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STYLE_ALIASES = {
    "minimal-lineart": ["简约线稿", "极简线稿", "minimal lineart"],
    "playful-craft": ["毛毡手作", "毛毡", "手作", "playful craft"],
    "sticker-collage": ["贴画拼贴", "贴画", "拼贴", "sticker collage"],
    "expressive-handdrawn": ["松弛手绘", "手绘", "expressive handdrawn"],
    "pop-impact": ["高冲击吸睛", "高冲击", "pop impact"],
    "art-print": ["艺术版画", "版画", "art print"],
}
IDENTITY_KEYS = {
    "inherits_identity_from",
    "identity_invariants",
    "reference_set",
    "character_bible",
}


def _text_sanitizer(private_id: str, private_name: str):
    replacements = (
        (f"../profiles/{private_id}-editorial-video-v1.json", "../profiles/editorial-baseline-v1.json"),
        (f"../profiles/{private_id}-character-style-v2.json", "profile://selected-character"),
        (f"../profiles/{private_id}-minimal-lineart-style-v1.json", "../profiles/render-styles/minimal-lineart-v1.json"),
        (f"../profiles/{private_id}-playful-craft-style-v1.json", "../profiles/render-styles/playful-craft-v1.json"),
        (f"../profiles/{private_id}-sticker-collage-style-v1.json", "../profiles/render-styles/sticker-collage-v1.json"),
        (f"../profiles/{private_id}-expressive-handdrawn-style-v1.json", "../profiles/render-styles/expressive-handdrawn-v1.json"),
        (f"../profiles/{private_id}-pop-impact-style-v1.json", "../profiles/render-styles/pop-impact-v1.json"),
        (f"../profiles/{private_id}-art-print-style-v1.json", "../profiles/render-styles/art-print-v1.json"),
        (f"{private_id}-ip-", "ip-"),
        (f"{private_id}-", ""),
        (private_id.capitalize(), "selected authorized"),
        (private_id.upper(), "SELECTED-AUTHORIZED"),
        (private_name + "老师", "已授权角色"),
        (private_name, "已授权角色"),
        ("AI 日报", "连续内容"),
        ("视频号", "静态竖屏"),
        ("小红书", "移动端竖屏"),
        ("公众号", "文章"),
        ("播客", "口播"),
        ("知识卡片", "IP 主题卡"),
        ("Content-factory", "上游内容调用方"),
        ("content-factory", "上游内容调用方"),
        ("Image Factory", "IP Pic"),
        ("image-factory", "ip-pic"),
        ("Video Factory", "下游视频工具"),
        ("audio-factory", "下游音频工具"),
        ("训练营", "教程项目"),
        ("布丁", "外部系统"),
        ("Obsidian", "外部笔记系统"),
        ("OB", "外部笔记系统"),
        ("小黑角色", "未授权第三方角色"),
        ("小黑", "未授权第三方角色"),
    )
    private_appearance = re.compile(
        r"(低马尾|阔腿裤|德训鞋|左手食指戒指|左腕[^，。；,;]*手环|"
        r"酒红[^，。；,;]*|深蓝[^，。；,;]*|真人神韵)"
    )

    def sanitize(value: str) -> str:
        result = value
        for source, target in replacements:
            if source:
                result = result.replace(source, target)
        result = private_appearance.sub("所选角色 profile 的连续性锚点", result)
        return result

    return sanitize


def _sanitize(value: Any, sanitize_text, *, strip_identity_keys: bool) -> Any:
    if isinstance(value, dict):
        return {
            key: _sanitize(item, sanitize_text, strip_identity_keys=strip_identity_keys)
            for key, item in value.items()
            if not (strip_identity_keys and key in IDENTITY_KEYS)
        }
    if isinstance(value, list):
        return [
            _sanitize(item, sanitize_text, strip_identity_keys=strip_identity_keys)
            for item in value
        ]
    if isinstance(value, str):
        return sanitize_text(value)
    return value


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"source JSON must be an object: {path}")
    return value


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "parity" / "ip-parity-manifest.json",
    )
    args = parser.parse_args()
    private_id = os.environ.get("IP_PIC_PRIVATE_SOURCE_ID", "").strip()
    private_name = os.environ.get("IP_PIC_PRIVATE_DISPLAY_NAME", "").strip()
    if not private_id or not private_name:
        raise SystemExit(
            "IP_PIC_PRIVATE_SOURCE_ID and IP_PIC_PRIVATE_DISPLAY_NAME are required"
        )
    sanitize_text = _text_sanitizer(private_id, private_name)
    manifest = _load(args.manifest)
    template_registry: list[dict[str, Any]] = []
    style_registry: list[dict[str, Any]] = []
    for entry in manifest["entries"]:
        capability = entry.get("capability")
        if capability in {
            "character-performance",
            "identity-lock",
            "composition-families",
            "delivery-modes",
            "full-rebuild",
            "role-scale-action",
            "multi-canvas-layout",
            "prompt-contract",
            "visual-qa",
            "style-dna",
            "style-orthogonality",
            "deterministic-typography",
            "license-lineage",
            "selection-receipt",
            "workflow-kernel",
            "api-boundary",
        }:
            source = args.source_root / str(entry["source"]).replace(
                "{private-id}",
                private_id,
            )
            target = ROOT / entry["target"]
            _write_text(target, sanitize_text(source.read_text(encoding="utf-8")))
            continue
        if capability == "regression-fixture":
            source = args.source_root / str(entry["source"]).replace(
                "{private-id}",
                private_id,
            )
            target = ROOT / entry["target"]
            value = _sanitize(
                _load(source),
                sanitize_text,
                strip_identity_keys=False,
            )
            _write(target, value)
            continue
        if capability not in {"formal-template", "compatibility-template", "render-style"}:
            continue
        source = args.source_root / str(entry["source"]).replace(
            "{private-id}",
            private_id,
        )
        target = ROOT / entry["target"]
        value = _sanitize(
            _load(source),
            sanitize_text,
            strip_identity_keys=capability == "render-style",
        )
        if capability == "render-style":
            source_id = str(value.get("id") or "")
            style_id = source_id.removesuffix("-style-v1")
            value["id"] = style_id
            value["schema_version"] = "render-style-profile/v1"
            value["scope"] = "render-style-only"
            _write(target, value)
            style_registry.append(
                {
                    "id": style_id,
                    "aliases": STYLE_ALIASES[style_id],
                    "profile": target.name,
                    "status": value.get("status", "experimental"),
                }
            )
            continue
        _write(target, value)
        template_registry.append(
            {
                "id": value["id"],
                "file": target.name,
                "scene": value["scene"],
                "classification": (
                    "formal" if capability == "formal-template" else "compatibility"
                ),
                "default_for_scene": bool(value.get("default_for_scene")),
                "aliases": value.get("aliases", []),
            }
        )
    _write(
        ROOT / "templates" / "registry.json",
        {
            "schema_version": "ip-template-registry/v1",
            "formal_count": 13,
            "compatibility_count": 1,
            "templates": sorted(template_registry, key=lambda item: item["id"]),
        },
    )
    _write(
        ROOT / "profiles" / "render-styles.json",
        {
            "schema_version": "render-style-registry/v1",
            "styles": sorted(style_registry, key=lambda item: item["id"]),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

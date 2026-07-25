from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


TEXT_SUFFIXES = {
    "",
    ".gitignore",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
BINARY_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
IGNORED_NAMES = {".git", "__pycache__", ".pytest_cache"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _private_patterns() -> list[str]:
    return [
        "ai" + "xiao",
        "艾" + "笑",
        "爱" + "笑",
        "布" + "丁",
        "content" + "-factory",
        "image" + "-factory",
        "ai" + "-router",
        "fei" + "shu",
        "ob" + "sidian",
        ".skill" + "-engineering",
        ".ai" + "-native",
        "/" + "Users" + "/",
        "/" + "home" + "/",
        "C:" + "\\Users\\",
        "#7A" + "2638",
        "#172" + "33B",
    ]


def _identity_fingerprint_patterns() -> list[tuple[str, ...]]:
    return [
        ("左" + "手", "食" + "指", "戒" + "指"),
        ("左" + "腕", "手" + "环"),
        ("裤" + "脚", "盖" + "住", "鞋"),
        ("left " + "wrist", "brace" + "let"),
        ("left " + "index", "ri" + "ng"),
    ]


def _secret_patterns() -> list[re.Pattern[str]]:
    return [
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"\b" + "s" + r"k-[A-Za-z0-9_-]{20,}\b"),
        re.compile(r"\b" + "gh" + r"p_[A-Za-z0-9]{20,}\b"),
        re.compile(
            r"(?i)\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*[\"']?[A-Za-z0-9_./+-]{12,}"
        ),
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ]


def _iter_release_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if any(part in IGNORED_NAMES for part in path.relative_to(root).parts):
            continue
        if path.is_file() or path.is_symlink():
            if path.suffix == ".pyc":
                continue
            yield path


def _load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "public-release-files/v1":
        raise ValueError("manifest.schema must equal public-release-files/v1")
    files = data.get("files")
    if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
        raise ValueError("manifest.files must be a list of paths")
    return data


def _check_markdown_links(path: Path, text: str, root: Path) -> list[str]:
    findings: list[str] = []
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        clean = target.strip("<>")
        if clean.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target_path = (path.parent / clean.split("#", 1)[0]).resolve()
        try:
            target_path.relative_to(root.resolve())
        except ValueError:
            findings.append(f"{path}: link escapes release root: {clean}")
            continue
        if not target_path.exists():
            findings.append(f"{path}: missing local link target: {clean}")
    return findings


def validate_release(
    root: Path,
    manifest_path: Path,
    private_patterns_path: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    manifest = _load_manifest(manifest_path)
    allowed = set(manifest["files"])
    findings: list[str] = []
    actual: set[str] = set()
    allowed_domains = set(manifest.get("allowed_domains", ["github.com"]))

    extra_private_patterns: list[str] = []
    if private_patterns_path is not None:
        extra_private_patterns = [
            line.strip()
            for line in private_patterns_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    private_patterns = [item.casefold() for item in _private_patterns()]
    private_patterns.extend(item.casefold() for item in extra_private_patterns)

    for path in _iter_release_files(root):
        relative = path.relative_to(root).as_posix()
        actual.add(relative)
        if path.is_symlink():
            findings.append(f"{relative}: symlink is not allowed")
            continue
        if path.suffix.lower() in BINARY_IMAGE_SUFFIXES:
            findings.append(f"{relative}: binary image assets are not allowed in v0.1")
        if "/../" in f"/{relative}/" or relative.startswith("../"):
            findings.append(f"{relative}: non-canonical path")

        suffix = path.suffix.lower() or (path.name if path.name.startswith(".") else "")
        if suffix not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"{relative}: expected UTF-8 text")
            continue
        folded = text.casefold()
        for pattern in private_patterns:
            if pattern in folded:
                findings.append(f"{relative}: private pattern detected")
                break
        for required_parts in _identity_fingerprint_patterns():
            if all(part.casefold() in folded for part in required_parts):
                findings.append(f"{relative}: identity fingerprint detected")
                break
        for pattern in _secret_patterns():
            if pattern.search(text):
                findings.append(f"{relative}: credential-like value detected")
                break
        if (".." + "/..") in text or ("file:" + "//") in folded:
            findings.append(f"{relative}: cross-directory or local URI reference detected")
        unfinished = r"\b(" + "TO" + "DO|" + "FIX" + r"ME)\b"
        if re.search(unfinished, text):
            findings.append(f"{relative}: unfinished marker detected")
        url_pattern = r"https?://[A-Za-z0-9.-]+(?:/[^\s<>\"')\]]*)?"
        for url in re.findall(url_pattern, text):
            hostname = (urlparse(url).hostname or "").lower()
            if hostname and hostname not in allowed_domains:
                findings.append(f"{relative}: domain is not allowlisted: {hostname}")
        if path.suffix.lower() == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                findings.append(f"{relative}: invalid JSON: {exc}")
        if path.suffix.lower() == ".md":
            findings.extend(_check_markdown_links(path, text, root))

    missing = sorted(allowed - actual)
    unlisted = sorted(actual - allowed)
    for relative in missing:
        findings.append(f"{relative}: allowlisted file is missing")
    for relative in unlisted:
        findings.append(f"{relative}: file is not allowlisted")

    hashes = {
        relative: sha256_file(root / relative)
        for relative in sorted(actual & allowed)
        if (root / relative).is_file() and not (root / relative).is_symlink()
    }
    return {
        "status": "pass" if not findings else "fail",
        "root": str(root),
        "files_checked": len(actual),
        "findings": findings,
        "sha256": hashes,
    }

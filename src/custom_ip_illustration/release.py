from __future__ import annotations

import hashlib
import json
import re
import struct
import zlib
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


TEXT_SUFFIXES = {
    ".gitignore",
    ".json",
    ".md",
    ".py",
    ".svg",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {"LICENSE", "NOTICE", "VERSION"}
IGNORED_NAMES = {".git", "__pycache__", ".pytest_cache"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SAFE_PNG_CHUNKS = {
    b"IHDR",
    b"PLTE",
    b"IDAT",
    b"IEND",
    b"cHRM",
    b"gAMA",
    b"iCCP",
    b"sBIT",
    b"sRGB",
    b"tRNS",
}


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
        "fei" + "shu",
        "ob" + "sidian",
        ".skill" + "-engineering",
        ".ai" + "-native",
        "/" + "Users" + "/",
        "/" + "home" + "/",
        "C:" + "\\Users\\",
        "mi" + "ra",
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
            r"(?i)(?<![A-Za-z0-9_])[\"']?(?:openai[_-]?)?"
            r"(?:api[_-]?key|token|secret|password)[\"']?"
            r"(?![A-Za-z0-9_])\s*[:=]\s*"
            r"[\"'][A-Za-z0-9_./+-]{12,}[\"']"
        ),
        re.compile(
            r"(?im)^\s*(?:export\s+)?(?<![A-Za-z0-9_])(?:openai[_-]?)?"
            r"(?:api[_-]?key|token|secret|password)"
            r"(?![A-Za-z0-9_])\s*=\s*"
            r"[A-Za-z0-9_./+-]{12,}\s*$"
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
    binary_assets = data.get("binary_assets", {})
    if not isinstance(binary_assets, dict) or not all(
        isinstance(relative, str)
        and isinstance(digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", digest)
        for relative, digest in binary_assets.items()
    ):
        raise ValueError(
            "manifest.binary_assets must map paths to lowercase SHA-256 digests"
        )
    return data


def _check_png(path: Path, relative: str) -> list[str]:
    findings: list[str] = []
    payload = path.read_bytes()
    if not payload.startswith(PNG_SIGNATURE):
        return [f"{relative}: invalid PNG signature"]

    offset = len(PNG_SIGNATURE)
    chunks: list[tuple[bytes, int]] = []
    while offset < len(payload):
        if len(payload) - offset < 12:
            findings.append(f"{relative}: truncated PNG chunk")
            return findings
        length = struct.unpack(">I", payload[offset : offset + 4])[0]
        chunk_type = payload[offset + 4 : offset + 8]
        chunk_end = offset + 12 + length
        if chunk_end > len(payload):
            findings.append(f"{relative}: truncated PNG chunk")
            return findings
        chunk_data = payload[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(
            ">I", payload[offset + 8 + length : chunk_end]
        )[0]
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            findings.append(f"{relative}: PNG chunk CRC mismatch")
        if chunk_type not in SAFE_PNG_CHUNKS:
            name = chunk_type.decode("ascii", errors="replace")
            findings.append(f"{relative}: PNG chunk is not allowed: {name}")
        chunks.append((chunk_type, length))
        offset = chunk_end
        if chunk_type == b"IEND":
            break

    chunk_types = [chunk_type for chunk_type, _ in chunks]
    if not chunk_types or chunk_types[0] != b"IHDR":
        findings.append(f"{relative}: PNG must start with IHDR")
    if chunk_types.count(b"IHDR") != 1:
        findings.append(f"{relative}: PNG must contain exactly one IHDR")
    elif chunks[chunk_types.index(b"IHDR")][1] != 13:
        findings.append(f"{relative}: PNG structure is invalid: IHDR length")
    if b"IDAT" not in chunk_types:
        findings.append(f"{relative}: PNG must contain IDAT")
    if chunk_types.count(b"IEND") != 1:
        findings.append(f"{relative}: PNG must contain exactly one IEND")
    else:
        iend_index = chunk_types.index(b"IEND")
        if chunks[iend_index][1] != 0:
            findings.append(f"{relative}: PNG structure is invalid: IEND length")
        if chunk_types[-1] != b"IEND" or offset != len(payload):
            findings.append(f"{relative}: PNG must end with IEND and no trailing data")

    plte_indices = [
        index for index, chunk_type in enumerate(chunk_types)
        if chunk_type == b"PLTE"
    ]
    idat_indices = [
        index for index, chunk_type in enumerate(chunk_types)
        if chunk_type == b"IDAT"
    ]
    if len(plte_indices) > 1:
        findings.append(f"{relative}: PNG structure is invalid: duplicate PLTE")
    if plte_indices and idat_indices and plte_indices[0] > idat_indices[0]:
        findings.append(f"{relative}: PNG structure is invalid: PLTE after IDAT")
    if idat_indices and idat_indices != list(
        range(idat_indices[0], idat_indices[-1] + 1)
    ):
        findings.append(f"{relative}: PNG structure is invalid: discontinuous IDAT")
    return findings


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
    binary_assets = manifest.get("binary_assets", {})

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
        suffix = (
            path.suffix.lower()
            or (path.name if path.name.startswith(".") else "")
        )
        is_text = suffix in TEXT_SUFFIXES or path.name in TEXT_FILENAMES
        is_binary = relative in binary_assets or not is_text
        if is_binary:
            expected_hash = binary_assets.get(relative)
            if expected_hash is None:
                findings.append(f"{relative}: binary asset is not allowlisted")
            elif path.suffix.lower() != ".png":
                findings.append(f"{relative}: only exact allowlisted PNG assets are allowed")
            else:
                actual_hash = sha256_file(path)
                if actual_hash != expected_hash:
                    findings.append(f"{relative}: binary asset SHA-256 mismatch")
                findings.extend(_check_png(path, relative))
        if "/../" in f"/{relative}/" or relative.startswith("../"):
            findings.append(f"{relative}: non-canonical path")
        if is_binary:
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
    binary_paths = set(binary_assets)
    for relative in sorted(binary_paths - allowed):
        findings.append(f"{relative}: binary asset is not in manifest.files")
    for relative in sorted(binary_paths - actual):
        findings.append(f"{relative}: allowlisted binary asset is missing")
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

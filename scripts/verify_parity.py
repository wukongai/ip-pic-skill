#!/usr/bin/env python3
"""Verify that every original IP source file has an explicit public decision."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.parity import ParityError, verify_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "parity" / "ip-parity-manifest.json",
    )
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = verify_manifest(args.manifest, args.source_root)
    except ParityError as exc:
        print(f"parity manifest invalid: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

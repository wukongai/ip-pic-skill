#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "src"))

from ip_pic.release import validate_release


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the public release allowlist and safety boundary."
    )
    parser.add_argument("--root", type=Path, default=SKILL_ROOT)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=SKILL_ROOT / "public-release-manifest.json",
    )
    parser.add_argument("--private-patterns", type=Path)
    args = parser.parse_args()
    try:
        result = validate_release(
            args.root,
            args.manifest,
            private_patterns_path=args.private_patterns,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

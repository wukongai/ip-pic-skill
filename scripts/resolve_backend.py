#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "src"))

from custom_ip_illustration.backend import resolve_backend
from custom_ip_illustration.errors import CustomIPIllustrationError


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve a provider-neutral image backend decision."
    )
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--requested", default="auto")
    parser.add_argument("--preference", default="auto")
    args = parser.parse_args()
    try:
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
        result = resolve_backend(
            inventory,
            requested=args.requested,
            preference=args.preference,
        )
    except (OSError, json.JSONDecodeError, CustomIPIllustrationError) as exc:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "backend_id": None,
                    "reason": str(exc),
                    "choices": [],
                    "choice_details": [],
                },
                ensure_ascii=False,
            )
        )
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

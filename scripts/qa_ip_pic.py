#!/usr/bin/env python3
"""Write one explicit per-image QA receipt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.qa import evaluate_image  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--pass-check", action="append", default=[])
    parser.add_argument("--fail-check", action="append", default=[])
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    observations = {name: True for name in args.pass_check}
    observations.update({name: False for name in args.fail_check})
    result = evaluate_image(manifest, args.image, observations)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

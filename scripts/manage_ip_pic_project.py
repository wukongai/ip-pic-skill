#!/usr/bin/env python3
"""Preview and apply private IP Pic customization in one user project."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.project_cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def example_profile() -> dict:
    return deepcopy(
        json.loads(
            (
                ROOT
                / "examples"
                / "characters"
                / "wukong"
                / "profile.json"
            ).read_text(encoding="utf-8")
        )
    )


def example_brief() -> dict:
    return deepcopy(
        json.loads(
            (ROOT / "examples" / "brief.example.json").read_text(encoding="utf-8")
        )
    )

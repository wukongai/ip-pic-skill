#!/usr/bin/env bash
set -euo pipefail

manifest="ip-pic-eval-output/run-manifest.json"
prompt_file="$(find ip-pic-eval-output -maxdepth 1 -name '*.prompt.md' -type f -print -quit 2>/dev/null || true)"

if [[ ! -f "$manifest" || -z "$prompt_file" ]]; then
  echo "missing direct-integrated compile artifacts"
  exit 1
fi

python3 - "$manifest" "$prompt_file" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
prompt = Path(sys.argv[2]).read_text(encoding="utf-8")

if manifest.get("compile_only") is not True:
    raise SystemExit("manifest does not declare compile_only")
if manifest.get("delivery", {}).get("mode") != "direct-integrated":
    raise SystemExit("delivery mode is not direct-integrated")
if manifest.get("delivery", {}).get("text_integrated") is not True:
    raise SystemExit("direct text integration is not required")
checks = manifest.get("visual_qa", {}).get("required_checks", [])
if "integrated_text_present" not in checks or "integrated_text_legible" not in checks:
    raise SystemExit("direct typography QA is incomplete")
if "一次生成图文融合" not in prompt:
    raise SystemExit("prompt lost the integrated typography instruction")
if list(Path("ip-pic-eval-output").rglob("*.png")):
    raise SystemExit("prompt-only evaluation unexpectedly rendered an image")

print("direct-integrated compile contract passed")
PY

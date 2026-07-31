from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.compiler import compile_request  # noqa: E402
from tests.test_selection_and_compiler import article_brief  # noqa: E402


def _normalize_paths(value: Any, roots: list[Path]) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_paths(item, roots) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_paths(item, roots) for item in value]
    if isinstance(value, str):
        result = value
        for root in sorted({str(item) for item in roots}, key=len, reverse=True):
            result = result.replace(root, "<output>")
        return result
    return value


def _projection(manifest: dict[str, Any]) -> dict[str, Any]:
    handoff = manifest["render_handoff"]
    return {
        "template_id": manifest["template"]["id"],
        "size": manifest["size"],
        "director_plan": manifest["director_plan"],
        "expected_outputs": manifest["expected_outputs"],
        "delivery": manifest["delivery"],
        "visual_qa": manifest["visual_qa"],
        "render_handoff": {
            "schema_version": handoff["schema_version"],
            "id": handoff["id"],
            "prompt_file": handoff["prompt_file"],
            "size": handoff["size"],
            "output_dir": handoff["output_dir"],
            "assets": handoff["assets"],
        },
    }


def _normalize_public_renames(value: Any, private_id: str) -> Any:
    if isinstance(value, dict):
        result = {
            key: _normalize_public_renames(item, private_id)
            for key, item in value.items()
        }
        if result.get("owner") in {"image-factory", "ip-pic"}:
            result["owner"] = "public-ip-director"
        return result
    if isinstance(value, list):
        return [_normalize_public_renames(item, private_id) for item in value]
    if isinstance(value, str):
        return (
            value.replace(f"{private_id}-ip-", "ip-")
            .replace("image-factory", "ip-pic")
        )
    return value


def _headers(prompt: str) -> list[str]:
    return re.findall(r"^【([^】]+)】$", prompt, flags=re.MULTILINE)


class CompilerDualEndTests(unittest.TestCase):
    def test_neutral_direct_integrated_contract_matches_original(self) -> None:
        source_value = os.environ.get("IMAGE_FACTORY_SOURCE")
        private_id = os.environ.get("IP_PIC_PRIVATE_SOURCE_ID")
        if not source_value or not private_id:
            self.skipTest("set source path and private id for dual-end parity")
        source = Path(source_value)
        brief = article_brief()
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            brief_path = temp_root / "brief.json"
            source_output = temp_root / "source"
            public_output = temp_root / "public"
            brief_path.write_text(
                json.dumps(brief, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["PYTHONPATH"] = str(source / "src")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(source / "scripts" / "generate_image_asset.py"),
                    "--brief",
                    str(brief_path),
                    "--template",
                    "custom-ip-handdrawn-article-v1",
                    "--output-dir",
                    str(source_output),
                ],
                cwd=source,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            public = compile_request(ROOT, brief, public_output, write=True)
            source_manifest = json.loads(
                (source_output / "image-asset-manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            source_prompt = next(source_output.glob("*.prompt.md")).read_text(
                encoding="utf-8"
            )

            expected = _normalize_public_renames(
                _normalize_paths(
                    _projection(source_manifest),
                    [source_output, source_output.resolve()],
                ),
                private_id,
            )
            actual = _normalize_public_renames(
                _normalize_paths(
                    _projection(public["manifest"]),
                    [public_output, public_output.resolve()],
                ),
                private_id,
            )

            self.assertEqual(actual, expected)
            self.assertEqual(_headers(public["prompt"]), _headers(source_prompt))
            for line in (
                "请一次生成一张图文融合的 IP 正文配图",
                "【一次生成图文融合硬约束】",
                "IP、物件、箭头和少量中文短标注必须组成一个整体画面",
                "请直接生成一次性图文融合成品",
            ):
                self.assertIn(line, source_prompt)
                self.assertIn(line, public["prompt"])


if __name__ == "__main__":
    unittest.main()

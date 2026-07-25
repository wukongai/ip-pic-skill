from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _support import ROOT, example_brief, example_profile
from custom_ip_illustration.compiler import compile_request
from custom_ip_illustration.errors import SecurityError


class CompilerTests(unittest.TestCase):
    def test_three_canvases_compile_with_independent_templates(self) -> None:
        expected = {
            "16:9": "article-landscape-v1",
            "1:1": "keyframe-square-v1",
            "9:16": "story-portrait-v1",
        }
        with tempfile.TemporaryDirectory() as temp:
            for canvas, template_id in expected.items():
                brief = example_brief()
                brief["canvas"] = canvas
                brief["image_count"] = 1
                output = Path(temp) / canvas.replace(":", "x")
                result = compile_request(
                    profile=example_profile(),
                    brief=brief,
                    output_dir=output,
                    skill_root=ROOT,
                )
                self.assertEqual(
                    result["run_manifest"]["template_id"],
                    template_id,
                )
                self.assertTrue((output / "prompts").is_dir())
                self.assertTrue((output / "render-request.json").is_file())

    def test_render_request_excludes_backend_controls(self) -> None:
        profile = example_profile()
        profile["references"] = [
            {
                "path": "refs/character.png",
                "purpose": "identity",
                "authorized": True,
            }
        ]
        with tempfile.TemporaryDirectory() as temp:
            result = compile_request(
                profile=profile,
                brief=example_brief(),
                output_dir=Path(temp) / "out",
                skill_root=ROOT,
            )
        serialized = json.dumps(result["render_request"])
        for forbidden in (
            '"provider"',
            '"model"',
            '"api_key"',
            '"base_url"',
            '"timeout"',
            '"retry"',
            '"fallback"',
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertIn("refs/character.png", serialized)

    def test_reference_path_is_not_written_into_prompt(self) -> None:
        profile = example_profile()
        profile["references"] = [
            {
                "path": "refs/character.png",
                "purpose": "identity",
                "authorized": True,
            }
        ]
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "out"
            compile_request(
                profile=profile,
                brief=example_brief(),
                output_dir=output,
                skill_root=ROOT,
            )
            prompt = next((output / "prompts").glob("*.md")).read_text(
                encoding="utf-8"
            )
        self.assertNotIn("refs/character.png", prompt)

    def test_output_inside_skill_is_blocked(self) -> None:
        with self.assertRaisesRegex(SecurityError, "outside"):
            compile_request(
                profile=example_profile(),
                brief=example_brief(),
                output_dir=ROOT / "outputs" / "forbidden",
                skill_root=ROOT,
            )

    def test_check_mode_does_not_create_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "not-created"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "compile_ip_illustration.py"),
                    "--profile",
                    str(ROOT / "examples" / "ip-profile.example.json"),
                    "--brief",
                    str(ROOT / "examples" / "brief.example.json"),
                    "--output-dir",
                    str(output),
                    "--check",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertFalse(output.exists())
            self.assertEqual(json.loads(completed.stdout)["status"], "validated")


if __name__ == "__main__":
    unittest.main()

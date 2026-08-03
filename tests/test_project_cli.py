from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "manage_ip_pic_project.py"


class ProjectCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name).resolve()
        self.draft_path = self.project / "style-draft.json"
        self.draft_path.write_text(
            json.dumps(
                {
                    "id": "warm-crayon",
                    "display_name": "温暖蜡笔",
                    "aliases": ["暖蜡笔"],
                    "base_style_id": "minimal-lineart",
                    "overrides": {
                        "line": "自然粗线",
                        "palette": ["暖黄", "砖红"],
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def create_preview(self) -> dict:
        result = self.run_cli(
            "plan-create",
            "--project-root",
            str(self.project),
            "--kind",
            "style",
            "--draft",
            str(self.draft_path),
            "--activate",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_plan_create_prints_machine_readable_preview(self) -> None:
        preview = self.create_preview()

        self.assertEqual(preview["status"], "preview")
        self.assertEqual(preview["kind"], "style")
        self.assertEqual(preview["version"], "v0001")
        self.assertTrue(Path(preview["plan_path"]).is_file())

    def test_apply_requires_confirm_and_returns_redacted_receipt(self) -> None:
        preview = self.create_preview()
        denied = self.run_cli(
            "apply",
            "--project-root",
            str(self.project),
            "--plan",
            preview["plan_path"],
        )
        self.assertEqual(denied.returncode, 2)
        error = json.loads(denied.stderr)
        self.assertEqual(error["status"], "error")
        self.assertIn("确认", error["error"])
        self.assertNotIn(str(self.project), denied.stderr)

        applied = self.run_cli(
            "apply",
            "--project-root",
            str(self.project),
            "--plan",
            preview["plan_path"],
            "--confirm",
        )
        self.assertEqual(applied.returncode, 0, applied.stderr)
        receipt = json.loads(applied.stdout)
        self.assertEqual(receipt["status"], "applied")
        self.assertEqual(receipt["version"], "v0001")
        self.assertNotIn(str(self.project), applied.stdout)
        self.assertNotIn("自然粗线", applied.stdout)

    def test_list_show_and_plan_activate_are_json_commands(self) -> None:
        preview = self.create_preview()
        self.run_cli(
            "apply",
            "--project-root",
            str(self.project),
            "--plan",
            preview["plan_path"],
            "--confirm",
        )

        listed = self.run_cli(
            "list",
            "--project-root",
            str(self.project),
            "--kind",
            "style",
        )
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(json.loads(listed.stdout)["assets"][0]["id"], "warm-crayon")

        shown = self.run_cli(
            "show",
            "--project-root",
            str(self.project),
            "--kind",
            "style",
            "--id",
            "暖蜡笔",
            "--version",
            "v0001",
        )
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertEqual(
            json.loads(shown.stdout)["overrides"]["line"],
            "自然粗线",
        )

        activate = self.run_cli(
            "plan-activate",
            "--project-root",
            str(self.project),
            "--kind",
            "style",
            "--id",
            "warm-crayon",
            "--version",
            "v0001",
        )
        self.assertEqual(activate.returncode, 0, activate.stderr)
        self.assertEqual(json.loads(activate.stdout)["operation"], "activate")

    def test_invalid_draft_error_does_not_echo_secret_or_absolute_paths(self) -> None:
        unsafe = json.loads(self.draft_path.read_text(encoding="utf-8"))
        unsafe["overrides"]["api_key"] = "sk-do-not-echo"
        self.draft_path.write_text(
            json.dumps(unsafe, ensure_ascii=False),
            encoding="utf-8",
        )

        result = self.run_cli(
            "plan-create",
            "--project-root",
            str(self.project),
            "--kind",
            "style",
            "--draft",
            str(self.draft_path),
        )

        self.assertEqual(result.returncode, 2)
        self.assertNotIn("sk-do-not-echo", result.stderr)
        self.assertNotIn(str(self.project), result.stderr)
        self.assertIn("禁止字段", json.loads(result.stderr)["error"])


if __name__ == "__main__":
    unittest.main()

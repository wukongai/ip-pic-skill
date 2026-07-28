from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _support import ROOT
from ip_pic.release import sha256_file


def release_hashes(root: Path) -> dict[str, str]:
    manifest = json.loads(
        (root / "public-release-manifest.json").read_text(encoding="utf-8")
    )
    return {
        relative: sha256_file(root / relative)
        for relative in manifest["files"]
        if (root / relative).is_file()
    }


class ColdStartTests(unittest.TestCase):
    def test_isolated_copy_compiles_three_canvases_without_mutating_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            installed = base / "installed-skill"
            shutil.copytree(
                ROOT,
                installed,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            before = release_hashes(installed)

            work = base / "用户项目 with spaces"
            work.mkdir()
            environment = dict(os.environ)
            environment["HOME"] = str(base / "fresh-home")
            environment["XDG_CONFIG_HOME"] = str(base / "fresh-xdg")
            environment["PYTHONPATH"] = ""

            source_brief = json.loads(
                (installed / "examples" / "brief.example.json").read_text(
                    encoding="utf-8"
                )
            )
            for character in ("wukong", "moon-rabbit", "ato"):
                for canvas in ("16:9", "1:1", "9:16"):
                    brief = dict(source_brief)
                    brief["canvas"] = canvas
                    brief["image_count"] = 1
                    slug = canvas.replace(":", "x")
                    brief_path = work / f"brief-{character}-{slug}.json"
                    brief_path.write_text(
                        json.dumps(brief, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    output = work / f"output-{character}-{slug}"
                    profile = (
                        installed
                        / "examples"
                        / "characters"
                        / character
                        / "profile.json"
                    )
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(
                                installed
                                / "scripts"
                                / "compile_ip_illustration.py"
                            ),
                            "--profile",
                            str(profile),
                            "--brief",
                            str(brief_path),
                            "--output-dir",
                            str(output),
                        ],
                        cwd=work,
                        env=environment,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertTrue(
                        (output / "render-request.json").is_file()
                    )
                    self.assertTrue((output / "run-manifest.json").is_file())

            self.assertEqual(release_hashes(installed), before)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _support import ROOT
from ip_pic.errors import SecurityError
from ip_pic.preferences import (
    DEFAULT_PREFERENCES,
    parse_extend,
    resolve_preferences,
)


class PreferenceTests(unittest.TestCase):
    def test_defaults_require_no_setup(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            values, source = resolve_preferences(
                project_root=base / "project",
                environment={
                    "HOME": str(base / "home"),
                    "XDG_CONFIG_HOME": str(base / "xdg"),
                },
            )
        self.assertIsNone(source)
        self.assertEqual(values, DEFAULT_PREFERENCES)

    def test_project_file_wins_and_first_hit_stops(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            project_file = (
                base / "project" / ".ip-pic" / "EXTEND.md"
            )
            xdg_file = base / "xdg" / "ip-pic" / "EXTEND.md"
            project_file.parent.mkdir(parents=True)
            xdg_file.parent.mkdir(parents=True)
            project_file.write_text(
                "```yaml\npreferred_image_backend: project-backend\n```\n",
                encoding="utf-8",
            )
            xdg_file.write_text(
                "```yaml\npreferred_image_backend: xdg-backend\n```\n",
                encoding="utf-8",
            )
            values, source = resolve_preferences(
                project_root=base / "project",
                environment={
                    "HOME": str(base / "home"),
                    "XDG_CONFIG_HOME": str(base / "xdg"),
                },
            )
        self.assertEqual(source, project_file.resolve())
        self.assertEqual(values["preferred_image_backend"], "project-backend")

    def test_new_ip_pic_path_has_priority_over_legacy_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            current = base / "project" / ".ip-pic" / "EXTEND.md"
            legacy = (
                base / "project" / ".custom-ip-illustration" / "EXTEND.md"
            )
            current.parent.mkdir(parents=True)
            legacy.parent.mkdir(parents=True)
            current.write_text(
                "```yaml\npreferred_image_backend: current\n```\n",
                encoding="utf-8",
            )
            legacy.write_text(
                "```yaml\npreferred_image_backend: legacy\n```\n",
                encoding="utf-8",
            )
            values, source = resolve_preferences(
                project_root=base / "project",
                environment={
                    "HOME": str(base / "home"),
                    "XDG_CONFIG_HOME": str(base / "xdg"),
                },
            )
        self.assertEqual(source, current.resolve())
        self.assertEqual(values["preferred_image_backend"], "current")

    def test_legacy_path_is_read_only_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            legacy = (
                base / "project" / ".custom-ip-illustration" / "EXTEND.md"
            )
            legacy.parent.mkdir(parents=True)
            legacy.write_text(
                "```yaml\npreferred_image_backend: legacy\n```\n",
                encoding="utf-8",
            )
            with self.assertWarnsRegex(DeprecationWarning, r"\.ip-pic"):
                values, source = resolve_preferences(
                    project_root=base / "project",
                    environment={
                        "HOME": str(base / "home"),
                        "XDG_CONFIG_HOME": str(base / "xdg"),
                    },
                )
        self.assertEqual(source, legacy.resolve())
        self.assertEqual(values["preferred_image_backend"], "legacy")

    def test_credential_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "EXTEND.md"
            path.write_text(
                "```yaml\napi_key: not-a-real-value\n```\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SecurityError, "not allowed"):
                parse_extend(path)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.project_store import (  # noqa: E402
    ConfirmationRequired,
    ProjectStoreError,
    apply_plan,
    list_assets,
    plan_activate,
    plan_create,
    resolve_asset,
)


class ProjectStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name).resolve()

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def style_draft(line: str = "自然粗线") -> dict:
        return {
            "id": "warm-crayon",
            "display_name": "温暖蜡笔",
            "aliases": ["暖蜡笔"],
            "base_style_id": "minimal-lineart",
            "overrides": {
                "line": line,
                "palette": ["暖黄", "砖红", "低饱和青绿"],
            },
        }

    def create_style(self, line: str = "自然粗线", *, activate: bool = True) -> dict:
        preview = plan_create(
            ROOT,
            self.project,
            "style",
            self.style_draft(line),
            activate=activate,
        )
        return apply_plan(
            ROOT,
            self.project,
            Path(preview["plan_path"]),
            confirmed=True,
        )

    def test_plan_is_preview_only_and_apply_requires_confirmation(self) -> None:
        preview = plan_create(
            ROOT, self.project, "style", self.style_draft(), activate=True
        )

        self.assertEqual(preview["status"], "preview")
        self.assertTrue(Path(preview["plan_path"]).is_file())
        self.assertFalse((self.project / ".ip-pic" / "registry.json").exists())
        self.assertFalse(
            (self.project / ".ip-pic" / "styles" / "warm-crayon" / "v0001.json").exists()
        )
        with self.assertRaisesRegex(ConfirmationRequired, "确认"):
            apply_plan(
                ROOT,
                self.project,
                Path(preview["plan_path"]),
                confirmed=False,
            )
        self.assertFalse((self.project / ".ip-pic" / "registry.json").exists())

    def test_confirmed_apply_creates_version_registry_and_redacted_receipt(self) -> None:
        receipt = self.create_style()
        registry = json.loads(
            (self.project / ".ip-pic" / "registry.json").read_text(encoding="utf-8")
        )

        self.assertEqual(receipt["status"], "applied")
        self.assertEqual(receipt["version"], "v0001")
        self.assertEqual(receipt["registry_revision"], 1)
        self.assertEqual(
            registry["active"]["style"],
            {"id": "warm-crayon", "version": "v0001"},
        )
        self.assertEqual(
            registry["assets"]["style"]["warm-crayon"]["versions"],
            ["v0001"],
        )
        self.assertNotIn(str(self.project), json.dumps(receipt, ensure_ascii=False))
        self.assertNotIn("自然粗线", json.dumps(receipt, ensure_ascii=False))

    def test_updates_are_immutable_versions_and_old_version_resolves(self) -> None:
        self.create_style("第一版线条")
        second = self.create_style("第二版线条")

        self.assertEqual(second["version"], "v0002")
        first = resolve_asset(
            self.project, "style", "warm-crayon", version="v0001"
        )
        active = resolve_asset(self.project, "style", "warm-crayon")
        self.assertEqual(first["overrides"]["line"], "第一版线条")
        self.assertEqual(active["version"], "v0002")
        self.assertEqual(active["overrides"]["line"], "第二版线条")

    def test_list_alias_resolution_and_activate_old_version(self) -> None:
        self.create_style("第一版")
        self.create_style("第二版")

        listing = list_assets(self.project, "style")
        self.assertEqual(listing["assets"][0]["versions"], ["v0001", "v0002"])
        by_alias = resolve_asset(self.project, "style", "暖蜡笔")
        self.assertEqual(by_alias["id"], "warm-crayon")

        preview = plan_activate(
            self.project, "style", "warm-crayon", "v0001"
        )
        receipt = apply_plan(
            ROOT,
            self.project,
            Path(preview["plan_path"]),
            confirmed=True,
        )
        self.assertEqual(receipt["operation"], "activate")
        self.assertEqual(
            resolve_asset(self.project, "style")["version"],
            "v0001",
        )
        self.assertTrue(
            (self.project / ".ip-pic" / "styles" / "warm-crayon" / "v0002.json").is_file()
        )

    def test_tampered_plan_fails_closed(self) -> None:
        preview = plan_create(
            ROOT, self.project, "style", self.style_draft(), activate=True
        )
        path = Path(preview["plan_path"])
        plan = json.loads(path.read_text(encoding="utf-8"))
        plan["content"]["overrides"]["line"] = "篡改后的线条"
        path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

        with self.assertRaisesRegex(ProjectStoreError, "hash"):
            apply_plan(ROOT, self.project, path, confirmed=True)
        self.assertFalse((self.project / ".ip-pic" / "registry.json").exists())

    def test_registry_revision_drift_rejects_stale_plan(self) -> None:
        stale = plan_create(
            ROOT, self.project, "style", self.style_draft("旧计划"), activate=True
        )
        other_draft = {
            "id": "paper-ink",
            "display_name": "纸墨",
            "base_style_id": "minimal-lineart",
            "overrides": {"material": "纸张与淡墨"},
        }
        other = plan_create(
            ROOT, self.project, "style", other_draft, activate=False
        )
        apply_plan(
            ROOT, self.project, Path(other["plan_path"]), confirmed=True
        )

        with self.assertRaisesRegex(ProjectStoreError, "revision"):
            apply_plan(
                ROOT,
                self.project,
                Path(stale["plan_path"]),
                confirmed=True,
            )

    def test_existing_target_and_lock_are_never_overwritten(self) -> None:
        preview = plan_create(
            ROOT, self.project, "style", self.style_draft(), activate=True
        )
        target = self.project / ".ip-pic" / "styles" / "warm-crayon" / "v0001.json"
        target.parent.mkdir(parents=True)
        target.write_text('{"owned":"by-user"}', encoding="utf-8")
        with self.assertRaisesRegex(ProjectStoreError, "已存在"):
            apply_plan(
                ROOT, self.project, Path(preview["plan_path"]), confirmed=True
            )
        self.assertEqual(target.read_text(encoding="utf-8"), '{"owned":"by-user"}')

        target.unlink()
        lock = self.project / ".ip-pic" / ".lock"
        lock.write_text("busy", encoding="utf-8")
        with self.assertRaisesRegex(ProjectStoreError, "正在"):
            apply_plan(
                ROOT, self.project, Path(preview["plan_path"]), confirmed=True
            )
        self.assertEqual(lock.read_text(encoding="utf-8"), "busy")

    def test_symlink_ip_pic_and_symlink_plan_are_rejected(self) -> None:
        outside = self.project / "outside"
        outside.mkdir()
        ip_pic = self.project / ".ip-pic"
        try:
            os.symlink(outside, ip_pic)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable")
        with self.assertRaisesRegex(ProjectStoreError, "符号链接"):
            plan_create(ROOT, self.project, "style", self.style_draft())

        ip_pic.unlink()
        preview = plan_create(
            ROOT, self.project, "style", self.style_draft(), activate=True
        )
        real_plan = Path(preview["plan_path"])
        linked_plan = real_plan.with_name("linked-plan.json")
        os.symlink(real_plan, linked_plan)
        with self.assertRaisesRegex(ProjectStoreError, "符号链接"):
            apply_plan(ROOT, self.project, linked_plan, confirmed=True)

    def test_plan_activate_rejects_unknown_version_and_invalid_kind(self) -> None:
        self.create_style()
        with self.assertRaisesRegex(ProjectStoreError, "不存在"):
            plan_activate(self.project, "style", "warm-crayon", "v9999")
        with self.assertRaisesRegex(ProjectStoreError, "kind"):
            list_assets(self.project, "unknown")

    def test_registry_contains_no_secret_or_absolute_path_fields(self) -> None:
        self.create_style()
        registry_text = (
            self.project / ".ip-pic" / "registry.json"
        ).read_text(encoding="utf-8")
        lowered = registry_text.casefold()
        for forbidden in ("api_key", "authorization", "token", str(self.project).casefold()):
            self.assertNotIn(forbidden, lowered)


if __name__ == "__main__":
    unittest.main()

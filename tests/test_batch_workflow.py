from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.batch import (  # noqa: E402
    build_shot_plan,
    rebuild_batch,
    retry_failed,
    run_batch,
)
from ip_pic.errors import IPPicError  # noqa: E402

from tests.test_selection_and_compiler import article_brief  # noqa: E402


def _items(count: int) -> list[dict]:
    result = []
    for index in range(count):
        brief = article_brief(canvas="1:1")
        brief["id"] = f"shot-{index + 1:02d}"
        brief["scene"] = "ip_video_keyframe"
        brief["selection_receipt"]["business_type"] = "ip_video_keyframe"
        brief["content"]["headline"] = f"第 {index + 1} 个判断"
        result.append(brief)
    return result


class BatchWorkflowTests(unittest.TestCase):
    def test_square_shot_plan_enforces_original_rotation_gates(self) -> None:
        plan = build_shot_plan(_items(8))
        shots = plan["shots"]

        self.assertEqual(plan["schema_version"], "ip-pic-shot-plan/v1")
        for previous, current in zip(shots, shots[1:]):
            previous_key = tuple(
                previous[key]
                for key in ("composition_family", "crop", "orientation", "action")
            )
            current_key = tuple(
                current[key]
                for key in ("composition_family", "crop", "orientation", "action")
            )
            self.assertNotEqual(previous_key, current_key)
        for index in range(len(shots) - 5):
            window = shots[index : index + 6]
            self.assertGreaterEqual(
                len({shot["composition_family"] for shot in window}),
                4,
            )
        first_six = shots[:6]
        self.assertIn("seated-loop", {shot["composition_family"] for shot in first_six})
        self.assertIn("top-down-partial", {shot["composition_family"] for shot in first_six})
        self.assertIn("close-hands", {shot["composition_family"] for shot in first_six})
        self.assertIn("object-dominant", {shot["composition_family"] for shot in first_six})
        for shot in shots:
            expected_anchor = (
                "right"
                if shot["text_layout_variant"] == "square-left"
                else "left"
            )
            self.assertEqual(
                shot["visual_anchor_position"],
                expected_anchor,
            )

    def test_partial_failure_preserves_success_and_retry_only_failed(self) -> None:
        calls: list[str] = []

        def flaky_renderer(manifest: dict, _item_dir: Path) -> dict:
            item_id = manifest["brief"]["id"]
            calls.append(item_id)
            if item_id == "shot-02":
                raise RuntimeError("temporary render failure")
            return {"status": "ok", "receipt_id": f"render-{item_id}"}

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "batch"
            manifest_path = run_batch(
                ROOT,
                {"schema_version": "ip-pic-batch/v1", "id": "demo", "items": _items(3)},
                output,
                renderer=flaky_renderer,
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "partial_failure")
            self.assertEqual(manifest["succeeded"], 2)
            self.assertEqual(manifest["failed"], 1)
            first_receipts = {
                item["id"]: item.get("render_receipt") for item in manifest["items"]
            }
            retry_calls: list[str] = []

            def retry_renderer(manifest: dict, _item_dir: Path) -> dict:
                item_id = manifest["brief"]["id"]
                retry_calls.append(item_id)
                return {
                    "status": "ok",
                    "receipt_id": f"retry-{item_id}",
                }

            retried_path = retry_failed(
                manifest_path,
                renderer=retry_renderer,
            )
            retried = json.loads(retried_path.read_text(encoding="utf-8"))

            self.assertEqual(retry_calls, ["shot-02"])
            self.assertEqual(retried["status"], "ok")
            self.assertEqual(retried["items"][0]["render_receipt"], first_receipts["shot-01"])
            self.assertEqual(retried["items"][2]["render_receipt"], first_receipts["shot-03"])
            self.assertEqual(
                retried["items"][1]["render_receipt"]["receipt_id"],
                "retry-shot-02",
            )
            self.assertEqual(retried["items"][1]["attempts"], 2)

    def test_full_rebuild_requires_new_directory_and_excludes_old_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old_output = root / "old"
            old_manifest_path = run_batch(
                ROOT,
                {"schema_version": "ip-pic-batch/v1", "id": "old", "items": _items(2)},
                old_output,
                renderer=lambda manifest, _item_dir: {
                    "status": "ok",
                    "receipt_id": manifest["brief"]["id"],
                },
            )
            old_manifest = json.loads(old_manifest_path.read_text(encoding="utf-8"))
            new_request = {
                "schema_version": "ip-pic-batch/v1",
                "id": "rebuilt",
                "items": copy.deepcopy(_items(2)),
            }
            old_image = old_output / "01-shot-01" / "image" / "shot-01.png"
            new_request["items"][0]["visual"]["authorized_assets"] = [
                {
                    "id": "rejected-output",
                    "path": str(old_image),
                    "purpose": "style",
                }
            ]

            with self.assertRaisesRegex(IPPicError, "旧批次|old batch"):
                rebuild_batch(
                    ROOT,
                    old_manifest_path,
                    new_request,
                    old_output,
                    renderer=lambda _manifest, _item_dir: {"status": "ok"},
                )

            new_output = root / "new"
            rebuilt_path = rebuild_batch(
                ROOT,
                old_manifest_path,
                new_request,
                new_output,
                renderer=lambda manifest, _item_dir: {
                    "status": "ok",
                    "receipt_id": manifest["brief"]["id"],
                },
            )
            rebuilt = json.loads(rebuilt_path.read_text(encoding="utf-8"))
            self.assertEqual(rebuilt["rebuild"]["source_batch"], str(old_manifest_path.resolve()))
            self.assertEqual(rebuilt["rebuild"]["old_assets_excluded"], [str(old_image.resolve())])
            self.assertEqual(
                rebuilt["items"][0]["compiled_manifest"]["inputs"]["authorized_visual_assets"],
                [],
            )
            self.assertEqual(
                old_manifest["items"][0]["render_receipt"]["receipt_id"],
                "shot-01",
            )

    def test_batch_refuses_to_overwrite_existing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "batch"
            output.mkdir()
            with self.assertRaisesRegex(IPPicError, "exists|覆盖"):
                run_batch(
                    ROOT,
                    {"schema_version": "ip-pic-batch/v1", "id": "demo", "items": _items(1)},
                    output,
                    renderer=lambda _manifest, _item_dir: {"status": "ok"},
                )


if __name__ == "__main__":
    unittest.main()

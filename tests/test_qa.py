from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.compiler import compile_request  # noqa: E402
from ip_pic.qa import evaluate_image  # noqa: E402

from tests.test_selection_and_compiler import article_brief  # noqa: E402


class ImageQATests(unittest.TestCase):
    def _manifest(self, root: Path, *, mode: str = "direct-integrated") -> dict:
        canvas = "1:1 -> 3:4" if mode == "two-step-publish" else "16:9"
        brief = article_brief(delivery_mode=mode, canvas=canvas)
        if mode == "two-step-publish":
            brief["selection_receipt"]["publish_extension_id"] = (
                "editorial-ink-v2"
            )
            brief["composition"]["publish_preset"] = "portrait_3_4"
        return compile_request(
            ROOT,
            brief,
            root / "compiled",
            write=True,
        )["manifest"]

    def test_direct_integrated_pure_illustration_fails_and_retries_render_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._manifest(root)
            output = Path(manifest["expected_outputs"]["final_image"])
            output.parent.mkdir(parents=True)
            Image.new("RGB", (32, 18), "white").save(output)

            result_path = evaluate_image(
                manifest,
                output,
                {
                    "ip_identity": True,
                    "semantic_action": True,
                    "integrated_text_present": False,
                    "integrated_text_legible": False,
                    "text_does_not_overlap_subject": True,
                },
            )
            result = json.loads(result_path.read_text(encoding="utf-8"))

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["failed_checks"], [
                "integrated_text_present",
                "integrated_text_legible",
            ])
            self.assertEqual(result["retry_scope"], "render")
            self.assertEqual(result["visual_acceptance"], "failed")

    def test_two_step_reviews_final_and_rejects_raw_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._manifest(root, mode="two-step-publish")
            raw = Path(manifest["expected_outputs"]["raw_image"])
            raw.parent.mkdir(parents=True)
            Image.new("RGB", (32, 32), "white").save(raw)

            result = json.loads(
                evaluate_image(
                    manifest,
                    raw,
                    {check: True for check in manifest["visual_qa"]["required_checks"]},
                ).read_text(encoding="utf-8")
            )

            self.assertEqual(result["status"], "failed")
            self.assertIn("reviewed_final_deliverable", result["failed_checks"])
            self.assertEqual(result["retry_scope"], "publish-layout")

    def test_all_checks_pass_still_requires_human_visual_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._manifest(root)
            output = Path(manifest["expected_outputs"]["final_image"])
            output.parent.mkdir(parents=True)
            Image.new("RGB", (32, 18), "white").save(output)
            checks = {
                check: True for check in manifest["visual_qa"]["required_checks"]
            }

            result = json.loads(
                evaluate_image(manifest, output, checks).read_text(encoding="utf-8")
            )

            self.assertEqual(result["status"], "checks_passed")
            self.assertEqual(result["visual_acceptance"], "pending_human")
            self.assertFalse(result["approved_for_release"])


if __name__ == "__main__":
    unittest.main()

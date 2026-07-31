from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.references import compile_reference_plan  # noqa: E402


class ReferenceStrategyTests(unittest.TestCase):
    def _assets(self, root: Path) -> list[dict]:
        assets = []
        for index, purpose in enumerate(("style", "identity", "composition"), 1):
            path = root / f"{purpose}.png"
            Image.new("RGB", (32 + index, 24 + index), (20 * index, 40, 60)).save(
                path
            )
            assets.append(
                {
                    "id": purpose,
                    "path": str(path),
                    "purpose": purpose,
                    "ownership": "project-original-tutorial",
                    "required": purpose == "identity",
                }
            )
        return assets

    def _compile(
        self,
        root: Path,
        strategy: str,
    ) -> dict:
        prompt = root / "prompt.md"
        prompt.write_text("public prompt", encoding="utf-8")
        return compile_reference_plan(
            item_id="neutral-item",
            template={"reference_strategy": {"type": strategy}},
            brief={"visual": {}},
            authorized_assets=self._assets(root),
            prompt_file=prompt,
            size="1536x864",
            output_dir=root / "output",
        )

    def test_primary_reference_prefers_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan = self._compile(Path(temp), "primary_reference")

        self.assertEqual(plan["selected_asset_count"], 1)
        self.assertEqual(plan["selected_assets"][0]["purpose"], "identity")
        self.assertFalse(plan["selection_required"])

    def test_native_multi_reference_preserves_all_authorized_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan = self._compile(Path(temp), "native_multi_reference")

        self.assertEqual(plan["selected_asset_count"], 3)
        self.assertEqual(
            {item["purpose"] for item in plan["selected_assets"]},
            {"identity", "style", "composition"},
        )

    def test_reference_board_has_source_provenance_and_one_selected_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan = self._compile(root, "reference_board")

            board = Path(plan["reference_board"]["path"])
            provenance = Path(plan["reference_board"]["manifest_path"])
            self.assertTrue(board.is_file())
            self.assertTrue(provenance.is_file())
            self.assertEqual(plan["reference_board"]["source_count"], 3)
            self.assertEqual(plan["selected_asset_count"], 1)
            self.assertEqual(plan["selected_assets"][0]["purpose"], "content")
            self.assertEqual(
                plan["selected_assets"][0]["ownership"],
                "derived_from_authorized_assets",
            )

    def test_candidate_handoffs_are_stable_and_require_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = self._compile(root, "candidate_handoffs")
            second_root = root / "second"
            second_root.mkdir()
            second = self._compile(second_root, "candidate_handoffs")

        self.assertTrue(first["selection_required"])
        self.assertEqual(len(first["candidates"]), 3)
        self.assertEqual(
            [item["candidate_id"].split("--candidate-", 1)[1] for item in first["candidates"]],
            [item["candidate_id"].split("--candidate-", 1)[1] for item in second["candidates"]],
        )
        for candidate in first["candidates"]:
            self.assertEqual(
                candidate["render_handoff"]["schema_version"],
                "image-render-handoff/v1",
            )

    def test_reference_plan_and_handoff_have_no_runtime_controls(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan = self._compile(Path(temp), "native_multi_reference")

        payload = json.dumps(plan, ensure_ascii=False).casefold()
        for forbidden in (
            '"provider"',
            '"model"',
            '"api_key"',
            '"retry"',
            '"fallback"',
            '"balance"',
        ):
            self.assertNotIn(forbidden, payload)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class ProductionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = yaml.safe_load(
            (ROOT / "skill.contract.yaml").read_text(encoding="utf-8")
        )

    def test_contract_declares_orchestrator_state_and_evidence(self) -> None:
        self.assertEqual(self.contract["kind"], "orchestrator")
        self.assertTrue(self.contract["state"]["files"])
        evaluation = self.contract["evaluation"]
        self.assertEqual(evaluation["score_scope"], "structural_readiness")
        self.assertFalse(evaluation["claims"]["utility"])
        self.assertEqual(
            set(evaluation["case_portfolio"]),
            {"success", "failure", "high_risk"},
        )
        self.assertEqual(
            set(evaluation["type_checks"]),
            {"cross_stage_io", "partial_failure", "aggregation"},
        )

    def test_openai_provider_contract_is_fail_closed_and_redacted(self) -> None:
        providers = {
            provider["name"]: provider
            for provider in self.contract["providers"]
        }
        provider = providers["openai-direct"]
        self.assertEqual(provider["credential_sources"], ["env"])
        self.assertTrue(provider["secrets_outside_skill_dir"])
        self.assertEqual(provider["network_allowlist"], ["api.openai.com"])
        self.assertTrue(
            provider["side_effect_boundary"][
                "apply_requires_explicit_user_approval"
            ]
        )
        self.assertTrue(provider["redaction"]["enabled"])
        self.assertIn(
            "references/credential-lifecycle.md",
            provider["docs"]["revoke_rotate_delete"],
        )

    def test_evaluation_and_security_artifacts_are_registered(self) -> None:
        tests = self.contract["tests"]
        registered = set(tests["regression_cases"])
        self.assertIn("tests/evaluation/suite.yaml", registered)
        self.assertGreaterEqual(len(tests["security_cases"]), 4)
        for path in (
            "tests/evaluation/suite.yaml",
            "tests/evaluation/baseline-results.json",
            "tests/evaluation/candidate-results.json",
            "references/credential-lifecycle.md",
        ):
            self.assertTrue((ROOT / path).is_file(), path)

    def test_root_entry_is_a_versioned_thin_router_with_reference_index(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = yaml.safe_load(skill.split("---", 2)[1])
        self.assertEqual(frontmatter["license"], "MIT")
        self.assertEqual(frontmatter["metadata"]["version"], "0.3.0-rc.2")
        self.assertIn("[能力与资源](references/README.md)", skill)
        self.assertIn("USE FOR:", skill)
        self.assertIn("DO NOT USE FOR:", skill)
        for required_selection in ("业务类型", "交付模式", "画布", "风格"):
            self.assertIn(required_selection, skill)
        self.assertIn("不得只问是否展开", skill)
        index = (ROOT / "references" / "README.md").read_text(encoding="utf-8")
        for reference in (ROOT / "references").glob("*.md"):
            if reference.name != "README.md":
                self.assertIn(reference.name, index)


if __name__ == "__main__":
    unittest.main()

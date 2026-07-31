from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.release import verify_release  # noqa: E402


class ReleaseGateTests(unittest.TestCase):
    def test_public_candidate_passes_static_release_gate(self) -> None:
        report = verify_release(ROOT)
        self.assertEqual(report.errors, ())
        self.assertTrue(report.ok)
        self.assertEqual(report.formal_templates, 13)
        self.assertEqual(report.compatibility_templates, 1)
        self.assertEqual(report.render_styles, 6)


if __name__ == "__main__":
    unittest.main()

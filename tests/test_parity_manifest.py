from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.parity import ParityError, verify_manifest  # noqa: E402


SOURCE = Path(
    os.environ.get(
        "IMAGE_FACTORY_SOURCE",
        "/Users/aim5/Documents/CodingProject/image-factory",
    )
)
MANIFEST = ROOT / "parity" / "ip-parity-manifest.json"


class ParityManifestTests(unittest.TestCase):
    def test_current_original_skill_is_fully_and_uniquely_mapped(self) -> None:
        report = verify_manifest(MANIFEST, SOURCE)

        self.assertEqual(report.source_file_count, 64)
        self.assertEqual(report.mapped_source_file_count, 64)
        self.assertEqual(report.unmapped_source_files, ())
        self.assertEqual(report.duplicate_source_files, ())
        self.assertEqual(report.formal_template_count, 13)
        self.assertEqual(report.compatibility_template_count, 1)
        self.assertEqual(report.render_style_count, 6)

    def test_excludes_require_a_replacement_or_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source_file = source / "skills" / "ip-illustration-factory" / "private.png"
            source_file.parent.mkdir(parents=True)
            source_file.write_bytes(b"private")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "ip-pic-parity-manifest/v1",
                        "allowed_decisions": ["exclude"],
                        "entries": [
                            {
                                "source": "skills/ip-illustration-factory/private.png",
                                "target": None,
                                "decision": "exclude",
                                "capability": "private-reference-binary",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ParityError, "replacement or reason"):
                verify_manifest(manifest, source)

    def test_new_original_file_blocks_release_until_mapped(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            skill = source / "skills" / "ip-illustration-factory"
            skill.mkdir(parents=True)
            (skill / "known.md").write_text("known", encoding="utf-8")
            (skill / "new-capability.md").write_text("new", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "ip-pic-parity-manifest/v1",
                        "allowed_decisions": ["copy"],
                        "entries": [
                            {
                                "source": "skills/ip-illustration-factory/known.md",
                                "target": "known.md",
                                "decision": "copy",
                                "capability": "known",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = verify_manifest(manifest, source)

            self.assertEqual(
                report.unmapped_source_files,
                ("skills/ip-illustration-factory/new-capability.md",),
            )
            self.assertFalse(report.ok)


if __name__ == "__main__":
    unittest.main()

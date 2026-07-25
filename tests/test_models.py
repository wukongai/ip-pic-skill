from __future__ import annotations

import unittest

from _support import example_brief, example_profile
from custom_ip_illustration.errors import ValidationError
from custom_ip_illustration.models import validate_brief, validate_profile


class ProfileValidationTests(unittest.TestCase):
    def test_licensed_demo_profile_passes(self) -> None:
        profile = validate_profile(example_profile())
        self.assertEqual(profile["ownership"]["status"], "licensed")

    def test_missing_ownership_fails_closed(self) -> None:
        profile = example_profile()
        del profile["ownership"]
        with self.assertRaisesRegex(ValidationError, "ownership"):
            validate_profile(profile)

    def test_unknown_ownership_fails(self) -> None:
        profile = example_profile()
        profile["ownership"]["status"] = "unknown"
        with self.assertRaisesRegex(ValidationError, "must be one of"):
            validate_profile(profile)

    def test_reference_must_be_authorized(self) -> None:
        profile = example_profile()
        profile["references"] = [
            {
                "path": "refs/character.png",
                "purpose": "identity",
                "authorized": False,
            }
        ]
        with self.assertRaisesRegex(ValidationError, "authorized must be true"):
            validate_profile(profile)


class BriefValidationTests(unittest.TestCase):
    def test_three_canvases_are_supported(self) -> None:
        for canvas in ("16:9", "1:1", "9:16"):
            brief = example_brief()
            brief["canvas"] = canvas
            validate_brief(brief)

    def test_image_count_is_bounded(self) -> None:
        brief = example_brief()
        brief["image_count"] = 13
        with self.assertRaisesRegex(ValidationError, "between 1 and 12"):
            validate_brief(brief)


if __name__ == "__main__":
    unittest.main()

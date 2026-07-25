from __future__ import annotations

import unittest

from _support import ROOT
from custom_ip_illustration.backend import resolve_backend


def inventory(*backends: dict) -> dict:
    return {"backends": list(backends)}


class BackendSelectionTests(unittest.TestCase):
    def test_request_override_wins(self) -> None:
        result = resolve_backend(
            inventory(
                {"id": "native", "kind": "native", "available": True},
                {"id": "chosen", "kind": "third_party", "available": True},
            ),
            requested="chosen",
        )
        self.assertEqual(result["backend_id"], "chosen")
        self.assertEqual(result["reason"], "request_override")

    def test_saved_preference_wins_when_available(self) -> None:
        result = resolve_backend(
            inventory(
                {"id": "native", "kind": "native", "available": True},
                {"id": "preferred", "kind": "third_party", "available": True},
            ),
            preference="preferred",
        )
        self.assertEqual(result["backend_id"], "preferred")

    def test_invalid_preference_falls_back_to_native(self) -> None:
        result = resolve_backend(
            inventory({"id": "native", "kind": "native", "available": True}),
            preference="missing",
        )
        self.assertEqual(result["backend_id"], "native")
        self.assertEqual(result["reason"], "host_native")

    def test_single_third_party_is_automatic(self) -> None:
        result = resolve_backend(
            inventory({"id": "only-one", "kind": "third_party", "available": True})
        )
        self.assertEqual(result["status"], "selected")
        self.assertEqual(result["backend_id"], "only-one")

    def test_multiple_third_party_requires_one_choice(self) -> None:
        result = resolve_backend(
            inventory(
                {"id": "b", "kind": "third_party", "available": True},
                {"id": "a", "kind": "third_party", "available": True},
            )
        )
        self.assertEqual(result["status"], "needs_user_choice")
        self.assertEqual(result["choices"], ["a", "b"])

    def test_no_backend_is_compile_only(self) -> None:
        result = resolve_backend(inventory())
        self.assertEqual(result["status"], "compile_only")
        self.assertIsNone(result["backend_id"])


if __name__ == "__main__":
    unittest.main()

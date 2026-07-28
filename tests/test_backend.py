from __future__ import annotations

import unittest

try:
    from _support import ROOT
except ModuleNotFoundError:
    from tests._support import ROOT
from ip_pic.backend import resolve_backend


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

    def test_available_public_request_is_selected(self) -> None:
        result = resolve_backend(
            inventory(
                {
                    "id": "openai-direct",
                    "kind": "third_party",
                    "available": True,
                    "configured": True,
                }
            ),
            requested="openai-direct",
        )
        self.assertEqual(result["status"], "selected")
        self.assertEqual(result["backend_id"], "openai-direct")
        self.assertEqual(result["reason"], "request_override")

    def test_unavailable_or_unconfigured_public_request_needs_setup(self) -> None:
        for backend_id in ("codex-image-tool", "openai-direct", "ai-router"):
            for available, configured in ((False, False), (True, False)):
                with self.subTest(
                    backend_id=backend_id,
                    available=available,
                    configured=configured,
                ):
                    result = resolve_backend(
                        inventory(
                            {"id": "native", "kind": "native", "available": True},
                            {
                                "id": backend_id,
                                "kind": (
                                    "native"
                                    if backend_id == "codex-image-tool"
                                    else "third_party"
                                ),
                                "available": available,
                                "configured": configured,
                                "requires_setup": True,
                            },
                        ),
                        requested=backend_id,
                    )
                    self.assertEqual(result["status"], "needs_setup")
                    self.assertEqual(result["backend_id"], backend_id)
                    self.assertEqual(
                        result["reason"], "requested_backend_unavailable"
                    )
                    self.assertEqual(result["choices"], [backend_id])
                    self.assertEqual(
                        [item["id"] for item in result["choice_details"]],
                        [backend_id],
                    )

    def test_unknown_request_returns_unavailable_choice_screen(self) -> None:
        result = resolve_backend(
            inventory({"id": "native", "kind": "native", "available": True}),
            requested="unknown-renderer",
        )
        self.assertEqual(result["status"], "needs_user_choice")
        self.assertIsNone(result["backend_id"])
        self.assertEqual(result["reason"], "requested_backend_unavailable")
        self.assertEqual(
            result["choices"],
            ["codex-image-tool", "openai-direct", "ai-router", "prompt-only"],
        )

    def test_saved_preference_wins_when_available(self) -> None:
        result = resolve_backend(
            inventory(
                {"id": "native", "kind": "native", "available": True},
                {"id": "preferred", "kind": "third_party", "available": True},
            ),
            preference="preferred",
        )
        self.assertEqual(result["backend_id"], "preferred")

    def test_unconfigured_public_saved_preference_is_not_selected(self) -> None:
        for backend_id in ("codex-image-tool", "openai-direct", "ai-router"):
            with self.subTest(backend_id=backend_id):
                result = resolve_backend(
                    inventory(
                        {"id": "native", "kind": "native", "available": True},
                        {
                            "id": backend_id,
                            "kind": (
                                "native"
                                if backend_id == "codex-image-tool"
                                else "third_party"
                            ),
                            "available": True,
                            "configured": False,
                            "requires_setup": True,
                        },
                    ),
                    preference=backend_id,
                )
                self.assertEqual(result["status"], "needs_user_choice")
                self.assertIsNone(result["backend_id"])
                self.assertEqual(
                    result["reason"], "saved_preference_unavailable"
                )
                self.assertEqual(
                    result["choices"],
                    [
                        "codex-image-tool",
                        "openai-direct",
                        "ai-router",
                        "prompt-only",
                    ],
                )

    def test_explicit_prompt_only_never_selects_a_rendering_backend(self) -> None:
        result = resolve_backend(
            inventory({"id": "native", "kind": "native", "available": True}),
            requested="prompt-only",
        )
        self.assertEqual(result["status"], "compile_only")
        self.assertEqual(result["backend_id"], "prompt-only")
        self.assertEqual(result["reason"], "request_override")

    def test_saved_prompt_only_preference_never_selects_a_rendering_backend(self) -> None:
        result = resolve_backend(
            inventory({"id": "native", "kind": "native", "available": True}),
            preference="prompt-only",
        )
        self.assertEqual(result["status"], "compile_only")
        self.assertEqual(result["backend_id"], "prompt-only")
        self.assertEqual(result["reason"], "saved_preference")

    def test_unavailable_saved_preference_returns_public_choices(self) -> None:
        result = resolve_backend(
            inventory(
                {
                    "id": "codex-image-tool",
                    "kind": "native",
                    "available": True,
                }
            ),
            preference="missing",
        )
        self.assertEqual(result["status"], "needs_user_choice")
        self.assertIsNone(result["backend_id"])
        self.assertEqual(result["reason"], "saved_preference_unavailable")
        self.assertEqual(
            result["choices"],
            ["codex-image-tool", "openai-direct", "ai-router", "prompt-only"],
        )

    def test_first_run_auto_returns_public_choices_with_details(self) -> None:
        result = resolve_backend(
            inventory(
                {
                    "id": "codex-image-tool",
                    "kind": "native",
                    "available": True,
                    "configured": True,
                    "label": "Hosted image generation",
                },
                {
                    "id": "openai-direct",
                    "kind": "third_party",
                    "available": False,
                    "configured": False,
                    "requires_setup": True,
                },
            )
        )
        self.assertEqual(result["status"], "needs_user_choice")
        self.assertIsNone(result["backend_id"])
        self.assertEqual(result["reason"], "first_run_choice")
        self.assertEqual(
            result["choices"],
            ["codex-image-tool", "openai-direct", "ai-router", "prompt-only"],
        )
        self.assertEqual(
            result["choice_details"],
            [
                {
                    "id": "codex-image-tool",
                    "label": "Hosted image generation",
                    "description": "Use Codex's built-in image generation tool.",
                    "available": True,
                    "configured": True,
                    "requires_setup": False,
                },
                {
                    "id": "openai-direct",
                    "label": "OpenAI Direct API",
                    "description": "Generate with your configured OpenAI API access.",
                    "available": False,
                    "configured": False,
                    "requires_setup": True,
                },
                {
                    "id": "ai-router",
                    "label": "Existing ai-router",
                    "description": "Use an ai-router installation already connected to this host.",
                    "available": False,
                    "configured": False,
                    "requires_setup": True,
                },
                {
                    "id": "prompt-only",
                    "label": "Prompt only",
                    "description": "Save the prompt and render request without generating an image.",
                    "available": True,
                    "configured": True,
                    "requires_setup": False,
                },
            ],
        )

    def test_ready_configured_choice_never_claims_setup_is_required(self) -> None:
        result = resolve_backend(
            inventory(
                {
                    "id": "openai-direct",
                    "kind": "third_party",
                    "available": True,
                    "configured": True,
                    "requires_setup": True,
                }
            )
        )
        detail = next(
            item
            for item in result["choice_details"]
            if item["id"] == "openai-direct"
        )
        self.assertFalse(detail["requires_setup"])
        self.assertEqual(result["status"], "needs_user_choice")
        self.assertIsNone(result["backend_id"])
        self.assertEqual(result["reason"], "first_run_choice")
        self.assertEqual(
            result["choices"],
            ["codex-image-tool", "openai-direct", "ai-router", "prompt-only"],
        )


if __name__ == "__main__":
    unittest.main()

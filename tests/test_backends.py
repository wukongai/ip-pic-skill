from __future__ import annotations

import base64
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.backends import (  # noqa: E402
    finalize_host_render,
    prepare_backend,
    render_openai_direct,
)
from ip_pic.compiler import compile_request  # noqa: E402
from ip_pic.errors import IPPicError  # noqa: E402

from tests.test_selection_and_compiler import article_brief  # noqa: E402


def _png_base64() -> str:
    data = io.BytesIO()
    Image.new("RGB", (16, 16), "#F7F2E9").save(data, format="PNG")
    return base64.b64encode(data.getvalue()).decode("ascii")


class _FakeImages:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            data=[SimpleNamespace(b64_json=_png_base64())],
            _request_id="req_test_123",
        )


class _FakeClient:
    def __init__(self) -> None:
        self.images = _FakeImages()


class BackendContractTests(unittest.TestCase):
    def _compiled(self, output: Path) -> dict:
        return compile_request(
            ROOT,
            article_brief(),
            output,
            write=True,
        )["manifest"]

    def test_all_backend_preparation_preserves_upstream_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._compiled(root / "compiled")
            baseline = copy.deepcopy(manifest)
            fingerprints = set()
            for backend in (
                "prompt-only",
                "codex-image-tool",
                "host-ai-router",
                "openai-direct",
            ):
                with self.subTest(backend=backend):
                    request = prepare_backend(
                        manifest,
                        backend,
                        root / f"{backend}.json",
                    )
                    self.assertEqual(manifest, baseline)
                    self.assertEqual(
                        request["upstream"]["director_plan"],
                        baseline["director_plan"],
                    )
                    self.assertEqual(
                        request["upstream"]["visual_qa"],
                        baseline["visual_qa"],
                    )
                    fingerprints.add(request["upstream_fingerprint"])
            self.assertEqual(len(fingerprints), 1)

    def test_prompt_only_does_not_claim_render_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._compiled(root / "compiled")
            request = prepare_backend(
                manifest,
                "prompt-only",
                root / "prompt-only.json",
            )
            self.assertEqual(request["status"], "prompt_ready")
            self.assertFalse(request["rendered"])
            self.assertNotIn("credential", json.dumps(request).lower())

    def test_host_backends_require_real_file_before_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._compiled(root / "compiled")
            request_path = root / "codex-request.json"
            request = prepare_backend(
                manifest,
                "codex-image-tool",
                request_path,
            )
            self.assertEqual(request["status"], "awaiting_host")
            self.assertFalse(request["rendered"])
            with self.assertRaisesRegex(IPPicError, "不存在|does not exist"):
                finalize_host_render(
                    request_path,
                    Path(request["expected_output"]),
                    receipt_id="host-001",
                )

            output = Path(request["expected_output"])
            output.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (16, 16), "white").save(output)
            receipt_path = finalize_host_render(
                request_path,
                output,
                receipt_id="host-001",
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"], "ok")
            self.assertTrue(receipt["rendered"])
            self.assertEqual(receipt["backend"], "codex-image-tool")
            self.assertEqual(len(receipt["output_sha256"]), 64)

    def test_openai_direct_uses_official_image_api_and_writes_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._compiled(root / "compiled")
            fake = _FakeClient()
            receipt_path = render_openai_direct(
                manifest,
                root / "openai-request.json",
                client=fake,
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

            self.assertEqual(fake.images.calls[0]["model"], "gpt-image-2")
            self.assertEqual(fake.images.calls[0]["size"], manifest["size"])
            self.assertIn(
                "一次生成图文融合",
                fake.images.calls[0]["prompt"],
            )
            self.assertEqual(receipt["status"], "ok")
            self.assertTrue(Path(receipt["output_image"]).is_file())
            self.assertEqual(receipt["request_id"], "req_test_123")


if __name__ == "__main__":
    unittest.main()

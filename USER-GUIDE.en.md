# IP Pic Beginner User Guide

This guide is for a first-time user. Follow the steps in order. Start with the no-cost `prompt-only` route before calling a real image backend.

## 1. Enter the complete Skill directory

Open a terminal, type `cd `, drag the complete `ip-pic` folder into the terminal, and press Enter. Verify:

```bash
pwd
test -f SKILL.md && test -f scripts/compile_ip_pic.py && echo "IP Pic root is correct"
```

The full directory is required. Copying only `SKILL.md` is not enough.

## 2. Install in an isolated environment

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

Python 3.10 or newer is required. Re-run `source .venv/bin/activate` after opening a new terminal.

## 3. Verify before rendering

```bash
python3 -B -m unittest discover -s tests -v
python3 scripts/verify_release.py
```

The unit-test run must end in `OK`, and the release check must report no errors.

## 4. Compile the first article illustration

```bash
python3 scripts/compile_ip_pic.py \
  --brief examples/article-brief.json \
  --output-dir outputs/manual-direct-01 \
  --print-prompt
```

Success creates `image_brief.json`, `ip-director-plan.json`, a prompt file, and `run-manifest.json`. Compilation never calls an image API.

Do not reuse an existing output directory. Give every retry a new task `id` and output directory.

## 5. Run the no-cost prompt-only handoff

```bash
python3 scripts/render_ip_pic.py prepare \
  --manifest outputs/manual-direct-01/run-manifest.json \
  --backend prompt-only \
  --request outputs/manual-direct-01/prompt-only.json
```

Success means `status=prompt_ready` and `rendered=false`. This verifies the handoff but is not a rendered or visually accepted image.

## 6. Choose one real backend

### Codex Image Tool

```bash
python3 scripts/render_ip_pic.py prepare \
  --manifest outputs/manual-direct-01/run-manifest.json \
  --backend codex-image-tool \
  --request outputs/manual-direct-01/codex-request.json
```

Ask the host Agent to read that request without rewriting its prompt, size, or reference selection; generate the image at `expected_output`; and complete the finalize flow.

```bash
python3 scripts/render_ip_pic.py finalize \
  --request outputs/manual-direct-01/codex-request.json \
  --output outputs/manual-direct-01/image/ato-intelligence-value.png \
  --receipt-id your-host-run-id
```

The prepared host request must say `status=awaiting_host` and `rendered=false`. The final receipt must say `status=ok`, `rendered=true`, and include `output_sha256`.

### OpenAI Direct

```bash
python3 -m pip install -e '.[openai]'
export OPENAI_API_KEY='your-key-from-a-secure-shell'
python3 scripts/render_ip_pic.py openai-direct \
  --manifest outputs/manual-direct-01/run-manifest.json \
  --request outputs/manual-direct-01/openai-request.json \
  --model gpt-image-2 \
  --quality high
```

Never store credentials in the Skill, a brief, Markdown, JSON, or committed `.env*`. Reference-image requests fail closed in the current direct adapter; use a host backend for those jobs. For this example, `output_image` must be `outputs/manual-direct-01/image/ato-intelligence-value.png`, and the receipt must include `status=ok`, `rendered=true`, and `output_sha256`.

### Host ai-router

Prepare with `--backend host-ai-router` and request path `outputs/manual-direct-01/ai-router-request.json`. Ask the installed host Agent to read that request and preserve its `prompt`, `size`, `assets`, and `expected_output`. The public Skill contains no private provider registry, adapter, balance, retry, fallback, or credential implementation.

After the host creates the real file:

```bash
python3 scripts/render_ip_pic.py finalize \
  --request outputs/manual-direct-01/ai-router-request.json \
  --output outputs/manual-direct-01/image/ato-intelligence-value.png \
  --receipt-id your-ai-router-run-id
```

Verify `ai-router-request.receipt.json` contains `status=ok`, `rendered=true`, and `output_sha256`.

## 7. Choose the article text mode

`direct-integrated` generates the character, objects, action, and a small amount of Chinese text in one image. A text-free illustration fails. The target is heavy upright black Chinese display lettering, one irregular hand-drawn emphasis line, and two supporting blue levels. A local font file cannot control this model-generated lettering.

`two-step-publish` first renders a text-free raw image and then adds a deterministic title layer:

```bash
python3 scripts/compile_ip_pic.py \
  --brief examples/article-two-step-brief.json \
  --output-dir outputs/manual-two-step-01 \
  --print-prompt
```

Prepare the complete Codex-hosted two-step run:

```bash
python3 scripts/render_ip_pic.py prepare \
  --manifest outputs/manual-two-step-01/run-manifest.json \
  --backend codex-image-tool \
  --request outputs/manual-two-step-01/codex-request.json
```

Ask the host to generate a text-free raw image at `outputs/manual-two-step-01/image/ato-two-step-judgement.png`, then finalize it:

```bash
python3 scripts/render_ip_pic.py finalize \
  --request outputs/manual-two-step-01/codex-request.json \
  --output outputs/manual-two-step-01/image/ato-two-step-judgement.png \
  --receipt-id your-two-step-host-run-id
```

After the receipt says `status=ok`, `rendered=true`, and includes `output_sha256`, choose one composition command. The default original typography is:

```bash
python3 scripts/compose_publish_layout.py \
  --run-manifest outputs/manual-two-step-01/run-manifest.json
```

The command preserves raw and creates `publish-layout.json`, a separate final PNG, and `.layout-result.json`.

To use a legally licensed Chinese font without overwriting any existing final:

```bash
python3 scripts/compose_publish_layout.py \
  --run-manifest outputs/manual-two-step-01/run-manifest.json \
  --layout-manifest outputs/manual-two-step-01/publish-layout-custom-font-01.json \
  --output-image outputs/manual-two-step-01/publish/custom-font-01/ato-two-step-judgement.png \
  --font-path "/full/path/to/YourChineseFont.ttf"
```

The explicit font uses face index 0. Visually inspect glyph coverage, wrapping, clipping, and tone.

The original default article title-band uses a macOS font path. On Windows or Linux, always supply `--font-path` on the first two-step composition, even if another Chinese system font is installed. Do not try to overwrite an already-created final.

## 8. Use your own character

The public package contains text-only profiles for original tutorial characters and no character reference images.

Copy [examples/article-brief.json](examples/article-brief.json) to a new work file. Replace `visual.ip_profile` with a non-sensitive public description and a rights declaration. Accepted ownership statuses are:

- `user-owned`
- `licensed`
- `project-original-tutorial`

Provide a non-empty rights basis, identity, appearance description, personality, at least three continuity anchors, and `authorized: true` for every profile reference. Register each real asset under `visual.authorized_assets` with `path`, `purpose`, `ownership`, and `required`.

Validate your edited JSON with `python3 -m json.tool path/to/brief.json`. The compiler validates the explicit profile. Every `authorized_assets` entry must also use an existing absolute path and an allowed ownership value; missing fields or files fail before handoff creation. Profile-reference paths are removed from public prompt text. A reference enters the actual render handoff only when it is also registered under `visual.authorized_assets`; those entries appear in `render_handoff.assets` and, after prepare, in the request's top-level `assets`.

A prepared reference is a local image that you selected, rights-checked, and registered before compilation. Inspect the manifest's `render_handoff.assets`, then the backend request's `assets`; they must match. Tell the host to attach every asset with `required=true` instead of copying only the text prompt. A receipt hash proves file identity, not character likeness, so a human must still compare the face, hair, palette, and continuity anchors.

## 9. Choose one of six article styles

Set `selection_receipt.style_variant_id` to:

- `minimal-lineart`
- `playful-craft`
- `sticker-collage`
- `expressive-handdrawn`
- `pop-impact`
- `art-print`

The style layer may change material, line, color, shape, and surface tone. It must not change identity, business scene, canvas, delivery mode, or director structure.

## 10. Compile a static video keyframe

```bash
python3 scripts/compile_ip_pic.py \
  --brief examples/video-square-brief.json \
  --template ip-editorial-video-square-v1 \
  --output-dir outputs/manual-video-square-01 \
  --print-prompt
```

Render the text-free raw image, then:

```bash
python3 scripts/compose_video_keyframe_text.py \
  --manifest outputs/manual-video-square-01/video-text-overlay.json
```

The prompt must begin with a text-free raw instruction and end with `无字视频关键帧 raw`; it must not say `请直接生成成品图片`. For the bundled example, raw is `outputs/manual-video-square-01/image/ato-video-square-01.png` and final is `outputs/manual-video-square-01/final/ato-video-square-01.png`. The overlay also creates `final/video-text-overlay-result.json` and refuses to overwrite an existing final.

Article and video style selection are not the same interface. Articles use `selection_receipt.style_variant_id`; video keyframes use existing video templates. The current video compiler does not consume the article selection receipt to switch style.

Square style templates are listed in [references/customization.md](references/customization.md). Portrait structures include `custom-ip-handdrawn-video-portrait-v1`, `ip-editorial-video-v3`, and `ip-editorial-video-subtitle-safe-v4`.

For video font overrides, add top-level `font_path` and optional `headline_font_path` to `video-text-overlay.json`, then validate it with `python3 -m json.tool outputs/manual-video-square-01/video-text-overlay.json`. A 9:16 headline uses `font_path`; a 1:1 headline may use `headline_font_path`. Windows requires an explicit Chinese font path. Linux only auto-falls back when one of the Noto CJK paths listed by the script exists; explicit paths are more reproducible. Verify the result on the target operating system. If a final already exists, copy the overlay and change its top-level `output_dir` to a new directory. Keep `items[0].output_file` as the filename; do not add `output` or `result_receipt`, because the composer creates the receipt automatically inside the new output directory.

## 11. Perform per-image QA

Read `visual_qa.required_checks` from `run-manifest.json`. Pass only checks that you actually observed:

```bash
python3 scripts/qa_ip_pic.py \
  --manifest outputs/manual-direct-01/run-manifest.json \
  --image outputs/manual-direct-01/image/ato-intelligence-value.png \
  --pass-check ip_identity \
  --pass-check semantic_action \
  --pass-check integrated_text_present \
  --pass-check integrated_text_legible \
  --pass-check text_does_not_overlap_subject
```

`checks_passed` still produces `visual_acceptance=pending_human` and `approved_for_release=false`. Automated structure is not human visual approval. Use `--fail-check` to record failures; the receipt identifies `render` or `publish-layout` as the retry scope.

See [references/qa-checklist.md](references/qa-checklist.md).

## 12. Retry and rebuild

- If only rendering failed and no expected image exists, prepare a new backend request against the same manifest.
- If content, selection, or director data is wrong, change the brief `id` and compile into a new directory.
- If an existing rendered image fails QA, keep it for audit, copy the brief to a new retry id, compile into a new directory, and never use the rejected image as a reference.
- If only a two-step title layer fails, preserve raw and write a new final:

```bash
python3 scripts/compose_publish_layout.py \
  --run-manifest outputs/manual-two-step-01/run-manifest.json \
  --layout-manifest outputs/manual-two-step-01/publish-layout-retry-01.json \
  --output-image outputs/manual-two-step-01/publish/retry-01/ato-two-step-judgement.png \
  --font-path "/full/path/to/YourChineseFont.ttf"
```

- Never use rejected output as a later reference.
- The Agent-level batch API provides `build_shot_plan`, `run_batch`, `retry_failed`, and `rebuild_batch`. It preserves successful items and rebuilds into a clean directory.

See [references/full-rebuild-playbook.md](references/full-rebuild-playbook.md).

## 13. Customize or add styles

Safe task-level customization—choosing a built-in style, supplying an authorized character, changing content/canvas/composition, or specifying a two-step font—does not modify the official Skill.

Editing a render-style profile, adding a seventh style, adding a title band, or changing video typography requires a personal fork. That fork is no longer the official fixed-six exact-parity distribution. Keep the MIT attribution, back up first, run all tests, and perform fresh visual regression.

Follow [references/customization.md](references/customization.md).

## Final release checklist

- Every character and asset has documented rights.
- No personal information, credentials, private paths, or private business data entered the Skill.
- Direct mode has real integrated Chinese text and one emphasis line.
- Two-step raw and final are separate, with legible typography.
- Video safe zones are clear.
- Every image has its own QA receipt.
- Automated tests pass.
- A human opened and accepted every final image.

Use [references/README.md](references/README.md) for the complete capability index.

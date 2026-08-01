# ip-pic

`ip-pic` is a standalone Codex Skill for Chinese article illustrations and static video keyframes featuring an original or properly licensed recurring character.

It preserves the complete IP director, 13 formal structures plus one compatibility structure, six render styles, direct-integrated and deterministic two-step text delivery, reference selection, batch continuity, failed-item retry, full rebuild, and per-image QA.

It intentionally excludes non-IP cards, covers, posters, note systems, course projects, publishing platforms, and all private routing, credentials, balance checks, retries, or provider fallbacks.

## Install

Python 3.10+ is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

Run the editable install from the complete Skill clone. When invoking the console entry from another directory, set `IP_PIC_HOME` to that complete directory; templates and profiles remain Skill assets rather than an isolated Python-only package.

For OpenAI Direct:

```bash
python3 -m pip install -e '.[openai]'
export OPENAI_API_KEY='set-this-outside-the-repository'
```

Never place credentials in a brief, manifest, Markdown file, command-line option, or committed `.env*`.

When installing as a Codex Skill, copy or link the complete repository directory as `ip-pic`. Templates, profiles, references, and scripts are runtime dependencies.

## Compile

The bundled example uses Ato, an original public tutorial character:

```bash
python3 scripts/compile_ip_pic.py \
  --brief examples/article-brief.json \
  --output-dir outputs/ato-article \
  --print-prompt
```

Compilation creates the normalized brief, director plan, prompt, run manifest, reference plan, and provider-neutral `image-render-handoff/v1`. It does not call an image API.

## Render backends

All four backends consume the same immutable upstream handoff.

### Codex Image Tool

```bash
python3 scripts/render_ip_pic.py prepare \
  --manifest outputs/ato-article/run-manifest.json \
  --backend codex-image-tool \
  --request outputs/ato-article/codex-request.json
```

The host calls its image tool and writes the real file to `expected_output`. Then finalize:

```bash
python3 scripts/render_ip_pic.py finalize \
  --request outputs/ato-article/codex-request.json \
  --output outputs/ato-article/image/ato-intelligence-value.png \
  --receipt-id host-run-id
```

The adapter cannot claim success until the expected regular file exists.

### OpenAI Direct

```bash
python3 scripts/render_ip_pic.py openai-direct \
  --manifest outputs/ato-article/run-manifest.json \
  --request outputs/ato-article/openai-request.json \
  --model gpt-image-2 \
  --quality high
```

This uses the official Image API `images.generate` flow. Reference-image handoffs fail closed in the current direct adapter; use a host backend so character references are not silently dropped. See the official [OpenAI image generation guide](https://developers.openai.com/api/docs/guides/image-generation).

### Host ai-router

Prepare with `--backend host-ai-router`, let the installed host invoke its own router, then use `finalize`. This repository contains no private provider registry, adapter, credential, balance, retry, or fallback implementation.

### Prompt only

Prepare with `--backend prompt-only`. The result remains `prompt_ready` and `rendered=false`; no network request is made.

## Delivery behavior

- `direct-integrated`: the generated final image must contain a small amount of legible Chinese text integrated with the character action and physical metaphor. A text-free illustration fails QA.
- `two-step-publish`: generate a text-free raw image, then create a separate deterministic final image. Raw is never publishable as final.
- video keyframes: generate text-free raw art, then run `scripts/compose_video_keyframe_text.py` for deterministic Chinese typography and protected safe zones.

The default direct-integrated typography follows the original host workflow: heavy, upright Chinese display type in black, one irregular hand-drawn emphasis line below the claim, and two distinct blue levels for navigation and supporting copy. It remains a single model render rather than switching to `two-step-publish` or adding a second text-overlay pass. Minor glyph variation is expected, but regular-script, calligraphic, childish, thin-serif, thin-weight, and outline lettering are failure signals.

## Batch and QA

`ip_pic.batch` provides shot planning, partial-failure preservation, failed-only retry, and clean full rebuild. Square sequences rotate six composition families and enforce recent-window diversity.

`ip_pic.qa.evaluate_image` records explicit observations. Passing structural checks still yields `pending_human`; it never impersonates human visual acceptance.

## Verify

```bash
python3 -m unittest discover -s tests -v
python3 scripts/verify_release.py
```

Private-source dual-end parity is optional for maintainers and is never distributed. Automated contracts, real-file E2E, and human visual acceptance are reported separately.

## License and attribution

Project code is MIT licensed. The workflow lineage derives from Ian Xiaohei Illustrations under MIT; the exact upstream license, attribution, and locked commit are retained in `UPSTREAM-LICENSE.txt`, `NOTICE.md`, and `upstream.lock.json`. No upstream character or example image is distributed.

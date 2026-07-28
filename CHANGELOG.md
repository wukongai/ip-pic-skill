# Changelog

## 0.1.0-rc.5

- Simplified normal use to one natural-language intent: users ask for illustrations while the host Agent analyzes the article, selects visual points, builds the brief and prompts, renders, and performs per-image QA.
- Reframed backend setup as three real rendering routes configured once, with `prompt-only` kept as a separate compile-only fallback.
- Added Study Guide Ato, including a synthetic source portrait, multi-view character master, and corrected portable profile.
- Rewrote the Simplified Chinese and English installation guides around a short-text smoke test, automatic long-article illustration, and then user-owned character replacement.

## 0.1.0-rc.4

- Renamed the public Skill, repository, Python package, configuration paths, schemas, evaluation IDs, and documentation to `ip-pic`.
- Added read-only migration discovery for the former preference and user-key locations; all new writes use `.ip-pic/`.

## 0.1.0-rc.3

- Added explicit rendering choices, direct GPT Image 2 support, and original Wukong and Moon Rabbit tutorial characters.
- Added deterministic public-release verification with an exact file allowlist and pinned PNG hashes.
- Linked the direct API guidance to the official [GPT Image documentation](https://developers.openai.com/api/docs/guides/image-generation).
- Hardened direct rendering with project-root file-descriptor anchoring, no-clobber output writes, bounded authorized references, prompt-data trust boundaries, and complete PNG stream validation.

## 0.1.0-rc.2

- Added complete Simplified Chinese and English installation and first-run tutorials.
- Introduced a temporary original adult demo character and SVG preview, later superseded before the rc.3 release.
- Added progressive first-run onboarding with explicit tutorial and own-character paths.
- Added project profile discovery and confirmation gates before saving or replacing a profile.
- Added documentation contract tests and UTF-8 privacy scanning for SVG assets.
- Stopped treating the archived rc.1 evaluation report as active portable utility evidence.
- Clarified installed-script resolution, Python requirements, project-local installation, profile privacy, and the single output-directory source of truth.

## 0.1.0-rc.1

- Added ownership-first IP onboarding.
- Added independent 16:9, 1:1 and 9:16 composition templates.
- Added provider-neutral prompt and render-request compilation.
- Added deterministic backend selection, preference resolution and release verification.
- Added success, failure, high-risk and negative-trigger regression cases.

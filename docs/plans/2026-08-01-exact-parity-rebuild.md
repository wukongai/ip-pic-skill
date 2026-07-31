# IP Pic Exact Parity Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the standalone public `ip-pic` Skill from the complete Image Factory IP behavior graph while allowing only the four approved publication differences.

**Architecture:** Extract the original director, structural templates, style profiles, delivery contracts, reference selection, deterministic typography, batch continuity and QA into an identity-neutral package. Keep rendering behind an immutable provider-neutral handoff and adapt only that boundary to Codex Image Tool, OpenAI Direct, host ai-router and prompt-only.

**Tech Stack:** Python 3.10+, standard-library `unittest`, Pillow for deterministic compositing, JSON/YAML/Markdown Skill assets.

## Global Constraints

- The current Image Factory working tree is read-only and remains unchanged.
- The rejected `0.2.0-rc.1` candidate is evidence and optional public backend-shell material, not an architecture source.
- Every original IP file or shared dependency has an explicit parity decision.
- No private identity, path, business data, credential or private ai-router implementation enters the candidate.
- Ian Xiaohei MIT attribution remains; Xiaohei character assets and examples do not.
- Do not push, tag, publish a GitHub Release or modify Global Skill.
- Structural tests, real-file E2E and human visual acceptance are reported separately.

---

### Task 1: Parity inventory and release gate

**Files:**
- Modify: `parity/ip-parity-manifest.json`
- Create: `src/ip_pic/parity.py`
- Create: `scripts/verify_parity.py`
- Create: `tests/test_parity_manifest.py`

**Interfaces:**
- Produces: `verify_manifest(manifest_path: Path, source_root: Path) -> ParityReport`
- Produces: `normalize_artifact(value: Any, replacements: dict[str, str]) -> Any`

- [ ] **Step 1: Write failing tests**

Create tests that require every file under `skills/ip-illustration-factory` to occur exactly once in the manifest, require all decisions to be allowlisted, require 13 formal templates plus one compatibility template, and fail on a synthetic unmapped source file.

- [ ] **Step 2: Verify RED**

Run: `python3 -m unittest tests.test_parity_manifest -v`

Expected: FAIL because `ip_pic.parity` and `scripts/verify_parity.py` do not exist.

- [ ] **Step 3: Implement the minimum verifier**

Parse JSON, compare normalized relative paths, reject duplicates, missing targets, unknown decisions and untracked source files. `exclude` entries must include a non-empty `replacement` or `reason`.

- [ ] **Step 4: Verify GREEN**

Run: `python3 -m unittest tests.test_parity_manifest -v`

Expected: all Task 1 tests pass.

### Task 2: Public package, licenses and identity-neutral profiles

**Files:**
- Create: `pyproject.toml`
- Create: `src/ip_pic/__init__.py`
- Create: `src/ip_pic/errors.py`
- Create: `profiles/characters/ato/profile.json`
- Create: `profiles/characters/wukong/profile.json`
- Create: `profiles/characters/moon-rabbit/profile.json`
- Create: `profiles/editorial-baseline-v1.json`
- Create: `UPSTREAM-LICENSE.txt`
- Create: `NOTICE.md`
- Create: `upstream.lock.json`
- Create: `tests/test_identity_and_license.py`

**Interfaces:**
- Produces: `load_character_profile(path: Path) -> dict[str, Any]`
- Produces: tutorial profiles with ownership `project-original-tutorial`

- [ ] **Step 1: Write failing tests**

Require all three tutorial profiles to validate ownership and continuity anchors; scan candidate text and JSON for private identity tokens and absolute private paths; require exact Ian MIT copyright and locked upstream commit; reject Xiaohei binary assets.

- [ ] **Step 2: Verify RED**

Run: `python3 -m unittest tests.test_identity_and_license -v`

Expected: FAIL because profiles and package metadata do not exist.

- [ ] **Step 3: Implement profiles and attribution**

Define Ato as an original adult learning guide with neutral public appearance anchors. Wukong and Moon Rabbit remain optional fictional tutorial profiles. Copy the upstream MIT text verbatim and write a notice that preserves attribution without distributing the character or examples.

- [ ] **Step 4: Verify GREEN**

Run: `python3 -m unittest tests.test_identity_and_license -v`

Expected: all Task 2 tests pass.

### Task 3: Exact director and character performance

**Files:**
- Create: `src/ip_pic/character_performance.py`
- Create: `src/ip_pic/director.py`
- Create: `references/character-performance.md`
- Create: `references/composition-patterns.md`
- Create: `references/ip-role-and-action.md`
- Create: `tests/test_director.py`
- Create: `tests/golden/director-neutral.json`

**Interfaces:**
- Produces: `plan(brief: dict[str, Any], template: dict[str, Any] | None = None) -> dict[str, Any]`
- Produces: `merge_missing(brief: dict[str, Any], template: dict[str, Any] | None = None) -> dict[str, Any]`
- Produces: `normalize_character_performance(value: Any) -> dict[str, Any] | None`

- [ ] **Step 1: Write failing parity tests**

Use the same neutral content for source and candidate. Normalize identity labels and assert exact equality for schema, owner, composition, visual, explicit overrides and provenance. Cover rotation across at least 12 shots and invalid enum failure.

- [ ] **Step 2: Verify RED**

Run: `IMAGE_FACTORY_SOURCE=<image-factory-source> python3 -m unittest tests.test_director -v`

Expected: FAIL because the public director is absent.

- [ ] **Step 3: Extract and sanitize the original runtime**

Port the original deterministic selection logic and character-performance presets. Replace `_default_identity()` with the caller-selected public profile loader; do not change action, structure, orientation, gaze or provenance behavior.

- [ ] **Step 4: Verify GREEN**

Run the Task 3 command again.

Expected: source/candidate normalized director contracts match.

### Task 4: Thirteen structures, compatibility template and six styles

**Files:**
- Create: `src/ip_pic/templates.py`
- Create: `src/ip_pic/styles.py`
- Create: `templates/*.json`
- Create: `profiles/render-styles/*.json`
- Create: `profiles/render-styles.json`
- Create: `references/style-variants.md`
- Create: `references/layout-recipes.md`
- Create: `tests/test_templates_and_styles.py`

**Interfaces:**
- Produces: `list_templates(root: Path, formal_only: bool = False) -> list[dict[str, Any]]`
- Produces: `resolve_template(root: Path, value: str) -> dict[str, Any]`
- Produces: `resolve_style(root: Path, value: str) -> dict[str, Any]`

- [ ] **Step 1: Write failing matrix tests**

Assert 13 formal structures, one compatibility structure and exactly 6 original selectable styles. For each formal template × style, assert style changes only surface fields and template mapping matches the parity manifest.

- [ ] **Step 2: Verify RED**

Run: `python3 -m unittest tests.test_templates_and_styles -v`

Expected: FAIL because templates and profiles are absent.

- [ ] **Step 3: Port each source JSON through explicit sanitization**

Preserve keys, layout, canvas, constraints, negative prompt, text and QA semantics. Rename only private id prefixes and paths. Replace private character descriptions with placeholders consumed from the selected character profile.

- [ ] **Step 4: Verify GREEN**

Run the Task 4 command again.

Expected: 13 formal + 1 compatibility and all 6 style matrix checks pass.

### Task 5: Selection, delivery and exact prompt compiler

**Files:**
- Create: `src/ip_pic/delivery_modes.py`
- Create: `src/ip_pic/selection.py`
- Create: `src/ip_pic/canvas.py`
- Create: `src/ip_pic/layout_profiles.py`
- Create: `src/ip_pic/compiler.py`
- Create: `scripts/compile_ip_pic.py`
- Create: `references/user-choice-flow.md`
- Create: `references/delivery-modes.md`
- Create: `references/prompt-template.md`
- Create: `tests/test_selection_user_journey.py`
- Create: `tests/test_compiler_golden.py`

**Interfaces:**
- Produces: `require_confirmed_selection(scene: str, brief: dict[str, Any]) -> dict[str, Any] | None`
- Produces: `compile_request(..., write: bool = True) -> dict[str, Any]`

- [ ] **Step 1: Write failing contract and golden tests**

Cover missing receipt, invented receipt, conflicts, recommendation acceptance, custom canvas and style/template separation. Compare normalized source/candidate prompt sections, direct-integrated text requirements, handoff, manifest and QA.

- [ ] **Step 2: Verify RED**

Run: `IMAGE_FACTORY_SOURCE=<image-factory-source> python3 -m unittest tests.test_selection_user_journey tests.test_compiler_golden -v`

Expected: FAIL because compiler modules do not exist.

- [ ] **Step 3: Implement exact IP-only compilation**

Extract the original normalizer, prompt compiler and manifest builder, removing only non-IP branches. direct-integrated must use mandatory text wording and direct final alias; two-step must create publish layout and raw-not-publishable contract.

- [ ] **Step 4: Verify GREEN**

Run the Task 5 command again.

Expected: normalized source/candidate compile artifacts match for the neutral fixture.

### Task 6: References and immutable render handoff

**Files:**
- Create: `src/ip_pic/reference_board.py`
- Create: `src/ip_pic/references.py`
- Create: `src/ip_pic/handoff.py`
- Create: `tests/test_references.py`
- Create: `tests/test_handoff.py`

**Interfaces:**
- Produces: `compile_reference_plan(...) -> dict[str, Any]`
- Produces: `build_render_handoff(...) -> dict[str, Any]`

- [ ] **Step 1: Write failing tests**

Cover primary, multi-reference, reference board, candidate handoffs, ownership, minimal selection, prompt path privacy and absence of runtime fields.

- [ ] **Step 2: Verify RED**

Run: `python3 -m unittest tests.test_references tests.test_handoff -v`

Expected: FAIL because reference modules do not exist.

- [ ] **Step 3: Extract original reference behavior**

Port the original algorithms and add only path-neutral serialization plus the backend adapter id outside the handoff payload.

- [ ] **Step 4: Verify GREEN**

Run the Task 6 command again.

Expected: all reference and handoff tests pass.

### Task 7: Deterministic article and video text layers

**Files:**
- Create: `src/ip_pic/publish.py`
- Create: `scripts/compose_publish_layout.py`
- Create: `scripts/compose_video_keyframe_text.py`
- Create: `references/typography-system.md`
- Create: `tests/test_publish.py`
- Create: `tests/test_video_text_overlay.py`

**Interfaces:**
- Produces: `compose_publish_layout(...) -> Path`
- Produces: `render_video_text_item(...) -> dict[str, Any]`

- [ ] **Step 1: Write failing pixel and contract tests**

Require raw preservation, output non-overwrite, kicker/headline/red underline/blue support, evidence limit, square-left/right, subtitle corridor and platform safe zones.

- [ ] **Step 2: Verify RED**

Run: `python3 -m unittest tests.test_publish tests.test_video_text_overlay -v`

Expected: FAIL because compositors do not exist.

- [ ] **Step 3: Extract compositors**

Port the original Pillow logic and sanitize brand names, fonts and channel-specific wording without changing geometry or hierarchy.

- [ ] **Step 4: Verify GREEN**

Run the Task 7 command again.

Expected: pixel and contract tests pass.

### Task 8: Batch continuity, full rebuild, partial failure and retry

**Files:**
- Create: `src/ip_pic/batch.py`
- Create: `scripts/run_ip_pic_batch.py`
- Create: `references/full-rebuild-playbook.md`
- Create: `references/batch-continuity.md`
- Create: `tests/test_batch.py`

**Interfaces:**
- Produces: `plan_batch(...) -> dict[str, Any]`
- Produces: `run_batch(...) -> dict[str, Any]`
- Produces: `retry_failed(receipt_path: Path, ...) -> dict[str, Any]`

- [ ] **Step 1: Write failing batch tests**

Cover one-shot short content, 4–8 shot long content, continuity rotation, three-image QA cadence, partial failure preservation, failed-only retry and full rebuild non-reuse.

- [ ] **Step 2: Verify RED**

Run: `python3 -m unittest tests.test_batch -v`

Expected: FAIL because the IP-only batch runtime does not exist.

- [ ] **Step 3: Implement the minimal IP-only batch runtime**

Reuse the single-item compiler; store explicit item states; never delete or overwrite prior runs.

- [ ] **Step 4: Verify GREEN**

Run the Task 8 command again.

Expected: all batch tests pass.

### Task 9: Four backend paths without behavior drift

**Files:**
- Create: `src/ip_pic/backends/base.py`
- Create: `src/ip_pic/backends/prompt_only.py`
- Create: `src/ip_pic/backends/codex_image_tool.py`
- Create: `src/ip_pic/backends/openai_direct.py`
- Create: `src/ip_pic/backends/host_ai_router.py`
- Create: `src/ip_pic/backends/registry.py`
- Create: `scripts/render_openai_direct.py`
- Create: `references/backend-selection.md`
- Create: `tests/test_backends.py`

**Interfaces:**
- Produces: `prepare_backend_request(adapter_id: str, handoff: dict[str, Any]) -> dict[str, Any]`
- Produces: `record_backend_result(request: dict[str, Any], output_files: list[Path]) -> dict[str, Any]`

- [ ] **Step 1: Write failing adapter invariance tests**

Assert all adapters receive byte-equivalent prompt and structurally equivalent handoff; prompt-only performs no network call; host-mediated adapters cannot claim completion without file receipts; OpenAI reads only documented environment variables.

- [ ] **Step 2: Verify RED**

Run: `python3 -m unittest tests.test_backends -v`

Expected: FAIL because backend modules do not exist.

- [ ] **Step 3: Implement adapters**

Keep Codex and ai-router host-mediated. Implement OpenAI HTTP calls with explicit dry-run, timeout and collision-safe output. Do not include private runtime routing.

- [ ] **Step 4: Verify GREEN**

Run the Task 9 command again.

Expected: all adapter contract tests pass.

### Task 10: QA, security, public docs and release verification

**Files:**
- Create: `src/ip_pic/qa.py`
- Create: `src/ip_pic/release.py`
- Create: `scripts/verify_release.py`
- Create: `SKILL.md`
- Create: `skill.contract.yaml`
- Create: `README.md`
- Create: `README.en.md`
- Create: `SECURITY.md`
- Create: `CONTRIBUTING.md`
- Create: `agents/openai.yaml`
- Create: `tests/test_qa.py`
- Create: `tests/test_release.py`
- Create: `tests/test_documentation.py`

**Interfaces:**
- Produces: `review_item(...) -> dict[str, Any]`
- Produces: `verify_release(root: Path) -> ReleaseReport`

- [ ] **Step 1: Write failing release tests**

Require thin Skill routing, complete bilingual docs, allowed-file manifest, no private identity/path/business/runtime leakage, no credential files, no overwrite and explicit human visual acceptance state.

- [ ] **Step 2: Verify RED**

Run: `python3 -m unittest tests.test_qa tests.test_release tests.test_documentation -v`

Expected: FAIL because public entry points and gates do not exist.

- [ ] **Step 3: Implement entry points and gates**

Keep `SKILL.md` as a router; place detailed behavior in references and scripts. Release verification defaults to deny and scans both paths and contents.

- [ ] **Step 4: Verify GREEN**

Run the Task 10 command again.

Expected: all QA, release and documentation tests pass.

### Task 11: Full verification, project E2E copy and Codex Image Tool evidence

**Files:**
- Create: `tests/e2e/direct-integrated-codex.json`
- Update: `<ip-pic-e2e-project>/.agents/skills/ip-pic`
- Update: `<ip-pic-e2e-project>/skills-lock.json`

**Interfaces:**
- Consumes: complete candidate and all previous verification reports.
- Produces: project-level test copy and a human-acceptance checklist.

- [ ] **Step 1: Run the full deterministic suite**

Run: `python3 -m unittest discover -s tests -v`

Expected: zero failures and zero errors.

- [ ] **Step 2: Run parity and release gates**

Run: `IMAGE_FACTORY_SOURCE=<image-factory-source> python3 scripts/verify_parity.py --manifest parity/ip-parity-manifest.json --source-root <image-factory-source>`

Run: `python3 scripts/verify_release.py`

Expected: zero unmapped files, zero privacy findings and zero release blockers.

- [ ] **Step 3: Run real backend checks**

Run prompt-only locally, OpenAI Direct only when credentials are ready, and execute Codex Image Tool plus host ai-router through their host tools. Each successful path must return a real image file receipt.

- [ ] **Step 4: Verify direct-integrated visual text**

Inspect the Codex output and record whether a short readable Chinese title or label is physically integrated with the character action and concept. A pure illustration is a failed E2E.

- [ ] **Step 5: Update the project-level E2E copy**

Copy the verified candidate Skill into the test project only after release verification passes. Do not modify Global Skill.

- [ ] **Step 6: Record remaining human acceptance**

List character continuity, template visual distinctness, six-style distinction, typography quality and batch rhythm as explicit unchecked human items.

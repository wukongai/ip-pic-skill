# IP Pic Project Customization Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, project-local runtime that lets an Agent preview, confirm, version, activate and compile reusable user characters, render styles and director presets.

**Architecture:** Natural-language interpretation remains in the host Agent. Focused validation modules normalize typed drafts; a transactional project store writes immutable versions and a revisioned registry only after explicit confirmation; a resolver injects selected project assets before the existing compiler pipeline. Installed Skill data and official styles remain immutable.

**Tech Stack:** Python 3 standard library, `unittest`, JSON contracts, SHA-256, atomic `os.replace`.

## Global Constraints

- All private customization is stored only in `<user-project>/.ip-pic/`.
- The installed Skill, original Image Factory and Global Skill remain unmodified.
- Existing no-project briefs, six official styles, 13 templates and delivery contracts remain compatible.
- Every write uses plan → preview → explicit confirmed apply; plans never mutate active state.
- Versions are immutable and use `vNNNN`; rollback changes only the active pointer.
- `.ip-pic`, plan, version and reference files may not be symlinks.
- Project references must resolve to ordinary files inside the project.
- Personal styles are render-style-only and may not contain identity, scene, canvas, delivery, backend or credential fields.
- Public prompt and run manifest may not contain the project absolute path.
- Version becomes `0.3.0-rc.3`.

---

## File Structure

- `src/ip_pic/project_assets.py`: strict validation and normalization for project character, style and director drafts.
- `src/ip_pic/project_store.py`: safe paths, revisioned registry, immutable versions, plans, apply, receipts, list/show/resolve.
- `src/ip_pic/project_resolver.py`: resolve project selections and merge them into an image brief.
- `src/ip_pic/project_cli.py`: Agent-facing command parsing and JSON output.
- `scripts/manage_ip_pic_project.py`: thin executable wrapper.
- `src/ip_pic/character_performance.py`: bounded custom expression description and body pose.
- `src/ip_pic/styles.py`: merge a validated project style over an official base style.
- `src/ip_pic/selection.py`: accept explicit project style selections without weakening official recommendation checks.
- `src/ip_pic/compiler.py`, `src/ip_pic/cli.py`: optional project-root resolution before normal compilation.
- `tests/test_project_assets.py`: asset validation contracts.
- `tests/test_project_store.py`: state, security, immutability and concurrency contracts.
- `tests/test_project_compile.py`: compiler integration and backward compatibility.
- `tests/test_user_customization_journey.py`: novice-style complete lifecycle.
- `examples/project-customization/`: public, identity-neutral structured drafts used by Agents.
- `SKILL.md`, `USER-GUIDE.zh-CN.md`, `USER-GUIDE.md`, `skill.contract.yaml`: public workflow and contract.
- `CHANGELOG.md`, version metadata and release manifest: `0.3.0-rc.3` release bookkeeping.

### Task 1: Validate the three project asset kinds

**Files:**
- Create: `tests/test_project_assets.py`
- Create: `src/ip_pic/project_assets.py`
- Modify: `src/ip_pic/character_performance.py`

**Interfaces:**
- Consumes: `profiles.load_character_profile(value)` and `styles.resolve_style(skill_root, style_id)`.
- Produces: `normalize_asset_draft(skill_root: Path, project_root: Path, kind: str, draft: dict) -> dict`.
- Produces: `character_performance.normalize(value)` accepting optional `expression_description` and `body_pose`.

- [ ] **Step 1: Write failing validation tests**

```python
def test_character_references_are_project_relative_and_authorized(self):
    result = normalize_asset_draft(SKILL_ROOT, self.project, "character", draft)
    self.assertEqual(result["profile"]["references"][0]["path"], "assets/xiao-he.png")

def test_style_rejects_identity_and_provider_keys_at_any_depth(self):
    with self.assertRaises(StyleError):
        normalize_asset_draft(SKILL_ROOT, self.project, "style", unsafe_draft)

def test_director_accepts_bounded_custom_performance(self):
    result = normalize_asset_draft(SKILL_ROOT, self.project, "director", draft)
    self.assertEqual(result["preset"]["character_performance"]["body_pose"], "身体前倾")
```

- [ ] **Step 2: Run tests and observe the missing module**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_assets -v`

Expected: FAIL with `ModuleNotFoundError: ip_pic.project_assets`.

- [ ] **Step 3: Implement strict normalization**

```python
KINDS = {"character", "style", "director"}
STYLE_OVERRIDE_FIELDS = {
    "line", "palette", "material", "shape_language",
    "surface_tone", "background_treatment", "typography_tone",
}

def normalize_asset_draft(skill_root, project_root, kind, draft):
    if kind == "character":
        return _normalize_character(project_root, draft)
    if kind == "style":
        return _normalize_style(skill_root, draft)
    if kind == "director":
        return _normalize_director(draft)
    raise ProjectAssetError(f"unknown project asset kind: {kind}")
```

Character normalization must call the existing profile validator, rewrite reference paths to normalized POSIX project-relative paths, and reject missing/outside/symlink files. Style normalization resolves the official base style and scans every nested key against the forbidden set. Director normalization accepts only `action` and `character_performance`, then calls the performance validator.

- [ ] **Step 4: Run asset tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_assets -v`

Expected: all tests PASS.

- [ ] **Step 5: Run existing performance and style tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_character_performance tests.test_templates_and_styles -v`

Expected: all existing tests PASS.

- [ ] **Step 6: Commit the validation slice**

```bash
git add tests/test_project_assets.py src/ip_pic/project_assets.py src/ip_pic/character_performance.py
git commit -m "feat: validate project customization assets"
```

### Task 2: Add plan, confirmed apply and immutable project storage

**Files:**
- Create: `tests/test_project_store.py`
- Create: `src/ip_pic/project_store.py`

**Interfaces:**
- Consumes: `normalize_asset_draft(...)`.
- Produces: `plan_create(skill_root, project_root, kind, draft, activate=False) -> dict`.
- Produces: `plan_activate(project_root, kind, asset_id, version) -> dict`.
- Produces: `apply_plan(skill_root, project_root, plan_path, confirmed=False) -> dict`.
- Produces: `list_assets(project_root, kind=None) -> dict`.
- Produces: `resolve_asset(project_root, kind, asset_id=None, version="active") -> dict`.

- [ ] **Step 1: Write failing store lifecycle tests**

```python
plan = plan_create(SKILL_ROOT, project, "character", draft, activate=True)
self.assertFalse((project / ".ip-pic" / "registry.json").exists())
with self.assertRaises(ConfirmationRequired):
    apply_plan(SKILL_ROOT, project, Path(plan["plan_path"]), confirmed=False)
receipt = apply_plan(SKILL_ROOT, project, Path(plan["plan_path"]), confirmed=True)
self.assertEqual(receipt["version"], "v0001")
```

Add cases for `v0002`, old-version activation, alias resolution, plan hash tampering, registry revision drift, target overwrite, lock contention, traversal, `.ip-pic` symlink and an invalid plan symlink.

- [ ] **Step 2: Run store tests and observe failure**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_store -v`

Expected: FAIL with `ModuleNotFoundError: ip_pic.project_store`.

- [ ] **Step 3: Implement safe registry and plan creation**

```python
REGISTRY_SCHEMA = "ip-pic-project-registry/v1"
PLAN_SCHEMA = "ip-pic-project-change-plan/v1"
VERSION_RE = re.compile(r"^v[0-9]{4}$")

def plan_create(skill_root, project_root, kind, draft, activate=False):
    project_root = _safe_project_root(project_root)
    normalized = normalize_asset_draft(skill_root, project_root, kind, draft)
    registry = _read_registry(project_root)
    version = _next_version(registry, kind, normalized["id"])
    plan = _build_plan("create", registry, kind, normalized["id"], version, normalized, activate)
    return _write_new_plan(project_root, plan)
```

Plans store `registry_revision`, canonical content hash and project-relative target. Plan creation may create `.ip-pic/plans/`, but must not create or change `registry.json`, version files or active pointers.

- [ ] **Step 4: Implement confirmed transactional apply**

```python
def apply_plan(skill_root, project_root, plan_path, confirmed=False):
    if not confirmed:
        raise ConfirmationRequired("explicit confirmation is required")
    with _project_lock(project_root):
        plan = _load_and_verify_plan(project_root, plan_path)
        registry = _read_registry(project_root)
        _require_revision(plan, registry)
        return _apply_create_or_activate(skill_root, project_root, plan, registry)
```

Write new versions and registry through same-directory temporary files and `os.replace`. Refuse all existing targets. Increment revision once. Write a redacted receipt containing kind, id, version, operation, content hash and resulting revision.

- [ ] **Step 5: Run store tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_store -v`

Expected: all tests PASS.

- [ ] **Step 6: Commit the store slice**

```bash
git add tests/test_project_store.py src/ip_pic/project_store.py
git commit -m "feat: add immutable project customization store"
```

### Task 3: Add the Agent-facing management command

**Files:**
- Create: `tests/test_project_cli.py`
- Create: `src/ip_pic/project_cli.py`
- Create: `scripts/manage_ip_pic_project.py`

**Interfaces:**
- Consumes: all public functions from `project_store.py`.
- Produces: commands `plan-create`, `plan-activate`, `apply`, `list`, `show`.
- Produces: JSON to stdout; errors as redacted JSON to stderr with nonzero exit.

- [ ] **Step 1: Write failing CLI tests**

```python
result = subprocess.run(
    [sys.executable, str(SCRIPT), "plan-create", "--project-root", str(project),
     "--kind", "style", "--draft", str(draft_path), "--activate"],
    text=True, capture_output=True,
)
self.assertEqual(result.returncode, 0)
preview = json.loads(result.stdout)
self.assertEqual(preview["status"], "preview")
```

Also verify `apply` fails without `--confirm`, list/show use machine-readable output, and errors do not expose draft contents or the absolute project path.

- [ ] **Step 2: Run CLI tests and observe failure**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_cli -v`

Expected: FAIL because `scripts/manage_ip_pic_project.py` does not exist.

- [ ] **Step 3: Implement parser and thin wrapper**

```python
def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = dispatch(args)
    except ProjectCustomizationError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
```

The script wrapper adds the repository root to `sys.path`, imports `ip_pic.project_cli.main`, and exits with its return code.

- [ ] **Step 4: Run CLI tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_cli -v`

Expected: all tests PASS.

- [ ] **Step 5: Commit the CLI slice**

```bash
git add tests/test_project_cli.py src/ip_pic/project_cli.py scripts/manage_ip_pic_project.py
git commit -m "feat: add project customization command"
```

### Task 4: Resolve project assets into compilation

**Files:**
- Create: `tests/test_project_compile.py`
- Create: `src/ip_pic/project_resolver.py`
- Modify: `src/ip_pic/styles.py`
- Modify: `src/ip_pic/selection.py`
- Modify: `src/ip_pic/director.py`
- Modify: `src/ip_pic/compiler.py`
- Modify: `src/ip_pic/cli.py`

**Interfaces:**
- Consumes: `resolve_asset(...)`.
- Produces: `apply_project_customization(skill_root, project_root, brief) -> (brief, context)`.
- Produces: `resolve_project_style(skill_root, project_style) -> dict`.
- Extends: `compile_request(root, brief, output_dir, ..., project_root=None)`.

- [ ] **Step 1: Write failing integration tests**

```python
result = compile_request(
    SKILL_ROOT, brief, output, write=False, project_root=project
)
self.assertIn("温暖蜡笔", result["prompt"])
self.assertEqual(result["manifest"]["project_customization"]["character"]["version"], "v0001")
self.assertNotIn(str(project), result["prompt"])
self.assertNotIn(str(project), json.dumps(result["manifest"], ensure_ascii=False))
```

Add cases for active defaults, explicit versions, unknown asset failure, explicit task action winning over director action, project style requiring `user-explicit`, reference handoff authorization, and exact equality of no-project compile output before/after the feature.

- [ ] **Step 2: Run integration tests and observe signature failure**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_compile -v`

Expected: FAIL because `compile_request()` has no `project_root`.

- [ ] **Step 3: Implement project resolution**

```python
def apply_project_customization(skill_root, project_root, brief):
    requested = brief.get("project_customization", {})
    character = _resolve_requested_or_active(project_root, "character", requested.get("character"))
    style = _resolve_requested_or_active(project_root, "style", requested.get("style"))
    director = _resolve_requested_or_active(project_root, "director", requested.get("director"))
    return _merge_assets_without_overwriting_task_fields(brief, character, style, director)
```

The returned context contains only kind, id, version and content hash. Character reference paths are absolute only in the internal authorized-assets value used by handoff; prompt sanitization removes paths and the public manifest stores redacted reference descriptors.

- [ ] **Step 4: Integrate style and director precedence**

```python
def resolve_project_style(root, project_style):
    base = resolve_style(root, project_style["base_style_id"])
    return _deep_merge_render_style(base, project_style["overrides"])
```

Apply director preset before calling existing `director.merge_missing`; preserve every explicitly supplied task value. Keep accepted recommendations restricted to official `RECOMMENDED`.

- [ ] **Step 5: Add `--project-root` to compile CLI**

```python
parser.add_argument("--project-root", type=Path)
result = compile_request(
    root, brief, args.output_dir, template_id=args.template,
    write=True, project_root=args.project_root,
)
```

- [ ] **Step 6: Run integration and existing compiler suites**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_compile tests.test_selection_and_compiler tests.test_director tests.test_templates_and_styles -v`

Expected: all tests PASS.

- [ ] **Step 7: Commit the compiler slice**

```bash
git add tests/test_project_compile.py src/ip_pic/project_resolver.py src/ip_pic/styles.py src/ip_pic/selection.py src/ip_pic/director.py src/ip_pic/compiler.py src/ip_pic/cli.py
git commit -m "feat: compile project character style and director presets"
```

### Task 5: Lock the complete novice lifecycle with an executable journey

**Files:**
- Create: `tests/test_user_customization_journey.py`
- Create: `examples/project-customization/character-draft.json`
- Create: `examples/project-customization/style-draft.json`
- Create: `examples/project-customization/director-draft.json`

**Interfaces:**
- Consumes: public management script and compile script only.
- Produces: an end-to-end automated contract for create, use, update and rollback.

- [ ] **Step 1: Write the failing clean-project journey**

```python
def test_agent_can_build_use_update_and_rollback_private_configuration(self):
    self.plan_and_confirm("character", character_v1, activate=True)
    self.plan_and_confirm("style", style_v1, activate=True)
    self.plan_and_confirm("director", director_v1, activate=True)
    first = self.compile_article("first")
    self.assertIn("身体前倾", first["prompt"])
    self.plan_and_confirm("character", character_v2, activate=True)
    self.activate("character", "xiao-he", "v0001")
    second = self.compile_article("rollback")
    self.assertEqual(second["manifest"]["project_customization"]["character"]["version"], "v0001")
```

The journey must also prove that a preview-only plan and an apply without confirmation leave registry revision and active pointers unchanged.

- [ ] **Step 2: Run journey and observe missing fixture behavior**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_user_customization_journey -v`

Expected: FAIL until public examples and all CLI flows exist.

- [ ] **Step 3: Add identity-neutral public drafts**

Use the fictional tutorial character “学习向导阿拓” only. Reference paths in the public example are placeholders interpreted relative to a user project and must not include a bundled private image. The style inherits `minimal-lineart`; the director uses `focused-operate`, a bounded expression description, gaze, action and body pose.

- [ ] **Step 4: Run the lifecycle test**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_user_customization_journey -v`

Expected: PASS with immutable `v0001` and `v0002`, active rollback to `v0001`, and no state mutation from unconfirmed operations.

- [ ] **Step 5: Commit the lifecycle slice**

```bash
git add tests/test_user_customization_journey.py examples/project-customization/character-draft.json examples/project-customization/style-draft.json examples/project-customization/director-draft.json
git commit -m "test: cover novice customization lifecycle"
```

### Task 6: Update Skill workflow, novice manuals and release contracts

**Files:**
- Modify: `SKILL.md`
- Modify: `USER-GUIDE.zh-CN.md`
- Modify: `USER-GUIDE.md`
- Modify: `skill.contract.yaml`
- Modify: `CHANGELOG.md`
- Modify: `pyproject.toml`
- Modify: `release/public-release-manifest.json`
- Modify: `tests/test_production_contract.py`
- Modify: `tests/evaluation/candidate-results.json`
- Modify: `evals/waza-eval.yaml`
- Modify: `tests/test_documented_user_flows.py`
- Modify: `tests/test_release_gate.py`

**Interfaces:**
- Consumes: the executable command and compiler behavior from Tasks 1–5.
- Produces: Agent-first instructions where every user example maps to a tested command path.

- [ ] **Step 1: Add failing documentation contract tests**

```python
def test_manual_explains_preview_confirmation_versions_and_rollback(self):
    text = GUIDE_ZH.read_text(encoding="utf-8")
    for phrase in ("确认保存", "新版本", "切回", ".ip-pic"):
        self.assertIn(phrase, text)

def test_skill_routes_natural_language_customization_to_manager(self):
    text = SKILL.read_text(encoding="utf-8")
    self.assertIn("scripts/manage_ip_pic_project.py", text)
    self.assertIn("不得修改 Skill 安装目录", text)
```

- [ ] **Step 2: Run documentation tests and observe failure**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_documented_user_flows tests.test_release_gate -v`

Expected: FAIL because the management runtime and confirmation workflow are not yet documented and allowlisted.

- [ ] **Step 3: Update `SKILL.md` and contracts**

Add a natural-language customization route:

```text
用户要求保存/修改角色、参考图、个人风格、表情、动作、视线或姿态
→ Agent 整理草稿
→ plan-create / plan-activate
→ 向用户展示预览
→ 只有用户明确确认后 apply --confirm
→ 编译时传入 --project-root
```

Add the management script to `skill.contract.yaml`, document project state and approval, and keep rendering/provider boundaries unchanged.

- [ ] **Step 4: Rewrite the novice-facing customization section**

Give copyable natural-language examples for:

- 保存第一个角色和参考图；
- 修改角色得到新版本；
- 新增个人风格；
- 保存表情/动作/视线/姿态；
- 给文章使用点名配置；
- 查看当前配置和切回旧版。

Do not require Python, JSON or terminal knowledge. Keep technical commands in a clearly marked maintainer section.

- [ ] **Step 5: Update release bookkeeping**

Change public version strings to `0.3.0-rc.3`, add a changelog entry, and map every new public file in the allowlist release manifest. Do not add private paths, assets or provider details.

- [ ] **Step 6: Run documentation and release tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_documented_user_flows tests.test_release_gate -v`

Expected: all tests PASS.

- [ ] **Step 7: Commit the documentation slice**

```bash
git add SKILL.md USER-GUIDE.zh-CN.md USER-GUIDE.md skill.contract.yaml CHANGELOG.md pyproject.toml release/public-release-manifest.json tests/test_documented_user_flows.py tests/test_release_gate.py tests/test_production_contract.py tests/evaluation/candidate-results.json evals/waza-eval.yaml
git commit -m "docs: expose natural language project customization"
```

### Task 7: Full regression, security audit and clean-room user simulation

**Files:**
- Create outside repository: a host-selected temporary directory named `ip-pic-project-customization-user-test-20260804`
- Create: `docs/reports/2026-08-04-project-customization-verification.md`

**Interfaces:**
- Consumes: complete candidate.
- Produces: reproducible automated and manual-simulation evidence without claiming visual E2E.

- [ ] **Step 1: Run the full automated suite**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`

Expected: all tests PASS; only documented environment-dependent skips are allowed.

- [ ] **Step 2: Run release and privacy gates**

Run: `python3 scripts/verify_release.py`

Expected: `release gate: ok`.

Run: `python3 scripts/verify_release.py` and review the release report's local-path and credential findings.

Expected: no private path, credential value or private identity leak; legitimate field-name matches are reviewed and documented.

- [ ] **Step 3: Run Skill Engineering validation from the external control directory**

Run the journey validate/evaluate commands with an external temporary control directory and the current isolated Skill worktree.

Expected: journey state is valid, structural evaluation passes, and no control receipts are created inside the public repository.

- [ ] **Step 4: Simulate a novice in a clean temporary project**

Create a fresh project with a generated non-private placeholder reference image outside the Skill. Follow only `USER-GUIDE.zh-CN.md`:

1. save a fictional authorized character;
2. save and activate a personal style;
3. save and activate an expression/action/gaze/posture director preset;
4. compile one direct-integrated article in prompt-only mode;
5. create version two;
6. activate version one;
7. compile again;
8. try an unconfirmed apply and verify no state change.

Record exact commands, exit codes, hashes, registry revisions and public path-leak checks in the report. This is a configuration/compiler user simulation, not a visual image E2E.

- [ ] **Step 5: Verify fresh-copy installation**

Copy only public release files into a new temporary `.agents/skills/ip-pic`, run the management lifecycle and compile example without importing the source checkout, then rerun `verify_release.py`.

Expected: the installed copy passes and no file resolves back to the development worktree.

- [ ] **Step 6: Write the verification report**

Document:

- test counts and skips;
- release gate result;
- Skill Engineering result;
- novice lifecycle receipts;
- compatibility proof;
- privacy scan;
- explicit remaining manual visual checks for character consistency, direct-integrated text beauty and personal-style rendering.

- [ ] **Step 7: Commit verification evidence**

```bash
git add docs/reports/2026-08-04-project-customization-verification.md
git commit -m "test: verify project customization release candidate"
```

- [ ] **Step 8: Stop before external publication**

Report the exact branch, commits, tests and remaining visual acceptance. Do not push, tag, create a GitHub Release, update Global Skill or publish until the user gives a separate explicit instruction.

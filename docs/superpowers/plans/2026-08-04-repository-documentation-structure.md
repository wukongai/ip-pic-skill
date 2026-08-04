# IP Pic Repository Documentation Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move long-form user and maintainer documentation out of the repository root into `docs/` while preserving every active workflow, link, release gate, and privacy boundary.

**Architecture:** Keep the repository root as a thin discovery and governance surface. Treat `docs/` as the public documentation layer, `references/` as Agent execution guidance, and tests as the deterministic path contract. The migration changes paths and links only; it does not change IP Pic runtime behavior or manual semantics.

**Tech Stack:** Markdown, Python 3 standard-library `unittest`, Git, existing `scripts/verify_release.py`.

## Global Constraints

- Work only in the isolated public candidate repository and branch.
- Do not modify Image Factory's private workflow.
- Do not change user-guide wording, templates, styles, prompts, render backends, QA behavior, or license content.
- Keep `README.*`, `SKILL.md`, licenses, community files, changelog, contracts, and package metadata at repository root.
- Move Chinese and English guide pairs together.
- Do not rewrite historical Specs, Plans, ADRs, or Changelog entries that record old paths as historical facts.
- Do not push without separate user confirmation.

---

### Task 1: Lock the documentation layout with a failing regression test

**Files:**
- Modify: `tests/test_documented_user_flows.py`

**Interfaces:**
- Consumes: repository root constant `ROOT`.
- Produces: deterministic contract for six guide paths under `docs/` and their absence from root.

- [ ] **Step 1: Add the new failing path contract**

Add this test to `DocumentedUserFlowTests`:

```python
def test_long_form_guides_live_under_docs_not_repository_root(self) -> None:
    guide_names = (
        "USER-GUIDE.zh-CN.md",
        "USER-GUIDE.en.md",
        "IMAGE-TOOL-SETUP.zh-CN.md",
        "IMAGE-TOOL-SETUP.en.md",
        "MAINTAINER-GUIDE.zh-CN.md",
        "MAINTAINER-GUIDE.en.md",
    )
    for name in guide_names:
        with self.subTest(name=name):
            self.assertTrue((ROOT / "docs" / name).is_file())
            self.assertFalse((ROOT / name).exists())
```

- [ ] **Step 2: Update existing test readers to describe the target paths**

Introduce constants near `ROOT`:

```python
DOCS = ROOT / "docs"
USER_GUIDE_ZH = DOCS / "USER-GUIDE.zh-CN.md"
USER_GUIDE_EN = DOCS / "USER-GUIDE.en.md"
IMAGE_TOOL_GUIDE_ZH = DOCS / "IMAGE-TOOL-SETUP.zh-CN.md"
IMAGE_TOOL_GUIDE_EN = DOCS / "IMAGE-TOOL-SETUP.en.md"
MAINTAINER_GUIDE_ZH = DOCS / "MAINTAINER-GUIDE.zh-CN.md"
MAINTAINER_GUIDE_EN = DOCS / "MAINTAINER-GUIDE.en.md"
```

Replace active test reads of the six root guide paths with these constants. Change the required-file tuple to `docs/<name>` entries. Do not change phrase assertions.

- [ ] **Step 3: Run the focused test and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_documented_user_flows.DocumentedUserFlowTests.test_long_form_guides_live_under_docs_not_repository_root
```

Expected: `FAIL` because `docs/USER-GUIDE.zh-CN.md` and the other target paths do not exist yet.

- [ ] **Step 4: Commit the red test**

```bash
git add tests/test_documented_user_flows.py
git commit -m "test: require long-form guides under docs"
```

### Task 2: Move all long-form guides and repair same-document links

**Files:**
- Move: `USER-GUIDE.zh-CN.md` → `docs/USER-GUIDE.zh-CN.md`
- Move: `USER-GUIDE.en.md` → `docs/USER-GUIDE.en.md`
- Move: `IMAGE-TOOL-SETUP.zh-CN.md` → `docs/IMAGE-TOOL-SETUP.zh-CN.md`
- Move: `IMAGE-TOOL-SETUP.en.md` → `docs/IMAGE-TOOL-SETUP.en.md`
- Move: `MAINTAINER-GUIDE.zh-CN.md` → `docs/MAINTAINER-GUIDE.zh-CN.md`
- Move: `MAINTAINER-GUIDE.en.md` → `docs/MAINTAINER-GUIDE.en.md`
- Modify: moved guide files only where their relative links changed

**Interfaces:**
- Consumes: the path contract from Task 1.
- Produces: complete bilingual documentation layer under `docs/`.

- [ ] **Step 1: Move the six files without rewriting their prose**

Use `git mv` for each source and target pair so Git records renames.

- [ ] **Step 2: Repair links inside moved files**

Apply these path rules:

```text
USER-GUIDE.zh-CN.md:
  IMAGE-TOOL-SETUP.zh-CN.md stays unchanged
  docs/VERIFICATION.zh-CN.md -> VERIFICATION.zh-CN.md

USER-GUIDE.en.md:
  IMAGE-TOOL-SETUP.en.md stays unchanged
  docs/VERIFICATION.en.md -> VERIFICATION.en.md

IMAGE-TOOL-SETUP.*:
  USER-GUIDE.* stays unchanged

MAINTAINER-GUIDE.*:
  USER-GUIDE.* stays unchanged
```

If a maintenance command names a root-level guide as an executable input, change it to `docs/<guide-name>`. Do not change historical narrative references.

- [ ] **Step 3: Run the new path contract and verify GREEN**

Run the same focused test from Task 1.

Expected: `OK`.

- [ ] **Step 4: Commit the document moves**

```bash
git add \
  USER-GUIDE.zh-CN.md USER-GUIDE.en.md \
  IMAGE-TOOL-SETUP.zh-CN.md IMAGE-TOOL-SETUP.en.md \
  MAINTAINER-GUIDE.zh-CN.md MAINTAINER-GUIDE.en.md \
  docs/USER-GUIDE.zh-CN.md docs/USER-GUIDE.en.md \
  docs/IMAGE-TOOL-SETUP.zh-CN.md docs/IMAGE-TOOL-SETUP.en.md \
  docs/MAINTAINER-GUIDE.zh-CN.md docs/MAINTAINER-GUIDE.en.md
git commit -m "docs: move long-form guides under docs"
```

### Task 3: Repair every active repository entry point

**Files:**
- Modify: `README.zh-CN.md`
- Modify: `README.en.md`
- Modify: `SKILL.md`
- Modify: `references/README.md`
- Modify: `references/delivery-modes.md`
- Modify: `tests/test_documented_user_flows.py`

**Interfaces:**
- Consumes: final guide paths from Task 2.
- Produces: valid discovery links for users, Agents, and maintainers.

- [ ] **Step 1: Update root entry links**

Use these exact active paths:

```text
README.zh-CN.md -> docs/USER-GUIDE.zh-CN.md
README.zh-CN.md -> docs/IMAGE-TOOL-SETUP.zh-CN.md
README.en.md -> docs/USER-GUIDE.en.md
README.en.md -> docs/IMAGE-TOOL-SETUP.en.md
SKILL.md -> docs/USER-GUIDE.zh-CN.md
SKILL.md -> docs/MAINTAINER-GUIDE.zh-CN.md
```

- [ ] **Step 2: Update reference-layer navigation**

Change:

```text
references/README.md:
  ../USER-GUIDE.zh-CN.md -> ../docs/USER-GUIDE.zh-CN.md
  ../MAINTAINER-GUIDE.zh-CN.md -> ../docs/MAINTAINER-GUIDE.zh-CN.md

references/delivery-modes.md:
  USER-GUIDE.zh-CN.md -> docs/USER-GUIDE.zh-CN.md
```

- [ ] **Step 3: Add a repository-wide active Markdown link check**

Extend `tests/test_documented_user_flows.py` with:

```python
def test_active_markdown_links_resolve_after_docs_migration(self) -> None:
    active_documents = (
        ROOT / "README.zh-CN.md",
        ROOT / "README.en.md",
        ROOT / "SKILL.md",
        ROOT / "references" / "README.md",
        DOCS / "USER-GUIDE.zh-CN.md",
        DOCS / "USER-GUIDE.en.md",
        DOCS / "IMAGE-TOOL-SETUP.zh-CN.md",
        DOCS / "IMAGE-TOOL-SETUP.en.md",
        DOCS / "MAINTAINER-GUIDE.zh-CN.md",
        DOCS / "MAINTAINER-GUIDE.en.md",
    )
    for document in active_documents:
        text = document.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            clean = target.split("#", 1)[0]
            resolved = (document.parent / clean).resolve()
            self.assertTrue(
                resolved.exists(),
                f"{document.relative_to(ROOT)} links to missing path: {target}",
            )
```

Replace the old user-guide-only link test with this broader check so relative links resolve from each document’s own directory.

- [ ] **Step 4: Run the documentation flow suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_documented_user_flows
```

Expected: all tests pass.

- [ ] **Step 5: Commit the entry-point repair**

```bash
git add \
  README.zh-CN.md README.en.md SKILL.md \
  references/README.md references/delivery-modes.md \
  tests/test_documented_user_flows.py
git commit -m "docs: route repository entries through docs"
```

### Task 4: Verify release integrity and absence of legacy root guides

**Files:**
- Modify only if a deterministic release check exposes an active stale path.

**Interfaces:**
- Consumes: migrated documentation tree and updated links.
- Produces: release evidence for structure, behavior, privacy, and licensing.

- [ ] **Step 1: Search active source for stale root-path references**

Run:

```bash
rg -n \
  '(^|\\.\\./)(USER-GUIDE|IMAGE-TOOL-SETUP|MAINTAINER-GUIDE)\\.(zh-CN|en)\\.md' \
  README.zh-CN.md README.en.md SKILL.md references docs/USER-GUIDE* \
  docs/IMAGE-TOOL-SETUP* docs/MAINTAINER-GUIDE* tests src
```

Expected: every active reference either includes `docs/` from root or is a valid same-directory link inside `docs/`. Historical files under `docs/specs/`, `docs/plans/` and `docs/superpowers/` are excluded from this migration check.

- [ ] **Step 2: Run the full automated suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected: all tests pass.

- [ ] **Step 3: Run the release gate**

Run:

```bash
python3 scripts/verify_release.py
```

Expected JSON:

```json
{
  "ok": true,
  "errors": [],
  "formal_templates": 13,
  "compatibility_templates": 1,
  "render_styles": 6
}
```

The `scanned_text_files` count may change because this plan adds design and plan documents; it is not a fixed acceptance value.

- [ ] **Step 4: Verify rename-only document content**

Run:

```bash
git diff --summary main...HEAD
git diff --stat main...HEAD
git status --short
```

Expected: six guide renames, link/test changes, no template, profile, runtime, prompt, backend, license-content, or private Image Factory changes.

- [ ] **Step 5: Record verification**

Create `docs/reports/2026-08-04-repository-documentation-structure-verification.md` containing:

```markdown
# Repository Documentation Structure Verification

- Six bilingual long-form guides moved from repository root to `docs/`.
- Root discovery, Agent, reference, and same-directory links resolve.
- Documented user-flow tests: PASS.
- Full automated suite: PASS.
- Public release verification: PASS.
- Runtime/template/style/backend behavior changed: no.
- Remote push performed: no.
```

- [ ] **Step 6: Commit verification evidence**

```bash
git add docs/reports/2026-08-04-repository-documentation-structure-verification.md
git commit -m "docs: record documentation structure verification"
```

## Completion Gate

Before reporting completion:

1. Confirm the six old root paths do not exist.
2. Confirm all six new `docs/` paths exist.
3. Confirm every active Markdown link resolves relative to its source file.
4. Confirm the full suite and release gate pass from fresh command output.
5. Confirm the branch has not been pushed.
6. Present the exact changed paths and ask the user whether to merge and push.

# IP Pic Release Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clear every privacy, Skill Engineering, Skill Up, and Waza blocker
before the user's final E2E.

**Architecture:** Keep private extraction outside the public repository. Make
the public candidate a sanitized runtime plus generic release verifier, thin
Skill router, explicit production contract, and two version-specific external
evaluation suites. Preserve all existing parity-controlled runtime behavior.

**Tech Stack:** Python 3.10+, unittest, YAML/JSON contracts, Skill Engineering
CLI, Alibaba Skill Up 0.7.0, Microsoft Waza 0.38.4.

## Global Constraints

- Work only in the isolated candidate selected for this task.
- Treat the private upstream behavior source as read-only.
- Do not push, tag, release, or modify Global Skill.
- Do not change director, template, prompt, delivery, handoff, or QA semantics.
- Every implementation change follows RED → GREEN → full regression.

---

### Task 1: Public privacy boundary

**Files:**
- Delete: `scripts/extract_public_slice.py`
- Modify: `src/ip_pic/release.py`
- Modify: `tests/test_identity_and_license.py`
- Modify: `tests/test_release_gate.py`
- Modify: public docs containing internal business identifiers

**Interfaces:**
- Consumes: sanitized public candidate tree
- Produces: `verify_release(root)` that rejects absolute local paths,
  obfuscated literal construction, private build helpers, images, env files,
  credential-shaped values, and internal business identifiers

- [x] Add failing tests that detect private extraction helpers, literal string
      concatenation, local absolute paths, and internal business identifiers.
- [x] Run targeted privacy/release tests and verify the new tests fail for the
      current candidate.
- [x] Delete the public extraction helper and replace identity-specific
      denylist code with generic structural scans.
- [x] Sanitize public documentation without changing capability boundaries.
- [x] Run targeted tests and verify they pass.

### Task 2: Production contract and provider safety

**Files:**
- Modify: `skill.contract.yaml`
- Modify: `src/ip_pic/backends.py`
- Modify: `tests/test_backends.py`
- Create: `references/credential-lifecycle.md`
- Create: `tests/evaluation/suite.yaml`
- Create: `tests/evaluation/baseline-results.json`
- Create: `tests/evaluation/candidate-results.json`

**Interfaces:**
- Consumes: OpenAI Direct, Codex host, host ai-router, and prompt-only handoffs
- Produces: explicit provider/security/evaluation contract and deterministic
  Skill Engineering evidence inputs

- [x] Add failing tests for missing OpenAI credentials, fixed official
      endpoint, redacted errors, and contract-required provider/evaluation
      fields.
- [x] Verify RED with targeted backend and contract tests.
- [x] Add minimal provider, state, security case, evaluation case, and evidence
      declarations; enforce the official OpenAI endpoint and safe missing-key
      failure.
- [x] Run Skill Engineering suite validation/evaluation and targeted tests.
- [x] Verify production Doctor has no credential/evaluation FAIL.

### Task 3: Thin Skill router and discoverable references

**Files:**
- Modify: `SKILL.md`
- Create: `references/README.md`
- Modify: `README.zh-CN.md`
- Modify: `README.en.md`

**Interfaces:**
- Consumes: existing reference modules and executable scripts
- Produces: Waza-compliant thin root router with linked progressive disclosure

- [x] Add a failing structure test requiring MIT/version metadata, a linked
      reference index, and no private business names in the root entry.
- [x] Verify RED.
- [x] Rewrite the root entry without changing trigger or stop semantics.
- [x] Link every reference through `references/README.md`.
- [x] Run structure tests and `waza check`; keep reducing only routing prose
      until the root is at or below 500 tokens.

### Task 4: Skill Up and Waza evaluation suites

**Files:**
- Create: `evals/eval.yaml`
- Create: `evals/cases/*.yaml`
- Create: `evals/fixtures/scripts/check-ip-pic.sh`
- Create: `eval.yaml`
- Create: `tasks/*.yaml`
- Create: `trigger_tests.yaml`

**Interfaces:**
- Consumes: current exact-parity Skill and public tutorial profile
- Produces: success, failure, high-risk, orchestrator, trigger, and holdout
  evaluation definitions for the two external tools

- [x] Add a failing release test requiring both suites and their required case
      categories.
- [x] Verify RED.
- [x] Add current-version cases for selection, direct-integrated,
      two-step-publish, unauthorized character, non-overwrite, partial failure,
      and privacy.
- [x] Validate with Skill Up and Waza.
- [x] Execute Skill Up with Codex and Waza's supported deterministic checks;
      store reports outside the release tree.

### Task 5: Version, full regression, and project test copy

**Files:**
- Modify: `pyproject.toml`
- Modify: `release/public-release-manifest.json`
- Create: `CHANGELOG.md`
- Modify: existing Product/Architecture/Spec/Plan release notes as needed

**Interfaces:**
- Consumes: verified 0.3.0-rc.2 candidate
- Produces: reproducible project-level E2E candidate

- [x] Align version and changelog.
- [x] Run all unit/contract tests, parity, release, diff check, package build,
      Skill Engineering production audit, Skill Up, and Waza.
- [x] Sync the verified candidate to the project-level test Skill with a
      recoverable backup.
- [x] Prove candidate/test-copy byte equivalence and run Skill self-test.
- [x] Hand off only the human visual checklist; do not claim visual acceptance.

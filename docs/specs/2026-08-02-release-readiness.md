# ip-pic 0.3.0-rc.2 Release Readiness Spec
## Goal

Make the exact-parity public candidate safe and structurally ready for a user
release without changing the private upstream workflow or any IP director,
template, prompt, delivery, backend handoff, or QA behavior.

## Required outcomes

1. The public tree contains no reconstructable private identity, appearance,
   clothing, accessory, local path, internal business, private build rule, or
   reference-image information.
2. Private-source extraction remains a private build concern. The public
   candidate ships only sanitized artifacts and generic verification.
3. `skill.contract.yaml` declares provider credentials, network allowlists,
   redaction, credential lifecycle, state, security cases, and production
   evaluation evidence.
4. Root `SKILL.md` remains a thin router and is at or below Waza's 500-token
   hard limit. Detailed behavior stays in linked references and executable
   contracts.
5. The candidate includes version-specific Skill Up and Waza evaluation
   suites. The rejected lightweight candidate is not an evidence source.
6. Existing exact-parity gates remain unchanged: 64/64 mapped private-source
   files, 13 formal structures, one compatibility structure, six render
   styles, direct-integrated text, two-step publish, video overlay, batch
   continuity, retry-only-failed, non-overwrite, receipts, and per-image QA.

## Release gates

- Full unit/contract suite passes.
- Parity verifier passes with no unmapped source capability.
- Public release verifier passes and rejects obfuscated private literals.
- Skill Engineering production audit has no FAIL.
- Skill Up validates and executes the current candidate suite.
- Waza reports `ready=true`; its spec and coverage checks pass.
- Project-level test copy is byte-equivalent to the isolated candidate.
- Real visual acceptance remains explicitly pending until the user completes
  E2E. Structural checks never impersonate visual approval.

## Non-goals

- No private upstream edits.
- No Global Skill installation.
- No push, tag, GitHub Release, or public distribution in this task.
- No provider, adapter, routing, balance, retry, or fallback details from the
  private host runtime.

# Repository Documentation Structure Verification

## Scope

- Six bilingual long-form guides moved from the repository root to `docs/`.
- Root README, Skill entry, reference index, delivery-mode reference, and guide-internal links updated.
- Runtime code, templates, styles, prompts, backends, QA behavior, licenses, and private Image Factory workflow unchanged.

## TDD evidence

- Baseline before the structure test: 134 tests passed, 4 skipped.
- New structure contract on the old layout: failed for all six guide paths.
- The same structure contract after migration: passed.
- Documented user-flow suite after link repair: 19 tests passed.

## Final verification

- Full automated suite: 135 tests passed, 4 skipped.
- Public release verification: passed.
- Formal templates: 13.
- Compatibility templates: 1.
- Render styles: 6.
- Scanned public text files: 180.
- Root-level legacy guide paths remaining: 0.
- Missing target guide paths under `docs/`: 0.
- Active Markdown links checked relative to their source documents: passed.
- Skill Engineering production audit: 100/A, evidence coverage 100%, no required or recommended structural findings.
- Remote push performed: no.

## Release boundary

This verification proves the repository structure, active documentation paths, automated behavior contracts, and public-release gates remain valid after the move. It does not replace human visual acceptance of generated images; the existing Beta and visual-QA statements remain unchanged.

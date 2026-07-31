# Contributing

Changes must preserve the separation between IP behavior and render backends.

1. Add or update a failing contract test first.
2. Keep director, templates, prompt, references and QA provider-neutral.
3. Update `parity/ip-parity-manifest.json` when the source behavior graph changes.
4. Run `python3 -m unittest discover -s tests -v`.
5. Run `python3 scripts/verify_release.py`.
6. Record real-file E2E separately from human visual acceptance.

Do not add private names, personal appearance details, local absolute paths, credentials, private backend routing, upstream character images, or unrelated publishing workflows.

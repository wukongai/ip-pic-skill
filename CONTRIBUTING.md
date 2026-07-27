# Contributing

## Principles

- Keep the root `SKILL.md` concise and route detailed knowledge to `references/`.
- Keep compilation provider-neutral and dependency-free.
- Do not add default people, brands, private reference images or customer data.
- Keep API credentials, provider routing, retry policy, and model selection out of the compiler and render request. The fixed GPT Image 2 direct adapter is isolated and may read only its documented user-level credential source.
- Add or update deterministic tests for every behavior change.

## Development

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/verify_release.py --root . --manifest public-release-manifest.json
```

Before proposing a new template, prove that it has an independent composition contract rather than being a crop of an existing canvas.

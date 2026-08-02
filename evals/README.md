# External behavior evaluations

This directory contains two Alibaba Skill Up 0.7-compatible entrypoints:

- `eval.yaml` runs both `with_skill` and `without_skill` configurations.
- `with-skill.yaml` is the release gate for the installed Skill itself.

Both use an isolated Codex home at `/tmp/ip-pic-skill-up-clean-home` so the
`without_skill` benchmark cannot discover another globally or project-installed
copy of `ip-pic`. Before running, authenticate Codex in that clean home using
your host's normal login flow. Credentials remain outside this repository.

```bash
skill-up validate evals/eval.yaml
skill-up run evals/with-skill.yaml
skill-up run evals/eval.yaml
```

The compile case is prompt-only: it creates deterministic manifests and prompts
but never calls an image API. Real image output still requires the separate
human E2E described in the user manual.

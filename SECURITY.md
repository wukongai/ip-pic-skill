# Security

## Supported version

Security fixes are prepared for the latest release candidate and the latest stable release.

## Report a problem

Open a private security report through the repository hosting platform. Do not include real credentials, private character assets, customer content, or unpublished reference images in a public issue.

## Credential boundary

Most backends keep image credentials in the host and do not expose them to this Skill. The optional direct OpenAI API backend requires a user-level key supplied through the current process environment or `~/.ip-pic/.env`. It must never be stored in the Skill, repository, preference files, examples, prompts, render requests, logs, or chat.

### Revoke, rotate or delete a direct API key

- Revoke a key from the OpenAI API Keys page when it should no longer work.
- To rotate it, revoke the old key, create a replacement, then run `configure` again or update the current process environment.
- To delete the local copy, remove only `~/.ip-pic/.env`; this does not revoke the key at OpenAI.
- Never publish either the old or replacement key in an issue or diagnostic log.

## Character rights

Only use characters and reference images you own, license or have permission to use. Missing ownership blocks compilation before any image backend is called.

## Release checks

Every release must pass the allowlist, credential-pattern, absolute-path, symlink, cross-directory reference and private-pattern gates in `scripts/verify_release.py`.

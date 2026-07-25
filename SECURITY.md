# Security

## Supported version

Security fixes are prepared for the latest release candidate and the latest stable release.

## Report a problem

Open a private security report through the repository hosting platform. Do not include real credentials, private character assets, customer content, or unpublished reference images in a public issue.

## Credential boundary

This Skill never needs an API key. Image credentials belong to the host image backend and must remain outside the Skill, preference files, examples, prompts and render requests.

## Character rights

Only use characters and reference images you own, license or have permission to use. Missing ownership blocks compilation before any image backend is called.

## Release checks

Every release must pass the allowlist, credential-pattern, absolute-path, symlink, cross-directory reference and private-pattern gates in `scripts/verify_release.py`.

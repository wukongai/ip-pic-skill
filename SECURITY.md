# Security

## Credentials

`ip-pic` never accepts API keys in briefs, templates, manifests or command-line flags. OpenAI Direct reads `OPENAI_API_KEY` through the official SDK. Host ai-router credentials remain owned by the host installation. Never commit `.env*`, cookies, tokens, private keys or host configuration.

## Character rights

Only use original, licensed or otherwise authorized character profiles and reference images. Every profile must state its rights basis. The bundled Ato, Wukong and Moon Rabbit profiles are tutorial characters; no private character image is distributed.

## Filesystem safety

All compile, render, publish and QA artifacts are new files. Existing directories, outputs, receipts and symbolic links fail closed. Full rebuilds must use a directory outside the previous batch tree.

## Reporting

Report suspected credential exposure, private identity leakage, unsafe overwrite behavior or third-party character redistribution privately to the repository maintainer. Do not include live credentials or private reference images in a public issue.

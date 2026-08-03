# IP Pic verification notes

This document separates a passing capability contract from a visually accepted image.

## Verified scope

Automated verification covers:

- 13 formal IP structures and one compatibility structure;
- six rendering styles;
- 16:9, 1:1, 3:4, and 9:16 canvases;
- direct-integrated text, text-free rendering followed by deterministic publishing, and static-video text overlays;
- article planning, paragraph-level cognitive anchors, and character expression, action, gaze, and pose contracts;
- authorized reference selection, selection receipts, batch continuity, partial failure, and retrying only failed items;
- Codex Image Tool, OpenAI Direct, host ai-router, and prompt-only boundaries;
- privacy, credentials, private paths, unauthorized images, no-overwrite behavior, and licensing gates.

Real-image sampling also verified that one six-paragraph article can produce six distinct direct-integrated illustrations that remain associated with their source paragraphs. Chinese headlines, supporting copy, heavy display lettering, and one hand-drawn emphasis line appeared in the real images. A mismatch in expression or gaze must still be treated as a retry even when the text is correct.

## What automation cannot guarantee

Image generation is stochastic. Different agents, image models, fonts, systems, and reference images can affect:

- character identity and clothing continuity;
- expression, action, gaze, and pose strength;
- small Chinese text accuracy;
- text contrast against a complex background;
- safe space and cropping on square or portrait canvases.

A structural pass is not a visual pass. The agent must show every final image to the user for identity, semantic association, typography, safe-area, and rights review.

## Safe first-use acceptance

1. Run the Ato short-passage example from the user guide.
2. Confirm that you received a real image, not only a prompt.
3. Confirm that the Chinese headline is readable and matches the scene.
4. Test two or three continuous illustrations with your own short article.
5. Only then switch to a character reference you own or are authorized to use.

At every stage, ask the agent to preserve accepted results and retry only failed items.

## Reporting a reproducible issue

Provide the smallest public input, the agent and image-tool type, the chosen style/canvas/text mode, the failed image, and the expected versus actual result.

Do not provide API keys, tokens, private routing configuration, unauthorized character images, or private identity information.

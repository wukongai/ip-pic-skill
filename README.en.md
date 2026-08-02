# ip-pic · Character-led Article Illustrations

[简体中文](README.zh-CN.md) | [English](README.en.md)

`ip-pic` is an Agent Skill for writers. It uses an original or licensed recurring character to create one illustration for a short passage, a continuous image set for a full Chinese article, or a static video keyframe.

Writers do not need to run commands, locate the Skill directory, or edit configuration. Give the public address and article to Codex, Claude Code, WorkBuddy, or another compatible Agent.

## Start in 30 seconds

Public installation address:

```text
https://github.com/wukongai/ip-pic-skill
```

Send this to your Agent:

```text
Install this Agent Skill in my current writing project:
https://github.com/wukongai/ip-pic-skill

Keep the installed name as ip-pic. Prefer a project-level installation and
do not change my global skills. Handle installation, dependency checks,
and self-tests yourself. Do not ask me to run commands or find the Skill root.
After installation, use ip-pic, verify it, and guide me through first use.
```

Then say:

```text
Use Learning Guide Ato to give this passage one illustration.
```

```text
Use my character to illustrate this article.
```

```text
Read my current Obsidian article and choose the moments worth illustrating.
```

Guides:

- [Writer User Guide](USER-GUIDE.en.md)
- [Maintainer Technical Guide](MAINTAINER-GUIDE.en.md)
- [Customization and Personal Forks](references/customization.md)

## Natural-language choices

Supported article styles are minimal line art, playful craft, sticker collage, expressive hand-drawn, pop impact, and art print.

```text
Switch this set to playful craft and 1:1. Create a new version without overwriting.
```

```text
Switch to a text-free image followed by the original heavy Chinese title layer
and one hand-drawn emphasis line.
```

```text
Keep accepted images and retry only failed items.
```

## Complete capability

- 13 formal IP illustration structures and one compatibility structure;
- 16:9, 1:1, 3:4, 9:16, and custom canvases;
- one-step integrated image and Chinese text;
- text-free raw images followed by deterministic Chinese title composition;
- original heavy Chinese display type, two blue text levels, and one emphasis line;
- direction for character scale, crop, action, expression, gaze, pose, and orientation;
- one image for short content and continuous multi-image article sets;
- square, landscape, and portrait static video keyframes;
- authorized reference selection, batch continuity, retries, and per-image checks;
- a host image tool, user-configured OpenAI image access, an already-installed image router, or prompt preparation only.

For one-pass integrated text, the original visual contract uses heavy, upright Chinese display type with one irregular hand-drawn emphasis line. The image model completes this in one pass; it does not silently switch to two-step publishing or add a second text overlay.

## Scope

IP Pic does not create knowledge cards, covers, posters, animations, lip sync, voiceover, video edits, or publishing-platform content. It does not manage Obsidian; a host Agent may read a Markdown article that the user provides and pass its content to IP Pic.

## Safety and license

- Character assets must be original or licensed.
- Credentials, tokens, cookies, private keys, and private router implementations do not enter the public Skill.
- User references remain in the user's project.
- Rejected images do not automatically become future references.
- Automated checks never replace the user's real visual review.

Project code is MIT licensed. Workflow methods derive from MIT-licensed Ian Xiaohei Illustrations; attribution is retained in `UPSTREAM-LICENSE.txt`, `NOTICE.md`, and `upstream.lock.json`. This project does not redistribute Ian's Xiaohei character or upstream example images.

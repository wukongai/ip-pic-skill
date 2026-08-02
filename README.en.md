# ip-pic · Character-led Article Illustrations

[简体中文](README.zh-CN.md) | [English](README.en.md)

`ip-pic` is an Agent Skill for writers. It uses an original or licensed recurring character to create one illustration for a short passage, a continuous image set for a full Chinese article, or a static video keyframe.

Give it to Codex, Claude Code, WorkBuddy, or another compatible Agent and start illustrating your article.

## Start in 30 seconds

Send this to your Agent:

```text
Install and use this illustration tool:
https://github.com/wukongai/ip-pic-skill
After installation, guide me through my first illustration.
```

Then say:

```text
Use IP Pic's Learning Guide Ato example to give the passage below one illustration:

Projects move faster when you get a small result to review early, not when you make the plan longer.
```

On the first run, the Agent may ask which project should hold the images. If you do not have one, it offers simple choices.

```text
After setting up my character, use it to illustrate this article.
```

```text
Read my current Obsidian article and choose the moments worth illustrating.
```

Guides:

- [Writer User Guide](USER-GUIDE.en.md)

GPT Image 2 is preferred by default. During normal use, the Agent selects an available image tool automatically. Open [Image Tool Setup](IMAGE-TOOL-SETUP.en.md) only when the Agent explicitly says no image tool is available.

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

## What it can do

- 16:9, 1:1, 3:4, 9:16, and custom canvases;
- one-step integrated image and Chinese text, or a text-free image followed by stable Chinese title composition;
- original heavy Chinese display type, two blue text levels, and one emphasis line;
- one image for short content and continuous multi-image article sets;
- square, landscape, and portrait static video keyframes;
- character continuity, retries, and per-image approval.

For one-pass integrated text, the original visual contract uses heavy, upright Chinese display type with one irregular hand-drawn emphasis line.

## Scope

IP Pic does not create knowledge cards, covers, posters, animations, lip sync, voiceover, video edits, or publishing-platform content. It does not manage Obsidian; a host Agent may read a Markdown article that the user provides and pass its content to IP Pic.

## Safety and license

- Character assets must be original or licensed.
- User references remain in the user's project.
- Rejected images do not automatically become future references.
- Automated checks never replace the user's real visual review.

Project code is MIT licensed. Workflow methods derive from MIT-licensed Ian Xiaohei Illustrations, with its license and attribution retained. This project does not redistribute Ian's Xiaohei character or upstream example images.

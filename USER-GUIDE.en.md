# IP Pic User Guide

This guide is for writers who use Codex, Claude Code, WorkBuddy, or another Agent that supports skills. You do not need to use a terminal, locate the Skill directory, edit JSON, or run Python yourself.

Give the Agent the prompts below. The Agent handles installation, article analysis, image planning, file management, rendering, and checks.

Developers and maintainers should use the [Maintainer Guide](MAINTAINER-GUIDE.en.md).

## What IP Pic does

IP Pic creates:

- one character-led illustration for a short passage;
- a continuous image set for a full Chinese article;
- static 16:9, 1:1, or 9:16 video keyframes.

It does not create knowledge cards, covers, posters, video edits, or publishing-platform content.

## 1. Give the installation address to your Agent

The public installation address is:

```text
https://github.com/wukongai/ip-pic-skill
```

Open your Agent in the project where you write. For an Obsidian article, open the vault or the folder containing that article. Then send:

```text
Install this Agent Skill in my current writing project:
https://github.com/wukongai/ip-pic-skill

Keep the installed name as ip-pic. Prefer a project-level installation;
do not change my global skills unless I explicitly approve it.
Handle downloading, path discovery, dependency checks, installation,
and self-tests yourself. Do not ask me to run Python, find the Skill root,
or edit configuration files.

If a permission is required, explain what it affects and wait for approval.
After installation, use ip-pic, verify it, and guide me through first use.
```

The Agent should report whether installation succeeded, whether real image generation is available, which image route it proposes, and the single next choice it needs from you.

If the public address is unavailable, the Agent must stop and report the real error. It must not install a similarly named unknown repository.

## 2. Let the Agent choose an available image tool

```text
Check which image-generation capability is available in this Agent.
Prefer the host's built-in image tool. If that is unavailable, check only
image capabilities I have already configured.

Recommend the best option that is already available and tell me whether it costs money.
Ask one result-changing question at a time.
Do not ask me to paste a secret into chat, and do not read or display secrets.
If you can only prepare a prompt, explicitly say that no image was generated.
```

The normal order is:

1. the Agent host's built-in image tool;
2. the user's securely configured OpenAI image capability;
3. an image router already installed by the user;
4. prompt preparation without rendering.

## 3. Create the tutorial character reference

The package includes the text profile for an original public tutorial character, Learning Guide Ato. It does not distribute character example images.

```text
Use the public Learning Guide Ato profile included with ip-pic.
First create an Ato tutorial reference image.

Show clear front, side, and full-body views with consistent clothing and color.
Do not add text, a watermark, or a logo, and do not imitate a third-party character.
Save it in my current project, never inside the installed Skill.

Show me the result. Use it as a later character reference only after I say
that I accept it.
```

If it looks right, say:

```text
I accept this Ato reference. Continue with it.
```

If it does not, describe the visible problem. The Agent must create a new version without overwriting the old one, and rejected output must not become a later reference.

## 4. Illustrate one short passage

```text
Use the accepted Learning Guide Ato reference and give the following passage
one illustration:

Many people think efficiency comes from writing a more detailed plan.
Projects actually move faster when the feedback loop is shorter:
deliver one small result that can be checked, then adjust.

Use the IP Pic recommendation: article illustration, 16:9, minimal line art,
and a small amount of integrated Chinese text.
Handle content extraction, visual direction, rendering, and checks yourself.
Do not ask me to edit JSON, fill forms, or choose internal templates.
```

A successful run produces a real image. Verify that:

- Ato still matches the accepted reference;
- the character performs the core action;
- the image communicates one judgment;
- the Chinese text is short and legible;
- the main title is heavy and upright;
- there is only one hand-drawn emphasis line;
- there is no gibberish, watermark, or unrelated logo.

Say either:

```text
This image passes. Keep it.
```

or describe the problem:

```text
The character is correct, but the image has no integrated text.
Keep the same content judgment and create a new version with the original
integrated text treatment.
```

## 5. Illustrate a full Obsidian article

You can paste the article, attach its Markdown file, or tell the Agent its location in the current Obsidian vault.

```text
Read my currently open Obsidian article and use ip-pic to illustrate it.

Reuse the accepted character reference and recommended style.
Analyze the title, sections, key judgments, and semantic turns.
Choose only the moments worth illustrating and decide a sensible image count.
Do not ask me to write image slots or prompts.

First tell me, in plain language, how many images you propose and what each
will express. After I approve, generate them and show them one by one.
```

Approve the plan with:

```text
Yes. Use those positions and that image count. Show each result to me,
but do not modify the article yet.
```

If the Agent cannot see the file, it should ask you to attach it or provide its location—not ask you to configure the Skill.

For direct execution:

```text
Use the accepted character reference to illustrate this article.
Use the recommended settings and choose the image count from the content.
Show every result to me; do not approve the visuals on my behalf.

<paste or attach the article>
```

The Agent should vary composition, action, expression, gaze, and character scale while preserving identity. If one image fails, it should keep accepted images and retry only the failed item.

After you accept every image, optionally ask the host Agent to place them:

```text
All images are accepted. Save them according to this Obsidian project's
existing attachment rules and insert their links at the planned article positions.
If no attachment rule exists, propose a safe, common, recoverable location
inside the project first; do not ask me to find a path.
Before editing, tell me which article and positions will change, and keep a
recoverable original. Do not ask me to find the attachment folder or edit Markdown.
```

This is a host Agent file operation, not an Obsidian-management or publishing capability of IP Pic. The Agent must preview the change scope first.

## 6. Use your own character

Attach one to five reference images that you own or are licensed to use.

```text
Replace the IP Pic tutorial character with my character.
I own these reference images or have permission to use them.

Propose a public character name, role, appearance summary, personality,
and continuity anchors from the material. Do not infer sensitive traits.
Ask one necessary question at a time and show the profile summary before saving.

Create the character profile and register each reference's purpose yourself.
Do not ask me to edit JSON, and never write my images into the installed Skill.
```

Approve the profile with:

```text
The profile is correct. Save it as "<character name>" and use that name later.
Do not overwrite the tutorial character.
```

After approval:

```text
Use "<character name>" to illustrate this article:

<paste or attach the article>
```

## 7. Change the result in natural language

Change style:

```text
Change this image set to playful craft. Keep the character and article meaning,
create a new version, and do not overwrite the old images.
```

Other supported article styles are minimal line art, sticker collage, expressive hand-drawn, pop impact, and art print.

Change canvas:

```text
Change the next image to 1:1. Keep the content and character unchanged.
```

```text
Use 16:9 for every article illustration.
```

Change text handling:

```text
Keep one-step image-and-text integration with only a little Chinese text.
```

```text
Switch to a text-free image followed by a deterministic title layer.
Use IP Pic's default heavy Chinese title style and one hand-drawn emphasis line.
If an approved text-free image already exists, only create a new text layout.
If I only have an integrated image with text, first create a new text-free image
for my approval, then add the title. Never place new text over old text.
```

The Agent must determine whether a reusable text-free image exists before following the matching branch above.

For a licensed font, attach the font file and say:

```text
Use the Chinese font I attached for the title.
Keep the approved text-free image and create a new text version.
Do not overwrite the previous final image.
```

An exact local font cannot control one-step model-generated lettering. When you request an exact font, the Agent should propose the two-step mode.

Change quantity:

```text
Create only three images for this article. Choose the three strongest moments.
```

## 8. Create a static video keyframe

```text
Use my character to turn the following content into a 1:1 static video keyframe.
Create a text-free visual first, then add the section label, heavy core idea,
one hand-drawn emphasis line, and supporting text.
Keep the character and important objects away from the text zone and bottom
subtitle-safe area.

<paste the content>
```

For portrait:

```text
Change it to a 9:16 static keyframe and keep the bottom subtitle-safe area clear.
```

IP Pic does not create animation, lip sync, voiceover, or video edits.

## 9. Review and retry

```text
The character in image 2 does not match. Keep all accepted images and retry
only image 2. Do not overwrite the old image or use it as a new reference.
```

```text
The character and base image pass. Make only the title heavier and preserve
the single original hand-drawn emphasis line.
```

```text
Keep the successful images and retry only failed items. Show every new result
for my approval.
```

The Agent may assist with character, text, composition, and safe-zone checks, but only you can give final visual approval.

## 10. Rights, privacy, and secrets

- Use only characters and images you own or are licensed to use.
- Do not request exact imitation of an unlicensed protected character.
- Never paste API keys, tokens, cookies, or private keys into chat or article files.
- Ask the Agent to use secure system storage for paid image access and explain cost first.
- Keep character references in your project, not inside the public Skill.
- Rejected images must not automatically become future references.

## If the Agent gets stuck

```text
Read ip-pic's USER-GUIDE.en.md and SKILL.md again.
I am a content user. I do not run installation commands, locate the Skill root,
edit JSON, manage internal filenames, or diagnose implementation stages.

Handle those operations yourself. Stop only for permission, possible cost,
missing character rights, or my real visual review.
If something fails, explain what did not complete and give me one next step.
Do not claim an image was generated when it was not, and never overwrite old output.
```

## Short prompts

```text
Use ip-pic, verify the installation, and guide me through first use.
```

```text
Use Learning Guide Ato to give this passage one illustration.
```

```text
Use my character to illustrate this article.
```

```text
Read my current Obsidian article and choose the moments worth illustrating.
```

```text
Switch to playful craft and 1:1. Create a new version without overwriting.
```

```text
Keep accepted images and retry only failed items.
```

Implementation details, backend setup, file contracts, font paths, recovery, and release validation belong in the [Maintainer Guide](MAINTAINER-GUIDE.en.md), which the Agent or maintainer reads when needed.

# IP Pic User Guide

IP Pic helps writers use an original or licensed recurring character to illustrate short passages, full articles, and static video frames.

Open Codex, Claude Code, WorkBuddy, or another Agent and send it the examples below. The Agent handles installation, content planning, direction, prompts, rendering, and checks.

Direct-integrated image and text is the default. Use the text-free-then-publish path only when you need a fixed font or want to change text without redrawing an accepted character scene.

<!-- IP-PIC-ILLUSTRATION:hero-user-journey Add an original IP illustration showing article -> Agent -> paragraph-related integrated images. -->

## 1. Ask your Agent to install and begin

```text
Install and use this illustration tool:
https://github.com/wukongai/ip-pic-skill
After installation, guide me through my first illustration.
```

The Agent handles installation and checks, then reports either “installation and self-check passed” or the single failure reason. It pauses only for your permission, your visual review, or a possible additional charge.

## 2. Run the example

After installation, send this:

```text
Use IP Pic's Learning Guide Ato example to give the passage below one illustration:

Projects move faster when you get a small result to review early, not when you make the plan longer.
```

You do not need to choose a template, style, aspect ratio, font, or image tool first. The Agent uses IP Pic's recommended defaults and prefers an available GPT Image 2 tool.

Before rendering, the Agent confirms the current writing project and image location. If no project is open, it explains that a writing project is simply a folder for articles and images, then offers two or three safe choices. After your approval, it may create an “IP Pic Tutorial Project.” It must not put character references, finished images, or personal styles inside the installed IP Pic Skill. After the first run, it reports the actual save location.

The public package includes Ato's original text profile but no character image. On the first run, the Agent automatically creates an Ato reference for you to review. If it looks right, reply:

```text
Approved. Continue.
```

If it does not, describe the visible problem:

```text
The character looks too young. Make Ato an adult learning guide, keep the glasses and clothing palette, and create a new version.
```

The Agent keeps the old result and never uses a rejected image as a future reference. After you approve the reference, it continues the example. You should receive a real illustration, not only a prompt.

If the Agent says no image tool is available, open [Image Tool Setup](IMAGE-TOOL-SETUP.en.md). Normal use does not require reading it first.

## 3. Illustrate your own writing

For a short passage:

```text
Use the same Ato to give the passage below one illustration:

<paste passage>
```

For a full article, paste it, attach its Markdown file, or say:

```text
Use the same Ato to illustrate this article:

<paste article or attach file>
```

If the Agent can read your currently open Obsidian article:

```text
Use the same Ato to illustrate my currently open Obsidian article.
```

The Agent analyzes the article and first tells you how many images it recommends and what each one expresses. After approval, it renders the set and shows every image. It should not illustrate every paragraph mechanically or ask you to write image prompts.

For strict paragraph-by-paragraph review, say:

```text
Analyze this article paragraph by paragraph.
Before rendering, list each paragraph's meaning and the planned scene, expression, action, and gaze.
After rendering, show which paragraph each image belongs to.
Do not approve an image that is unrelated to its source paragraph.
```

<!-- IP-PIC-ILLUSTRATION:article-paragraph-map Add an original IP example of several paragraphs becoming distinct scenes and performances. -->

After you approve every image, you may say:

```text
All images are approved.
Follow this Obsidian project's existing attachment rules,
save the images, and insert their links at the planned article positions.
If there is no attachment rule, propose a safe and recoverable project-local option first.
Before editing, tell me which article and positions will change, and preserve a recoverable original.
```

Your host Agent performs this file operation. IP Pic itself does not manage Obsidian or publish content.

## Make IP Pic your own reusable workflow

Your Agent can save and keep improving characters, references, personal styles, and director presets for you. You describe the result, approve a preview, and review the final image; you do not need to open or edit configuration files.

Private settings live in the current writing project's `.ip-pic/` area, outside the public Skill. Before every save, the Agent must show a plain-language preview of the character anchors, reference purposes, style changes, or expression, action, gaze, and body pose. It writes only after you explicitly confirm.

To save a character:

```text
These are character references I created or am licensed to use.
Organize the character as "Xiao He" and show me the appearance and continuity anchors first.
After I confirm, save it and make it this project's default character.
```

To save a personal style:

```text
Create "Warm Learning Linework" from Minimal Lineart:
make the lines slightly heavier, the palette warmer, and keep a light paper grain.
Show me the save preview first. After I confirm, make it the default style.
```

To save reusable performance direction:

```text
Save a director preset called "Careful Breakdown":
lean slightly forward, move a workflow card with the right hand,
use a focused expression, and look at the current step.
Preview it first and save only after I confirm.
```

Changes create new versions and never overwrite the old version:

```text
Change Xiao He's jacket to blue and keep every other continuity anchor.
Show me the new profile version, then save and activate it after I confirm.
```

To inspect or roll back:

```text
List every version of "Xiao He" and the current default. Explain the differences without changing anything.
```

```text
Switch "Xiao He" back to the previous version. Tell me the exact version first and wait for my confirmation.
```

Normal article use remains one sentence:

```text
Use "Xiao He", "Warm Learning Linework", and "Careful Breakdown" to illustrate this article:

<paste article or provide the Obsidian file>
```

Settings stay in one project. For another project, ask the Agent to read the confirmed source version and prepare a new save preview in the target project. Confirm again before anything private is registered there.

## 4. Use your own character and references

Attach one to five character images that you own or are licensed to use, then say:

```text
I want to use my own character for IP illustrations.
These references are my original work or licensed for this use.

Build a character profile and continuity anchors from them and show me the result first.
After approval, save it in my writing project, not in the public Skill.
```

The Agent organizes the character name, public identity, appearance, personality, and continuity anchors. It should not infer sensitive traits such as age, health, ethnicity, or religion. If something essential is missing, it asks one question at a time.

Approve with:

```text
The profile is correct. Save it as "<character name>" and use that name from now on.
```

Normal use is then:

```text
Use "<character name>" to illustrate this article:

<paste article or provide the Obsidian file>
```

To use only one reference:

```text
Use only the front-view character image I just attached. Do not include the others.
```

You can also change performance without changing the approved content:

```text
Keep the content and style. Change only the character performance:
use a realization expression, lean slightly forward, and look at the completion marker.
Create a new version without overwriting the old image.
```

### Build a stronger reference set

Only do this when you want better character continuity:

```text
Create a new reference set for "<character name>":
front, side, full-body, and common expressions, with consistent clothing and palette.
Do not add text, watermarks, or logos.

Show every image first. Save approved images as a new reference version
named "<character name>-references-02" without overwriting the current default.
```

Continue adjusting in ordinary language:

```text
The side view does not match the front view. Keep the face shape, hair, and glasses, and redo only the side view.
```

To find or switch reference versions:

```text
List the existing reference versions, default version, and creation time for "<character name>".
Use "<version name>" for this run and do not delete other versions.
```

## 5. Change an existing style

Describe the change and ask for a new version. The Agent keeps the character identity, article meaning, and previous results.

```text
Switch this set to playful craft. Create a new version without overwriting the old one.
```

Other built-in choices are:

```text
Switch to minimal line art.
```

```text
Switch to sticker collage.
```

```text
Switch to expressive hand-drawn.
```

```text
Switch to pop impact.
```

```text
Switch to art print.
```

To customize a built-in style while preserving the original:

```text
Start from IP Pic's "playful craft" style.
Lower the saturation and reduce the paper texture; keep all other rules.
Make one Ato preview, then save the approved result as my personal style "soft-craft-01".
Do not modify or overwrite the built-in playful craft style.
```

Aspect ratios are just as simple:

```text
Make the next image 1:1. Keep the content and character unchanged.
```

```text
Use 16:9 landscape for this whole article.
```

```text
Switch to 9:16 portrait and keep the lower subtitle-safe area clear.
```

## 6. Add your own style

When the built-in choices do not fit, create a personal style from words or licensed style references.

### Describe it in words

```text
I want to add my own illustration style:
colored-pencil journal sketches, lightly textured paper, low saturation,
relaxed character lines, but a heavy upright Chinese title and one hand-drawn emphasis line.

Make one Ato example preview first. Do not change any built-in style.
```

### Explain it with images

Attach original or licensed style references, then say:

```text
Analyze only the line, material, palette, whitespace, and typography of these images.
Do not copy their people, brands, wording, or distinctive compositions.
Make one Ato preview in the new style.
```

When approved:

```text
Approved. Save this as my personal style "<style name>".
Use that name in future and do not overwrite any built-in style.
```

To tune it:

```text
Reduce the paper grain and make the character lines slightly heavier.
Keep everything else. Save it as "<style name>-02" without overwriting the previous version.
```

Personal styles stay in the current project by default. For another project, ask the Agent to read the confirmed source version and prepare a new registration preview in the target project; confirm again before saving. A style changes visual treatment; it must not silently change character identity, article meaning, canvas, or text mode.

For a different project:

```text
Read my personal style "<name>" from the current project and prepare the same named style in "<new project>".
Show the source version and target save preview first.
After I confirm, save it without overwriting a style with the same name.
```

## 7. Change the text treatment

For text and illustration in one generation:

```text
Keep the one-pass integrated layout with a small amount of Chinese text.
```

The default target is heavy, upright Chinese display lettering with one hand-drawn emphasis line, not calligraphy, children's lettering, or thin type.

For a stable text layer:

```text
Switch to a text-free image followed by a title.
Use IP Pic's default heavy Chinese title and hand-drawn emphasis line.
If an approved text-free image already exists, recompose only the text.
If only an integrated image exists, create a new text-free image for my approval first,
then add the title; do not place new text over old text.
```

To use a font you are licensed to use, attach it and say:

```text
Use the Chinese font I just provided for the title.
Keep the approved text-free image and create a new text version without overwriting.
```

Model-generated integrated text cannot precisely lock to a local font. Use the two-step flow when the exact font matters.

## 8. Control count, versions, and retries

```text
Make only three illustrations for this article. Choose the three most useful moments.
```

```text
Make the first two and wait for my approval before continuing.
```

```text
The character in image two does not match. Keep all accepted images and redo only image two.
Do not overwrite or use the rejected image as a reference.
```

```text
The character and base image are approved. Make only the title heavier and keep one emphasis line.
```

```text
Keep this set as the old version and rebuild the whole set in a new direction.
Do not inherit rejected images.
```

The Agent may assist with character, composition, text, and safe-area checks, but only you can give final visual approval.

To inspect accumulated assets without changing them:

```text
List the characters, reference versions, and personal styles in this project.
Explain the current defaults in plain language and do not modify anything.
```

## 9. Static video keyframes

```text
Use my character to turn the content below into a 1:1 static video keyframe.
Create a text-free image first, then add the series name, a heavy key message,
one hand-drawn emphasis line, and supporting text. Keep the lower subtitle area clear.

<paste content>
```

IP Pic creates static keyframes only. It does not animate, lip-sync, narrate, or edit video.

## Rights, privacy, and cost

- Use only original or licensed characters, fonts, and reference images.
- Do not request an exact copy of an unlicensed known character.
- Character profiles, references, and personal styles stay in your project, not the public Skill.
- Rejected images never become future references automatically.
- The Agent must explain and ask before a route may create additional API charges.

## About this standalone release

IP Pic was extracted from a larger production workflow into a standalone public Skill. The release is covered by automated contract, privacy, security, template, style, batch, retry, and real-image tests. Different agents, image models, fonts, and environments can still produce visual differences.

Run the Ato short-passage example first, then test your article and an authorized character. Report reproducible issues with the public input, agent, image-tool type, failed image, and visible symptom. Never include credentials or references you are not allowed to publish. See [Verification Notes](docs/VERIFICATION.en.md).

<!-- IP-PIC-ILLUSTRATION:release-feedback Add an original IP illustration of user review and retrying only failed items. -->

## If the Agent gets stuck

Start with:

```text
Continue using the IP Pic user guide. Do not make me handle internal commands or configuration.
If an image tool is truly missing, tell me the single next step.
```

Only when the Agent explicitly says no image tool is available, give it [Image Tool Setup](IMAGE-TOOL-SETUP.en.md).

## Useful one-line prompts

```text
Use IP Pic's Learning Guide Ato example to give this passage one illustration: <passage>
```

```text
Use "<character name>" to illustrate this article: <article or file>
```

```text
Switch to playful craft and 1:1. Create a new version without overwriting.
```

```text
Save this as my personal style "<style name>" without overwriting built-in styles.
```

```text
Keep accepted images and retry only failed items.
```

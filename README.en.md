# IP Pic Skill

[简体中文](README.md) | [English](README.en.md)

This is the installation and usage guide for IP Pic Skill. Install it, configure one rendering route, and complete two tests with a tutorial character. Replace the character with your own only after the workflow works.

For normal use, simply ask to “illustrate this passage” or “illustrate this article.” The Agent analyzes the content, chooses illustration points, recommends a count, builds the brief and prompts, renders, and checks every image.

## 1. Install the Skill

Run this from the project where you write:

```bash
npx skills add wukongai/ip-pic-skill
```

The installer asks for the target Agent and installation scope. Reopen the task, then say:

```text
Use ip-pic. Check the installation and guide me through the first run.
```

The Agent locates the installed Skill and its scripts. Normal users do not need to study JSON, script paths, or dependencies.

## 2. Configure one rendering route

IP Pic has three real rendering routes. You configure it once, then simply ask for illustrations.

1. **Codex Image Tool / built-in `imagegen` (recommended)**: uses GPT Image 2 through Codex and requires no API key from you.
2. **Direct OpenAI API**: uses the Skill's bundled GPT Image 2 renderer with your `OPENAI_API_KEY`; usage is billed to your OpenAI API account.
3. **Existing `ai-router`**: for a host where `ai_router.generate_image` is already installed and registered; keys, provider, model, retries, and fallback remain inside the Router.

After the first choice, the Agent can save it as this project's default. Normal illustration requests reuse it until it becomes unavailable or you ask to change it.

`prompt-only` is a compile-only fallback, not a fourth real rendering route. It creates prompts, `render-request.json`, and a manifest but does not create image files; the status is `compile_only`.

### Safe direct OpenAI API setup

For Direct OpenAI API, ask the Agent to run:

```bash
python3 <skill-root>/scripts/openai_backend.py doctor
python3 <skill-root>/scripts/openai_backend.py configure
```

Run `configure` only when `doctor` returns `missing_credentials`. It uses hidden input and writes the key to the user-level `~/.ip-pic/.env`. You may instead provide `OPENAI_API_KEY` in the current process.

Never paste the key into chat, an article, this repository, a character profile, or `EXTEND.md`. Create one at [OpenAI API Keys](https://platform.openai.com/api-keys); API usage may require account credit or organization verification. If the check returns `unsupported_platform`, choose Codex Image Tool or an existing `ai-router`.

The direct renderer uses exact dimensions: `16:9 = 1536x864`, `1:1 = 1024x1024`, and `9:16 = 1152x2048`. Both edges must be multiples of 16. If an output file already exists, the call stops before billing; use a new output filename. It will not overwrite the original.

### Existing ai-router

An AI Router is a unified image entry already exposed to the host through MCP. `ip-pic` only calls the existing `ai_router.generate_image`; it does not read the Router's `.env` or manage its credentials, models, or fallback. This project does not direct users to download a private Router repository.

## 3. Start with a tutorial character

Do not begin by creating your own character. First choose one original tutorial character:

| Wukong Knowledge Maker | Moon Rabbit Mapmaker | Study Guide Ato |
|---|---|---|
| ![Wukong Knowledge Maker](examples/characters/wukong/preview.png) | ![Moon Rabbit Mapmaker](examples/characters/moon-rabbit/preview.png) | ![Study Guide Ato](examples/characters/ato/preview.png) |
| [Character profile](examples/characters/wukong/profile.json) | [Character profile](examples/characters/moon-rabbit/profile.json) | [Character profile](examples/characters/ato/profile.json) |

Ato also includes a [synthetic source portrait](examples/characters/ato/source-synthetic-photo.png) to demonstrate the “portrait to original cartoon master” workflow. It is a generated tutorial asset and does not depict a real person.

For example:

```text
Use Study Guide Ato for this tutorial.
```

None of these roles is written to your `.ip-pic/ip-profile.json`.

## 4. Test one short passage

Use this sample:

> Many people think efficiency comes from making plans more detailed. In practice, projects move faster when feedback cycles get shorter. Deliver one small result that can be checked, learn from it, and then continue.

Then say only:

```text
Illustrate the following passage with Study Guide Ato in one image:
<paste the passage>
```

The Agent extracts the core idea, chooses the scene, creates the image, and checks character consistency. Success means a real image exists, the role remains recognizable, the scene explains the passage, and there is no broken text, watermark, or meaningless lettering.

## 5. Illustrate a long article automatically

After the short test succeeds, provide a full article:

```text
Illustrate the following article with Study Guide Ato:
<paste the article>
```

That is the whole request. The Agent analyzes headings, sections, and semantic turns, selects useful visual points, recommends a sensible count, compiles, renders, and checks every image. It does not blindly create one image per paragraph or ask you to write the brief and prompts.

Add an override only when you want one, such as “create three 16:9 illustrations.” Otherwise, let the Skill decide.

A successful real backend returns image files, prompts, `render-request.json`, and a run manifest. With `prompt-only`, the result contains compile artifacts only and must state `compile_only`; it must not claim that images were created.

## 6. Replace it with your own character

Once both tests work, prepare a clear photo of yourself or someone you are authorized to depict. A single person, even lighting, and visible hairstyle, face shape, glasses, and clothing anchors work best.

For Codex Image Tool or existing `ai-router`, attach the real photo and this character-master prompt:

```text
Turn this photo of myself or a person I am authorized to use into an original cartoon IP character master. Preserve recognizable, non-sensitive appearance anchors such as hairstyle, face shape, and glasses without inferring sensitive attributes. Show a full-body character on a clean neutral background, with multiple views (front, side, and back) plus four useful expressions. Keep the design simple and consistent for a series of article illustrations. Use no text, watermark, or logo, and imitate no third-party character traits.
```

For Direct OpenAI API, ask the Agent to stay in your user project directory and run:

```bash
python3 <skill-root>/scripts/openai_backend.py master --reference <project-photo-path> --output <project-character-master.png>
```

The input and output must remain in your project, not the installed Skill directory. If the output file already exists, choose a new output filename; the call will not overwrite an existing master.

With `prompt-only`, the Skill provides the character-master prompt but cannot create the image. Use the photo and prompt in an external image tool, upload the resulting master, or keep using a tutorial character.

When the master looks right, say:

```text
Build my ip-profile from this cartoon master. Ask one question at a time and show it to me before saving.
```

The Agent confirms the rights basis, summarizes identity, appearance, personality, and continuity anchors, then writes `.ip-pic/ip-profile.json`. You do not hand-edit JSON.

Normal use is now:

```text
Illustrate the following article with my character:
<paste the article>
```

### Add poses and expressions

Put optional references under:

```text
.ip-pic/assets/poses/
.ip-pic/assets/expressions/
```

Do not replace the character master. Ask the Agent to record each reference's purpose and authorization in the profile. Each image should use only the few references it needs.

The profile may contain local paths. Add `.ip-pic/` to the project `.gitignore` if it should not sync through Git or cloud storage.

## If installation or the first run fails

- Installation fails: check Node.js and `npx`, then confirm the installation scope.
- Installation succeeds but compilation fails: check Python 3.10+ and the actual executable.
- You get prompts but no images: confirm whether you selected `prompt-only` or whether the real backend still needs setup.
- Direct OpenAI API returns `unsupported_platform`: choose another real rendering route. Windows can still install the Skill and use the other routes.

PowerShell uses the same single-line command:

```powershell
npx skills add wukongai/ip-pic-skill
```

## Optional preferences

To retain a canvas, style, or backend, copy `EXTEND.example.md` to `.ip-pic/EXTEND.md` in your project. Never store a key, token, cookie, service URL, or model route there.

## Migrate from the previous name

If you installed `custom-ip-illustration`:

1. Remove the previous Skill with your Skill manager.
2. Run `npx skills add wukongai/ip-pic-skill`.
3. To preserve profiles and preferences, move files from project `.custom-ip-illustration/` to `.ip-pic/`.

## Developer verification

```bash
git clone https://github.com/wukongai/ip-pic-skill.git
cd ip-pic-skill
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/verify_release.py --root . --manifest public-release-manifest.json
```

See [SECURITY.md](SECURITY.md) for security reports and [CONTRIBUTING.md](CONTRIBUTING.md) for contributions.

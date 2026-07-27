# Custom IP Illustration Skill

[简体中文](README.md) | [English](README.en.md)

Turn an article into a series of illustrations performed by one consistent, original IP character. You do not need to understand the scripts, JSON, or model parameters first—follow these four steps.

## 1. Install the Skill

Run this from your project directory:

```bash
npx skills add wukongai/custom-ip-illustration-skill
```

The installer asks for the target Agent and installation scope. Then tell your Agent:

```text
Use custom-ip-illustration. Check the installation, then guide me through my first run.
```

The Agent locates the installed Skill and runs its scripts. A normal user does not install dependencies manually.

## 2. Choose how to render

On the first run, the Agent must show these four choices and let you decide. It does not silently select one:

1. **Codex Image Tool / built-in `imagegen` (recommended)**: uses GPT Image 2 through Codex; you do not provide or configure an API key.
2. **Direct OpenAI API**: this Skill includes its own GPT Image 2 renderer; it needs your `OPENAI_API_KEY`, and usage is billed to your OpenAI API account. If its check returns `unsupported_platform`, this route is unavailable; choose another method.
3. **Existing `ai-router`**: only for users who already have `ai_router.generate_image` installed and registered; keys, provider, and model stay inside the Router.
4. **`prompt-only`**: compiles prompts, a render request, and a manifest but does not create image files; the result is `compile_only`.

For example:

```text
Use Codex Image Tool for this task only. Do not save it as my default.
```

The Agent saves a backend preference only when you explicitly say “use this by default from now on.” If that backend later becomes unavailable, it asks again instead of silently switching to a potentially paid route.

### Safe direct OpenAI API setup

After you choose Direct OpenAI API, ask the Agent to run `doctor`. If credentials are missing, it can run `configure`. `configure` uses hidden input and writes the key to the user-level `~/.custom-ip-illustration/.env` with user-only permissions. You may instead provide `OPENAI_API_KEY` in the current process environment.

Never paste the key into chat, this repository, a character profile, `EXTEND.md`, or an article. The Agent must not echo it. Create a key at [OpenAI API Keys](https://platform.openai.com/api-keys); API usage may also require account credit or organization verification.

The direct renderer uses the exact dimensions from the compiled request: `16:9 = 1536x864`, `1:1 = 1024x1024`, and `9:16 = 1152x2048`. Both edges must be multiples of 16 and remain within GPT Image 2 edge, aspect-ratio, and total-pixel limits; the renderer never substitutes an approximate size. Every `render` run must use unused output filenames. If any target already exists, it stops before the API call and preserves the original file.

### Existing ai-router

This route only calls `ai_router.generate_image` already exposed by the host. This project does not direct users to download a private Router repository and never reads Router environment files. Your Router owns connection setup, credentials, model selection, retries, and fallback.

## 3. Create your cartoon IP

To create your own character, prepare a real photo of yourself or someone you are authorized to depict, plus this compact character-master prompt:

```text
Turn this photo of myself or a person I am authorized to use into an original cartoon IP character master. Preserve recognizable, non-sensitive appearance anchors such as hairstyle, face shape, and glasses without inferring sensitive attributes. Show a full-body character on a clean neutral background, with multiple views (front, side, and back) plus four useful expressions. Keep the design simple and consistent for a series of article illustrations. Use no text, watermark, or logo, and imitate no third-party character traits.
```

Continue according to your Step 2 choice:

- **Codex Image Tool or existing `ai-router`**: attach the real photo and character-master prompt in the conversation, then ask the selected tool to create `character-master.png`.
- **Direct OpenAI API**: complete `doctor / configure`, then ask the Agent to stay in your user project directory and locate the installed script through `<skill-root>`:

```bash
python3 <skill-root>/scripts/openai_backend.py master --reference <project-photo-path> --output <project-character-master.png>
```

Both `<project-photo-path>` and `<project-character-master.png>` must be inside your project, never inside the installed Skill directory. The master output must use a `.png` suffix.

If the output file already exists, the command stops before calling the Image API. Choose a new output filename; it will not overwrite an existing master.

If the earlier `doctor` returns `unsupported_platform`, do not run `master`, keep retrying, or silently fall back. Return to Step 2 and choose Codex Image Tool, existing `ai-router`, or `prompt-only`.

- **`prompt-only`**: the Skill outputs the character-master prompt but cannot turn the photo into an image. Use the photo and prompt in your own external image tool, then upload the resulting master, or choose a tutorial character below.

When the master looks right, tell your Agent:

```text
Build my ip-profile from this cartoon master. Ask one question at a time and show it to me before saving.
```

The Agent confirms the rights basis, then extracts identity, appearance, personality, and continuity anchors. It saves `.custom-ip-illustration/ip-profile.json` only after your confirmation. The file may contain local reference paths; add `.custom-ip-illustration/` to your project `.gitignore` if it should not sync to Git or cloud storage.

If you do not want to upload a photo, try one original tutorial character:

| Wukong Knowledge Maker | Moon Rabbit Mapmaker |
|---|---|
| ![Wukong Knowledge Maker](examples/characters/wukong/preview.png) | ![Moon Rabbit Mapmaker](examples/characters/moon-rabbit/preview.png) |
| [Character profile](examples/characters/wukong/profile.json) | [Character profile](examples/characters/moon-rabbit/profile.json) |

Choose one explicitly. Neither character is selected by default or saved as your profile; each is only a tutorial option for the current run.

## 4. Give the Skill your article

Shortest useful request:

```text
Use my IP to create three 16:9 illustrations for the article below with Codex Image Tool. Show the illustration points first, then render and check each image: <paste article>
```

For a tutorial, replace “my IP” with “Wukong Knowledge Maker” or “Moon Rabbit Mapmaker.” The Skill writes every prompt under `prompts/` before it renders and checks each image through the backend you selected.

- With one of the first three ready backends and a successful render, the result contains real image files, prompts, `render-request.json`, and a run manifest.
- With `prompt-only`, the result contains prompts, `render-request.json`, and a manifest only; it must not claim that images were created.
- If one image fails, the Agent reports it individually instead of claiming complete success.

## If installation or the first run fails

The Agent handles normal dependencies. If installation fails, check Node.js and `npx`. If installation succeeds but the first compilation fails, then check Python 3.10+.

Windows can still install the Skill and use the other rendering methods. If Direct OpenAI API returns `unsupported_platform`, choose another method. Use this single-line PowerShell install command:

```powershell
npx skills add wukongai/custom-ip-illustration-skill
```

## Optional preferences

To retain a canvas, style, or rendering choice, copy `EXTEND.example.md` to `.custom-ip-illustration/EXTEND.md` in your project. Preferences may contain ordinary settings only—never a key, token, cookie, service URL, or model route.

## Developer verification

```bash
git clone https://github.com/wukongai/custom-ip-illustration-skill.git
cd custom-ip-illustration-skill
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/verify_release.py --root . --manifest public-release-manifest.json
```

See [SECURITY.md](SECURITY.md) for security reports and [CONTRIBUTING.md](CONTRIBUTING.md) for contributions.

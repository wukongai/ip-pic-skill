# IP Pic Image Tool Setup

Use this guide only when the Agent explicitly says that no image tool is available. For normal illustration work, return to the [user guide](USER-GUIDE.en.md) and run the Ato example.

IP Pic recommends GPT Image 2 by default. It supports three real rendering methods; choose one:

| Your situation | Use | Where configuration lives |
|---|---|---|
| You use Codex | Codex Image Tool (recommended) | Managed by Codex; no API key to configure |
| You do not use Codex | OpenAI official API, or a relay already connected to your host | Key, service URL, and model stay in the host's secure configuration |
| You already have ai-router | Host `ai_router.generate_image` | Credentials and routing remain in your own ai-router |

## Codex Image Tool (recommended)

Codex image generation uses GPT Image 2 and counts toward Codex usage limits. Send this to Codex:

```text
Use Codex Image Tool and GPT Image 2 for this run.
Explicitly invoke `$imagegen` with the complete IP Pic prompt, canvas size, and character references.
After rendering, complete IP Pic's per-image checks and show me the real image.
```

There is no API key for you to configure. You do not need to repeat this prompt inside the same task.

## Without Codex: OpenAI official API

```text
I do not use Codex. Use the OpenAI official API and GPT Image 2 for IP Pic.
Guide me to save `OPENAI_API_KEY` in this Agent's secure secret store
or the current process environment. Never ask me to paste the key into chat or a project file.
Use the official base URL `https://api.openai.com/v1`.
Check access before continuing the first illustration.
```

You must enter the key yourself in the host's secure secret surface, operating-system password storage, or secure environment. Never place it in IP Pic, an article, an Obsidian note, a character profile, or a Git repository. The Agent may report only “configured” or “not configured,” never the full key.

The official adapter uses image generation without references and image editing with every selected authorized reference. It must not drop references merely to continue.

After configuration, the Agent also checks GPT Image 2 access, organization verification, and usable credit. A stored key alone does not prove rendering readiness.

## Without Codex: an existing relay service

A relay service is not the OpenAI official direct route. Keep its URL, key, and model in the host tool or ai-router user-level configuration, not in IP Pic.

```text
Connect my existing image relay as this host's image tool or through my ai-router.
Keep its URL, key, and model only in the host or Router's user-level secure configuration.
Do not store them in IP Pic, my writing, character profile, or project repository.
Verify that it accepts prompts, canvas size, and character references before continuing.
```

You must enter a relay key yourself in the secure surface; never paste it into chat. IP Pic has no universal relay configuration file because the exact location belongs to the host or Router.

## An existing ai-router

When the host already exposes `ai_router.generate_image`:

```text
Check whether this host already has `ai_router.generate_image`.
If it does, use it for the real IP Pic render and pass the complete prompt,
canvas size, character references, and expected output location.
Do not read, display, or modify ai-router credentials, providers, routing, retries, or fallback.
```

The ai-router URL, key, model, and routing remain in its own user-level configuration outside IP Pic.

## First readiness check

Ask the Agent to report status without revealing secrets:

```text
Image tool readiness:
Connection source:
Rendering method:
Actual model:
Supports character references:
Creates separate API charges:
```

“Supports character references” must be “yes” before a fixed-character workflow continues. For an API or relay, the Agent must also say whether it is “OpenAI official” or a “third-party relay.” It must explain and obtain approval before a route creates separate API charges.

## If rendering is still unavailable

`prompt-only` does not generate an image. It prepares prompts and a rendering contract, so the Agent must say that no real image has been generated.

Default priority is Codex Image Tool → a verified reference-capable host image tool → a registered ai-router → OpenAI official API → `prompt-only`.

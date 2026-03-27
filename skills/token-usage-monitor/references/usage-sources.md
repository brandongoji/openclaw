# Usage sources and limits

## What this skill can measure now

The bundled script reads OpenClaw session transcript files from the local state directory and summarizes assistant-turn usage blocks.

That gives reliable access to:
- input tokens
- output tokens
- cache read tokens
- cache write tokens
- total tokens
- estimated cost when the provider reports it
- per-model rollups inside a session

## What this does not replace

This is not the same thing as:
- OpenAI/Codex subscription quota remaining
- VS Code/Cursor cloud-side usage dashboards
- a live always-visible Control UI widget

Those require either:
- provider APIs / provider dashboards, or
- a Control UI/source modification in OpenClaw itself

## Recommended use

Use this skill when the user wants:
- current session token totals
- last-call token usage
- which model is burning the most tokens in a session
- a local audit of OpenClaw transcript usage

If the user wants a persistent live panel in the web UI, treat that as a product/code customization task rather than a pure skill task.

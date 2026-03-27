---
name: token-usage-monitor
description: Inspect and summarize OpenClaw token usage from local session transcripts, including current-session totals, last-call usage, cache usage, estimated cost, and per-model breakdowns. Use when the user asks about token burn, wants a usage calculator/monitor in chat, wants to know which model is consuming tokens, or needs a local usage report for an OpenClaw session.
---

# Token usage monitor

Use the bundled script to read local OpenClaw session transcript usage and produce a compact report.

## Quick start

Run the script against the default Hagios 1 state directory:

```bash
python3 {baseDir}/scripts/token_usage_monitor.py
```

Check an explicit session key:

```bash
python3 {baseDir}/scripts/token_usage_monitor.py --session-key agent:main:main
```

Emit JSON for further processing:

```bash
python3 {baseDir}/scripts/token_usage_monitor.py --format json
```

## What to report

Prefer a short summary first:
- total input / output / cache / total tokens
- estimated cost if present
- last assistant call usage
- per-model breakdown when more than one model appears

Then add one or two actionable observations, for example:
- heartbeats are cheap now / still too expensive
- one model is dominating spend
- cache reads are helping or absent

## Good use cases

Use this skill for:
- “How many tokens has this session used?”
- “Which model is burning my usage?”
- “Show me a token monitor in chat.”
- “Give me a local usage breakdown for Hagios 1.”

## Limits

Read `references/usage-sources.md` when the user expects provider-side quota remaining or a VS Code/Cursor-style persistent UI widget.

This skill reads local OpenClaw transcript usage. It does **not** directly know the provider subscription cap remaining unless another external source is added.

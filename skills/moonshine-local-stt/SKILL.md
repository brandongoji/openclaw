---
name: moonshine-local-stt
description: Local speech-to-text using Moonshine models (tiny/base) with CPU/RAM safety limits. Use when the user asks for private, local microphone transcription, model size selection, or browser/chat mic controls that should avoid freezes.
---

# Moonshine Local STT

Use this skill to run **local** Moonshine transcription with explicit model control and conservative runtime limits.

## Quick start

- Transcribe an audio file with model selection:
  - `./scripts/moonshine-transcribe.ps1 -InputFile <audio> -Model tiny`
  - `./scripts/moonshine-transcribe.ps1 -InputFile <audio> -Model base`
- Default output file: `<input>.moonshine.txt`

## Safety defaults (anti-freeze)

Always prefer lower load unless user asks otherwise:

- Start with `tiny`
- Cap clip length (default 20s)
- Cooldown between runs (default 1s)
- Single worker/thread by default

For browser/chat mic features, chunk microphone audio into short segments and process sequentially.

## Recommended workflow

1. Confirm model: `tiny` (speed/stability) vs `base` (better accuracy).
2. Run `moonshine-transcribe.ps1` with default safety limits.
3. If users report lag/freezes, reduce load in this order:
   - shorter `-MaxSeconds`
   - `tiny` model
   - longer `-CooldownMs`
4. Return transcript and include the exact model + limits used.

## Notes

- This skill assumes a local Moonshine runtime/CLI is installed.
- If Moonshine binary is missing, the script exits with install guidance.
- Keep this skill local-first; do not switch to cloud STT unless user asks.

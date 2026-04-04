---
name: huggy-transcribe
description: Unified transcription skill combining Moonshine local STT (tiny/base), local Whisper CLI models, and OpenAI whisper-1 API. Use when working on Hagios/TellMeMo transcription speed, live/local STT quality tuning, model switching, hotword accuracy, or emulator microphone transcription workflows.
---

# Huggy Transcribe

Use this skill to run transcription with a model ladder optimized for speed first, then quality.

## Quick Start

- Local fastest path:
  - `./scripts/moonshine-transcribe.ps1 -InputFile <audio> -Model tiny`
- Local improved quality:
  - `./scripts/moonshine-transcribe.ps1 -InputFile <audio> -Model base`
- OpenAI API fallback:
  - `./scripts/openai-transcribe.sh <audio> --model whisper-1`

## Workflow

1. Start with Moonshine `tiny` for short clips and rapid iteration.
2. Retry with Moonshine `base` if proper nouns or names are wrong.
3. Use Whisper local/API when Moonshine quality is still insufficient.
4. Include a keyword prompt for name-sensitive clips (for example: Hagios, Huggy).
5. If output repeatedly mishears the same word, apply deterministic post-processing.

## Model Guidance

Read `references/model-selection.md` for model speed/accuracy tradeoffs and fallback order.
Read `references/browser-integration.md` for browser and mic integration notes.

## Included Scripts

- `scripts/moonshine-transcribe.ps1`
- `scripts/moonshine-transcribe-wav.py`
- `scripts/whisper-transcribe-wav.py`
- `scripts/openai-transcribe.sh`

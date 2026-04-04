# Model Selection

## Goal
Pick the fastest transcription path that still meets quality needs.

## Priority Order
1. `moonshine tiny` for fastest local CPU transcription.
2. `moonshine base` when tiny misses words.
3. `whisper turbo` or `whisper small` local when Moonshine quality is not enough.
4. `openai whisper-1` API when cloud use is acceptable.

## Recommended Defaults
- Start with `moonshine tiny` for clips under 30 seconds.
- If proper nouns are wrong, retry with `moonshine base`.
- If still wrong, use Whisper with a prompt that includes expected names/keywords.

## Latency Notes
- First model load can be slow if weights are not cached.
- Keep one model warm when running repeated short clips.
- Avoid large models on CPU for short interactive clips.

## Accuracy Notes
- Prefer keyword prompts for names (for example: Hagios, Huggy).
- Post-process known misrecognitions where needed.

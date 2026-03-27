# Browser integration notes (Moonshine)

Use these defaults when wiring a chat mic button to local Moonshine:

- Segment length: 5-10s chunks
- Inference queue: single in-flight request
- Cooldown: 500-1000ms between chunks
- Default model: tiny
- Upgrade to base only on explicit user request

## Freeze prevention checklist

1. Never run concurrent transcriptions from the same tab.
2. Stop recording before starting the next inference.
3. Abort immediately on tab hidden/backgrounded state.
4. Enforce max clip duration in UI.
5. Surface non-fatal errors inline (avoid modal spam).

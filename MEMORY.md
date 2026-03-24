# MEMORY

## Architecture & Preferences

- Hagios 1/Hagios 2 split is intentional: Hagios 2 is the backup updater/fixer; Hagios 1 is the active customized instance.
- Preserve OpenClaw core behavior in Hagios 1 where possible; use skill-only customization for new features.
- If cross-instance handoffs are sent, include explicit identity (for example: `From: Hagios 1`).
- Prefer low-token handoff channels over browser/Playwright UI interaction for routine delegation.

## Project Direction

- Follow an upstream-overlay strategy similar to OSS derivatives (minimal custom patch surface + disciplined upstream sync).
- Goal: integrate custom features while keeping updates from upstream OpenClaw maintainable.

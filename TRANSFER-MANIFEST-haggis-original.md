# Transfer manifest: haggis-original -> Hagios 1

Date: 2026-03-20 05:28 EDT
Source root: /Volumes/Samsung USB/Mac/original Hagios
Target root: /Users/hagios/Documents/Hagios 1

## Copied into live Hagios 1

### Custom skills
- /Volumes/Samsung USB/Mac/original Hagios/.openclaw-personal/workspace/skills/autonomous-observer -> /Users/hagios/Documents/Hagios 1/openclaw/skills/autonomous-observer
- /Volumes/Samsung USB/Mac/original Hagios/.openclaw-personal/workspace/skills/parakeet-local-stt -> /Users/hagios/Documents/Hagios 1/openclaw/skills/parakeet-local-stt
  - copied with `.venv/` intentionally excluded from `scripts/.venv/` because it is a bundled Windows virtualenv/dependency dump, not safe/current runtime state for this Mac

### Old memories archive
- /Volumes/Samsung USB/Mac/original Hagios/.openclaw-personal/workspace/MEMORY.md -> /Users/hagios/Documents/Hagios 1/workspace/old-memories/MEMORY.md
- /Volumes/Samsung USB/Mac/original Hagios/.openclaw-personal/workspace/memory/2026-02-16.md -> /Users/hagios/Documents/Hagios 1/workspace/old-memories/memory/2026-02-16.md
- /Volumes/Samsung USB/Mac/original Hagios/.openclaw-personal/workspace/memory/2026-02-17.md -> /Users/hagios/Documents/Hagios 1/workspace/old-memories/memory/2026-02-17.md
- /Volumes/Samsung USB/Mac/original Hagios/.openclaw-personal/workspace/memory/2026-02-18.md -> /Users/hagios/Documents/Hagios 1/workspace/old-memories/memory/2026-02-18.md
- /Volumes/Samsung USB/Mac/original Hagios/.openclaw-personal/workspace/memory/2026-02-19.md -> /Users/hagios/Documents/Hagios 1/workspace/old-memories/memory/2026-02-19.md

## Staged for manual review/merge only
Base staging dir:
- /Users/hagios/Documents/Hagios 1/state/import-from-haggis-original/personal-state

From /Volumes/Samsung USB/Mac/original Hagios/.openclaw-personal:
- .env
- openclaw.json
- openclaw.json.bak
- openclaw.json.bak.1
- openclaw.json.bak.2
- openclaw.json.bak.3
- openclaw.json.bak.4
- openclaw.json.bak.emotionbot
- openclaw.json.bak.persona
- agents/
- subagents/
- devices/
- identity/
- cron/
- delivery-queue/
- browser/openclaw/user-data/ (copy started separately due size; verify completion before merge)

## Intentionally skipped
- /Volumes/Samsung USB/Mac/original Hagios/OpenClaw/openclaw (app/source/UI code; out of scope)
- /Volumes/Samsung USB/Mac/original Hagios/.openclaw (mirrored non-personal/shared state tree; skipped to avoid duplicate/conflicting import)
- logs/, media/, memory/main.sqlite, sandboxes/, canvas/, exec-approvals.json, gateway.cmd, update-check.json (kept scope tight; review manually if needed)

## Next manual checks
1. Review staged .env and openclaw.json* before merging any secrets, URLs, plugin creds, or model config.
2. Diff staged agents/, subagents/, devices/, identity/, cron/, and delivery-queue/ against current Hagios 1 state before replacing anything.
3. Verify whether `state/import-from-haggis-original/personal-state/browser/openclaw/user-data` finished copying; merge selectively only if browser session continuity is actually needed.
4. Smoke-test the imported custom skills; for `parakeet-local-stt`, recreate/install a local Mac-native environment instead of reusing the excluded Windows `.venv`.
5. If extra continuity is needed later, inspect skipped memory/main.sqlite and media/inbound in the source, but only import deliberately.

## Resume note
If migration continues later, start from:
- /Users/hagios/Documents/Hagios 1/workspace/TRANSFER-MANIFEST-haggis-original.md
- /Users/hagios/Documents/Hagios 1/state/import-from-haggis-original/
No source files were modified.

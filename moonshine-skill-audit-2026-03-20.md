# Moonshine / custom voice-to-text audit (2026-03-20)

## Result
- **Moonshine was not found as a live skill folder** anywhere under:
  - `/Users/hagios/Documents/Hagios 1/**`
  - `/Users/hagios/Documents/Hagios 2/**`
  - `/Volumes/Samsung USB/Mac/original Hagios/**`
- Hagios 1 **does** contain a custom local STT skill:
  - `/Users/hagios/Documents/Hagios 1/openclaw/skills/parakeet-local-stt/`
- Hagios 1 also has standard Whisper skills:
  - `/Users/hagios/Documents/Hagios 1/openclaw/skills/openai-whisper/`
  - `/Users/hagios/Documents/Hagios 1/openclaw/skills/openai-whisper-api/`

## Strong evidence Moonshine existed previously
- Imported personal state still enables it:
  - `/Users/hagios/Documents/Hagios 1/state/import-from-haggis-original/personal-state/openclaw.json`
    - `skills.entries.moonshine-local-stt.enabled = true`
- Imported session logs reference the old Windows repo and files:
  - `C:\Vibe Coding DO NOT DELETE\OpenClaw\openclaw\skills\moonshine-local-stt\SKILL.md`
  - `C:\Vibe Coding DO NOT DELETE\OpenClaw\openclaw\skills\moonshine-local-stt\scripts\moonshine-transcribe.ps1`
  - `C:\Vibe Coding DO NOT DELETE\OpenClaw\openclaw\skills\moonshine-local-stt\scripts\transcribe_wav.py`
  - `C:\Vibe Coding DO NOT DELETE\OpenClaw\openclaw\src\gateway\server-methods\moonshine.ts`
- Evidence source on this Mac:
  - `/Users/hagios/Documents/Hagios 1/state/import-from-haggis-original/personal-state/agents/main/sessions/93956cf7-9aab-40a6-86a9-a947b5be4d9f.jsonl`

## What Moonshine appears to have been
Not just a generic reference. It appears to have been a **separate custom skill folder plus a custom gateway handler/UI integration**.

Pieces referenced in imported logs:
- `skills/moonshine-local-stt/SKILL.md`
- `skills/moonshine-local-stt/scripts/moonshine-transcribe.ps1`
- `skills/moonshine-local-stt/scripts/transcribe_wav.py`
- `src/gateway/server-methods/moonshine.ts`
- gateway registrations for `moonshine.transcribe`
- UI state/calls in `ui/src/ui/app.ts`, `ui/src/ui/app-render.ts`, `ui/src/ui/app-view-state.ts`, `ui/src/ui/views/chat.ts`

## What currently exists on Hagios 1
- Custom Parakeet skill with scripts:
  - `/Users/hagios/Documents/Hagios 1/openclaw/skills/parakeet-local-stt/SKILL.md`
  - `/Users/hagios/Documents/Hagios 1/openclaw/skills/parakeet-local-stt/scripts/parakeet_hf_transcribe.py`
  - `/Users/hagios/Documents/Hagios 1/openclaw/skills/parakeet-local-stt/scripts/parakeet_transcribe.py`
  - `/Users/hagios/Documents/Hagios 1/openclaw/skills/parakeet-local-stt/scripts/parakeet-transcribe.ps1`
  - `/Users/hagios/Documents/Hagios 1/openclaw/skills/parakeet-local-stt/scripts/install-parakeet.ps1`
- Temporary copy also exists:
  - `/Users/hagios/Documents/Hagios 1/openclaw/skills/parakeet-local-stt.tmpcopy/`
- Hagios 2 does **not** contain `moonshine-local-stt` or `parakeet-local-stt` skill folders.

## Missing pieces for Moonshine-based voice-to-text on Hagios 1
Likely missing at minimum:
1. `openclaw/skills/moonshine-local-stt/` folder
2. `moonshine-transcribe.ps1`
3. `transcribe_wav.py`
4. `src/gateway/server-methods/moonshine.ts`
5. any gateway method registration for `moonshine.transcribe`
6. any Python dependency install path for `moonshine_voice`

## Copy/staging action taken
- **No file copy performed.**
- Reason: I did not find an actual source copy of `moonshine-local-stt` on Hagios 2 or the mounted flash-drive path; only evidence inside imported state/session logs.

## Safe next step
1. Recover the actual Moonshine files from the old Windows repo if available (`C:\Vibe Coding DO NOT DELETE\OpenClaw\openclaw`).
2. If unavailable, reconstruct a staged skill under Hagios 1 from imported log snippets, but it will still need the gateway handler + registrations, not just the skill folder.
3. Consider disabling stale `moonshine-local-stt` state entry until the real files are restored.

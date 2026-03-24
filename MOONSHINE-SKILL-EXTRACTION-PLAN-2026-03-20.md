# Moonshine skill extraction plan (2026-03-20)

## Verdict
Yes — the old Moonshine transcriber was **partly a skill folder** and **partly embedded in OpenClaw source**. It was **not** a standalone skill-only implementation.

## Exact source paths found on flash drive
Under:
`/Volumes/Samsung USB/Mac/original Hagios/OpenClaw/openclaw`

### Skill files
- `skills/moonshine-local-stt/SKILL.md`
- `skills/moonshine-local-stt/references/browser-integration.md`
- `skills/moonshine-local-stt/scripts/moonshine-transcribe.ps1`
- `skills/moonshine-local-stt/scripts/transcribe_wav.py`

### Gateway/source-coupled files
- `src/gateway/server-methods/moonshine.ts`
- `src/gateway/server-methods.ts`
- `src/gateway/server-methods-list.ts`

### UI/source-coupled files
- `ui/src/ui/app.ts`
- `ui/src/ui/app-render.ts`
- `ui/src/ui/app-view-state.ts`
- `ui/src/ui/views/chat.ts`

## What the embedded code does
- `src/gateway/server-methods/moonshine.ts`
  - defines gateway RPC method `moonshine.transcribe`
  - accepts `audioBase64`, `model`, `language`, `maxSeconds`
  - writes temp WAV
  - runs Python script: `skills/moonshine-local-stt/scripts/transcribe_wav.py`
  - returns transcript text to UI
- `src/gateway/server-methods.ts`
  - imports `moonshineHandlers`
  - registers them into core handlers
  - adds `moonshine.transcribe` to write-scoped methods
- `src/gateway/server-methods-list.ts`
  - exposes `moonshine.transcribe` in method list
- `ui/src/ui/app.ts`
  - browser mic capture (`getUserMedia` + 16k WAV encoding)
  - chunking / push-to-talk lifecycle
  - calls `moonshine.transcribe`
  - appends transcript into chat draft
  - model switch also multiplexes Whisper/Parakeet through same UI
- `ui/src/ui/app-render.ts`, `ui/src/ui/app-view-state.ts`, `ui/src/ui/views/chat.ts`
  - wire button/state/settings dropdown for the transcriber UI

## Minimum subset to extract later for a skill-only rebuild
### Copy mostly as-is
1. `skills/moonshine-local-stt/SKILL.md`
2. `skills/moonshine-local-stt/scripts/transcribe_wav.py`
3. maybe `skills/moonshine-local-stt/references/browser-integration.md` as design notes
4. maybe parts of `skills/moonshine-local-stt/scripts/moonshine-transcribe.ps1` for Windows/manual CLI usage only

### Rewrite (cannot remain source-coupled)
1. **Gateway RPC layer**
   - `src/gateway/server-methods/moonshine.ts`
   - registration in `src/gateway/server-methods.ts`
   - listing in `src/gateway/server-methods-list.ts`
   - For skill-only future: replace with direct tool/exec-based workflow, not custom RPC.
2. **Web UI mic integration**
   - `ui/src/ui/app.ts`
   - `ui/src/ui/app-render.ts`
   - `ui/src/ui/app-view-state.ts`
   - `ui/src/ui/views/chat.ts`
   - For skill-only future: cannot depend on built-in webchat mic button unless OpenClaw source is patched again.

## Best skill-only reconstruction target
Build a skill that works like this:
1. user provides a local audio file
2. skill runs `python <skill>/scripts/transcribe_wav.py --input <wav> --model tiny|base --language en`
3. skill returns transcript text

Optional later wrapper scripts:
- macOS/Linux shell wrapper
- PowerShell wrapper for Windows/manual use

## What to copy vs what to derive
### Copy on March 22
- `skills/moonshine-local-stt/SKILL.md`
- `skills/moonshine-local-stt/scripts/transcribe_wav.py`
- `skills/moonshine-local-stt/references/browser-integration.md`
- maybe `skills/moonshine-local-stt/scripts/moonshine-transcribe.ps1` for reference/manual mode

### Derive/rewrite on March 22
- new skill-only `SKILL.md` instructions for file-based transcription
- dependency/install notes for `moonshine_voice`
- any macOS wrapper if wanted
- no custom gateway method
- no webchat mic toggle unless source patching is intentionally reintroduced

## What cannot stay source-coupled
These old assumptions must be removed for a clean skill-only version:
- custom gateway method name `moonshine.transcribe`
- gateway handler registration
- browser/webchat mic capture path in UI
- UI state fields named around `moonshine*`
- direct client.request RPC from web UI

## Practical conclusion
The old system was a hybrid:
- **skill assets**: Python/script/docs
- **embedded OpenClaw modifications**: gateway RPC + web UI mic controls

So the answer is: **yes, the transcriber was embedded in source code, not just a standalone skill**.

## What still waits until March 22
- deciding whether to restore only a skill-only file-transcription flow, or also reintroduce mic/webchat integration
- copying the exact skill files into the new target repo/workspace
- writing new install/dependency instructions for the current environment
- testing whether `moonshine_voice` still installs/runs cleanly on the target machine
- choosing whether to keep/port the old PowerShell wrapper or replace it with a cross-platform shell/python wrapper

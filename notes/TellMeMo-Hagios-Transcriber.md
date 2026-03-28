# TellMeMo / Hagios Transcriber

_Last updated: 2026-03-28 America/Detroit_

## Mission
Run a Mac-hosted TellMeMo staging stack that your dev team can actually use, connect a custom Android APK to that stack for internal testing, and keep the Hagios Transcriber subsystem documented as a nested note.

## Relationship to Hagios 1 task system
- Main notes index: `notes/MAIN-TASKS.md`
- Task list: `memory/task-board.json`
- Source project in Hagios 2: `projects/tellmemo-app/TODO.md`
- Source deep note in Hagios 2: `projects/tellmemo-app/notes/transcriber-notes.md`

## Recovered context
- Hagios 1 previously had a task-board item for:
  - `Build transcriber pipeline for podcasts/social audio to create private business knowledge assistants`
- TellMeMo work already recovered in Hagios 2 includes:
  - Mac-hosted staging deployment files
  - Android scaffold + debug APK artifacts
  - build-time config path for a custom API base URL
- Current shell blockers last seen:
  - `flutter` not on PATH
  - `docker` not on PATH

## Core assumptions
- Do not assume the APK will ask for an IP/server URL.
- Prefer a custom APK pointed at a staging HTTPS host.
- Best likely access path is Cloudflare Tunnel first, then Tailscale, then direct public exposure only if necessary.
- Parent app deployment planning belongs with TellMeMo; subsystem-specific transcription planning belongs here.

## Specific todo list

### T1 — Confirm transcription dependency path
Status: open
- inspect backend config/env usage for transcription provider keys and URLs
- identify whether self-hosted transcription is already supported
- document expected request/response shape if found

### T2 — Define Mac-as-server transcription plan
Status: open
- choose Cloudflare Tunnel / Tailscale / direct public model
- map external hostname to backend/reverse-proxy path
- decide whether the transcriber runs in Docker on the Mac or stays external

### T3 — Validate long-audio operational risks
Status: open
- note Mac sleep/App Nap requirements
- note Docker resource requirements
- note upload/websocket/proxy timeout risks
- note model caching / persistent volume needs if local transcription is used

### T4 — Confirm Android-to-server contract
Status: open
- verify build-time `API_BASE_URL` path in Flutter app
- verify HTTPS requirement
- verify microphone/upload/transcription flow assumptions

### T5 — Keep resume checklist current
Status: active
- append confirmed provider/runtime details after each meaningful step
- append exact commands/paths after each meaningful step
- keep this file resumable without rereading whole chats

## Short VS Code task pack
```bash
cd "/Users/hagios/Documents/Hagios 2/workspace/projects/tellmemo-app"
find backend -maxdepth 3 -type f | sort | grep -Ei 'env|config|settings|transcrib|whisper|assembly|audio|worker|queue'
```

If ripgrep exists:

```bash
cd "/Users/hagios/Documents/Hagios 2/workspace/projects/tellmemo-app"
rg -n -i 'transcrib|whisper|assemblyai|audio|speech|faster-whisper|deepgram|openai|queue|worker' backend .env* docker-compose* infra lib
```

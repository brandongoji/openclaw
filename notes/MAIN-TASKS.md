# Main Tasks

_Last updated: 2026-03-29 America/Detroit_

## Project: TellMeMo / Hagios Transcriber

- Mission: Run TellMeMo on Brandon's Mac as a reachable staging server and connect a custom Android APK to it for internal testing, with a dedicated transcriber subsystem plan.
- Status: active
- Current phase: Local transcriber architecture pivot (Whisper + speaker recognition + BYOK)
- Next action: re-run one real TellMeMo emulator login/signup now that the origin-path failure mode is documented and the launcher preflight warns when Docker/origin is down; if auth still fails after `/api/v1/healthz` is healthy, capture backend/auth logs before resuming the local Whisper + diarization pivot.
- Files:
  - `notes/TellMeMo-Hagios-Transcriber.md`
  - `memory/task-board.json`

## Notes

- This board is intentionally brief. Deep project detail lives in linked project notes and task lists.
- This TellMeMo item was handed over from Hagios 2 into Hagios 1 so it is resumable from files.

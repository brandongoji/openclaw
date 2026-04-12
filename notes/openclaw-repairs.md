# OpenClaw Repairs

## 2026-04-09 - Control UI root path 404 ("Not Found")

### Root cause

- Gateway was healthy on `127.0.0.1:18789`, but Control UI was mounted at `basePath: "/ui"` in H1 config.
- Result: requesting `http://127.0.0.1:18789/` returned plain `404 Not Found` by design, while `http://127.0.0.1:18789/ui` redirected to UI (`/ui/`).
- This looked like a gateway failure even though the listener/process were up.

### Repair

- Verified H1 route behavior:
  - `GET /` -> plain `404 Not Found`
  - `GET /ui` -> control-ui route (canonical entry)
- Tried `basePath: "/"` as a prevention attempt, but H1 still returned 404 and the route was not served correctly.
- Final stable config: keep `gateway.controlUi.basePath = "/ui"` and use `/ui` as the dashboard path.

### Verification

- `curl -i http://127.0.0.1:18789/` returns `404 Not Found` (expected with `/ui` mount).
- In some restart windows, `GET /` may also hang/timeout briefly before returning.
- `curl -i http://127.0.0.1:18789/ui` serves control-ui path (canonical URL).
- Browser should use `http://127.0.0.1:18789/ui` (or `/ui/`).

### Practical takeaway

- If dashboard shows plain `Not Found` at `:18789`, first try `:18789/ui`.
- This symptom is usually route/basePath mismatch, not a dead gateway process.

### 2026-04-09 update - recurring `/ui/` `Not Found` fixed

- New root cause found for the repeated `/ui/` 404:
  - `gateway.controlUi.root` had been set explicitly.
  - In that mode, OpenClaw enables stricter file checks and rejected hardlinked Control UI assets.
  - H1 bundled UI files were hardlinked (`index.html` link count > 1), so `/ui` still redirected but `/ui/` and `/ui/index.html` fell through to `404 Not Found`.
- Repair applied:
  - removed `gateway.controlUi.root` from `/Users/hagios/Documents/Hagios 1/state/openclaw.json`
  - kept `gateway.controlUi.basePath = "/ui"`
  - restarted `ai.hagios.1`
- Verification:
  - `GET /health` => `200`
  - `GET /ui/` => `200` (Control UI HTML served)
  - `GET /ui/index.html` => `200`

## 2026-04-08 - openclaw-control-ui

### Model dropdown likely indirect repair

- No confirmed dropdown-specific code patch was applied.
- The model dropdown may have started working again as a side effect of surrounding repairs.
- Plausible contributing repairs:
  - fixed invalid streaming config shape in both instances
  - cleaned up and restarted gateway paths / relaunch flow
  - corrected per-instance gateway and token routing
  - removed a restrictive `agents.defaults.models` allowlist in Hagios 1 that had narrowed the visible catalog to 6 models
- Practical takeaway: if the model dropdown breaks again, inspect both the gateway/runtime state and any restrictive model allowlist before assuming the dropdown component itself is broken.

### Control UI / local dashboard repair trail

- Confirmed the earlier `openclaw not found` failure was not reproducible in the current shell once `which openclaw` and `openclaw status` succeeded.
- Found and repaired a real Hagios 1 vs Hagios 2 LaunchAgent/config mismatch:
  - CLI config: `/Users/hagios/Documents/Hagios 1/state/openclaw.json`
  - old service config: `/Users/hagios/Documents/Hagios 2/state/openclaw.json`
- Reinstalled the gateway service so CLI and service pointed to Hagios 1 again.
- Remaining issue after that repair: stale gateway process/port ownership confusion could still leave an old listener serving `404 Not Found` instead of the expected Control UI route.
- Practical takeaway: if the dashboard still 404s after a config repair, verify the live listener PID actually matches the current gateway runtime.

## 2026-04-08 - MiniMax coding token setup (H1)

### Goal

- Configure MiniMax as the active coding model in H1 OpenClaw using the provided token (token intentionally redacted in notes).

### What worked (final successful configuration)

- Verified OpenClaw config path and applied MiniMax global API settings in H1 config:
  - `models.providers.minimax.baseUrl = https://api.minimax.io/v1`
  - `models.providers.minimax.api = openai-completions`
  - `models.providers.minimax.apiKey = <set>`
  - `auth.profiles["minimax-portal:default"].mode = api_key`
- Set default model stack:
  - primary: `minimax/MiniMax-M2.7`
  - fallback: `minimax/MiniMax-M2.7-highspeed`
- Validated with `openclaw config validate` (passed).
- Verified runtime health with `openclaw health` and `openclaw status`.

### Issues encountered

- `openclaw configure` / `openclaw onboard` interactive TUI had redraw/input issues in terminal, making wizard completion unreliable.
- Initial auth mode was set as `api` (invalid); OpenClaw required `api_key`.
- Early chat failures mixed two root causes:
  - Docker daemon not running (`Cannot connect to docker.sock`) while sandbox mode required Docker.
  - OpenAI fallback token refresh failure (401) when fallback still pointed to `openai-codex/gpt-5.4`.
- Agent policy/workspace mismatches caused tool failures even after model auth was fixed:
  - active session stuck on `agent:pals:main`
  - `pals` initially denied `exec`/`fs`/`memory` and had restrictive sandbox settings
  - default workspace pointed at `~/.openclaw/workspace` instead of H1 workspace.
- Heartbeat noise in private chat:
  - periodic injected HEARTBEAT prompts
  - `api_limit_heartbeat_check.py` crashed on changed `openclaw status --usage --json` shape (`windows` missing, provider error present)
  - noisy `System (untrusted) ... Exec completed ...` messages cluttered conversation.

### Fixes applied

- Started Docker when sandbox-backed runs needed it.
- Removed OpenAI dependency from fallback path (switched fallback to MiniMax highspeed).
- Split private/public agents cleanly:
  - `claw` (private): host mode for trusted private workflow, workspace bound to H1
  - `pals` (public): locked down (sandboxed, `exec/process/fs/memory` denied)
- Updated bindings so private context routes to `claw`; public channels remain on `pals`.
- Corrected workspace to `/Users/hagios/Documents/Hagios 1/workspace` for H1 workflows.
- Repaired heartbeat checker script to be resilient to missing usage windows/provider errors and suppress repeat spam alerts.
- Disabled exec completion notification noise in config:
  - `tools.exec.notifyOnExit = false`
  - `tools.exec.notifyOnExitEmptySuccess = false`

### Verification checkpoints

- `openclaw config validate` returned valid.
- `openclaw health` showed `claw` active/default session path.
- MiniMax responses and tool calls succeeded in `agent:claw:main`.
- Heartbeat script no longer hard-crashes on provider window parse mismatch; now handles source error gracefully.

### Current caveat

- `openclaw status --usage --json` currently reports MiniMax usage provider error (`cookie is missing, log in again`), so 5h/weekly usage windows are unavailable until provider/session auth is refreshed.

## 2026-04-09 - Control UI blank screen after microphone repair patch

### Symptom

- Control UI at `http://127.0.0.1:18789/ui/` returned HTTP 200 for HTML but displayed a blank screen.
- Gateway and all assets (JS/CSS) returned 200 individually, ruling out 404s.
- Browser DevTools console showed no obvious errors.

### Root cause

- During a microphone permission repair/patch applied via the gateway tool, the Control UI bundle (`dist/control-ui/assets/index-Dts6VHgr.js`) was modified/overwritten at `21:50`.
- The bundle appeared to be corrupted or incompatible after the patch, causing the UI to fail to render.
- Log showed: `gateway tool: restart requested (delayMs=default, reason=Reload patched Control UI microphone bundle so the mic permission fix is served)`

### Repair

- Restored clean Control UI assets from checkpoint backup:
  - Source: `/Users/hagios/Documents/Hagios 1/openclaw_checkpoint_20260322_105131/dist/control-ui/`
  - Target: `/Users/hagios/Documents/Hagios 1/runtime/node-v22.22.1-darwin-arm64/lib/node_modules/openclaw/dist/control-ui/`
- Copied all files recursively with `cp -r`
- Restarted the gateway

### Verification

- `curl http://127.0.0.1:18789/health` => `{"ok":true,"status":"live"}`
- `curl http://127.0.0.1:18789/ui/` => HTML served, assets accessible
- Browser displayed Control UI correctly after refresh

### Practical takeaway

- If Control UI goes blank after a gateway tool patch/restart, check if bundled UI assets were modified.
- Restore from checkpoint backup or reinstall openclaw npm package.
- Hard refresh (`Cmd+Shift+R`) may still be needed after restore.

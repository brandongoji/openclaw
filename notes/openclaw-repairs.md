# OpenClaw Repairs

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

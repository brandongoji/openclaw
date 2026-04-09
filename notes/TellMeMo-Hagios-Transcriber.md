# TellMeMo emulator microphone + network notes

## Required launcher

Use:

```bash
~/bin/run-tellmemo-avd.sh
```

This guarantees `tellmemo-avd` starts with:

- `-allow-host-audio`

Without that flag, the Android emulator records silence/zeroed input even though the app thinks recording started.

## If TellMeMo still hears nothing

Check macOS microphone permission:

- System Settings → Privacy & Security → Microphone
- Allow microphone access for:
  - Android Emulator
  - and, if present, QEMU / `qemu-system-aarch64`

Then fully relaunch the emulator with:

```bash
~/bin/run-tellmemo-avd.sh
```

## If TellMeMo says network/login failed

Check the origin before blaming emulator Wi-Fi:

```bash
curl -sS http://localhost:8000/api/v1/healthz
curl -sS https://emulator.hagios.cc/api/v1/healthz
```

Interpretation:

- `localhost:8000` failing means the local TellMeMo stack is down or still warming up.
- `emulator.hagios.cc` returning Cloudflare `502` while emulator internet otherwise works means Cloudflare Tunnel is alive but the Mac origin behind it is unavailable.
- In that case, this is **not** primarily an emulator network bug.

The launcher now warns about this case and opens Docker Desktop if the Docker socket is missing.

## Verification

1. Launch emulator with the helper.
2. If the helper warns that the local backend is down, wait for Docker/TellMeMo to recover first.
3. Open TellMeMo.
4. For mic testing, start a recording and speak for 3–5 seconds.
5. Confirm the resulting upload is no longer described as `0-second audio`.
6. For network testing, confirm `https://emulator.hagios.cc/api/v1/healthz` returns JSON and login/signup no longer throws a generic network error.

## Known findings

- App-level `RECORD_AUDIO` permission was granted.
- TellMeMo recording + upload pipeline starts and stops correctly.
- Empty transcription after a successful upload points to host audio not reaching the emulator.
- Missing `-allow-host-audio` was one cause and is now handled by the launcher helper.
- If the issue persists after using the helper, macOS mic permission for the emulator process is the next likely blocker.
- Separate network finding (2026-04-04): the flaky/failed emulator path was caused by the local TellMeMo origin being unavailable (`localhost:80` / `localhost:8000` down) while `cloudflared` was still running. That presents externally as Cloudflare `502` on `https://emulator.hagios.cc/...` even when general emulator internet is fine.

## Current microphone diagnosis (2026-04-04)

Observed:

- Emulator is booted and `-allow-host-audio` is active.
- Android `RECORD_AUDIO` permission is granted and foreground appops are allowed.
- TellMeMo requests audio focus normally during recording.
- The app still does not appear to access the microphone path reliably from the host.

Likely causes still worth checking:

1. macOS microphone privacy permission for Android Emulator/QEMU is still missing or stuck.
2. The emulator may be using a host audio path that is present but not mapped to the selected input device.
3. The TellMeMo app may be opening the recorder but receiving silence from the host audio bridge.
4. Another audio app or system privacy layer may be intercepting mic access.
5. The emulator may need a fresh relaunch after privacy changes so macOS re-prompts/refreshes TCC.
6. If the app can record but transcription remains empty, the issue is in host audio capture rather than Android permissions.

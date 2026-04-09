# Android Emulator fix report — 2026-04-04

## Summary

- Confirmed the Android SDK is installed at: `/Users/hagios/Library/Android/sdk`
- Confirmed the emulator is the official Google Android SDK package located at: `/Users/hagios/Library/Android/sdk/emulator/emulator`
- Repaired a nonstandard command-line tools layout that caused `sdkmanager` warnings:
  - before: `cmdline-tools/latest` and `cmdline-tools/latest-2`
  - after: canonical `cmdline-tools/latest`
  - preserved backup: `/Users/hagios/Library/Android/sdk/cmdline-tools/latest-backup-20260404-165158`
- Updated the emulator package through the official Google SDK channel using `sdkmanager`
  - before: `36.4.10.0` (build `15004761`)
  - after: `36.5.10.0` (build `15081367`)
- Existing AVDs were preserved. Existing AVD found:
  - `tellmemo-avd`
  - AVD files remain under `~/.android/avd/`

## Evidence it is the official SDK package

- `sdkmanager --list_installed` reports:
  - `emulator | 36.5.10 | Android Emulator | emulator`
  - `cmdline-tools;latest | 20.0 | Android SDK Command-line Tools (latest)`
- Emulator metadata file:
  - `/Users/hagios/Library/Android/sdk/emulator/source.properties`
  - contains:
    - `Pkg.Path=emulator`
    - `Pkg.Revision=36.5.10`
    - `Pkg.BuildId=15081367`

## What was wrong

- `sdkmanager` warned about an inconsistent package location:
  - observed package id `cmdline-tools;latest` in `/Users/hagios/Library/Android/sdk/cmdline-tools/latest-2`
  - expected canonical path `/Users/hagios/Library/Android/sdk/cmdline-tools/latest`
- This indicates a prior install/update left duplicate command-line tools directories.

## Changes made

1. Backed up the preexisting `cmdline-tools/latest` directory by renaming it to:
   - `/Users/hagios/Library/Android/sdk/cmdline-tools/latest-backup-20260404-165158`
2. Moved the packaged directory into the canonical location:
   - `/Users/hagios/Library/Android/sdk/cmdline-tools/latest`
3. Ran official update via:
   - `/Users/hagios/Library/Android/sdk/cmdline-tools/latest/bin/sdkmanager --sdk_root=/Users/hagios/Library/Android/sdk --install emulator`

## Verification

- Emulator version now:
  - `Android emulator version 36.5.10.0 (build_id 15081367)`
- `sdkmanager` no longer reports the inconsistent `latest-2` warning.
- `emulator-check accel` reports Hypervisor.Framework is available.
- A test launch against `tellmemo-avd` reached the new emulator binary successfully, but exited because the same AVD appears to already have been in use:
  - `FATAL | Running multiple emulators with the same AVD is an experimental feature. Please use -read-only flag to enable this feature.`
- This means the updated emulator binary is runnable; the test did **not** indicate a broken install.

## How to launch afterward

From Terminal:

```bash
export ANDROID_SDK_ROOT="$HOME/Library/Android/sdk"
export ANDROID_HOME="$ANDROID_SDK_ROOT"
"$ANDROID_SDK_ROOT/emulator/emulator" -list-avds
"$ANDROID_SDK_ROOT/emulator/emulator" -avd tellmemo-avd
```

If you want the tools on `PATH`:

```bash
export ANDROID_SDK_ROOT="$HOME/Library/Android/sdk"
export ANDROID_HOME="$ANDROID_SDK_ROOT"
export PATH="$ANDROID_SDK_ROOT/emulator:$ANDROID_SDK_ROOT/platform-tools:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$PATH"
```

Then you can use:

```bash
emulator -list-avds
emulator -avd tellmemo-avd
```

## Notes

- Launch test warning about software GL was due to current system memory pressure, not a package integrity problem.
- No AVDs or system images were deleted.
- If desired later, the backup directory can be removed after confirming everything works, but it is currently safe to keep.

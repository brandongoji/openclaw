# Tasks After Codex Renewal

## Top Priority

1. Create a proper git repo for the Hagios/OpenClaw skill work so changes are tracked cleanly.
2. Rebuild the custom skills as skills-first implementations, not OpenClaw core patches.
3. Set up a backup Discord presence/agent path so if Hagios 1 crashes, there is still a way to help bring Hagios back up.
4. Reduce dependence on fragile manual gateway babysitting; prefer a stable self-starting/local setup that does not randomly fall over.

## Rebuild Queue

### 1) Moonshine local STT
- Recover the old Moonshine skill files from the older OpenClaw source snapshot.
- Rebuild it as a skill-only implementation first.
- Make it cross-platform where possible: Mac, Windows, Linux.
- Do not patch OpenClaw core unless there is a very strong reason.
- Use the extraction plan:
  - `MOONSHINE-SKILL-EXTRACTION-PLAN-2026-03-20.md`

### 2) Parakeet local STT
- Convert it into a proper installable skill.
- Make the runtime and wrappers cross-platform.
- Keep core logic platform-neutral where possible.

### 3) Reminder / task visibility
- Keep an always-readable task list in workspace files.
- Prefer skill-driven workflows over source modifications.

## Design Rules
- Skill-first architecture.
- Cross-platform by default when reasonably possible.
- Avoid interfering with upstream OpenClaw developers.
- Treat this as vibe coding for skills.

## Hagios 1 Status Notes
- Discord was restored on Hagios 1.
- Old personal memories were archived under `old-memories`.
- Import notes and transfer manifests were written into the Hagios 1 workspace.

## Useful Resume Files
- `TRANSFER-RESUME-haggis-original.txt`
- `TRANSFER-MANIFEST-haggis-original.md`
- `moonshine-skill-audit-2026-03-20.md`
- `MOONSHINE-SKILL-EXTRACTION-PLAN-2026-03-20.md`
- `DISCORD-SETUP-STATUS-2026-03-20.txt`
- `DISCORD-RUNTIME-RESUME-2026-03-20-0542.txt`

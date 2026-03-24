---
name: discord-channel-boundaries
description: Enforce and audit Discord trust boundaries for this workspace. Use when changing or reviewing which Discord servers/channels are control-enabled vs chat-only, when binding channels to agents, when restricting exec approvals, or when hardening Discord/OpenClaw policy after accidental overexposure.
---

# Discord Channel Boundaries

Treat Discord channel trust as a two-layer system:

1. **OpenClaw config layer** — routing, agent bindings, tool policy, exec approvals.
2. **Discord permission layer** — server/channel permissions such as Use Application Commands, Use External Apps, bot role permissions, and per-channel overrides.

Do not assume one layer replaces the other.

## Required local policy for this workspace

### Control channel

- Guild `1473419068743618764`
- Channel `1473419070761337067`
- This is the private control channel.
- Bind it to agent `main`.
- Discord exec approvals should only be surfaced for `main` here.

### Chat-only server/channels

- Guild `1473450991109144598` (Hagios pals)
- Channels:
  - `1473450991847211226` (`general`)
  - `1473451920130703582` (`guest-chat`)
- Bind these to agent `pals`.
- `pals` must remain chat-only.
- Deny at minimum:
  - filesystem tools
  - exec/process
  - browser/canvas
  - memory/session tools
  - Discord administrative channel/category actions

## Rules

- Never broaden Discord control access in Hagios pals without explicit confirmation.
- When changing Discord control policy, update both the live config and the workspace notes.
- If the user says a server/channel is chat-only, prefer a **restricted agent binding** over relying on social instructions alone.
- If exec approvals are enabled for Discord, restrict them so chat-only agents/channels cannot surface approval prompts.
- If there is ambiguity about whether the issue is OpenClaw-side or Discord-side, check OpenClaw config first; Discord Developer Portal is not the same thing as server/channel permission settings.

## Minimal checklist

1. Verify `bindings` route control channels to `main` and chat-only channels to `pals`.
2. Verify `pals` tool policy remains restrictive.
3. Verify Discord exec approvals are filtered to `main`.
4. Update `TOOLS.md` if IDs or channel purposes changed.
5. If the user wants defense in depth, also harden Discord server/channel permissions in the normal Discord UI.

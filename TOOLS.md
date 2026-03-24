# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

### Discord

- `1473419068743618764` → current private control server
  - Control-enabled channel:
    - `1473419070761337067`
  - Bound agent in control channel: `main`
  - In-channel Discord exec approvals should be limited to `main` / this control path.
- `1473450991109144598` → Hagios pals
  - Chat-only channels:
    - `1473450991847211226` (`general`)
    - `1473451920130703582` (`guest-chat`)
  - Bound agent in those channels: `pals`
  - `pals` must stay restricted: no filesystem access, no command execution, no browser/canvas, no memory/session tools, no Discord admin channel actions.
- Guardrail: do not rely on notes alone. Keep this enforced in OpenClaw config and in `skills/discord-channel-boundaries/SKILL.md`.
- Hard lock requirement: Discord exec approvals must stay filtered to agent `main` and session `agent:main:discord:channel:1473419070761337067` only.
- Hard lock requirement: `pals` must keep an explicit denylist covering fs/exec/process/browser/canvas/memory/sessions plus Discord admin/moderation actions (`message.delete`, `message.edit`, `message.pin`, `message.unpin`, `message.channel-*`, `message.category-*`, `message.permissions`, `message.voice-status`, `message.event-*`).
- If these servers get real human-friendly names later, update this section immediately so IDs are never ambiguous again.

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

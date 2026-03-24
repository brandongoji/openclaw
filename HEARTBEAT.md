# HEARTBEAT.md

- Check Codex weekly usage with:
  `python3 "/Users/hagios/Documents/Hagios 1/workspace/scripts/codex_usage_heartbeat_check.py"`
- If the command prints nothing, do nothing and continue with the rest of the heartbeat.
- If it prints a Codex weekly usage alert, send that same alert text in both places:
  - current in-session chat reply
  - Discord via `message.send` with `channel="discord"` and `target="1473419070761337067"`
- Do not send duplicate reminders inside the same 10% weekly remaining bucket. The script state file handles this.
- Treat a higher weekly remaining bucket as a quiet weekly reset; update state without alerting.
- Popup + sound note: no workspace-level OpenClaw setting for desktop popup/sound alerts was found in the local config/CLI surface checked here. Nearest supported alternative is the Discord message above, which can use Discord's own notifications, plus the normal in-session chat alert.

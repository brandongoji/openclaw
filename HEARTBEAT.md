# HEARTBEAT.md

- Check API usage with:
  `python3 "/Users/hagios/Documents/Hagios 1/workspace/scripts/api_limit_heartbeat_check.py"`
- This checks both OpenClaw usage windows for the Codex provider:
  - 5-hour window
  - weekly window
- If the command prints nothing, do nothing and continue with the rest of the heartbeat.
- If it prints an API limit alert, send that same alert text in both places:
  - current in-session chat reply
  - Discord via `message.send` with `channel="discord"` and `target="1473419070761337067"`
- The checker suppresses duplicates deterministically per window using persistent state in:
  `/Users/hagios/Documents/Hagios 1/workspace/memory/api-limit-alert-by-hagios-state.json`
- Alert rules per window:
  - each new 10% used crossing
  - warning at 25% remaining
  - red alert at 10% remaining
- Treat higher remaining headroom as a quiet reset for that window; update state without alerting.
- Popup + sound note: no workspace-level OpenClaw setting for desktop popup/sound alerts was found in the local config/CLI surface checked here. Nearest supported alternative is the Discord message above, which can use Discord's own notifications, plus the normal in-session chat alert.

## Optional: Discord response-delivery check

- Check for likely missed/stuck assistant replies with:
  `python3 "/Users/hagios/Documents/Hagios 1/workspace/scripts/response_delivery_heartbeat_check.py"`
- This inspects the local OpenClaw session transcript for the primary Discord control channel and looks for a recent user message that never got a later assistant final answer.
- Default thresholds:
  - recent lookback: 45 minutes
  - response timeout: 6 minutes
  - running-session grace: 12 minutes
- If the command prints nothing, do nothing and continue with the rest of the heartbeat.
- If it prints a response-delivery alert, send that same alert text in both places:
  - current in-session chat reply
  - Discord via `message.send` with `channel="discord"` and `target="1473419070761337067"`
- The checker suppresses duplicates deterministically using persistent state in:
  `/Users/hagios/Documents/Hagios 1/workspace/memory/response-delivery-monitor-state.json`
- Important limitation: this is a best-effort local transcript heuristic, not a guaranteed Discord delivery receipt.

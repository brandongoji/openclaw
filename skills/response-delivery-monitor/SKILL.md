---
name: response-delivery-monitor-by-hagios
description: Monitor likely Discord response-delivery gaps by checking local OpenClaw session history for recent user messages that never get a later assistant final answer. Use when the user wants heartbeat-friendly reply-gap detection, cron-friendly Discord response monitoring, local alerting for stuck/failed replies, or a deterministic checker that suppresses duplicate alerts with workspace state.
---

# Response Delivery Monitor by Hagios

Monitor the primary Discord conversation for likely reply failures using only local OpenClaw session files and a deterministic state file.

## Resources

- `scripts/check_response_delivery.py` — inspect one Discord-backed session, detect a recent unanswered user message, and suppress duplicate alerts.
- `references/assumptions-and-limits.md` — read when you need the exact heuristic boundaries or limitations.
- `/Users/hagios/Documents/Hagios 1/workspace/scripts/response_delivery_heartbeat_check.py` — thin wrapper for heartbeat/cron use.

## Workflow

1. Pick the target Discord session.
2. Read the current session entry from `state/agents/main/sessions/sessions.json`.
3. Inspect the referenced JSONL transcript.
4. Find the latest Discord user message and the latest assistant final answer.
5. Alert only when a recent user message has no later assistant reply and the timeout has elapsed.
6. Reuse the same state file so the same stuck message id does not alert repeatedly.

## Defaults

- target channel id: `1473419070761337067`
- default session key pattern: `agent:main:discord:channel:<channel-id>`
- lookback window: `45` minutes
- response timeout: `6` minutes
- running-session grace: `12` minutes

## Run directly

```bash
python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/response-delivery-monitor/scripts/check_response_delivery.py"
```

Explicit channel override:

```bash
python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/response-delivery-monitor/scripts/check_response_delivery.py" \
  --channel-id 1473419070761337067
```

JSON output for debugging:

```bash
python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/response-delivery-monitor/scripts/check_response_delivery.py" \
  --json
```

## State

Default state file:

```text
/Users/hagios/Documents/Hagios 1/workspace/memory/response-delivery-monitor-state.json
```

The checker records the last alerted Discord message id per session so repeated heartbeat runs stay quiet until a new missing-reply situation appears or the session recovers.

## Heartbeat integration

Use the wrapper when heartbeat should perform the check in one command:

```bash
python3 "/Users/hagios/Documents/Hagios 1/workspace/scripts/response_delivery_heartbeat_check.py"
```

If the wrapper prints nothing, do nothing.
If it prints an alert, forward that exact alert text to the current chat and to the Discord control channel.

## Tuning

Override timing when needed:

```bash
python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/response-delivery-monitor/scripts/check_response_delivery.py" \
  --response-timeout-min 10 \
  --running-grace-min 15 \
  --lookback-min 60
```

## Limitations

This is a best-effort local heuristic, not a true Discord delivery receipt.

Read `references/assumptions-and-limits.md` when you need the exact caveats.

## Quick validation

```bash
python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/response-delivery-monitor/scripts/check_response_delivery.py" --json
python3 "/Users/hagios/Documents/Hagios 1/workspace/scripts/response_delivery_heartbeat_check.py"
```

Expected behavior:
- recent unanswered Discord user message older than the threshold prints one alert
- repeated runs for the same stuck message stay quiet
- a later assistant reply clears the prior alert state quietly

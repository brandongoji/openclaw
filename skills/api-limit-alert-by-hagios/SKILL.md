---
name: api-limit-alert-by-hagios
description: Alert when OpenClaw API usage headroom drops into a new lower 10% bucket for either the 5-hour or weekly usage window, without repeating the same alert for the same window, and produce deterministic per-task Codex usage summaries from before/after snapshots. Use when the user wants periodic API/Codex usage reminders, heartbeat-friendly quota checks, cron-friendly local monitoring that reads `openclaw status --usage --json`, or a compact per-task report showing token deltas plus 5-hour/weekly usage deltas after substantial agentic work.
---

# API Limit Alert by Hagios

Monitor OpenClaw usage headroom for both the 5-hour and weekly windows with deterministic 10% bucket alerts, plus low-budget policy warnings, and emit deterministic per-task usage summaries for substantial work.

## Resources

- `scripts/check_usage_bucket.py` — evaluate one usage window at a time, suppress duplicates, and persist per-window state.
- `scripts/task_usage_tracker.py` — capture normalized before/after snapshots and summarize one task's token + usage deltas.
- `references/research-notes.md` — brief design notes kept from the original skill.
- `/Users/hagios/Documents/Hagios 1/workspace/scripts/api_limit_heartbeat_check.py` — heartbeat-friendly wrapper that reads `openclaw status --usage --json`, checks both windows, and prints alerts only when something newly crosses a threshold.

## Workflow

1. For periodic monitoring, gather usage for one window (`5h` or `weekly`) or call the heartbeat wrapper to check both.
2. Run `scripts/check_usage_bucket.py` for each window you want to track.
3. Reuse the same state file across runs.
4. Only send a user-facing reminder when the script returns an alert.
5. For substantial agentic work, treat per-task reporting as standard: capture a normalized snapshot before the task, capture another after the task, then run the summarizer and include the compact summary in your completion note.

## Window rules

Each window is tracked independently.

For both the `5h` and `weekly` windows:
- Alert on each newly crossed 10% used boundary.
- Warn once when remaining budget drops to `25%` or below.
- Raise a red alert once when remaining budget drops to `10%` or below.
- Reset quietly when headroom increases again, so a new window can alert later without duplicates.

For the `weekly` window specifically:
- Alert once at `20%` remaining as the low-budget threshold.
- Alert once at `15%` remaining as the token-saving threshold.
- At `15%`, use explicit policy language: `chat/planning only, hold off on heavy tasks until weekly renew`.

## Run the checker directly

### Explicit remaining percentage

```bash
python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/api-limit-alert-by-hagios/scripts/check_usage_bucket.py" \
  --window-label 5h \
  --remaining-percent 87
```

### Parse raw status text

```bash
printf '%s\n' '5-hour remaining: 63%' | \
python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/api-limit-alert-by-hagios/scripts/check_usage_bucket.py" \
  --window-label 5h
```

If the raw status text reports **used** percentage instead of **remaining**, set the mode explicitly:

```bash
printf '%s\n' 'Weekly usage: 37%' | \
python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/api-limit-alert-by-hagios/scripts/check_usage_bucket.py" \
  --window-label weekly \
  --window-percent-mode used
```

## State

Default state file:

```text
/Users/hagios/Documents/Hagios 1/workspace/memory/api-limit-alert-by-hagios-state.json
```

The state file stores independent records under `windows.5h` and `windows.weekly` so duplicate suppression stays deterministic per window.

## Per-task tracker

Use the tracker when the user wants to know how much a concrete task cost, especially after creating/editing a skill, running a coding sub-agent, or doing any substantial multi-step task.

### Capture a normalized snapshot before the task

```bash
python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/api-limit-alert-by-hagios/scripts/task_usage_tracker.py" \
  snapshot \
  --status-file /tmp/status-before.json \
  --provider codex \
  --token-file /tmp/tokens-before.json \
  --pretty > /tmp/task-usage-before.json
```

### Capture a normalized snapshot after the task

```bash
python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/api-limit-alert-by-hagios/scripts/task_usage_tracker.py" \
  snapshot \
  --status-file /tmp/status-after.json \
  --provider codex \
  --token-file /tmp/tokens-after.json \
  --pretty > /tmp/task-usage-after.json
```

### Emit the compact summary

```bash
python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/api-limit-alert-by-hagios/scripts/task_usage_tracker.py" \
  summarize \
  --before /tmp/task-usage-before.json \
  --after /tmp/task-usage-after.json \
  --task "create skill: api-limit-alert-by-hagios" \
  --format text
```

### Snapshot notes

- The tracker prefers normalized window data from `openclaw status --usage --json`.
- The optional token JSON is for deterministic task/session counters. Pass it when you have a reliable source; otherwise the tracker will attempt to extract token counters from the status payload.
- The text summary includes task label, timestamp, token deltas, 5-hour delta, weekly delta, remaining-before/after, and the low-budget policy line when weekly remaining is at or below 20% or 15%.
- For sub-agent workflows, the clean pattern is: requester saves raw pre-status JSON, sub-agent saves raw post-status JSON, then either side runs `snapshot` + `summarize`.

## Heartbeat integration

Use the wrapper when heartbeat should check both OpenClaw usage windows in one shot:

```bash
python3 "/Users/hagios/Documents/Hagios 1/workspace/scripts/api_limit_heartbeat_check.py"
```

If the wrapper prints nothing, do nothing.
If it prints alert text, forward that exact text to the current chat and to the Discord control channel.

## Cron-friendly integration

Use cron when the user wants exact periodic timing.

Example pattern:
- run `python3 "/Users/hagios/Documents/Hagios 1/workspace/scripts/api_limit_heartbeat_check.py"`
- forward output only when the command prints alerts

Do not hardcode secrets, tokens, or webhooks into the skill.

## Example alert

```text
API Limit Alert by Hagios — weekly window: crossed 40% used (remaining: 58.0%, previous alert bucket: 60% remaining).
```

## Example per-task summary

```text
Task usage — create skill: api-limit-alert-by-hagios
Timestamp: 2026-03-25T15:05:42+00:00
Tokens: input 2,400 | output 900 | total 3,300
5h usage: Δused 1.2% | remaining 63.4% → 62.2%
Weekly usage: Δused 0.8% | remaining 18.1% → 17.3%
Low-budget policy: weekly remaining is at or below 20%; avoid unnecessary heavy work and batch follow-ups carefully.
```

## Quick validation steps

```bash
STATE="/tmp/api-limit-alert-by-hagios-test.json"
SCRIPT="/Users/hagios/Documents/Hagios 1/workspace/skills/api-limit-alert-by-hagios/scripts/check_usage_bucket.py"

python3 "$SCRIPT" --state-file "$STATE" --window-label weekly --remaining-percent 95
python3 "$SCRIPT" --state-file "$STATE" --window-label weekly --remaining-percent 89
python3 "$SCRIPT" --state-file "$STATE" --window-label weekly --remaining-percent 79
python3 "$SCRIPT" --state-file "$STATE" --window-label weekly --remaining-percent 24
python3 "$SCRIPT" --state-file "$STATE" --window-label weekly --remaining-percent 9
python3 "$SCRIPT" --state-file "$STATE" --window-label weekly --remaining-percent 98
python3 "$SCRIPT" --state-file "$STATE" --window-label 5h --remaining-percent 49
```

Expected behavior:
- first weekly run seeds state quietly
- 89 alerts for the 80% remaining bucket / 10% used crossing
- 79 alerts for the 70% remaining bucket / 20% used crossing
- 24 adds the 25% warning once
- 9 adds the 10% red alert once
- 98 resets the weekly window quietly
- the `5h` window uses the same state file without interfering with weekly history

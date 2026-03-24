---
name: codex-usage-bucket-alert
description: Alert when weekly Codex usage headroom drops into a new lower 10% bucket (100, 90, 80 ... 0) without repeating the same alert. Use when the user wants periodic Codex usage reminders, a heartbeat-friendly quota check, or a cron-friendly local monitor that parses status text or accepts an explicit remaining percentage and persists state in the workspace.
---

# Codex Usage Bucket Alert

Monitor weekly Codex headroom with a deterministic 10% bucket rule and a persistent local state file. Prefer this skill when the user wants low-noise reminders instead of constant usage spam.

## Resources

- `scripts/check_usage_bucket.py` — parse weekly usage input, compute the current 10% bucket, suppress duplicate alerts, and persist state.
- `references/research-notes.md` — brief external feature ideas reviewed during design.

## Workflow

1. Gather the current weekly usage value.
   - Prefer a direct remaining percentage if it is already available.
   - Otherwise pass raw status text that contains a weekly percentage.
2. Run `scripts/check_usage_bucket.py`.
3. Only send a user-facing reminder when the script returns an alert.
4. Reuse the same state file across runs so bucket crossings are remembered.

## Run the checker

### Direct test with an explicit remaining percentage

```bash
python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/codex-usage-bucket-alert/scripts/check_usage_bucket.py" \
  --remaining-percent 87
```

Expected behavior:
- First run seeds state at `80%` and stays quiet.
- Later runs at `79` or `72` alert once per newly crossed bucket.
- Repeated runs inside the same bucket do nothing.
- A higher value after weekly reset updates state quietly.

### Parse raw status text

If the main agent has raw status output, pass it directly:

```bash
printf '%s\n' 'Weekly remaining: 63%' | \
python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/codex-usage-bucket-alert/scripts/check_usage_bucket.py"
```

If the raw status text reports **used** percentage instead of **remaining**, set the mode explicitly:

```bash
printf '%s\n' 'Weekly usage: 37%' | \
python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/codex-usage-bucket-alert/scripts/check_usage_bucket.py" \
  --weekly-percent-mode used
```

## State

Default state file:

```text
/Users/hagios/Documents/Hagios 1/workspace/memory/codex-usage-bucket-alert-state.json
```

Rules:
- On first run, initialize state without alert unless `--first-run-alert` is set.
- Alert only when `current_bucket < last_alerted_bucket`.
- Do not alert again inside the same bucket.
- If the bucket moves upward, treat that as a reset/new window and update state silently.

## Heartbeat integration

Use heartbeat when the check can be batched with other lightweight periodic checks.

Add a short item to `HEARTBEAT.md` such as:

```markdown
- Check Codex weekly usage. If current status text or remaining percent is available, run:
  python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/codex-usage-bucket-alert/scripts/check_usage_bucket.py" --remaining-percent <VALUE>
  Only message the user if the script returns an alert.
```

If the environment exposes raw session status text during heartbeat, pipe that text into the script instead of `<VALUE>`.

## Cron-friendly integration

Use cron when the user wants exact periodic timing.

Example cron entry for every 30 minutes **if another command or wrapper can supply the weekly remaining percentage**:

```cron
*/30 * * * * printf '%s\n' 'Weekly remaining: 63%' | python3 "/Users/hagios/Documents/Hagios 1/workspace/skills/codex-usage-bucket-alert/scripts/check_usage_bucket.py"
```

Practical pattern:
- Step 1: obtain weekly remaining percent or raw status text from the local environment.
- Step 2: feed that value/text into `check_usage_bucket.py`.
- Step 3: only forward output when it is an alert.

Do not hardcode secrets, tokens, or webhooks into the skill.

## Example alert

```text
Codex weekly usage alert: remaining budget dropped into the 60% bucket (current: 63.0%, previous alert bucket: 70%).
```

## Quick validation steps

```bash
STATE="/tmp/codex-usage-bucket-alert-test.json"
SCRIPT="/Users/hagios/Documents/Hagios 1/workspace/skills/codex-usage-bucket-alert/scripts/check_usage_bucket.py"

python3 "$SCRIPT" --state-file "$STATE" --remaining-percent 95
python3 "$SCRIPT" --state-file "$STATE" --remaining-percent 91
python3 "$SCRIPT" --state-file "$STATE" --remaining-percent 89
python3 "$SCRIPT" --state-file "$STATE" --remaining-percent 88
python3 "$SCRIPT" --state-file "$STATE" --remaining-percent 79
python3 "$SCRIPT" --state-file "$STATE" --remaining-percent 98
```

Expected sequence:
- 95 → initialize at 90, no alert
- 91 → no alert
- 89 → alert for 80 bucket
- 88 → no duplicate alert
- 79 → alert for 70 bucket
- 98 → quiet reset to 90 bucket

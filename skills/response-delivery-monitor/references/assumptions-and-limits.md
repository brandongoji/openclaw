# Assumptions and limits

## What this checker uses

- `state/agents/main/sessions/sessions.json` for the current Discord session record, status, and session file path.
- The session JSONL transcript referenced by that index entry.
- A local state file at `memory/response-delivery-monitor-state.json` for duplicate suppression.

## Heuristic used

The checker raises an alert when all of these are true:

1. A recent Discord user message exists in the target session transcript.
2. No later assistant final-answer message is present after that user message.
3. The user message is older than the configured timeout.
4. The same missing-reply situation for the same Discord message id has not already been alerted.

Default timing:

- recent-window lookback: 45 minutes
- normal response timeout: 6 minutes
- running-session grace: 12 minutes

## Why this is best-effort

This does **not** call privileged Discord APIs and does **not** prove whether Discord actually rendered the outbound message.
It only checks whether local OpenClaw session history recorded an assistant final answer after a recent inbound Discord message.

That means:

- false positives are possible if the transcript is delayed or rotated
- false negatives are possible if a reply was recorded locally but Discord delivery failed afterward
- it is strongest for catching likely stuck sessions, failed runs, or missing assistant output

## Known transcript assumptions

- Discord-origin user turns include a `message_id` inside the text payload metadata.
- Assistant replies are treated as completed when the transcript contains an assistant text block with a `final_answer` text signature, or at minimum a non-empty assistant text block.
- The checker only inspects one session key at a time unless wrapped externally.

## Good use cases

- heartbeat/cron monitoring for the primary Discord control channel
- catching recent unanswered messages after a model failure or workflow stall
- low-noise local alerting without extra services or tokens

## Bad use cases

- proving end-to-end Discord delivery guarantees
- auditing every guild/channel in parallel without a higher-level wrapper
- replacing direct provider telemetry if OpenClaw later exposes explicit outbound delivery receipts

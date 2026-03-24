---
name: hagios-handoff
description: Low-token cross-instance delegation between Hagios systems, especially Hagios 1 handing work to Hagios 2 as backup/fixer. Use when the user wants Hagios 2 to investigate, compare, verify, or prepare work without changing core code; when browser/Playwright messaging would waste tokens; or when a handoff should clearly identify the sender instance.
---

# Hagios Handoff

Delegate work between Hagios instances with the smallest practical token footprint. Prefer direct session messaging over browser-driven chat UI automation.

## Default rules

- Identify yourself in the first line, e.g. `From: Hagios 1`.
- State the receiver role briefly, e.g. `To: Hagios 2 (backup fixer)`.
- Keep the request compact and structured.
- Prefer `sessions_send` to an existing target session over browser automation.
- Use `sessions_list` only to discover a target when needed; do not poll it repeatedly.
- Use browser chat handoff only as a fallback when no direct session target is available and the user still wants the handoff.
- Respect the architecture rule: do not propose custom core patches when the user wants original-source behavior.

## Handoff format

Use this template and keep it short:

```text
From: Hagios 1
To: Hagios 2
Role: backup fixer
Task: <one-sentence objective>
Constraints:
- <constraint 1>
- <constraint 2>
Deliverable:
- <what to report back>
Context:
- <only the facts needed>
```

## Workflow

1. Decide whether a handoff is actually needed.
   - If local work is cheap and safe, do it locally.
   - If the user wants Hagios 2 involved, or Hagios 1 should avoid risk, hand off.

2. Choose the lowest-token path.
   - First choice: `sessions_send` to a known Hagios 2 session.
   - Second choice: discover the Hagios 2 target with `sessions_list`, then `sessions_send`.
   - Last resort: browser/open the Hagios 2 chat URL and send a compact message.

3. Compress aggressively.
   - Remove narration, filler, and repeated background.
   - Include only objective, constraints, required output, and 2-6 critical facts.
   - Prefer bullet points over paragraphs.

4. Mark identity clearly.
   - Always begin with `From: Hagios 1` when Hagios 1 is sending.
   - If relevant, include why the receiver is being used, e.g. `Role: backup fixer`.

5. Ask for a bounded result.
   - Request a report, comparison, or yes/no decision with evidence.
   - Ask for exact file paths/lines only when that matters.

## Good handoff example

```text
From: Hagios 1
To: Hagios 2
Role: backup fixer
Task: Compare Hagios 1's attach-button chat code against Hagios 2 and upstream OpenClaw.
Constraints:
- Do not patch Hagios 1 core.
- Keep Hagios 2 untouched except for investigation.
Deliverable:
- Say whether Hagios 2 matches Hagios 1, whether upstream differs, and whether Hagios 1 should be restored to newer original source instead of custom-editing core.
Context:
- Hagios 1 uses `document.querySelector('.agent-chat__file-input')?.click()`.
- The file input is hidden.
```

## Avoid

- Long conversational setup before the actual task.
- Sending full transcripts when a 5-line summary will do.
- Browser/Playwright UI messaging when direct session tools can reach the target.
- Repeating constraints in multiple sections.

## Browser fallback

If browser fallback is unavoidable:

- Open the exact Hagios 2 chat URL the user provides.
- Send the compact handoff template, not a natural-language essay.
- Identify yourself in the first line.
- Do not browse around or gather extra UI context unless needed to complete the send.

## Success criteria

A good handoff is:

- identifiable
- short
- actionable
- constrained
- sent by the cheapest available path

# Research notes

External references reviewed for ideas only; nothing imported.

## What showed up

- A VS Code/Cursor/Windsurf extension (`Codex Rate Limit Monitor`) that shows both 5-hour and weekly usage, color-codes warnings, refreshes automatically, and offers a detailed view.
- OpenAI billing/project guidance that emphasizes threshold-based notifications and budget tracking rather than constant manual checking.
- Generic usage-monitoring writeups that recommend threshold alerts, anti-noise behavior, and multiple notification targets.

## Useful ideas worth keeping

- Use threshold buckets instead of noisy continuous updates.
- Track weekly budget separately from shorter windows.
- Persist state so the same threshold crossing is only announced once.
- Reset quietly when a new budget window begins and headroom increases again.
- Make the checker scriptable so it works from heartbeat, cron, or another wrapper.
- Prefer exact, low-noise alert messages that include both the new bucket and the current remaining percentage.

## Ideas intentionally not copied

- No external extension code.
- No downloaded skills.
- No dependence on VS Code UI or third-party services.
- No secrets, API keys, or webhooks baked into the skill.

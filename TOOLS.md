# Workspace Notes

## Discord trust boundaries

### Private control server
- Guild: `1473419068743618764`
- Channel: `1473419070761337067`
- Bound agent: `main`
- Purpose: private control + exec approval surface

### Hagios Pals server
- Guild: `1473450991109144598`
- Channels:
  - `1473450991847211226` (`general`)
  - `1473451920130703582` (`guest-chat`)
- Bound agent: `pals`
- Purpose: chat-only + web search only
- Explicitly denied: filesystem tools, exec/process, browser/canvas, gateway/cron/nodes, memory/session tools, proactive messaging tools

### Exec approvals
- Discord exec approvals are enabled only for agent `main`
- Discord exec approvals are filtered to channel `1473419070761337067`
- Hagios Pals must never surface Discord exec approvals

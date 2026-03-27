---
summary: "Use OpenAI via API keys or Codex subscription in OpenClaw"
read_when:
  - You want to use OpenAI models in OpenClaw
  - You want Codex subscription auth instead of API keys
title: "OpenAI"
---

# OpenAI

OpenAI provides developer APIs for GPT models. Codex supports **ChatGPT sign-in** for subscription
access or **API key** sign-in for usage-based access. Codex cloud requires ChatGPT sign-in.

Key distinction:

- `openai/*` uses the OpenAI Platform API (API key, usage based billing).
- `openai-codex/*` uses Codex OAuth (ChatGPT sign-in, subscription access when your account has it).

## Option A: OpenAI API key (OpenAI Platform)

**Best for:** direct API access and usage-based billing.
Get your API key from the OpenAI dashboard.

### CLI setup

```bash
openclaw onboard --auth-choice openai-api-key
# or non-interactive
openclaw onboard --openai-api-key "$OPENAI_API_KEY"
```

### Config snippet

```json5
{
  env: { OPENAI_API_KEY: "sk-..." },
  agents: { defaults: { model: { primary: "openai/gpt-5.1-codex" } } },
}
```

If you see `HTTP 429` errors like `insufficient_quota` while using `openai/*`, that is almost
always an API key billing or credits issue. Switching to `openai-codex/*` does not change API key
quota behavior.

## Option B: OpenAI Code (Codex) subscription

**Best for:** using ChatGPT/Codex subscription access instead of an API key.
Codex cloud requires ChatGPT sign-in, while the Codex CLI supports ChatGPT or API key sign-in.

### CLI setup (Codex OAuth)

```bash
# Run Codex OAuth in the wizard
openclaw onboard --auth-choice openai-codex

# Or run OAuth directly
openclaw models auth login --provider openai-codex
```

### Minimal setup (recommended)

Run these commands on the gateway host:

```bash
openclaw models auth login --provider openai-codex
openclaw models set openai-codex/gpt-5.3-codex
openclaw models status
```

In `openclaw models status`, you should see an OAuth profile for `openai-codex` in an `ok` state.

### Config snippet (Codex subscription)

```json5
{
  agents: { defaults: { model: { primary: "openai-codex/gpt-5.3-codex" } } },
}
```

## Avoiding rate limits (429)

You cannot bypass upstream rate limits from OpenClaw. What you can do is avoid triggering them
constantly:

- Keep concurrency low:

```json5
{
  agents: {
    defaults: {
      maxConcurrent: 1,
      subagents: { maxConcurrent: 1 },
    },
  },
}
```

- Keep `agents.defaults.model.fallbacks` minimal so one message does not fan out into multiple
  provider calls.
- If you still see `HTTP 429` all day on `openai-codex/*`, it is usually upstream account-level
  throttling (burst or per-window). The fixes are to wait for the window, reduce concurrency, or
  upgrade or enable higher limits on the provider side.

## Notes

- Model refs always use `provider/model` (see [/concepts/models](/concepts/models)).
- Auth details + reuse rules are in [/concepts/oauth](/concepts/oauth).

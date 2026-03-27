#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Tuple

DEFAULT_STATE_DIR = Path('/Users/hagios/Documents/Hagios 1/state')
DEFAULT_AGENT_ID = 'main'


def fmt_int(value: int) -> str:
    return f"{value:,}"


def fmt_money(value: float) -> str:
    return f"${value:,.4f}"


@dataclass
class UsageTotals:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read: int = 0
    cache_write: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0

    def add(self, usage: dict[str, Any]) -> None:
        self.calls += 1
        self.input_tokens += int(usage.get('input') or usage.get('promptTokens') or 0)
        self.output_tokens += int(usage.get('output') or usage.get('completionTokens') or 0)
        self.cache_read += int(usage.get('cacheRead') or 0)
        self.cache_write += int(usage.get('cacheWrite') or 0)
        self.total_tokens += int(usage.get('totalTokens') or (usage.get('input') or 0) + (usage.get('output') or 0))
        cost = usage.get('cost') or {}
        if isinstance(cost, dict):
            self.total_cost += float(cost.get('total') or 0.0)


def load_sessions_index(state_dir: Path, agent_id: str) -> dict[str, Any]:
    path = state_dir / 'agents' / agent_id / 'sessions' / 'sessions.json'
    with path.open() as f:
        return json.load(f)


def resolve_session_file(state_dir: Path, agent_id: str, session_key: Optional[str]) -> Tuple[str, Path]:
    sessions = load_sessions_index(state_dir, agent_id)
    if session_key:
        entry = sessions.get(session_key)
        if not entry:
            raise SystemExit(f'Session key not found: {session_key}')
        return session_key, Path(entry['sessionFile'])

    if not sessions:
        raise SystemExit('No sessions found')

    best_key, best_entry = max(
        sessions.items(),
        key=lambda kv: int((kv[1] or {}).get('updatedAt') or 0),
    )
    session_file = Path(best_entry['sessionFile'])
    return best_key, session_file


def iter_jsonl(path: Path):
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def summarize_session(session_file: Path):
    totals = UsageTotals()
    by_model = defaultdict(UsageTotals)
    last_assistant_usage = None

    for obj in iter_jsonl(session_file):
        if obj.get('type') != 'message':
            continue
        message = obj.get('message') or {}
        if message.get('role') != 'assistant':
            continue
        usage = message.get('usage')
        if not isinstance(usage, dict):
            continue
        totals.add(usage)
        provider = (message.get('provider') or obj.get('provider') or 'unknown').strip()
        model = (message.get('model') or obj.get('model') or 'unknown').strip()
        key = f'{provider}/{model}' if '/' not in model else model
        by_model[key].add(usage)
        last_assistant_usage = {
            'timestamp': obj.get('timestamp'),
            'provider': provider,
            'model': model,
            'usage': usage,
            'stopReason': message.get('stopReason') or obj.get('stopReason'),
        }

    return totals, by_model, last_assistant_usage


def markdown_report(session_key: str, totals: UsageTotals, by_model, last_call: Optional[dict[str, Any]]) -> str:
    lines = []
    lines.append('# Token usage monitor')
    lines.append('')
    lines.append(f'- Session: `{session_key}`')
    lines.append(f'- Assistant calls counted: **{fmt_int(totals.calls)}**')
    lines.append(f'- Input tokens: **{fmt_int(totals.input_tokens)}**')
    lines.append(f'- Output tokens: **{fmt_int(totals.output_tokens)}**')
    lines.append(f'- Cache read: **{fmt_int(totals.cache_read)}**')
    lines.append(f'- Cache write: **{fmt_int(totals.cache_write)}**')
    lines.append(f'- Total tokens: **{fmt_int(totals.total_tokens)}**')
    lines.append(f'- Estimated cost: **{fmt_money(totals.total_cost)}**')
    lines.append('')

    if last_call:
        usage = last_call['usage']
        lines.append('## Last assistant call')
        lines.append(f"- Time: `{last_call.get('timestamp') or 'unknown'}`")
        lines.append(f"- Model: `{last_call.get('provider')}/{last_call.get('model')}`")
        lines.append(f"- Input: **{fmt_int(int(usage.get('input') or 0))}**")
        lines.append(f"- Output: **{fmt_int(int(usage.get('output') or 0))}**")
        lines.append(f"- Cache read: **{fmt_int(int(usage.get('cacheRead') or 0))}**")
        lines.append(f"- Total: **{fmt_int(int(usage.get('totalTokens') or 0))}**")
        cost = usage.get('cost') or {}
        if isinstance(cost, dict):
            lines.append(f"- Cost: **{fmt_money(float(cost.get('total') or 0.0))}**")
        if last_call.get('stopReason'):
            lines.append(f"- Stop reason: `{last_call['stopReason']}`")
        lines.append('')

    if by_model:
        lines.append('## By model')
        for model_name, model_totals in sorted(by_model.items(), key=lambda kv: kv[1].total_tokens, reverse=True):
            lines.append(
                f"- `{model_name}` — calls **{fmt_int(model_totals.calls)}**, total **{fmt_int(model_totals.total_tokens)}** tokens, input **{fmt_int(model_totals.input_tokens)}**, output **{fmt_int(model_totals.output_tokens)}**, cache read **{fmt_int(model_totals.cache_read)}**, cost **{fmt_money(model_totals.total_cost)}**"
            )
        lines.append('')

    lines.append('## Notes')
    lines.append('- This reads persisted session transcript usage from OpenClaw session JSONL files.')
    lines.append('- It reflects assistant model calls recorded in the session, not an external provider billing dashboard.')
    lines.append('- Cache read/write only appears when the provider/runtime reports it.')
    return '\n'.join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description='Summarize OpenClaw token usage from session transcripts.')
    parser.add_argument('--state-dir', default=str(DEFAULT_STATE_DIR), help='OpenClaw state directory')
    parser.add_argument('--agent-id', default=DEFAULT_AGENT_ID, help='Agent id (default: main)')
    parser.add_argument('--session-key', help='Explicit session key, e.g. agent:main:main')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown')
    args = parser.parse_args()

    state_dir = Path(args.state_dir).expanduser()
    session_key, session_file = resolve_session_file(state_dir, args.agent_id, args.session_key)
    totals, by_model, last_call = summarize_session(session_file)

    if args.format == 'json':
        payload = {
            'sessionKey': session_key,
            'sessionFile': str(session_file),
            'totals': totals.__dict__,
            'byModel': {k: v.__dict__ for k, v in by_model.items()},
            'lastCall': last_call,
        }
        print(json.dumps(payload, indent=2))
        return

    print(markdown_report(session_key, totals, by_model, last_call))


if __name__ == '__main__':
    main()

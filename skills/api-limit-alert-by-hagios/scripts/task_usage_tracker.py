#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

DEFAULT_STATUS_CMD = ["openclaw", "status", "--usage", "--json"]
WINDOW_ALIASES = {
    "5h": "5h",
    "5hour": "5h",
    "5hours": "5h",
    "week": "weekly",
    "weekly": "weekly",
    "7day": "weekly",
    "7days": "weekly",
}
TOKEN_INPUT_KEYS = ["input", "inputTokens", "input_tokens", "promptTokens", "prompt_tokens"]
TOKEN_OUTPUT_KEYS = ["output", "outputTokens", "output_tokens", "completionTokens", "completion_tokens"]
TOKEN_TOTAL_KEYS = ["total", "totalTokens", "total_tokens"]
TOKEN_CONTAINER_KEYS = ["tokens", "tokenUsage", "token_usage", "usage", "metrics"]


def clamp_percent(value: Any) -> Optional[float]:
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return None


def normalize_window_label(label: str) -> Optional[str]:
    cleaned = ''.join(ch for ch in str(label or '').lower() if ch.isalnum())
    return WINDOW_ALIASES.get(cleaned)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Optional[str]) -> Any:
    if not path or path == '-':
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding='utf-8'))


def load_status_payload(path: Optional[str]) -> dict:
    if path:
        return load_json(path)
    proc = subprocess.run(DEFAULT_STATUS_CMD, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'openclaw status --usage --json failed')
    return json.loads(proc.stdout)


def extract_usage_windows(status_payload: dict, provider_hint: Optional[str]) -> Dict[str, Dict[str, Optional[float]]]:
    usage = status_payload.get('usage') or {}
    providers = usage.get('providers') or []
    if provider_hint:
        hint = provider_hint.lower()
        providers = [
            provider for provider in providers
            if hint in (str(provider.get('provider', '')) + ' ' + str(provider.get('displayName', ''))).lower()
        ]

    windows: Dict[str, Dict[str, Optional[float]]] = {}
    for provider in providers:
        for window in provider.get('windows') or []:
            normalized = normalize_window_label(window.get('label', ''))
            if normalized not in {'5h', 'weekly'} or normalized in windows:
                continue
            used = clamp_percent(window.get('usedPercent'))
            remaining = clamp_percent(window.get('remainingPercent'))
            if remaining is None and used is not None:
                remaining = clamp_percent(100.0 - used)
            if used is None and remaining is not None:
                used = clamp_percent(100.0 - remaining)
            windows[normalized] = {
                'label': normalized,
                'used_percent': used,
                'remaining_percent': remaining,
            }
    return windows


def walk_candidates(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from walk_candidates(nested)
    elif isinstance(value, list):
        for item in value:
            yield from walk_candidates(item)


def first_number(mapping: Dict[str, Any], keys: Iterable[str]) -> Optional[float]:
    for key in keys:
        if key in mapping:
            try:
                return float(mapping[key])
            except (TypeError, ValueError):
                continue
    return None


def extract_token_counts(payload: Any) -> Dict[str, Optional[float]]:
    best: Dict[str, Optional[float]] = {'input': None, 'output': None, 'total': None}

    if isinstance(payload, dict):
        direct = {
            'input': first_number(payload, TOKEN_INPUT_KEYS),
            'output': first_number(payload, TOKEN_OUTPUT_KEYS),
            'total': first_number(payload, TOKEN_TOTAL_KEYS),
        }
        if any(value is not None for value in direct.values()):
            if direct['total'] is None and direct['input'] is not None and direct['output'] is not None:
                direct['total'] = direct['input'] + direct['output']
            return direct

    for candidate in walk_candidates(payload):
        if not isinstance(candidate, dict):
            continue

        ordered_mappings = []
        for container_key in TOKEN_CONTAINER_KEYS:
            nested = candidate.get(container_key)
            if isinstance(nested, dict):
                ordered_mappings.append(nested)
        ordered_mappings.append(candidate)

        for mapping in ordered_mappings:
            found = {
                'input': first_number(mapping, TOKEN_INPUT_KEYS),
                'output': first_number(mapping, TOKEN_OUTPUT_KEYS),
                'total': first_number(mapping, TOKEN_TOTAL_KEYS),
            }
            if any(value is not None for value in found.values()):
                if found['total'] is None and found['input'] is not None and found['output'] is not None:
                    found['total'] = found['input'] + found['output']
                return found

    return best


def build_snapshot(status_payload: dict, provider_hint: Optional[str], token_payload: Optional[Any], token_label: Optional[str]) -> dict:
    windows = extract_usage_windows(status_payload, provider_hint)
    tokens = extract_token_counts(token_payload if token_payload is not None else status_payload)
    return {
        'capturedAt': now_iso(),
        'providerHint': provider_hint,
        'windows': windows,
        'tokens': tokens,
        'tokenSource': token_label or ('status' if token_payload is None else 'external'),
    }


def format_percent(value: Optional[float]) -> str:
    return 'n/a' if value is None else f'{value:.1f}%'


def format_number(value: Optional[float]) -> str:
    if value is None:
        return 'n/a'
    integer = int(round(value))
    return f'{integer:,}'


def delta(after: Optional[float], before: Optional[float]) -> Optional[float]:
    if after is None or before is None:
        return None
    return after - before


def low_budget_message(weekly_remaining_after: Optional[float]) -> Optional[str]:
    if weekly_remaining_after is None:
        return None
    if weekly_remaining_after <= 15:
        return 'Low-budget policy: weekly remaining is at or below 15%; chat/planning only, hold off on heavy tasks until weekly renew.'
    if weekly_remaining_after <= 20:
        return 'Low-budget policy: weekly remaining is at or below 20%; avoid unnecessary heavy work and batch follow-ups carefully.'
    return None


def summarize(before: dict, after: dict, task_label: str) -> dict:
    windows_before = before.get('windows') or {}
    windows_after = after.get('windows') or {}
    tokens_before = before.get('tokens') or {}
    tokens_after = after.get('tokens') or {}

    token_delta = {
        'input': delta(tokens_after.get('input'), tokens_before.get('input')),
        'output': delta(tokens_after.get('output'), tokens_before.get('output')),
        'total': delta(tokens_after.get('total'), tokens_before.get('total')),
    }
    if token_delta['total'] is None and token_delta['input'] is not None and token_delta['output'] is not None:
        token_delta['total'] = token_delta['input'] + token_delta['output']

    windows_summary = {}
    for label in ('5h', 'weekly'):
        before_window = windows_before.get(label) or {}
        after_window = windows_after.get(label) or {}
        before_used = before_window.get('used_percent')
        after_used = after_window.get('used_percent')
        before_remaining = before_window.get('remaining_percent')
        after_remaining = after_window.get('remaining_percent')
        windows_summary[label] = {
            'used_delta_percent': delta(after_used, before_used),
            'remaining_before_percent': before_remaining,
            'remaining_after_percent': after_remaining,
            'used_before_percent': before_used,
            'used_after_percent': after_used,
        }

    policy_message = low_budget_message((windows_summary.get('weekly') or {}).get('remaining_after_percent'))

    return {
        'task': task_label,
        'timestamp': after.get('capturedAt') or now_iso(),
        'tokens': token_delta,
        'windows': windows_summary,
        'policy': {
            'low_budget_message': policy_message,
            'weekly_low_budget': bool(policy_message),
        },
    }


def summary_text(summary: dict) -> str:
    five = summary['windows'].get('5h') or {}
    weekly = summary['windows'].get('weekly') or {}
    lines = [
        f"Task usage — {summary['task']}",
        f"Timestamp: {summary['timestamp']}",
        f"Tokens: input {format_number(summary['tokens'].get('input'))} | output {format_number(summary['tokens'].get('output'))} | total {format_number(summary['tokens'].get('total'))}",
        (
            '5h usage: '
            f"Δused {format_percent(five.get('used_delta_percent'))} | remaining {format_percent(five.get('remaining_before_percent'))} → {format_percent(five.get('remaining_after_percent'))}"
        ),
        (
            'Weekly usage: '
            f"Δused {format_percent(weekly.get('used_delta_percent'))} | remaining {format_percent(weekly.get('remaining_before_percent'))} → {format_percent(weekly.get('remaining_after_percent'))}"
        ),
    ]
    policy = (summary.get('policy') or {}).get('low_budget_message')
    if policy:
        lines.append(policy)
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description='Capture and summarize per-task Codex/OpenClaw usage snapshots.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    snapshot_parser = subparsers.add_parser('snapshot', help='Capture a normalized usage snapshot.')
    snapshot_parser.add_argument('--status-file', help='Read raw openclaw status --usage --json from a file. If omitted, invoke openclaw directly.')
    snapshot_parser.add_argument('--provider', default='codex', help='Provider/display-name hint used to select the usage provider.')
    snapshot_parser.add_argument('--token-file', help='Optional JSON file containing task/session token counters.')
    snapshot_parser.add_argument('--token-label', help='Optional label describing the token counter source.')
    snapshot_parser.add_argument('--pretty', action='store_true', help='Pretty-print JSON output.')

    summarize_parser = subparsers.add_parser('summarize', help='Compare before/after snapshots and emit a per-task summary.')
    summarize_parser.add_argument('--before', required=True, help='Normalized snapshot JSON captured before the task.')
    summarize_parser.add_argument('--after', required=True, help='Normalized snapshot JSON captured after the task.')
    summarize_parser.add_argument('--task', required=True, help='Human-readable task label.')
    summarize_parser.add_argument('--format', choices=['text', 'json'], default='text', help='Summary output format.')
    summarize_parser.add_argument('--pretty', action='store_true', help='Pretty-print JSON summary output.')

    args = parser.parse_args()

    if args.command == 'snapshot':
        status_payload = load_status_payload(args.status_file)
        token_payload = load_json(args.token_file) if args.token_file else None
        snapshot = build_snapshot(status_payload, args.provider, token_payload, args.token_label)
        if args.pretty:
            print(json.dumps(snapshot, indent=2, sort_keys=True))
        else:
            print(json.dumps(snapshot, sort_keys=True))
        return 0

    before = load_json(args.before)
    after = load_json(args.after)
    summary = summarize(before, after, args.task)
    if args.format == 'json':
        if args.pretty:
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            print(json.dumps(summary, sort_keys=True))
    else:
        print(summary_text(summary))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

WORKSPACE = Path('/Users/hagios/Documents/Hagios 1/workspace')
DEFAULT_SESSIONS_INDEX = WORKSPACE.parent / 'state' / 'agents' / 'main' / 'sessions' / 'sessions.json'
DEFAULT_STATE_FILE = WORKSPACE / 'memory' / 'response-delivery-monitor-state.json'
TARGET_SESSION_KEY = 'agent:main:discord:channel:{channel_id}'


@dataclass
class CheckResult:
    status: str
    alert: Optional[str]
    should_write_state: bool
    state_reason: str
    details: Dict[str, Any]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Best-effort Discord response-delivery monitor using local OpenClaw session files.')
    p.add_argument('--channel-id', default='1473419070761337067', help='Discord channel id to inspect.')
    p.add_argument('--session-key', help='Explicit session key override. Defaults to agent:main:discord:channel:<channel-id>.')
    p.add_argument('--sessions-index', default=str(DEFAULT_SESSIONS_INDEX))
    p.add_argument('--state-file', default=str(DEFAULT_STATE_FILE))
    p.add_argument('--lookback-min', type=float, default=45.0, help='Ignore stale conversations older than this many minutes.')
    p.add_argument('--response-timeout-min', type=float, default=6.0, help='Alert when a recent user message has no later assistant reply after this many minutes.')
    p.add_argument('--running-grace-min', type=float, default=12.0, help='Suppress alerts a bit longer while a session status is running.')
    p.add_argument('--json', action='store_true')
    return p.parse_args()


def parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    value = value.replace('Z', '+00:00')
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def find_session_entry(index: Dict[str, Any], session_key: str) -> Dict[str, Any]:
    entry = index.get(session_key)
    if not entry:
        raise KeyError(f'Session key not found in sessions index: {session_key}')
    return entry


def extract_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ''
    parts: List[str] = []
    for item in content:
        if isinstance(item, dict) and item.get('type') == 'text':
            parts.append(str(item.get('text', '')))
    return '\n'.join(parts)


def extract_user_message_id(text: str) -> Optional[str]:
    m = re.search(r'"message_id"\s*:\s*"([0-9]+)"', text)
    return m.group(1) if m else None


def extract_assistant_text(message_obj: Dict[str, Any]) -> Optional[str]:
    message = message_obj.get('message') or {}
    if message.get('role') != 'assistant':
        return None
    content = message.get('content') or []
    texts = []
    final_answer = False
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get('type') == 'text':
            txt = str(item.get('text', ''))
            texts.append(txt)
            sig = str(item.get('textSignature', ''))
            if 'final_answer' in sig:
                final_answer = True
    if not texts:
        return None
    combined = '\n'.join(texts).strip()
    if final_answer or combined:
        return combined
    return None


def load_events(jsonl_path: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    with jsonl_path.open('r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def last_relevant_events(events: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    last_user = None
    last_assistant = None
    for event in events:
        if event.get('type') != 'message':
            continue
        message = event.get('message') or {}
        role = message.get('role')
        if role == 'user':
            text = extract_text_from_content(message.get('content'))
            if extract_user_message_id(text):
                last_user = {
                    'event_timestamp': event.get('timestamp'),
                    'message_timestamp': message.get('timestamp'),
                    'message_id': extract_user_message_id(text),
                    'text': text,
                }
        elif role == 'assistant':
            assistant_text = extract_assistant_text(event)
            if assistant_text:
                last_assistant = {
                    'event_timestamp': event.get('timestamp'),
                    'text': assistant_text,
                }
    return last_user, last_assistant


def build_alert(session_key: str, last_user: Dict[str, Any], session_status: str, age_min: float, response_timeout_min: float, last_assistant: Optional[Dict[str, Any]]) -> str:
    message_id = last_user.get('message_id') or 'unknown'
    assistant_note = 'no assistant final answer recorded after that user message'
    if last_assistant:
        assistant_note = f'latest assistant reply predates it ({last_assistant.get("event_timestamp")})'
    return (
        f'Response Delivery Alert — possible Discord reply gap for {session_key}: '
        f'user message {message_id} is {age_min:.1f} min old, session status={session_status}, '
        f'threshold={response_timeout_min:.1f} min, and {assistant_note}.'
    )


def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {'alerts': {}}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {'alerts': {}}
    if not isinstance(data, dict):
        return {'alerts': {}}
    data.setdefault('alerts', {})
    return data


def save_state(path: Path, state: Dict[str, Any]) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def evaluate(args: argparse.Namespace) -> CheckResult:
    now = datetime.now(timezone.utc)
    session_key = args.session_key or TARGET_SESSION_KEY.format(channel_id=args.channel_id)
    index = load_json(Path(args.sessions_index))
    entry = find_session_entry(index, session_key)
    session_file = Path(entry['sessionFile'])
    events = load_events(session_file)
    last_user, last_assistant = last_relevant_events(events)
    details: Dict[str, Any] = {
        'session_key': session_key,
        'session_status': entry.get('status'),
        'session_file': str(session_file),
        'updated_at_ms': entry.get('updatedAt'),
        'last_user': last_user,
        'last_assistant': last_assistant,
    }
    if not last_user:
        return CheckResult('ok', None, False, 'no-user-message', details)

    user_ts = parse_ts(last_user.get('event_timestamp')) or parse_ts(last_user.get('message_timestamp'))
    assistant_ts = parse_ts(last_assistant.get('event_timestamp')) if last_assistant else None
    if not user_ts:
        return CheckResult('ok', None, False, 'missing-user-timestamp', details)

    age_min = (now - user_ts).total_seconds() / 60.0
    details['last_user_age_min'] = round(age_min, 3)
    if age_min > args.lookback_min:
        return CheckResult('ok', None, True, 'stale-window', details)

    if assistant_ts and assistant_ts >= user_ts:
        return CheckResult('ok', None, True, 'assistant-replied', details)

    session_status = str(entry.get('status') or 'unknown')
    threshold = args.response_timeout_min
    if session_status == 'running':
        threshold = max(threshold, args.running_grace_min)
    details['effective_threshold_min'] = threshold

    if age_min < threshold:
        return CheckResult('ok', None, False, 'within-threshold', details)

    alert = build_alert(session_key, last_user, session_status, age_min, threshold, last_assistant)
    return CheckResult('alert', alert, True, 'missing-assistant-reply', details)


def apply_dedupe(state_file: Path, result: CheckResult) -> CheckResult:
    state = load_state(state_file)
    session_key = result.details['session_key']
    alert_key = None
    if result.status == 'alert':
        alert_key = f"{result.details['last_user'].get('message_id')}|{result.state_reason}"
        prior = state['alerts'].get(session_key, {})
        if prior.get('alert_key') == alert_key:
            result = CheckResult('ok', None, False, 'duplicate-alert-suppressed', result.details)
        else:
            state['alerts'][session_key] = {
                'alert_key': alert_key,
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'details': {
                    'message_id': result.details['last_user'].get('message_id'),
                    'reason': result.state_reason,
                },
            }
            save_state(state_file, state)
            return result

    if result.should_write_state:
        prior = state['alerts'].get(session_key)
        if prior:
            state['alerts'].pop(session_key, None)
            save_state(state_file, state)
        elif not state_file.exists():
            save_state(state_file, state)
    return result


def main() -> int:
    args = parse_args()
    result = apply_dedupe(Path(args.state_file), evaluate(args))
    payload = {
        'status': result.status,
        'alert': result.alert,
        'state_reason': result.state_reason,
        'details': result.details,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif result.status == 'alert' and result.alert:
        print(result.alert)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

WORKSPACE = Path('/Users/hagios/Documents/Hagios 1/workspace')
DEFAULT_STATUS_CMD = ['openclaw', 'status', '--usage', '--json']
DEFAULT_CHECK_SCRIPT = WORKSPACE / 'skills' / 'api-limit-alert-by-hagios' / 'scripts' / 'check_usage_bucket.py'
DEFAULT_STATE_FILE = WORKSPACE / 'memory' / 'api-limit-alert-by-hagios-state.json'


def load_status_json(status_file: Optional[str]) -> dict:
    if status_file:
        return json.loads(Path(status_file).read_text(encoding='utf-8'))
    proc = subprocess.run(DEFAULT_STATUS_CMD, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'openclaw status --usage --json failed')
    return json.loads(proc.stdout)


def normalize_window_label(label: str) -> Optional[str]:
    cleaned = ''.join(ch for ch in str(label).lower() if ch.isalnum())
    aliases = {
        '5h': '5h',
        '5hour': '5h',
        '5hours': '5h',
        'week': 'weekly',
        'weekly': 'weekly',
        '7day': 'weekly',
        '7days': 'weekly',
    }
    return aliases.get(cleaned)


def extract_target_windows(status_payload: dict, provider_hint: Optional[str]) -> Dict[str, float]:
    usage = status_payload.get('usage') or {}
    providers = usage.get('providers') or []
    if provider_hint:
        providers = [
            p for p in providers
            if provider_hint.lower() in (str(p.get('provider', '')) + ' ' + str(p.get('displayName', ''))).lower()
        ]

    windows: Dict[str, float] = {}
    for provider in providers:
        for window in provider.get('windows') or []:
            normalized = normalize_window_label(window.get('label', ''))
            if normalized not in {'5h', 'weekly'} or normalized in windows:
                continue
            used = window.get('usedPercent')
            if used is None:
                raise ValueError(f'{normalized} usage window found but usedPercent is missing.')
            windows[normalized] = max(0.0, min(100.0, 100.0 - float(used)))

    missing = [label for label in ('5h', 'weekly') if label not in windows]
    if missing:
        raise ValueError(f'Could not find usage windows in openclaw status output for: {", ".join(missing)}.')
    return windows


def run_checker(check_script: str, state_file: str, window_label: str, remaining: float) -> dict:
    cmd = [
        sys.executable,
        check_script,
        '--remaining-percent',
        f'{remaining:.3f}',
        '--state-file',
        state_file,
        '--window-label',
        window_label,
        '--json',
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f'check_usage_bucket.py failed for {window_label}')
    return json.loads(proc.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description='Run dual-window API limit checks from openclaw status --usage JSON.')
    parser.add_argument('--status-file', help='Read prior openclaw status --usage --json output from a file instead of invoking the CLI.')
    parser.add_argument('--provider', default='codex', help='Provider/display-name hint to select the usage provider (default: codex).')
    parser.add_argument('--state-file', default=str(DEFAULT_STATE_FILE))
    parser.add_argument('--check-script', default=str(DEFAULT_CHECK_SCRIPT))
    parser.add_argument('--json', action='store_true', help='Emit wrapper metadata plus checker result as JSON.')
    args = parser.parse_args()

    status_payload = load_status_json(args.status_file)
    windows = extract_target_windows(status_payload, args.provider)
    results: List[dict] = []
    alerts: List[str] = []

    for label in ('5h', 'weekly'):
        checker = run_checker(args.check_script, args.state_file, label, windows[label])
        results.append(checker)
        if checker.get('status') == 'alert' and checker.get('alert'):
            alerts.append(checker['alert'])

    payload = {
        'ok': True,
        'source': 'openclaw status --usage --json',
        'windows': {label: round(value, 3) for label, value in windows.items()},
        'results': results,
        'alerts': alerts,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif alerts:
        print('\n\n'.join(alerts))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

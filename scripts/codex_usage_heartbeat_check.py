#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

WORKSPACE = Path('/Users/hagios/Documents/Hagios 1/workspace')
DEFAULT_STATUS_CMD = ['openclaw', 'status', '--usage', '--json']
DEFAULT_CHECK_SCRIPT = WORKSPACE / 'skills' / 'codex-usage-bucket-alert' / 'scripts' / 'check_usage_bucket.py'


def load_status_json(status_file: Optional[str]) -> dict:
    if status_file:
        return json.loads(Path(status_file).read_text(encoding='utf-8'))
    proc = subprocess.run(DEFAULT_STATUS_CMD, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'openclaw status --usage --json failed')
    return json.loads(proc.stdout)


def extract_weekly_remaining(status_payload: dict, provider_hint: Optional[str]) -> float:
    usage = status_payload.get('usage') or {}
    providers = usage.get('providers') or []
    if provider_hint:
        providers = [p for p in providers if provider_hint.lower() in (p.get('provider', '') + ' ' + p.get('displayName', '')).lower()]
    for provider in providers:
        for window in provider.get('windows') or []:
            label = str(window.get('label', '')).strip().lower()
            if label == 'week':
                used = window.get('usedPercent')
                if used is None:
                    raise ValueError('Weekly usage window found but usedPercent is missing.')
                return max(0.0, min(100.0, 100.0 - float(used)))
    raise ValueError('Could not find a weekly usage window in openclaw status output.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Run Codex weekly bucket check from openclaw status --usage JSON.')
    parser.add_argument('--status-file', help='Read prior openclaw status --usage --json output from a file instead of invoking the CLI.')
    parser.add_argument('--provider', default='codex', help='Provider/display-name hint to select the usage provider (default: codex).')
    parser.add_argument('--state-file', default=str(WORKSPACE / 'memory' / 'codex-usage-bucket-alert-state.json'))
    parser.add_argument('--check-script', default=str(DEFAULT_CHECK_SCRIPT))
    parser.add_argument('--json', action='store_true', help='Emit wrapper metadata plus checker result as JSON.')
    args = parser.parse_args()

    status_payload = load_status_json(args.status_file)
    remaining = extract_weekly_remaining(status_payload, args.provider)
    cmd = [
        sys.executable,
        args.check_script,
        '--remaining-percent',
        f'{remaining:.3f}',
        '--state-file',
        args.state_file,
        '--label',
        'weekly',
        '--json',
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'check_usage_bucket.py failed')
    checker = json.loads(proc.stdout)

    if args.json:
        print(json.dumps({
            'ok': True,
            'source': 'openclaw status --usage --json',
            'percent_remaining': round(remaining, 3),
            'checker': checker,
        }, indent=2, sort_keys=True))
    elif checker.get('status') == 'alert' and checker.get('alert'):
        print(checker['alert'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

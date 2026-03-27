#!/usr/bin/env python3
import json, subprocess, pathlib

STATE = pathlib.Path('/Users/hagios/Documents/Hagios 1/workspace/memory/task-cost-last.json')


def get_usage():
    out = subprocess.check_output(['openclaw','status','--usage','--json'], text=True)
    j = json.loads(out)
    # tolerant lookup
    weekly = j.get('weekly') or j.get('week') or {}
    h5 = j.get('5h') or j.get('fiveHour') or j.get('window5h') or {}
    return {
        'weekly_remaining': float(weekly.get('remainingPercent', weekly.get('remaining', 0))),
        'h5_remaining': float(h5.get('remainingPercent', h5.get('remaining', 0))),
    }


def main():
    now = get_usage()
    if not STATE.exists():
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(now, indent=2))
        print('Cost: baseline set (no delta yet).')
        return

    prev = json.loads(STATE.read_text())
    d_week = round(prev['weekly_remaining'] - now['weekly_remaining'], 2)
    d_h5 = round(prev['h5_remaining'] - now['h5_remaining'], 2)
    print(f'Cost: 5h -{d_h5}% | week -{d_week}%')
    STATE.write_text(json.dumps(now, indent=2))


if __name__ == '__main__':
    main()

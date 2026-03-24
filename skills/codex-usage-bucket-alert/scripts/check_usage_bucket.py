#!/usr/bin/env python3
import argparse
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def clamp_percent(value: float) -> float:
    return max(0.0, min(100.0, value))


def bucket_for(percent_remaining: float) -> int:
    return int(math.floor(clamp_percent(percent_remaining) / 10.0) * 10)


def load_text(args: argparse.Namespace) -> str:
    if args.status_text is not None:
        return args.status_text
    if args.status_file is not None:
        return Path(args.status_file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def extract_weekly_percent(status_text: str, mode: str) -> float:
    text = status_text.strip()
    if not text:
        raise ValueError("No status text provided. Use --remaining-percent, --status-text, --status-file, or pipe text on stdin.")

    patterns = {
        "remaining": [
            r"weekly[^\n%]{0,60}?(?:remaining|left|available|headroom)[^0-9]{0,10}(\d{1,3}(?:\.\d+)?)\s*%",
            r"(\d{1,3}(?:\.\d+)?)\s*%[^\n]{0,40}?weekly[^\n]{0,20}?(?:remaining|left|available|headroom)",
        ],
        "used": [
            r"weekly[^\n%]{0,60}?(?:used|usage|consumed|spent)[^0-9]{0,10}(\d{1,3}(?:\.\d+)?)\s*%",
            r"(\d{1,3}(?:\.\d+)?)\s*%[^\n]{0,40}?weekly[^\n]{0,20}?(?:used|usage|consumed|spent)",
        ],
    }

    def try_patterns(kind: str):
        for pattern in patterns[kind]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1)), kind
        return None

    if mode in {"remaining", "auto"}:
        found = try_patterns("remaining")
        if found:
            return clamp_percent(found[0])

    if mode in {"used", "auto"}:
        found = try_patterns("used")
        if found:
            return clamp_percent(100.0 - found[0]) if mode != "remaining" else clamp_percent(found[0])

    weekly_lines = [line.strip() for line in text.splitlines() if "weekly" in line.lower()]
    for line in weekly_lines:
        percents = re.findall(r"(\d{1,3}(?:\.\d+)?)\s*%", line)
        if len(percents) == 1:
            value = float(percents[0])
            lower = line.lower()
            if any(word in lower for word in ["remaining", "left", "available", "headroom"]):
                return clamp_percent(value)
            if any(word in lower for word in ["used", "usage", "consumed", "spent"]):
                return clamp_percent(100.0 - value)
            if mode == "remaining":
                return clamp_percent(value)
            if mode == "used":
                return clamp_percent(100.0 - value)

    raise ValueError("Could not extract a weekly percentage from status text. Pass --remaining-percent directly or use --weekly-percent-mode remaining|used to disambiguate.")


def load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"State file is not valid JSON: {path}") from exc


def save_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_alert(bucket: int, percent_remaining: float, previous_bucket: Optional[int]) -> str:
    previous = "unknown" if previous_bucket is None else f"{previous_bucket}%"
    return (
        f"Codex weekly usage alert: remaining budget dropped into the {bucket}% bucket "
        f"(current: {percent_remaining:.1f}%, previous alert bucket: {previous})."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Alert when weekly Codex remaining usage falls into a new lower 10%% bucket.")
    parser.add_argument("--remaining-percent", type=float, help="Weekly percent remaining (0-100). Bypasses text parsing.")
    parser.add_argument("--status-text", help="Raw status text containing weekly usage information.")
    parser.add_argument("--status-file", help="File containing raw status text.")
    parser.add_argument("--weekly-percent-mode", choices=["auto", "remaining", "used"], default="auto", help="Interpretation for percentages found in status text.")
    parser.add_argument("--state-file", default="/Users/hagios/Documents/Hagios 1/workspace/memory/codex-usage-bucket-alert-state.json", help="JSON state file used to suppress duplicate alerts.")
    parser.add_argument("--label", default="weekly", help="Label stored in state for the tracked budget window.")
    parser.add_argument("--first-run-alert", action="store_true", help="Emit an alert on first run instead of silently seeding state.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON instead of plain text.")
    args = parser.parse_args()

    if args.remaining_percent is not None:
        percent_remaining = clamp_percent(args.remaining_percent)
    else:
        percent_remaining = extract_weekly_percent(load_text(args), args.weekly_percent_mode)

    current_bucket = bucket_for(percent_remaining)
    state_path = Path(os.path.expanduser(args.state_file))
    state = load_state(state_path)
    previous_bucket = state.get("last_alerted_bucket")

    now = datetime.now(timezone.utc).isoformat()
    result = {
        "ok": True,
        "label": args.label,
        "percent_remaining": round(percent_remaining, 3),
        "current_bucket": current_bucket,
        "last_alerted_bucket": previous_bucket,
        "state_file": str(state_path),
        "status": "noop",
        "alert": None,
        "reason": None,
    }

    if previous_bucket is None:
        state.update({
            "label": args.label,
            "last_alerted_bucket": current_bucket,
            "last_seen_percent_remaining": round(percent_remaining, 3),
            "last_checked_at": now,
            "last_alerted_at": now if args.first_run_alert else None,
        })
        save_state(state_path, state)
        if args.first_run_alert:
            result["status"] = "alert"
            result["alert"] = build_alert(current_bucket, percent_remaining, previous_bucket)
        else:
            result["status"] = "initialized"
            result["reason"] = "State initialized without alert."
    elif current_bucket < int(previous_bucket):
        state.update({
            "label": args.label,
            "last_alerted_bucket": current_bucket,
            "last_seen_percent_remaining": round(percent_remaining, 3),
            "last_checked_at": now,
            "last_alerted_at": now,
        })
        save_state(state_path, state)
        result["status"] = "alert"
        result["alert"] = build_alert(current_bucket, percent_remaining, int(previous_bucket))
    else:
        state.update({
            "label": args.label,
            "last_seen_percent_remaining": round(percent_remaining, 3),
            "last_checked_at": now,
            **({"last_alerted_bucket": current_bucket} if current_bucket > int(previous_bucket) else {}),
        })
        save_state(state_path, state)
        result["status"] = "noop"
        if current_bucket == int(previous_bucket):
            result["reason"] = "Already alerted for this bucket."
        else:
            result["reason"] = "Bucket moved upward; state reset without alert."

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        if result["status"] == "alert":
            print(result["alert"])
        elif result["status"] == "initialized":
            print(f"Initialized state at bucket {current_bucket}% with no alert.")
        else:
            print(f"No alert: {result['reason']} Current bucket: {current_bucket}%. Remaining: {percent_remaining:.1f}%.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

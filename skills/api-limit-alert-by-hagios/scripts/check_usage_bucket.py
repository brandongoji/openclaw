#!/usr/bin/env python3
import argparse
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_STATE_FILE = "/Users/hagios/Documents/Hagios 1/workspace/memory/api-limit-alert-by-hagios-state.json"


def clamp_percent(value: float) -> float:
    return max(0.0, min(100.0, value))


def bucket_for(percent_remaining: float) -> int:
    return int(math.floor(clamp_percent(percent_remaining) / 10.0) * 10)


def normalize_window_label(label: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "", (label or "").strip().lower())
    aliases = {
        "5h": "5h",
        "5hour": "5h",
        "5hours": "5h",
        "fivehour": "5h",
        "fivehours": "5h",
        "week": "weekly",
        "weekly": "weekly",
        "7day": "weekly",
        "7days": "weekly",
    }
    return aliases.get(cleaned, cleaned or "unknown")


def human_window_label(label: str) -> str:
    normalized = normalize_window_label(label)
    return {"5h": "5-hour", "weekly": "weekly"}.get(normalized, label)


def load_text(args: argparse.Namespace) -> str:
    if args.status_text is not None:
        return args.status_text
    if args.status_file is not None:
        return Path(args.status_file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def extract_window_percent(status_text: str, mode: str, window_label: str) -> float:
    text = status_text.strip()
    if not text:
        raise ValueError("No status text provided. Use --remaining-percent, --status-text, --status-file, or pipe text on stdin.")

    target = human_window_label(window_label).lower()
    label_patterns = {
        "5h": r"(?:5\s*[- ]?hour|5h)",
        "weekly": r"(?:week|weekly|7\s*[- ]?day)",
    }
    label_pattern = label_patterns.get(normalize_window_label(window_label), re.escape(target))

    patterns = {
        "remaining": [
            rf"{label_pattern}[^\n%]{{0,80}}?(?:remaining|left|available|headroom)[^0-9]{{0,10}}(\d{{1,3}}(?:\.\d+)?)\s*%",
            rf"(\d{{1,3}}(?:\.\d+)?)\s*%[^\n]{{0,60}}?{label_pattern}[^\n]{{0,30}}?(?:remaining|left|available|headroom)",
        ],
        "used": [
            rf"{label_pattern}[^\n%]{{0,80}}?(?:used|usage|consumed|spent)[^0-9]{{0,10}}(\d{{1,3}}(?:\.\d+)?)\s*%",
            rf"(\d{{1,3}}(?:\.\d+)?)\s*%[^\n]{{0,60}}?{label_pattern}[^\n]{{0,30}}?(?:used|usage|consumed|spent)",
        ],
    }

    def try_patterns(kind: str) -> Optional[float]:
        for pattern in patterns[kind]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None

    if mode in {"remaining", "auto"}:
        found = try_patterns("remaining")
        if found is not None:
            return clamp_percent(found)

    if mode in {"used", "auto"}:
        found = try_patterns("used")
        if found is not None:
            return clamp_percent(100.0 - found)

    for line in text.splitlines():
        lower = line.lower()
        if not re.search(label_pattern, lower, re.IGNORECASE):
            continue
        percents = re.findall(r"(\d{1,3}(?:\.\d+)?)\s*%", line)
        if len(percents) != 1:
            continue
        value = float(percents[0])
        if any(word in lower for word in ["remaining", "left", "available", "headroom"]):
            return clamp_percent(value)
        if any(word in lower for word in ["used", "usage", "consumed", "spent"]):
            return clamp_percent(100.0 - value)
        if mode == "remaining":
            return clamp_percent(value)
        if mode == "used":
            return clamp_percent(100.0 - value)

    raise ValueError(
        f"Could not extract a percentage for the {human_window_label(window_label)} window from status text. "
        "Pass --remaining-percent directly or use --window-percent-mode remaining|used to disambiguate."
    )


def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"windows": {}}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"State file is not valid JSON: {path}") from exc

    if "windows" in raw and isinstance(raw["windows"], dict):
        raw.setdefault("version", 2)
        return raw

    legacy_label = normalize_window_label(raw.get("label") or "weekly")
    return {
        "version": 2,
        "windows": {
            legacy_label: {
                "label": legacy_label,
                "last_alerted_bucket": raw.get("last_alerted_bucket"),
                "last_seen_percent_remaining": raw.get("last_seen_percent_remaining"),
                "last_checked_at": raw.get("last_checked_at"),
                "last_alerted_at": raw.get("last_alerted_at"),
                "threshold_alerts": raw.get("threshold_alerts") or {"warn25": False, "weekly20": False, "weekly15": False, "red10": False},
            }
        },
    }


def save_state(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_bucket_alert(window_label: str, percent_remaining: float, previous_bucket: Optional[int]) -> str:
    used = 100.0 - percent_remaining
    crossed_used = int(math.floor(used / 10.0) * 10)
    previous = "unknown" if previous_bucket is None else f"{previous_bucket}% remaining"
    return (
        f"API Limit Alert by Hagios — {human_window_label(window_label)} window: crossed {crossed_used}% used "
        f"(remaining: {percent_remaining:.1f}%, previous alert bucket: {previous})."
    )


def build_threshold_alert(window_label: str, kind: str, percent_remaining: float) -> str:
    prefix = f"API Limit Alert by Hagios — {human_window_label(window_label)} window"
    if kind == "warn25":
        return f"⚠️ {prefix}: only {percent_remaining:.1f}% remaining (25% threshold reached)."
    if kind == "weekly20":
        return f"⚠️ {prefix}: weekly remaining is down to {percent_remaining:.1f}% (20% low-budget threshold reached)."
    if kind == "weekly15":
        return (
            f"⚠️ {prefix}: weekly remaining is down to {percent_remaining:.1f}% (15% token-saving threshold reached). "
            "Low-budget policy: chat/planning only, hold off on heavy tasks until weekly renew."
        )
    if kind == "red10":
        return f"🚨 {prefix}: only {percent_remaining:.1f}% remaining (10% threshold reached)."
    raise ValueError(f"Unknown threshold alert kind: {kind}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Alert when API remaining usage falls into a new lower 10% bucket.")
    parser.add_argument("--remaining-percent", type=float, help="Percent remaining (0-100). Bypasses text parsing.")
    parser.add_argument("--status-text", help="Raw status text containing usage information.")
    parser.add_argument("--status-file", help="File containing raw status text.")
    parser.add_argument("--window-label", default="weekly", help="Window label to track (for example: 5h or weekly).")
    parser.add_argument("--window-percent-mode", choices=["auto", "remaining", "used"], default="auto", help="Interpretation for percentages found in status text.")
    parser.add_argument("--state-file", default=DEFAULT_STATE_FILE, help="JSON state file used to suppress duplicate alerts.")
    parser.add_argument("--first-run-alert", action="store_true", help="Emit an alert on first run instead of silently seeding state.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON instead of plain text.")
    args = parser.parse_args()

    window_label = normalize_window_label(args.window_label)
    if args.remaining_percent is not None:
        percent_remaining = clamp_percent(args.remaining_percent)
    else:
        percent_remaining = extract_window_percent(load_text(args), args.window_percent_mode, window_label)

    current_bucket = bucket_for(percent_remaining)
    state_path = Path(os.path.expanduser(args.state_file))
    state = load_state(state_path)
    state.setdefault("version", 2)
    windows = state.setdefault("windows", {})
    window_state = windows.setdefault(window_label, {
        "label": window_label,
        "last_alerted_bucket": None,
        "last_seen_percent_remaining": None,
        "last_checked_at": None,
        "last_alerted_at": None,
        "threshold_alerts": {"warn25": False, "weekly20": False, "weekly15": False, "red10": False},
    })
    threshold_alerts = window_state.get("threshold_alerts") or {"warn25": False, "weekly20": False, "weekly15": False, "red10": False}
    previous_bucket = window_state.get("last_alerted_bucket")
    now = datetime.now(timezone.utc).isoformat()

    result = {
        "ok": True,
        "window_label": window_label,
        "window_display": human_window_label(window_label),
        "percent_remaining": round(percent_remaining, 3),
        "current_bucket": current_bucket,
        "last_alerted_bucket": previous_bucket,
        "state_file": str(state_path),
        "status": "noop",
        "alert": None,
        "alerts": [],
        "reason": None,
    }

    def persist() -> None:
        window_state["label"] = window_label
        window_state["threshold_alerts"] = threshold_alerts
        windows[window_label] = window_state
        save_state(state_path, state)

    if previous_bucket is None:
        window_state.update({
            "last_alerted_bucket": current_bucket,
            "last_seen_percent_remaining": round(percent_remaining, 3),
            "last_checked_at": now,
            "last_alerted_at": now if args.first_run_alert else None,
        })
        if args.first_run_alert:
            result["status"] = "alert"
            result["alerts"].append(build_bucket_alert(window_label, percent_remaining, previous_bucket))
        else:
            result["status"] = "initialized"
            result["reason"] = "State initialized without alert."
    elif current_bucket < int(previous_bucket):
        window_state.update({
            "last_alerted_bucket": current_bucket,
            "last_seen_percent_remaining": round(percent_remaining, 3),
            "last_checked_at": now,
            "last_alerted_at": now,
        })
        result["status"] = "alert"
        result["alerts"].append(build_bucket_alert(window_label, percent_remaining, int(previous_bucket)))
    elif current_bucket == int(previous_bucket):
        last_seen = window_state.get("last_seen_percent_remaining")
        hit_exact_decile = abs(percent_remaining - current_bucket) < 1e-9
        crossed_into_decile = hit_exact_decile and isinstance(last_seen, (int, float)) and float(last_seen) > float(current_bucket)
        window_state.update({
            "last_seen_percent_remaining": round(percent_remaining, 3),
            "last_checked_at": now,
            **({"last_alerted_at": now} if crossed_into_decile else {}),
        })
        if crossed_into_decile:
            result["status"] = "alert"
            result["alerts"].append(build_bucket_alert(window_label, percent_remaining, int(previous_bucket)))
        else:
            result["status"] = "noop"
            result["reason"] = "Already alerted for this bucket."
    else:
        window_state.update({
            "last_seen_percent_remaining": round(percent_remaining, 3),
            "last_checked_at": now,
            "last_alerted_bucket": current_bucket,
        })
        result["status"] = "noop"
        result["reason"] = "Bucket moved upward; state reset without alert."

    threshold_messages = []
    if percent_remaining <= 25 and not threshold_alerts.get("warn25"):
        threshold_alerts["warn25"] = True
        threshold_messages.append(build_threshold_alert(window_label, "warn25", percent_remaining))
    if window_label == "weekly" and percent_remaining <= 20 and not threshold_alerts.get("weekly20"):
        threshold_alerts["weekly20"] = True
        threshold_messages.append(build_threshold_alert(window_label, "weekly20", percent_remaining))
    if window_label == "weekly" and percent_remaining <= 15 and not threshold_alerts.get("weekly15"):
        threshold_alerts["weekly15"] = True
        threshold_messages.append(build_threshold_alert(window_label, "weekly15", percent_remaining))
    if percent_remaining <= 10 and not threshold_alerts.get("red10"):
        threshold_alerts["red10"] = True
        threshold_messages.append(build_threshold_alert(window_label, "red10", percent_remaining))
    if percent_remaining > 25:
        threshold_alerts["warn25"] = False
    if percent_remaining > 20:
        threshold_alerts["weekly20"] = False
    if percent_remaining > 15:
        threshold_alerts["weekly15"] = False
    if percent_remaining > 10:
        threshold_alerts["red10"] = False

    result["alerts"].extend(threshold_messages)
    if result["alerts"]:
        result["status"] = "alert"
        result["alert"] = "\n".join(result["alerts"])

    persist()

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        if result["alerts"]:
            print("\n".join(result["alerts"]))
        elif result["status"] == "initialized":
            print(f"Initialized {human_window_label(window_label)} state at bucket {current_bucket}% with no alert.")
        else:
            print(
                f"No alert: {result['reason']} Window: {human_window_label(window_label)}. "
                f"Current bucket: {current_bucket}%. Remaining: {percent_remaining:.1f}%."
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

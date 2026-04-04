#!/usr/bin/env python3
"""
Fetch MiniMax API usage and report with precise time calculations.
"""

import json
import os
import sys
import urllib.request
import yaml
from datetime import datetime, timezone, timedelta
from time_calc import get_current_interval, get_next_reset_time, get_time_until_reset, get_elapsed_in_interval

def get_local_timezone():
    import zoneinfo
    return datetime.now().astimezone().tzinfo

def get_timezone(tz_name=None):
    if tz_name is None:
        tz_name = os.environ.get("MINIMAX_TIMEZONE")
        if tz_name is None:
            return get_local_timezone()
    
    import zoneinfo
    try:
        return zoneinfo.ZoneInfo(tz_name)
    except KeyError:
        print(f"⚠️  Invalid timezone '{tz_name}', falling back to local timezone")
        return get_local_timezone()

def load_config():
    config_paths = [os.path.expanduser("~/.minimax_config.yml"), "config.yml"]
    for path in config_paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
    return {}

def init_timezone():
    config = load_config()
    tz_name = os.environ.get("MINIMAX_TIMEZONE") or config.get("timezone")
    if tz_name is None:
        return get_local_timezone()
    import zoneinfo
    try:
        return zoneinfo.ZoneInfo(tz_name)
    except KeyError:
        print(f"⚠️  Invalid timezone '{tz_name}', falling back to local timezone")
        return get_local_timezone()

TZ = init_timezone()

def now_utc8():
    return datetime.now(timezone.utc).astimezone(TZ)

def load_cookies():
    cookies = os.environ.get("MINIMAX_COOKIES", "")
    if not cookies:
        config = load_config()
        cookies = config.get("minimax_cookies", "")
    if not cookies:
        print("❌ MINIMAX_COOKIES env var not set.")
        print("   Set MINIMAX_COOKIES env var or create config.yml with minimax_cookies")
        sys.exit(1)
    return cookies

def fetch_usage():
    cookies = load_cookies()
    
    req = urllib.request.Request(
        "https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains?GroupId=2034608336271319731",
        headers={
            "Cookie": cookies,
            "origin": "https://platform.minimaxi.com",
            "referer": "https://platform.minimaxi.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = response.read().decode("utf-8")
    except urllib.error.URLError as e:
        print(f"❌ Network error: {e.reason}")
        print("   Please check your internet connection.")
        sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP error: {e.code}")
        print("   Cookies may be expired. Please update MINIMAX_COOKIES env var.")
        sys.exit(1)
    
    if not result.strip():
        print("❌ Failed to fetch usage data. Cookies may be expired.")
        print("   Please update MINIMAX_COOKIES env var.")
        sys.exit(1)
    
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        print("❌ Invalid response from API. Cookies may be expired.")
        print("   Please update MINIMAX_COOKIES env var.")
        sys.exit(1)

def format_time_remaining(hours, minutes, seconds):
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def time_bar(elapsed_hours, total_hours, block="█", width=20, label="", emoji="⏱️"):
    """Draw bar for time elapsed. e.g. ███████░░░░░░░░░░░░░ Time: 36% (3h 10m) ⏱️"""
    if total_hours <= 0:
        return block * width + " (N/A)" + (f" {label}" if label else "")
    filled = round((elapsed_hours / total_hours) * width)
    empty = width - filled
    pct = int((elapsed_hours / total_hours) * 100)
    remaining_mins = int((total_hours - elapsed_hours) * 60)
    if remaining_mins >= 60:
        remaining = f"{remaining_mins // 60}h {remaining_mins % 60}m"
    else:
        remaining = f"{remaining_mins}m"
    label_str = f"{label} " if label else ""
    emoji_str = f" {emoji}" if emoji else ""
    return block * filled + "░" * empty + f" {label_str}{pct}% ({remaining}){emoji_str}"

def ascii_bar(used, total, block="█", width=20, label=""):
    """Draw a horizontal ASCII bar chart. Each block = 5% (20 blocks for 100%)."""
    if total == 0:
        return block * width + " " + "(N/A)" + (f" {label}" if label else "")
    filled = round((used / total) * width)
    empty = width - filled
    bar = block * filled + "░" * empty
    pct = (used / total) * 100
    label_str = f"{label} " if label else ""
    return f"{bar} {label_str}{pct:.0f}% ({used}/{total})"

def main():
    now = now_utc8()
    data = fetch_usage()
    
    if data["base_resp"]["status_code"] == 1004:
        print("❌ Cookies expired. Please update MINIMAX_COOKIES env var:")
        print("   export MINIMAX_COOKIES='<your cookies>'")
        return
    
    print(f"📊 MiniMax Usage Report — {now.strftime('%Y-%m-%d %H:%M UTC+8')}\n")
    
    for model in data["model_remains"]:
        if model["model_name"] not in ["MiniMax-M*", "MiniMax-Hailuo-2.3-Fast-6s-768p"]:
            continue
            
        total = model.get("current_interval_total_count", 0)
        remaining = model.get("current_interval_usage_count", 0)
        used = total - remaining
        
        if total == 0:
            continue
        
        # Time calculations
        interval_start, interval_end = get_current_interval(now)
        next_reset = get_next_reset_time(now)
        hours, minutes, seconds = get_time_until_reset(now)
        time_str = format_time_remaining(hours, minutes, seconds)
        
        # Calculate interval total hours (handles 20:00→00:00 = 4h edge case)
        if interval_end.day != interval_start.day:
            total_interval_hours = 24 - interval_start.hour + interval_end.hour
        else:
            total_interval_hours = interval_end.hour - interval_start.hour
        
        # Hours elapsed as float (total - remaining time)
        hours_elapsed = total_interval_hours - (hours + minutes / 60 + seconds / 3600)
        
        # Format interval string
        if interval_end.day != interval_start.day:
            interval_str = f"{interval_start.hour:02d}:00 – {interval_end.hour:02d}:00+1day UTC+8"
        else:
            interval_str = f"{interval_start.hour:02d}:00 – {interval_end.hour:02d}:00 UTC+8"
        
        usage_pct = (remaining / total) * 100 if total > 0 else 0
        
        print(f"**{model['model_name']}**")
        print(f"  {ascii_bar(used, total, label='Quota:')}")
        print(f"  {time_bar(hours_elapsed, total_interval_hours, label='Time:')}")
        print(f"  Next reset: {next_reset.strftime('%H:%M UTC+8')}")
        
        if usage_pct < 10:
            print(f"  ⚠️  Warning: Quota nearly exhausted ({usage_pct:.0f}%)")
        print()

if __name__ == "__main__":
    main()

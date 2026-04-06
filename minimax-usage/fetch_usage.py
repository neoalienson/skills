#!/usr/bin/env python3
"""
Fetch MiniMax API usage and report with precise time calculations.
"""

import argparse
import functools
import json
import os
import sys
import urllib.request
import zoneinfo
import yaml
from datetime import datetime, timezone
from time_calc import get_current_interval, get_next_reset_time, get_time_until_reset

STATUS_SUCCESS = 0
STATUS_COOKIES_EXPIRED = 1004


class CookiesNotFoundError(Exception):
    pass


class CookiesExpiredError(Exception):
    pass


class NetworkError(Exception):
    pass


class HTTPError(Exception):
    pass


class InvalidResponseError(Exception):
    pass


def get_local_timezone():
    return datetime.now().astimezone().tzinfo


@functools.lru_cache(maxsize=1)
def get_timezone(tz_name=None, config_path=None, debug=False):
    if tz_name is None:
        if config_path:
            if debug:
                print(f"[DEBUG] Loading timezone from config: {config_path}")
            config = load_config(config_path)
            tz_name = config.get("timezone")
            if debug:
                print(f"[DEBUG]   Found timezone in config: {tz_name}")
        else:
            tz_name = os.environ.get("MINIMAX_TIMEZONE")
            if debug:
                print(f"[DEBUG] Checking MINIMAX_TIMEZONE env var: {tz_name}")
    
    if tz_name is None:
        local_tz = get_local_timezone()
        if debug:
            print(f"[DEBUG] No timezone found, using local: {local_tz}")
        return local_tz
    
    try:
        return zoneinfo.ZoneInfo(tz_name)
    except KeyError:
        print(f"⚠️  Invalid timezone '{tz_name}', falling back to local timezone")
        return get_local_timezone()


def load_config(config_path=None):
    if config_path:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return yaml.safe_load(f) or {}
        return {}
    
    config_paths = [os.path.expanduser("~/.minimax_config.yml"), "config.yml"]
    for path in config_paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
    return {}

def now_utc8(config_path=None, debug=False):
    return datetime.now(timezone.utc).astimezone(get_timezone(config_path=config_path, debug=debug))


def load_cookies(config_path=None, debug=False):
    if config_path:
        if debug:
            print(f"[DEBUG] Loading cookies from config: {config_path}")
        if not os.path.exists(config_path):
            raise CookiesNotFoundError(f"Config file not found: {config_path}")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
        if "minimax_cookies" in config and config["minimax_cookies"]:
            if debug:
                print(f"[DEBUG]   Found cookies in config")
            return config["minimax_cookies"]
        raise CookiesNotFoundError(f"Config file {config_path} does not contain 'minimax_cookies' field")
    
    cookies = os.environ.get("MINIMAX_COOKIES", "")
    if cookies:
        if debug:
            print(f"[DEBUG] Found cookies in MINIMAX_COOKIES env var")
        return cookies
    if debug:
        print(f"[DEBUG] No cookies in MINIMAX_COOKIES env var")
    
    config = load_config(config_path)
    if "minimax_cookies" in config and config["minimax_cookies"]:
        if debug:
            print(f"[DEBUG] Found cookies in default config file")
        return config["minimax_cookies"]
    
    raise CookiesNotFoundError(
        "No cookies found in MINIMAX_COOKIES env var or any config file. "
        "Set MINIMAX_COOKIES env var, or create config.yml with minimax_cookies"
    )

def fetch_usage(config_path=None, debug=False):
    cookies = load_cookies(config_path, debug=debug)
    
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
    except urllib.error.HTTPError as e:
        raise HTTPError(f"HTTP error {e.code}. Cookies may be expired.")
    except urllib.error.URLError as e:
        raise NetworkError(f"Network error: {e.reason}. Please check your internet connection.")
    
    if not result.strip():
        raise InvalidResponseError("Failed to fetch usage data. Cookies may be expired.")
    
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        raise InvalidResponseError("Invalid response from API. Cookies may be expired.")

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

def main(config_path=None, debug=False):
    try:
        if debug:
            print("[DEBUG] Loading timezone...")
        now = now_utc8(config_path, debug=debug)
        if debug:
            print("[DEBUG] Fetching usage data...")
        data = fetch_usage(config_path, debug=debug)
    except CookiesNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except (NetworkError, HTTPError, InvalidResponseError) as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    if data["base_resp"]["status_code"] == STATUS_COOKIES_EXPIRED:
        print("❌ Cookies may be expired. Please update your cookies.")
        print("   Check your config file or MINIMAX_COOKIES env var.")
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
        
        interval_start, interval_end = get_current_interval(now)
        next_reset = get_next_reset_time(now)
        hours, minutes, seconds = get_time_until_reset(now)
        
        if interval_end.day != interval_start.day:
            total_interval_hours = 24 - interval_start.hour + interval_end.hour
        else:
            total_interval_hours = interval_end.hour - interval_start.hour
        
        hours_elapsed = total_interval_hours - (hours + minutes / 60 + seconds / 3600)
        
        usage_pct = (remaining / total) * 100 if total > 0 else 0
        
        print(f"**{model['model_name']}**")
        print(f"  {ascii_bar(used, total, label='Usage:')}")
        print(f"  {time_bar(hours_elapsed, total_interval_hours, label='Time:')}")
        print(f"  Next reset: {next_reset.strftime('%H:%M UTC+8')}")
        
        if usage_pct < 10:
            print(f"  ⚠️  Warning: Usage nearly exhausted ({usage_pct:.0f}%)")
        print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch MiniMax API usage and report")
    parser.add_argument("-c", "--config", dest="config_path", help="Path to config file")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    main(args.config_path, debug=args.debug)

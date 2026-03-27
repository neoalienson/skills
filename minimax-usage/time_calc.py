"""
MiniMax usage reset time calculator.
Handles UTC+8 timezone with 5-hour reset intervals at 00:00, 05:00, 10:00, 15:00, 20:00.
"""

from datetime import datetime, timedelta
from typing import Tuple

RESET_HOURS = [0, 5, 10, 15, 20]  # UTC+8

def get_current_interval_start(now: datetime) -> int:
    """
    Return the reset hour (0,5,10,15,20) that started the current interval.
    
    Intervals:
      00:00 – 04:59 → start_hour = 0
      05:00 – 09:59 → start_hour = 5
      10:00 – 14:59 → start_hour = 10
      15:00 – 19:59 → start_hour = 15
      20:00 – 23:59 → start_hour = 20
    
    At exact reset time (HH:00:00.000), the NEW interval has just begun.
    """
    h = now.hour
    m = now.minute
    s = now.second
    ms = now.microsecond
    
    is_exact_reset = (m == 0 and s == 0 and ms == 0)
    
    # Find the largest reset hour <= current hour
    candidate = None
    for reset_hour in RESET_HOURS:
        if h > reset_hour:
            candidate = reset_hour
        elif h == reset_hour:
            if is_exact_reset:
                # At exact boundary: new interval is starting at this hour
                return reset_hour
            else:
                # Past the exact boundary (HH:MM:SS with M/S/MS > 0): in this interval
                return reset_hour
    
    # h < all reset hours (e.g., h=0 with m>0 — past 00:00 midnight)
    # The interval is 20:xx → which is the 20:00 reset from "yesterday"
    if candidate is None:
        candidate = RESET_HOURS[-1]  # 20
    
    return candidate

def get_next_reset_time(now: datetime) -> datetime:
    """
    Return the next UTC+8 reset datetime.
    
    At exact reset times (HH:00:00.000), that reset just happened,
    so the next distinct reset is the following one.
    """
    h = now.hour
    m = now.minute
    s = now.second
    ms = now.microsecond
    
    is_exact_reset = (m == 0 and s == 0 and ms == 0)
    
    for reset_hour in RESET_HOURS:
        if h < reset_hour:
            return now.replace(hour=reset_hour, minute=0, second=0, microsecond=0)
        elif h == reset_hour:
            if is_exact_reset:
                # At exact reset: this reset just happened, find the NEXT one
                continue
            else:
                # Past this reset's exact time: the next reset is the NEXT one
                # e.g., at 00:01, we've passed 00:00, so next is 05:00
                continue
    
    # All resets passed today → next is tomorrow 00:00
    tomorrow = now + timedelta(days=1)
    return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

def get_current_interval(now: datetime) -> Tuple[datetime, datetime]:
    """Return (interval_start, interval_end) for the current UTC+8 interval."""
    start_hour = get_current_interval_start(now)
    
    start = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    
    idx = RESET_HOURS.index(start_hour)
    if idx == len(RESET_HOURS) - 1:
        end = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        end_hour = RESET_HOURS[idx + 1]
        end = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)
    
    return start, end

def get_time_until_reset(now: datetime) -> Tuple[int, int, int]:
    """Return (hours, minutes, seconds) until next reset."""
    next_reset = get_next_reset_time(now)
    delta = next_reset - now
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return hours, minutes, seconds

def get_elapsed_in_interval(now: datetime) -> Tuple[int, int, int]:
    """Return (hours, minutes, seconds) elapsed in the current interval."""
    interval_start, interval_end = get_current_interval(now)
    delta = now - interval_start
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return hours, minutes, seconds

def format_interval(start: datetime, end: datetime) -> str:
    """Format interval as 'HH:MM – HH:MM UTC+8'."""
    return f"{start.hour:02d}:00 – {end.hour if end.day == start.day else (end.hour + 24) % 24:02d}:00 UTC+8"

def format_time_remaining(hours: int, minutes: int, seconds: int) -> str:
    """Format time remaining as 'Xh Ym' or 'Ym Zs'."""
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

---
name: minimax-usage
description: Check MiniMax API usage and quota. Triggers on phrases like "minimax usage", "minimax quota", "check API usage", "remaining units", "current interval usage". Fetches the current_interval_usage_count and remaining quota from the MiniMax API.
---

# MiniMax Usage

## Overview

Check your MiniMax API usage by calling the MiniMax platform API endpoint. Uses precise Python time calculations to correctly determine interval boundaries and next reset times.

## Files

- `fetch_usage.py` — Main script that fetches and reports usage
- `time_calc.py` — Time calculation module with full unit tests
- `test_time_calc.py` — 35 unit tests covering edge cases

## Usage

```bash
python3 fetch_usage.py
```

## Output Format

The script outputs a **horizontal bar chart** for each model, e.g.:

```
📊 MiniMax Usage Report — 2026-03-27 08:30 UTC+8

**MiniMax-M***
  Quota:  ████░░░░░░░░░░░░░░░░ 17% (103/600)
  ⏱️  Time: ██████████████░░░░░ 70% (1h 30m)
  Next reset: 10:00 UTC+8
```

Each `█` block represents 5% (20 blocks = 100%). Empty slots are shown as `░`.

## Usage Reset Schedule

Resets at **00:00, 05:00, 10:00, 15:00, 20:00** (UTC+8) — every 5 hours.

| Interval    | Start | End            |
| ----------- | ----- | -------------- |
| 00:00–05:00 | 00:00 | 05:00          |
| 05:00–10:00 | 05:00 | 10:00          |
| 10:00–15:00 | 10:00 | 15:00          |
| 15:00–20:00 | 15:00 | 20:00          |
| 20:00–00:00 | 20:00 | 00:00 (+1 day) |

## Time Calculation Rules

- **At exact reset time** (HH:00:00.000): The NEW interval has just begun
- **After reset** (HH:MM:SS with M/S/MS > 0): In the current interval
- **At midnight with past-time** (00:01+): Still in 00:00–05:00 interval

## Cookies

Set the `MINIMAX_COOKIES` environment variable with your session cookies:

```bash
export MINIMAX_COOKIES='<your cookies>'
```

If the API returns `{"base_resp":{"status_code":1004,"status_msg":"cookie is missing, log in again"}}`, the cookies have expired — refresh them in your browser and update the env var.

## API Endpoint

```bash
curl 'https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains?GroupId=2034608336271319731' \
  -H "Cookie: $MINIMAX_COOKIES" \
  -H 'origin: https://platform.minimaxi.com' \
  -H 'referer: https://platform.minimaxi.com/' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0'
```

## Key Interpretation

- `current_interval_usage_count` = **remaining** quota (NOT used count)
- `current_interval_total_count` = total allowed in interval
- Used = total − remaining

## Running Tests

```bash
cd ~/openclaw-git/skills/minimax-usage
python3 -m pytest test_time_calc.py -v
```

---
name: minimax-usage
description: Check MiniMax API usage and quota. Triggers on phrases like "minimax usage", "minimax quota", "check API usage", "remaining units", "current interval usage". Fetches the current_interval_usage_count and remaining quota from the MiniMax API.
---

# MiniMax Usage

## Overview

Check your MiniMax API usage by calling the MiniMax platform API endpoint. Uses precise Python time calculations to correctly determine interval boundaries and next reset times.

## Files

- `fetch_usage.py` — Main script that fetches and reports usage

## Usage

```bash
python3 fetch_usage.py -c `path to run config.yml`
```

## Output Format

The script outputs a **horizontal bar chart** for each model, e.g.:

```
📊 MiniMax Usage Report — 2026-03-27 08:30 UTC+8

**MiniMax-M***
  ███████████████░░░░░ Usage: 73% (440/600) 
  ███████░░░░░░░░░░░░░ Time:  36% (3h 10m) ⏱️
  Next reset: 15:00 UTC+8
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

## Key Interpretation

- `current_interval_usage_count` = **remaining** quota (NOT used count)
- `current_interval_total_count` = total allowed in interval
- Used = total − remaining

If the API returns `{"base_resp":{"status_code":1004,"status_msg":"cookie is missing, log in again"}}`, the cookies have expired — refresh them in your browser and update the env var.


# MiniMax Usage Checker

A CLI tool to fetch and display your MiniMax API usage with precise time calculations.

## Requirements

- Python 3.9+
- PyYAML (`pip install -r requirements.txt`)

## Setup

### 1. Get Cookies

1. Login to [https://platform.minimaxi.com](https://platform.minimaxi.com)
2. Open Developer Tools (F12) → Application → Cookies
3. Copy the cookie value

### 2. Configure Credentials

**Option A: Environment Variable**
```bash
export MINIMAX_COOKIES='your_cookie_value'
```

**Option B: config.yml**
Create a `config.yml` file:
```yaml
minimax_cookies: your_cookie_value_here
# timezone: (optional, defaults to system timezone)
```

### 3. Configure Timezone (Optional)

Set in `config.yml` or via `MINIMAX_TIMEZONE` env var (defaults to system timezone):
```yaml
timezone: Asia/Shanghai
```

Common values:
- `UTC` - Coordinated Universal Time
- `Asia/Shanghai` - China (UTC+8)
- `Asia/Hong_Kong` - Hong Kong (UTC+8)
- `America/New_York` - US Eastern
- `America/Los_Angeles` - US Pacific
- `Europe/London` - UK

## Usage

```bash
python fetch_usage.py [-c CONFIG_PATH]
```

Options:
- `-c CONFIG_PATH`  Path to config file (overrides default locations)

## Sample Config

```yaml
minimax_cookies: sensorsdata2015jssdkchannel=...; HERTZ-SESSION=...
timezone: Asia/Hong_Kong
```

## Automated Scheduling

The script is designed for isolated, scheduled execution. Key settings for effective automation:

### Recommended Schedule

For Hong Kong timezone (UTC+8), runs before and after each 5-hour quota window:
```
0 02,03,08,09,13,14,16,18,19,22,23 * * *
```

### Session Settings

- **isolated**: Fast execution, no context carryover
- **wakeMode: now**: Start immediately at scheduled time
- **timeoutSeconds: 600**: 10 minutes max per run
- **lightContext: true**: Reduced context for speed

### Sample Prompt for Job Scheduler

```
Use the "minimax-usage" skill for this request
/home/neo/skills/minimax-usage/SKILL.md
The config file locates at /home/neo/skills/minimax-usage/config.yml
do not create new file
stop when encounter any error
keep the output format from the skill
```

### Sample cronjob in json

```json
 jobs.json
{
  "version": 1,
  "jobs": [
    {
      "agentId": "isadora",
      "name": "MiniMax Usage",
      "enabled": true,
      "schedule": {
        "kind": "cron",
        "expr": "0 02,03,08,09,13,14,16,18,19,22,23 * * *",
        "tz": "Asia/Hong_Kong"
      },
      "sessionTarget": "isolated",
      "wakeMode": "now",
      "payload": {
        "kind": "agentTurn",
        "message": "Use the \"minimax-usage\" skill for this request\nThe config file locates at /skills/minimax-usage/config.yml\ndo not create new file\nstop when encounter any error\nkeep the output format from the skill",
        "timeoutSeconds": 600,
        "lightContext": true
      },
      "deleteAfterRun": false,
      "sessionKey": "agent:isadora:main",
      "delivery": {
        "mode": "announce",
        "channel": "telegram",
        "bestEffort": false
      }
    }
  ]
}
```

## Run Tests

```bash
pytest
```

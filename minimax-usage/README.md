# MiniMax Usage Checker

A CLI tool to fetch and display your MiniMax API usage with precise time calculations.

## Requirements

- Python 3.9+
- PyYAML (`pip install -r requirements.txt`)

## Setup

### 1. Get API Key

1. Login to [https://platform.minimaxi.com](https://platform.minimaxi.com)
2. Go to Settings → API Keys
3. Create a new API key and copy it

### 2. Configure API Key

**Option A: Environment Variable**
```bash
export MINIMAX_API_KEY='your_api_key'
```

**Option B: config.yml**
Create a `config.yml` file:
```yaml
api_key: your_api_key_here
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
python scripts/minimax-usage.py [-c CONFIG_PATH]
```

Options:
- `-c CONFIG_PATH`  Path to config file (overrides default locations)

## Troubleshooting

### "complex interpreter invocation detected" Error

If you see this error when scheduling:
```
[tools] exec failed: exec preflight: complex interpreter invocation detected; refusing to run without script preflight validation.
```

**Cause**: The scheduler is using a complex command like `cd /path && python3 script.py` which triggers preflight validation.

**Solution**: Use the `-c` flag to specify the config path directly, avoiding the need for `cd`:

```bash
python3 /skills/minimax-usage/scripts/minimax-usage.py -c /skills/minimax-usage/config.yml
```

In your scheduler prompt, pass the config path via `-c`:
```
Use the "minimax-usage" skill for this request
/skills/minimax-usage/SKILL.md
-c /skills/minimax-usage/config.yml
do not create new file
stop when encounter any error
keep the output format from the skill
```

## Sample Config

```yaml
api_key: your_api_key_here
timezone: Asia/Shanghai
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
/skills/minimax-usage/SKILL.md
The config file locates at /skills/minimax-usage/config.yml
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

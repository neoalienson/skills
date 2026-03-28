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
- `America/New_York` - US Eastern
- `America/Los_Angeles` - US Pacific
- `Europe/London` - UK

## Usage

```bash
python fetch_usage.py
```

## Run Tests

```bash
pytest
```

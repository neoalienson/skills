# MiniMax Usage Checker

A CLI tool to fetch and display your MiniMax API usage with precise time calculations.

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

**Option B: Local Config File**
Create a file named `cookies.txt` (or `.minimax_cookies`) in the project directory:
```
MINIMAX_COOKIES=your_cookie_value
```

## Usage

```bash
python fetch_usage.py
```

## Run Tests

```bash
python test_fetch_usage.py
```

#!/usr/bin/env python3
"""Update cookie in config.yml extracted from a curl command file."""

import argparse
import re
import sys
import os


def extract_cookie_from_curl_file(curl_file_path: str) -> str:
    """Extract cookie value from a curl command file."""
    if not os.path.exists(curl_file_path):
        raise FileNotFoundError(f"File '{curl_file_path}' not found")

    with open(curl_file_path, "r") as f:
        content = f.read()

    match = re.search(r"-b\s+['\"]([^'\"]+)['\"]", content)
    if not match:
        raise ValueError("No cookie found in curl command")

    return match.group(1)


def update_cookie_in_config(config_path: str, cookie: str) -> None:
    """Update or add minimax_cookies in config.yml, preserving other values."""
    escaped_cookie = cookie.replace("\\", "\\\\").replace("'", "''")

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            lines = f.readlines()
    else:
        lines = []

    updated = False
    new_lines = []
    for line in lines:
        if line.startswith("minimax_cookies:"):
            new_lines.append(f"minimax_cookies: '{escaped_cookie}'\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"minimax_cookies: '{escaped_cookie}'\n")

    with open(config_path, "w") as f:
        f.writelines(new_lines)


def main():
    parser = argparse.ArgumentParser(description="Update cookie in config.yml from curl command file")
    parser.add_argument("curl_file", help="Path to file containing curl command with cookie")
    parser.add_argument("--config", default="config.yml", help="Path to config file (default: config.yml)")
    args = parser.parse_args()

    try:
        cookie = extract_cookie_from_curl_file(args.curl_file)
        update_cookie_in_config(args.config, cookie)
        print(f"Cookie updated in {args.config}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

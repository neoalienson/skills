#!/bin/bash

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <curl_command_file>"
  exit 1
fi

CURL_FILE="$1"
CONFIG_FILE="config.yml"

if [ ! -f "$CURL_FILE" ]; then
  echo "Error: File '$CURL_FILE' not found"
  exit 1
fi

COOKIE=$(sed -n "s/.*-b '\([^']*\)'.*/\1/p" "$CURL_FILE")

if [ -z "$COOKIE" ]; then
  COOKIE=$(sed -n 's/.*-b "\([^"]*\)".*/\1/p' "$CURL_FILE")
fi

if [ -z "$COOKIE" ]; then
  echo "Error: No cookie found in curl command"
  exit 1
fi

ESCAPED_COOKIE=$(echo "$COOKIE" | sed 's/["\]/\\&/g')

sed -i "s|^minimax_cookies:.*|minimax_cookies: $ESCAPED_COOKIE|" "$CONFIG_FILE"

echo "Cookie updated in $CONFIG_FILE"
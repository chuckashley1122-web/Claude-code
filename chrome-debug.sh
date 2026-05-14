#!/usr/bin/env bash
# chrome-debug.sh — launch Chrome with the DevTools Protocol enabled so that
# the chrome-devtools MCP server (see .mcp.json) can drive it from Claude Code.
#
# Usage:
#   ./chrome-debug.sh [url]
#   CHROME_DEBUG_PORT=9333 ./chrome-debug.sh https://example.com
#
# Chrome runs against an isolated profile (default: /tmp/claude-chrome-debug)
# so it does not touch your normal browsing data. Leave the process running
# while you work with Claude Code; close the window to stop.

set -euo pipefail

port="${CHROME_DEBUG_PORT:-9222}"
profile_dir="${CHROME_DEBUG_PROFILE:-/tmp/claude-chrome-debug}"
url="${1:-about:blank}"

if [[ -n "${CHROME_BIN:-}" ]]; then
    chrome="$CHROME_BIN"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
else
    chrome=$(command -v google-chrome \
        || command -v google-chrome-stable \
        || command -v chromium \
        || command -v chromium-browser \
        || true)
fi

if [[ -z "$chrome" || ! -x "$chrome" ]]; then
    echo "Chrome not found. Install Google Chrome or set CHROME_BIN." >&2
    exit 1
fi

mkdir -p "$profile_dir"

echo "Launching Chrome with remote debugging on port $port"
echo "Profile:      $profile_dir"
echo "DevTools URL: http://127.0.0.1:$port"

exec "$chrome" \
    --remote-debugging-port="$port" \
    --user-data-dir="$profile_dir" \
    --no-first-run \
    --no-default-browser-check \
    "$url"

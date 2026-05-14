#!/usr/bin/env bash
# setup-chrome-debug.sh — wire Claude Code to a debuggable Chrome instance.
#
# Steps:
#   1. Ensure the Claude Code CLI is installed (`npm i -g @anthropic-ai/claude-code`).
#   2. Launch Chrome with --remote-debugging-port using a dedicated profile.
#   3. Register the chrome-devtools-mcp server with Claude Code so it can drive Chrome.
#
# Usage:
#   ./setup-chrome-debug.sh                       Run the full setup on port 9222
#   ./setup-chrome-debug.sh --port 9333           Use a different debugging port
#   ./setup-chrome-debug.sh --no-launch           Skip the Chrome launch (already running)
#   ./setup-chrome-debug.sh --profile-dir PATH    Override the debug profile directory
#   ./setup-chrome-debug.sh --scope project       Register MCP at project scope (default: user)

set -euo pipefail

port=9222
launch_chrome=1
profile_dir="$HOME/.chrome-debug-profile"
mcp_scope="user"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --port) port="$2"; shift 2 ;;
        --no-launch) launch_chrome=0; shift ;;
        --profile-dir) profile_dir="$2"; shift 2 ;;
        --scope) mcp_scope="$2"; shift 2 ;;
        -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
        *) echo "Unknown arg: $1" >&2; exit 2 ;;
    esac
done

# 1. Claude Code CLI
if ! command -v claude >/dev/null 2>&1; then
    if ! command -v npm >/dev/null 2>&1; then
        echo "npm not found. Install Node.js from https://nodejs.org and retry." >&2
        exit 1
    fi
    echo "Installing @anthropic-ai/claude-code globally..."
    npm install -g @anthropic-ai/claude-code
fi
echo "Claude Code: $(claude --version 2>/dev/null || echo installed)"

# 2. Locate Chrome
chrome=""
for cand in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "$(command -v google-chrome 2>/dev/null || true)" \
    "$(command -v google-chrome-stable 2>/dev/null || true)" \
    "$(command -v chromium 2>/dev/null || true)" \
    "$(command -v chromium-browser 2>/dev/null || true)"; do
    if [[ -n "$cand" && -x "$cand" ]]; then
        chrome="$cand"
        break
    fi
done

if [[ -z "$chrome" ]]; then
    echo "Could not find Chrome or Chromium. Install Chrome and retry." >&2
    exit 1
fi
echo "Chrome: $chrome"

# 3. Launch Chrome with remote debugging
if [[ "$launch_chrome" -eq 1 ]]; then
    if curl -fs "http://127.0.0.1:$port/json/version" >/dev/null 2>&1; then
        echo "Chrome already listening on port $port — skipping launch."
    else
        mkdir -p "$profile_dir"
        echo "Launching Chrome (--remote-debugging-port=$port, profile=$profile_dir)..."
        "$chrome" \
            --remote-debugging-port="$port" \
            --user-data-dir="$profile_dir" \
            >/dev/null 2>&1 &

        for _ in 1 2 3 4 5 6 7 8 9 10; do
            if curl -fs "http://127.0.0.1:$port/json/version" >/dev/null 2>&1; then break; fi
            sleep 1
        done
        if ! curl -fs "http://127.0.0.1:$port/json/version" >/dev/null 2>&1; then
            echo "Chrome did not open a debugging endpoint on port $port." >&2
            exit 1
        fi
    fi
fi

# 4. Register chrome-devtools-mcp with Claude Code
echo "Registering chrome-devtools MCP server (scope=$mcp_scope)..."
claude mcp remove chrome-devtools --scope "$mcp_scope" 2>/dev/null || true
claude mcp add chrome-devtools \
    --scope "$mcp_scope" \
    -- npx -y chrome-devtools-mcp@latest --browser-url "http://127.0.0.1:$port"

echo
echo "Done. Start a Claude Code session and try:"
echo "  > open https://example.com and tell me the <h1> text"

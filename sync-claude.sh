#!/usr/bin/env bash
# sync-claude.sh — sync ~/.claude between this machine and OneDrive.
#
# Usage:
#   ./sync-claude.sh pull              Copy from OneDrive to ~/.claude (restore)
#   ./sync-claude.sh push              Copy from ~/.claude to OneDrive (backup)
#   ./sync-claude.sh pull --dry-run    Preview without copying
#   CLAUDE_ONEDRIVE_PATH=/path/to/OneDrive/ClaudeBackup/.claude ./sync-claude.sh pull
#
# OneDrive path auto-detected for macOS (~/Library/CloudStorage/OneDrive-*).
# On Linux without OneDrive client, set CLAUDE_ONEDRIVE_PATH or use rclone separately.

set -euo pipefail

direction="${1:-}"
dry_run=""
if [[ "${2:-}" == "--dry-run" ]]; then
    dry_run="--dry-run"
fi

if [[ "$direction" != "pull" && "$direction" != "push" ]]; then
    echo "Usage: $0 {pull|push} [--dry-run]" >&2
    exit 2
fi

local_claude="$HOME/.claude"

if [[ -n "${CLAUDE_ONEDRIVE_PATH:-}" ]]; then
    onedrive_claude="$CLAUDE_ONEDRIVE_PATH"
else
    # macOS OneDrive default location.
    onedrive_root=$(find "$HOME/Library/CloudStorage" -maxdepth 1 -type d -name 'OneDrive-*' 2>/dev/null | head -n1 || true)
    if [[ -z "$onedrive_root" ]]; then
        echo "OneDrive not detected. Set CLAUDE_ONEDRIVE_PATH to your backup folder." >&2
        exit 1
    fi
    onedrive_claude="$onedrive_root/ClaudeBackup/.claude"
fi

if [[ "$direction" == "pull" ]]; then
    src="$onedrive_claude"
    dst="$local_claude"
else
    src="$local_claude"
    dst="$onedrive_claude"
fi

if [[ ! -d "$src" ]]; then
    echo "Source not found: $src" >&2
    exit 1
fi

mkdir -p "$dst"

echo "Syncing $src/ -> $dst/"
[[ -n "$dry_run" ]] && echo "(dry run — no files will be copied)"

# Additive sync (no --delete). Excludes credentials, caches, transient state.
rsync -av $dry_run \
    --exclude='.credentials.json' \
    --exclude='.lock' \
    --exclude='*.log' \
    --exclude='statsig/' \
    --exclude='cache/' \
    --exclude='shell-snapshots/' \
    --exclude='todos/' \
    --exclude='ide/' \
    --exclude='logs/' \
    "$src/" "$dst/"

echo "Done."

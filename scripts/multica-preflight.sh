#!/usr/bin/env bash
# multica-preflight.sh — check whether this machine can host a Multica runtime.
#
# Usage:
#   ./scripts/multica-preflight.sh
#
# Read-only: reports what's present and what's missing. Installs nothing and
# changes no state. See docs/multica-setup.md for what to do about each gap.
#
# Exit codes: 0 = ready to run `multica setup`, 1 = blocking gaps found.

set -uo pipefail

blockers=0
notes=0

ok()    { printf '  \033[32mok\033[0m    %s\n' "$1"; }
gap()   { printf '  \033[31mgap\033[0m   %s\n' "$1"; blockers=$((blockers + 1)); }
note()  { printf '  \033[33mnote\033[0m  %s\n' "$1"; notes=$((notes + 1)); }

echo
echo "Multica preflight — $(hostname)"
echo

# --- Agent CLIs -------------------------------------------------------------
# The daemon auto-detects these at startup; at least one must be installed AND
# signed in, or an agent will have no provider to run.
echo "Agent CLIs (need at least one):"
found_cli=0
for cli in claude codex cursor-agent opencode copilot; do
    if command -v "$cli" >/dev/null 2>&1; then
        ok "$cli — $(command -v "$cli")"
        found_cli=$((found_cli + 1))
    fi
done
if [[ "$found_cli" -eq 0 ]]; then
    gap "none found. Install at least one (e.g. Claude Code) and sign in."
else
    note "installed ≠ signed in. Run one manually once to confirm it authenticates."
fi
echo

# --- Multica CLI ------------------------------------------------------------
echo "Multica CLI:"
if command -v multica >/dev/null 2>&1; then
    # `multica version` (not `--version`) — matches how install.sh probes it.
    ok "multica — $(multica version 2>/dev/null | head -n1 || echo 'version unknown')"

    echo
    echo "Daemon:"
    if multica daemon status >/dev/null 2>&1; then
        ok "daemon responding to \`multica daemon status\`"
        note "confirm the machine shows as active under Settings → Runtimes."
    else
        gap "daemon not responding. Run \`multica setup\` (first time), or \`multica daemon start\`."
    fi

    echo
    echo "Authentication:"
    if multica auth status >/dev/null 2>&1; then
        ok "CLI is authenticated"
    else
        gap "not authenticated. Run \`multica setup\`, or \`multica login --token <TOKEN>\`."
    fi
else
    gap "not installed. See docs/multica-setup.md Part 1a."
fi
echo

# --- Docker (self-hosting only) ---------------------------------------------
echo "Docker (only needed to self-host the server):"
if ! command -v docker >/dev/null 2>&1; then
    note "docker not installed — fine unless you plan to self-host."
elif docker info >/dev/null 2>&1; then
    ok "docker installed and daemon running"
else
    note "docker installed but the daemon isn't running — start it before \`multica setup self-host\`."
fi
echo

# --- Persistence ------------------------------------------------------------
# A runtime is tied to the machine that registered it. Ephemeral containers
# deregister themselves when they're reclaimed, which looks like a runtime that
# silently vanishes.
echo "Host persistence:"
if [[ -f /.dockerenv ]] || grep -qaE '(docker|containerd|kubepods)' /proc/1/cgroup 2>/dev/null; then
    gap "this looks like a container. Runtimes registered here disappear when it's reclaimed — run on a persistent machine."
else
    # Only container markers are detectable here; a microVM or a cloud dev box
    # leaves none, so this is a hint, not a verdict.
    note "no container markers found — but confirm this machine actually stays up. Runtimes on ephemeral hosts vanish when reclaimed."
fi
echo

# --- Summary ----------------------------------------------------------------
if [[ "$blockers" -eq 0 ]]; then
    echo "Ready. Next: \`multica setup\`, then check Settings → Runtimes."
    exit 0
fi

echo "$blockers blocking gap(s) above. See docs/multica-setup.md."
exit 1

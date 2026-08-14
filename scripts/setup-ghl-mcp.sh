#!/usr/bin/env bash
# Set up the GoHighLevel MCP server for Claude Code.
#
# Prompts for a Private Integration Token, verifies it against the live
# GoHighLevel API, and registers the server with Claude Code. Safe to re-run.
#
#   ./scripts/setup-ghl-mcp.sh
#
# Create the token first: Settings -> Integrations -> Private Integrations in
# your GoHighLevel dashboard. See docs/ghl-mcp-setup.md.

set -euo pipefail

SERVER_NAME="ghl-mcp"
SERVER_PKG="@nerdsnipe-inc/ghl-mcp-server"
API_HOST="https://services.leadconnectorhq.com"
API_VERSION="2021-07-28"
DEFAULT_LOCATION="te1aYxyEeYsXcFJhnET6"

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
info() { printf '  %s\n' "$1"; }
warn() { printf '\033[33m  %s\033[0m\n' "$1"; }
fail() { printf '\033[31merror:\033[0m %s\n' "$1" >&2; exit 1; }
step() { printf '\n'; bold "==> $1"; }

# --- 1. Prerequisites ---------------------------------------------------------
step "Checking prerequisites"

command -v node >/dev/null || fail "Node.js is not installed. Need 18+: https://nodejs.org"
command -v npx  >/dev/null || fail "npx is not available (it ships with npm)."
command -v curl >/dev/null || fail "curl is not installed."

node_major="$(node -p 'process.versions.node.split(".")[0]')"
[ "$node_major" -ge 18 ] || fail "Node.js 18+ required, found $(node --version)."
info "node: $(node --version)"

# --- 2. Collect credentials ---------------------------------------------------
step "Credentials"

cat <<EOF
  Create a Private Integration Token in your GoHighLevel dashboard:
    Settings -> Integrations -> Private Integrations -> Create new integration

  Enable the scopes you want Claude to have. Read-only scopes
  (contacts.readonly, opportunities.readonly, ...) are a safe starting point;
  write scopes change live CRM data.

EOF

warn "Prefer a sandbox sub-account here. $DEFAULT_LOCATION is a live location,"
warn "and these tools change real records. Switch to production once tested."
printf '\n'

read -r -p "  Location ID [$DEFAULT_LOCATION]: " ghl_location
ghl_location="${ghl_location:-$DEFAULT_LOCATION}"

if [ "$ghl_location" = "$DEFAULT_LOCATION" ]; then
  read -r -p "  That is the live location. Continue anyway? [y/N] " confirm
  case "$confirm" in
    [yY]|[yY][eE][sS]) ;;
    *) fail "Aborted. Re-run with a sandbox location ID." ;;
  esac
fi

read -r -s -p "  Private Integration Token (hidden): " ghl_pit_token
printf '\n'
[ -n "$ghl_pit_token" ] || fail "Token cannot be empty."

case "$ghl_pit_token" in
  pit-*) ;;
  *) warn "That doesn't start with 'pit-'. A regular API key will not work here." ;;
esac

# --- 3. Verify the token before wiring anything up ----------------------------
step "Verifying the token against $API_HOST"

http_code="$(
  curl -s -o /dev/null -w '%{http_code}' --max-time 30 \
    -H "Authorization: Bearer $ghl_pit_token" \
    -H "Version: $API_VERSION" \
    "$API_HOST/contacts/?locationId=$ghl_location&limit=1" || echo 000
)"

case "$http_code" in
  200)
    info "token works and can read contacts in $ghl_location"
    ;;
  401)
    fail "401 Unauthorized — the token is wrong, revoked, or not a Private Integration token."
    ;;
  403)
    warn "403 Forbidden — the token is valid but lacks 'contacts.readonly'."
    warn "Continuing; add the scopes you need in Settings -> Integrations."
    ;;
  404)
    fail "404 — location '$ghl_location' not found for this token. Check the ID."
    ;;
  000)
    fail "Could not reach $API_HOST. Check your network and try again."
    ;;
  *)
    warn "Unexpected HTTP $http_code from the API. Continuing anyway."
    ;;
esac

# --- 4. Register with Claude Code ---------------------------------------------
step "Registering with Claude Code"

if ! command -v claude >/dev/null; then
  warn "the 'claude' CLI is not on PATH — register it manually with:"
  info "claude mcp add $SERVER_NAME -s user \\"
  info "  --env GHL_PIT_TOKEN=<your-token> \\"
  info "  --env GHL_LOCATION=$ghl_location \\"
  info "  -- npx -y $SERVER_PKG"
else
  if claude mcp get "$SERVER_NAME" >/dev/null 2>&1; then
    info "'$SERVER_NAME' already registered — replacing it"
    claude mcp remove "$SERVER_NAME" -s user >/dev/null 2>&1 || true
  fi
  claude mcp add "$SERVER_NAME" -s user \
    --env "GHL_PIT_TOKEN=$ghl_pit_token" \
    --env "GHL_LOCATION=$ghl_location" \
    -- npx -y "$SERVER_PKG"
  info "registered '$SERVER_NAME' for your user account"
fi

unset ghl_pit_token

# --- 5. Done ------------------------------------------------------------------
step "Done"

cat <<EOF
  Verify with:

      claude mcp list          # $SERVER_NAME should show as connected
      claude mcp get $SERVER_NAME

  Then ask Claude for something read-only first, e.g.
  "list the opportunities in my GoHighLevel location".

  To use this repo's .mcp.json entry too, export both values in your shell
  profile (keep the token out of anything you commit):

      export GHL_PIT_TOKEN=<your-token>
      export GHL_LOCATION=$ghl_location

  Remember: these tools write to the live CRM. There is no sandbox.
EOF

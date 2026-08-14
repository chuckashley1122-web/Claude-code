#!/usr/bin/env bash
# Set up the GoHighLevel MCP server (open-ghl-mcp) for Claude Code.
#
# Clones the server, installs it, collects your Marketplace app credentials,
# runs the OAuth flow, and registers it with Claude Code. Safe to re-run.
#
#   ./scripts/setup-ghl-mcp.sh [install-dir]
#
# See docs/ghl-mcp-setup.md for what each step is doing and why.

set -euo pipefail

REPO_URL="https://github.com/basicmachines-co/open-ghl-mcp.git"
SERVER_NAME="ghl-mcp"
INSTALL_DIR="${1:-${GHL_MCP_DIR:-$HOME/code/open-ghl-mcp}}"

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
info() { printf '  %s\n' "$1"; }
fail() { printf '\033[31merror:\033[0m %s\n' "$1" >&2; exit 1; }

step() { printf '\n'; bold "==> $1"; }

# --- 1. Prerequisites ---------------------------------------------------------
step "Checking prerequisites"

command -v git >/dev/null || fail "git is not installed."
command -v uv >/dev/null || fail "uv is not installed. See https://docs.astral.sh/uv/getting-started/installation/"

# open-ghl-mcp needs Python 3.12+. uv can fetch it, so this is informational.
if command -v python3 >/dev/null; then
  py_version="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  info "system python3: $py_version (server needs 3.12+; uv will fetch it if missing)"
fi
info "uv:        $(uv --version)"
info "install to: $INSTALL_DIR"

# --- 2. Clone or update -------------------------------------------------------
step "Fetching the server"

if [ -d "$INSTALL_DIR/.git" ]; then
  info "already cloned, pulling latest"
  git -C "$INSTALL_DIR" pull --ff-only
else
  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

# --- 3. Credentials -----------------------------------------------------------
step "Configuring credentials"

ENV_FILE="$INSTALL_DIR/.env"

if [ -f "$ENV_FILE" ] && grep -q '^GHL_CLIENT_ID=.' "$ENV_FILE" 2>/dev/null; then
  info "$ENV_FILE already has GHL_CLIENT_ID — leaving it alone"
  info "(delete the file and re-run this script to replace the credentials)"
else
  cat <<'EOF'
  You need a GoHighLevel Marketplace app (marketplace.gohighlevel.com ->
  My Apps -> Create App), with its Redirect URL set to exactly:

      http://localhost:8080/oauth/callback

  Creating an app requires agency-level access. If you do not see "My Apps",
  ask the agency owner to create it and send you the two values below.

EOF
  read -r -p "  GHL Client ID: " ghl_client_id
  read -r -s -p "  GHL Client Secret (hidden): " ghl_client_secret
  printf '\n'

  [ -n "$ghl_client_id" ]     || fail "Client ID cannot be empty."
  [ -n "$ghl_client_secret" ] || fail "Client Secret cannot be empty."

  # Written with restrictive permissions; never echoed back to the terminal.
  umask 077
  cat > "$ENV_FILE" <<EOF
GHL_CLIENT_ID=$ghl_client_id
GHL_CLIENT_SECRET=$ghl_client_secret
EOF
  chmod 600 "$ENV_FILE"
  unset ghl_client_secret
  info "wrote $ENV_FILE (mode 600, gitignored by the server repo)"
fi

# --- 4. Install ---------------------------------------------------------------
step "Installing dependencies"

cd "$INSTALL_DIR"
uv venv
uv pip install -r requirements.txt

# --- 5. Authorize -------------------------------------------------------------
step "Authorizing against GoHighLevel"

cat <<'EOF'
  A browser window will open. When it does:

    - choose the SUB-ACCOUNT (location) scope, not the agency/company scope
    - select the location you want Claude to manage

  A location token is locked to that one sub-account; a company token can
  reach every sub-account under the agency.

  The server keeps running after authorizing (that is what an idle stdio MCP
  server looks like). Once the browser says it succeeded, press Ctrl-C here
  and this script will continue.

EOF
read -r -p "  Press Enter to start the OAuth flow... " _

# The server does not exit on its own, so Ctrl-C is the expected way out.
# Don't let that abort the script.
set +e
trap ' ' INT
uv run python -m src.main --reauth
trap - INT
set -e

# --- 6. Register with Claude Code ---------------------------------------------
step "Registering with Claude Code"

if ! command -v claude >/dev/null; then
  info "the 'claude' CLI is not on PATH — register it manually with:"
  info "  claude mcp add $SERVER_NAME -s user -- uv run --directory $INSTALL_DIR python -m src.main"
else
  if claude mcp get "$SERVER_NAME" >/dev/null 2>&1; then
    info "'$SERVER_NAME' is already registered — removing and re-adding"
    claude mcp remove "$SERVER_NAME" -s user >/dev/null 2>&1 || true
  fi
  claude mcp add "$SERVER_NAME" -s user -- \
    uv run --directory "$INSTALL_DIR" python -m src.main
  info "registered '$SERVER_NAME' for your user account"
fi

# --- 7. Done ------------------------------------------------------------------
step "Done"

cat <<EOF
  Verify with:

      claude mcp list          # $SERVER_NAME should show as connected
      claude mcp get $SERVER_NAME

  To use this repo's .mcp.json entry as well, export the install path in your
  shell profile so it resolves:

      export GHL_MCP_DIR=$INSTALL_DIR

  Then, in Claude Code, try a read-only call first — ask for the opportunities
  in your location. Every location-scoped tool takes a locationId, which is the
  ID in your dashboard URL (.../v2/location/<locationId>/...).

  Re-authorize later (e.g. after changing scopes):

      cd $INSTALL_DIR && uv run python -m src.main --reauth
EOF

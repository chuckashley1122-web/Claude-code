# Wiring GoHighLevel to Claude Code (GHL MCP)

This guide connects your GoHighLevel sub-account to Claude Code, so Claude can
read and act on contacts, opportunities, calendars, forms, and workflows the
same way it reads and writes code here.

Your account is on a **white-labelled** GHL instance:

| Thing | Value |
|-------|-------|
| Dashboard | `https://app.scalecertified.com` |
| Location (sub-account) ID | `te1aYxyEeYsXcFJhnET6` |
| API host | `https://services.leadconnectorhq.com` (same for all white-labels) |
| Integrations page | [Settings → Integrations](https://app.scalecertified.com/v2/location/te1aYxyEeYsXcFJhnET6/integration) |

The white-label only changes the *dashboard* domain — the API is still
GoHighLevel's, so everything below works unchanged.

## Fast path

```bash
./scripts/setup-ghl-mcp.sh
```

Prompts for a Private Integration Token, verifies it against the live API,
and registers the server with Claude Code. Safe to re-run. Create the token
first (Part 1), which takes about a minute.

> **Point this at a sandbox sub-account first.** `te1aYxyEeYsXcFJhnET6` is a
> real location — anything Claude does through these tools happens to real
> records. Create or clone a disposable sub-account, wire that up, prove the
> workflow, and only then switch `GHL_LOCATION` to production.

## How it works

```
 Claude Code  ─▶  ghl-mcp (stdio, npx)  ─▶  services.leadconnectorhq.com  ─▶  your location
                        │
                        └─ Private Integration Token, scoped to one sub-account
```

The server runs **on your machine** as a stdio MCP server — Claude Code starts
it as a subprocess and talks to it over stdin/stdout. `npx` fetches it on
demand, so there is nothing to clone, build, or host.

### Why a Private Integration Token

GoHighLevel offers two ways in, and the token is the one you can actually
self-serve:

| | Private Integration Token | OAuth Marketplace app |
|---|---|---|
| Who can create it | **Any sub-account user** | Agency-level access only |
| Setup | Paste a token | Create app, browser OAuth, localhost callback |
| Scope | Locked to one sub-account | Agency-wide or per-location |
| Lifetime | Long-lived until revoked | Auto-refreshing |

On a white-labelled instance you're likely a sub-account user under someone
else's agency, so the Marketplace path would mean asking the owner of
`app.scalecertified.com` to create an app for you. The token skips that
entirely. The trade-off is that it doesn't expire on its own — treat it as a
password and revoke it if it leaks.

---

## Part 1 — Create the Private Integration Token

1. Open [Settings → Integrations](https://app.scalecertified.com/v2/location/te1aYxyEeYsXcFJhnET6/integration)
   for the location, and go to the **Private Integrations** tab.
2. Click **Create new integration**. Name it something you'll recognize later,
   e.g. `claude-code`.
3. **Select scopes.** Enable only what you want Claude able to do — the token
   can do anything its scopes allow, and the write scopes change live CRM data.
   A reasonable starting set:

   | Read-only (safe to start with) | Add for write access |
   |---|---|
   | `contacts.readonly` | `contacts.write` |
   | `opportunities.readonly` | `opportunities.write` |
   | `calendars.readonly` | `calendars.write` |
   | `conversations.readonly` | `conversations.write` |
   | `forms.readonly` | |
   | `workflows.readonly` | |
   | `locations.readonly` | |
   | `users.readonly` | |

   Starting read-only and adding write scopes later is a good way to get
   comfortable — you can edit the integration's scopes at any time.
4. Create it and **copy the token**. It's shown once. It looks like
   `pit-xxxxxxxx-xxxx-...`.

> If you don't see a **Private Integrations** tab, the agency has disabled the
> feature for sub-accounts. In that case you're back to needing the agency
> owner — see [Appendix: the OAuth route](#appendix-the-oauth-route).

---

## Part 2 — Wire it into Claude Code

Requires **Node.js 18+** (`node --version`). Pick one:

### 2a. The script (recommended)

```bash
./scripts/setup-ghl-mcp.sh
```

It verifies the token against the live API before registering anything, so a
bad token fails immediately with a clear message rather than showing up later
as a mystery MCP error.

### 2b. By hand

```bash
claude mcp add ghl-mcp -s user \
  --env GHL_PIT_TOKEN=pit-your-token-here \
  --env GHL_LOCATION=te1aYxyEeYsXcFJhnET6 \
  -- npx -y @nerdsnipe-inc/ghl-mcp-server
```

`-s user` registers it for your whole account rather than just this project.

### 2c. Via this repo's `.mcp.json`

The repo ships a secret-free `ghl-mcp` entry that reads both values from the
environment, so no token is ever committed:

```json
"ghl-mcp": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@nerdsnipe-inc/ghl-mcp-server"],
  "env": {
    "GHL_PIT_TOKEN": "${GHL_PIT_TOKEN}",
    "GHL_LOCATION": "${GHL_LOCATION}"
  }
}
```

Export both in your shell profile, then open this repo in Claude Code and
approve the server when prompted:

```bash
export GHL_PIT_TOKEN=pit-your-token-here
export GHL_LOCATION=te1aYxyEeYsXcFJhnET6
```

## Verify

```bash
claude mcp list          # ghl-mcp should show as connected
claude mcp get ghl-mcp
```

Then in Claude Code, try a **read** first:

> list the opportunities in my GoHighLevel location

You can also check the token directly without involving Claude at all:

```bash
curl -s -H "Authorization: Bearer $GHL_PIT_TOKEN" \
     -H "Version: 2021-07-28" \
     "https://services.leadconnectorhq.com/contacts/?locationId=$GHL_LOCATION&limit=1"
```

A JSON body means the token works; a 401 means it's wrong or revoked.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `claude mcp list` shows the server failed | Run `npx -y @nerdsnipe-inc/ghl-mcp-server` by hand with the two env vars set — you'll see the real error. Usually Node < 18 or a missing variable. |
| 401 from every tool | Token wrong, revoked, or it's a regular API key rather than a **Private Integration** token. Regenerate it in Settings → Integrations. |
| 403 on one specific action | The token is missing that scope. Edit the integration, add the scope, save — no need to regenerate the token. |
| Tools work but touch the wrong records | `GHL_LOCATION` points at a different sub-account. It must be `te1aYxyEeYsXcFJhnET6`. |
| `${GHL_PIT_TOKEN}` unresolved | The variable must be exported in the environment Claude Code was launched from; restart the app after editing your shell profile. |
| No **Private Integrations** tab | The agency disabled it for sub-accounts. See the appendix. |

## Security notes

- The token grants full API access to sub-account `te1aYxyEeYsXcFJhnET6` within
  its scopes. It lives only in your environment — `.gitignore` blocks `.env`,
  `.env.*`, `*.key`, and `*.pem` so it can't be committed from here.
- Give it the narrowest scopes that do the job, and start read-only.
- It does **not** expire on its own. Revoke it in Settings → Integrations if it
  is ever exposed, if a machine is lost, or when you stop using it.
- MCP tools write to the **live CRM**. There is no sandbox — a deleted contact
  is really deleted. Confirm before letting Claude create or change records.
- `@nerdsnipe-inc/ghl-mcp-server` is a third-party MIT-licensed package pulled
  at run time by `npx`. Pin a version (`@nerdsnipe-inc/ghl-mcp-server@2.0.0`)
  if you'd rather not track its latest release automatically.

---

## Appendix: the OAuth route

If you have (or can get) agency-level access and would prefer auto-refreshing
OAuth tokens over a long-lived one, [open-ghl-mcp](https://github.com/basicmachines-co/open-ghl-mcp)
is the Python equivalent:

1. Create a Marketplace app at https://marketplace.gohighlevel.com → **My Apps
   → Create App**, redirect URL exactly `http://localhost:8080/oauth/callback`,
   with the scopes you want.
2. Clone it, put `GHL_CLIENT_ID` and `GHL_CLIENT_SECRET` in its `.env`, and
   install with `uv venv && uv pip install -r requirements.txt` (needs Python
   3.12+).
3. Run `python -m src.main` once and complete the browser flow, choosing the
   **sub-account** scope so the token is locked to one location.
4. Register it with
   `claude mcp add ghl-mcp -s user -- uv run --directory /path/to/open-ghl-mcp python -m src.main`.

Note that its "standard mode" hosted app is still listed as coming soon
upstream, so a custom Marketplace app is currently the only working way in.

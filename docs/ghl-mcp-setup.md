# Wiring GoHighLevel to Claude Code (GHL MCP)

This guide connects your GoHighLevel sub-account to Claude Code through the
[open-ghl-mcp](https://github.com/basicmachines-co/open-ghl-mcp) server, so
Claude can read and act on contacts, opportunities, calendars, forms, and
workflows in GHL the same way it reads and writes code here.

Your account is on a **white-labelled** GHL instance:

| Thing | Value |
|-------|-------|
| Dashboard | `https://app.scalecertified.com` |
| Location (sub-account) ID | `te1aYxyEeYsXcFJhnET6` |
| API host | `https://services.leadconnectorhq.com` (same for all white-labels) |
| Marketplace | `https://marketplace.gohighlevel.com` (same for all white-labels) |

The white-label only changes the *dashboard* domain. The API and the app
marketplace are still GoHighLevel's, so everything below works unchanged.

## How it works

```
 Claude Code  ─▶  ghl-mcp (stdio, local)  ─▶  services.leadconnectorhq.com  ─▶  your location
                        │
                        └─ OAuth 2.0, tokens cached + auto-refreshed locally
```

The server runs **on your machine** as a stdio MCP server. It is not hosted and
does not need to be — Claude Code launches it as a subprocess and talks to it
over stdin/stdout.

---

## Part 1 — Create a GoHighLevel Marketplace app

open-ghl-mcp advertises a "standard mode" using a hosted app, but that is still
listed as coming soon upstream. **Custom mode is the working path**, so you need
your own Marketplace app to get a client ID and secret.

1. Go to https://marketplace.gohighlevel.com and sign in with your GHL account.
2. **My Apps → Create App.** Give it a name (e.g. `claude-code-mcp`), and choose
   distribution type **Private** (it is only ever used by you).
3. **Redirect URL** — set it exactly to:
   ```
   http://localhost:8080/oauth/callback
   ```
   This must match character-for-character or the OAuth handshake fails.
4. **Scopes** — enable read/write for the domains you want Claude to touch:
   `contacts`, `opportunities`, `calendars`, `forms`, `conversations`,
   `locations/customFields`, `locations/customValues`, `users`, `workflows`.
   Grant only what you actually want Claude able to change.
5. Copy the **Client ID** and **Client Secret** from the app's settings.

> **If you can't create an app:** creating Marketplace apps requires
> agency-level access. On a white-labelled instance you may be a sub-account
> user under someone else's agency — if **My Apps** isn't available to you, ask
> the agency owner of `app.scalecertified.com` to create the app and hand you
> the client ID/secret, or to add you as an agency user.

---

## Part 2 — Install and authorize the server

Requires **Python 3.12+** and [`uv`](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/basicmachines-co/open-ghl-mcp.git
cd open-ghl-mcp
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

Create `.env` in the `open-ghl-mcp` directory with the credentials from Part 1
(see [`.env.example`](../.env.example) in this repo for the shape):

```
GHL_CLIENT_ID=your_client_id
GHL_CLIENT_SECRET=your_client_secret
```

Note the `GHL_` prefix — plain `CLIENT_ID` / `CLIENT_SECRET` will not be read.

Now run the server once by hand to complete the OAuth flow:

```bash
python -m src.main
```

On first run it opens your browser to authorize the app. **Pick the sub-account
scope and select the location `te1aYxyEeYsXcFJhnET6`** (a location token is
locked to that one sub-account — safer than a company token, which can reach
every sub-account under the agency). It redirects back to
`http://localhost:8080/oauth/callback`, caches the tokens locally, and refreshes
them automatically from then on.

Optional sanity checks before wiring it up:

```bash
pytest                 # test suite
pytest --cov=src       # with coverage
python -m src.main --reauth   # redo the OAuth flow later, e.g. to change scopes
```

If `python -m src.main` starts and sits there waiting on stdin, that's success —
that is what an idle stdio MCP server looks like. Ctrl-C out of it.

---

## Part 3 — Add it to Claude Code

Pick **one** of these. The stdio methods are equivalent; use whichever you find
easier to re-run.

### 3a. From this repo (already configured)

This repo's `.mcp.json` ships a secret-free `ghl-mcp` entry alongside the
ElevenLabs one. It resolves the checkout path from an environment variable, so
no machine-specific path is committed:

```json
"ghl-mcp": {
  "type": "stdio",
  "command": "uv",
  "args": ["run", "--directory", "${GHL_MCP_DIR}", "python", "-m", "src.main"]
}
```

Export the path to your clone (in your shell profile, so it persists):

```bash
export GHL_MCP_DIR=$HOME/code/open-ghl-mcp
```

Open this repo in local Claude Code and approve the server when prompted. The
credentials stay in `open-ghl-mcp/.env`; nothing secret enters this repo.

### 3b. `claude mcp add` (available in every project)

```bash
claude mcp add ghl-mcp -s user -- uv run --directory /path/to/open-ghl-mcp python -m src.main
```

`-s user` registers it for your whole user account rather than one project. Use
the absolute path to your clone; `uv run --directory` is what makes it work from
any working directory. (Upstream's README names the server `ghl`; this repo uses
`ghl-mcp` — the name is arbitrary, just be consistent.)

### 3c. `claude mcp add-json`

Same thing expressed as config:

```bash
claude mcp add-json ghl-mcp '{"type":"stdio","command":"uv","args":["run","--directory","/path/to/open-ghl-mcp","python","-m","src.main"]}'
```

Do **not** put `GHL_CLIENT_ID` / `GHL_CLIENT_SECRET` in the `env` block of an
`add-json` command — that writes your secret into shell history and into
`~/.claude.json` in plaintext. Keep them in `open-ghl-mcp/.env`.

### 3d. Remote HTTP — only if you host it yourself

open-ghl-mcp is a stdio server; there is no hosted endpoint to point at. If you
deploy it behind an HTTP transport yourself:

```bash
claude mcp add --transport http ghl-mcp https://your-ghl-mcp-host/mcp \
  --header "Authorization: Bearer YOUR_TOKEN"
```

Running `/mcp` inside Claude Code then completes browser OAuth *against your
host*. Note that `/mcp` OAuth applies to **remote** servers only — for the local
stdio setup above, authorization is the Part 2 browser flow, not `/mcp`.

Hosting it exposes a live write path into your CRM, so put real auth in front of
it before it leaves localhost.

---

## Verify

```bash
claude mcp list          # ghl-mcp should be listed and connected
claude mcp get ghl-mcp   # shows the resolved command and transport
```

Then in Claude Code, `/mcp` lists the server's tools. Try a read-only call
first — ask for opportunities in the location:

> get opportunities for location `te1aYxyEeYsXcFJhnET6`

Every location-scoped tool takes a `locationId`, so keep that ID handy — it's
the same one that appears in your dashboard URL:
`app.scalecertified.com/v2/location/te1aYxyEeYsXcFJhnET6/...`

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `claude mcp list` shows the server as failed | Run the command from `claude mcp get ghl-mcp` by hand — you'll see the real error. Usually a wrong `--directory` or Python < 3.12. |
| Browser flow ends on an error page | The app's Redirect URL must be exactly `http://localhost:8080/oauth/callback`. |
| Port 8080 already in use during auth | Stop whatever is on 8080 and re-run `python -m src.main --reauth`. |
| Tools return 401 after working fine | Token expired and refresh failed — re-run `python -m src.main --reauth`. |
| Tools return 403 on a specific action | The Marketplace app is missing that scope. Add it, then `--reauth` (new scopes need a fresh authorization). |
| Requests to another sub-account are refused | Expected with a location token — it's locked to one location. Re-authorize with company scope only if you truly need agency-wide access. |
| `${GHL_MCP_DIR}` unresolved | The variable must be exported in the environment Claude Code was launched from; restart the app after editing your shell profile. |

## Security notes

- The client secret lives only in `open-ghl-mcp/.env` on your machine, and the
  OAuth tokens only in that server's local cache. Neither belongs in this repo —
  `.gitignore` blocks `.env`, `.env.*`, `*.key`, and `*.pem`.
- Prefer a **location token** over a company token. A company token can reach
  every sub-account under the agency; the location token can only touch
  `te1aYxyEeYsXcFJhnET6`.
- Scope the Marketplace app to the domains you actually want automated. MCP
  tools can write — contacts and opportunities changed through them are real
  changes in the live CRM, not a sandbox.
- The location ID isn't a credential (it's in every dashboard URL), but the
  client secret is. Rotate the secret in the Marketplace if it's ever exposed.

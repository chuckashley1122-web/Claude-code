# Wiring Jarvis (ElevenLabs) to Claude Code

This guide connects your ElevenLabs voice agent ("Jarvis") to Claude Code so you
can **speak a task and get a pull request**. Follow it top to bottom; it takes
about 20 minutes and requires no server hosting.

## How it works

```
 You speak  ─▶  Jarvis (ElevenLabs)  ─▶  webhook tool  ─▶  GitHub issue "@claude …"
                                                                    │
                                                                    ▼
                          PR appears  ◀─  Claude Code Action executes the task
```

- **Jarvis** is the voice front-end (already built).
- A **server tool** on Jarvis fires an HTTP request that opens a GitHub issue.
- The issue body begins with `@claude`, which trips this repo's GitHub Action
  (`.github/workflows/claude.yml`).
- Claude Code does the coding on a branch and opens a **pull request**.

GitHub is the task queue. Nothing to host, and every task has an audit trail.

---

## Part 1 — The Claude Code side (this repo)

These files are already in the repo:

- `.github/workflows/claude.yml` — the executor. Runs Claude on any issue/comment
  containing `@claude`.
- `CLAUDE.md` — tells Claude how to behave as "Jarvis's hands."
- `.claude/agents/coder.md`, `.claude/agents/reviewer.md` — specialized subagents.

You (a repo admin) still need to do two one-time things:

### 1a. Install the Claude GitHub App

Install it on the `chuckashley1122-web/claude-code` repo:
👉 https://github.com/apps/claude

It needs Read & Write on **Contents**, **Issues**, and **Pull requests**.

> Shortcut: from a Claude Code terminal you can run `/install-github-app`, which
> installs the app and offers to add the workflow + secret for you.

### 1b. Add your Claude Max subscription token as a repo secret

The workflow authenticates against your **Claude Max plan** — no per-token API
billing. You generate a long-lived OAuth token from the Claude Code CLI:

1. In a terminal with Claude Code installed and logged into your Max account,
   run:
   ```
   claude setup-token
   ```
   Copy the token it prints (it authorizes against your subscription).
2. In the repo: **Settings → Secrets and variables → Actions → New repository secret**
3. Name it exactly `CLAUDE_CODE_OAUTH_TOKEN`, paste the token, save.

> Prefer pay-as-you-go instead? Swap `claude_code_oauth_token` for
> `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}` in
> `.github/workflows/claude.yml` and store an `ANTHROPIC_API_KEY` secret from
> https://console.anthropic.com instead. Use one or the other, not both.

**Test it:** open a new issue with a body like
`@claude add a comment to sync-claude.sh explaining the rsync flags`.
Within a minute the Action should run and open a PR. If it doesn't, see
Troubleshooting below.

---

## Part 2 — The GitHub token Jarvis will use

Jarvis needs permission to *create issues* in the repo. Create a scoped token so
that permission is as small as possible.

1. Go to https://github.com/settings/personal-access-tokens/new
   (Fine-grained personal access token).
2. **Resource owner:** `chuckashley1122-web` · **Repository access:** only
   `claude-code`.
3. **Repository permissions:** set **Issues** to **Read and write**. Leave
   everything else at "No access."
4. Set an expiration you're comfortable with, generate, and **copy the token**
   (starts with `github_pat_...`). You won't see it again.

Keep this token handy for the next step. Treat it like a password.

---

## Part 3 — The ElevenLabs side (Jarvis)

Do this in the ElevenLabs Agents dashboard for your Jarvis agent
(`agent_0001ktn3bhnsfwcs1csfy3qf6xky`).

### 3a. Store the GitHub token as a workspace secret

**Agent settings → Secrets** (or Workspace secrets) → add a secret:

- **Name:** `GITHUB_TOKEN`
- **Value:** the `github_pat_...` token from Part 2.

Using a secret (instead of pasting the token into the tool) keeps it out of the
tool config and logs.

### 3b. Add a webhook (server) tool: `assign_coding_task` (multi-repo)

**Agent → Tools → Add tool → Webhook** (a.k.a. server tool). Configure it:

| Field | Value |
|-------|-------|
| **Name** | `assign_coding_task` |
| **Description** | `Create a coding task for Claude Code by opening a GitHub issue in the chosen repository. Use whenever the user asks to build, fix, change, or implement something in code.` |
| **Method** | `POST` |
| **URL** | `https://api.github.com/repos/chuckashley1122-web/{{repo}}/issues` |

The `{{repo}}` segment is a **path parameter** — Jarvis fills it in with the repo
name based on what you say. (Owner is fixed to `chuckashley1122-web`; see the note
below if you want repos under other owners too.)

**Headers:**

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer {{secret__GITHUB_TOKEN}}` |
| `Accept` | `application/vnd.github+json` |
| `X-GitHub-Api-Version` | `2022-11-28` |
| `User-Agent` | `jarvis-agent` |

> The exact syntax for injecting a secret into a header depends on the ElevenLabs
> UI version — look for a "secret" / auth option on the header value field and
> select `GITHUB_TOKEN`. The header must resolve to `Bearer github_pat_...`.

**Path parameters:**

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `repo` | string | The GitHub repository name to file the task in — one of the user's known repos (see the list in the system prompt, 3c). Use the exact repo name, e.g. `claude-code`. Default to `claude-code` if the user doesn't name one. | yes |

**Body parameters** (the values Jarvis fills in from what you say — give each a
clear description so the model populates them well):

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `title` | string | A short (5–10 word) title summarizing the coding task. | yes |
| `body` | string | The full task. **Must begin with the literal text `@claude `** followed by a clear, detailed description of what to build or fix, including any files, behavior, or acceptance criteria the user mentioned. | yes |

So a request Jarvis sends to
`https://api.github.com/repos/chuckashley1122-web/personal-site/issues` with body:

```json
{
  "title": "Add a login page",
  "body": "@claude Build a login page with email + password fields, client-side validation, and a submit handler that posts to /api/login. Match the existing component style."
}
```

The leading `@claude` is what triggers the Action — if it's missing, nothing runs.

> **Repos under a different owner?** Change the `repo` parameter to hold the full
> `owner/name` (e.g. `someorg/api`) and set the URL to
> `https://api.github.com/repos/{{repo}}/issues`. Then Jarvis must say the owner
> too, and your GitHub token must have access to those repos.

### 3c. Teach Jarvis when to use the tool

Add this to Jarvis's **system prompt** (append it to what's already there).
**Replace the repo list with your real repos** — this is how Jarvis maps what you
say ("my website", "the API") to an actual repo name for the `repo` parameter:

```
You can assign coding tasks to Claude Code, which writes the code and opens a
GitHub pull request. When the user asks you to build, fix, change, refactor, or
implement anything in software, call the `assign_coding_task` tool.

Choosing the repo: set the `repo` parameter to the repository the task belongs
to, picked from this list of the user's repositories:
  - claude-code        — the Jarvis integration hub and default catch-all
  - personal-site      — the user's personal website / blog        [EDIT ME]
  - <repo-name>        — <what it is, and what the user calls it>   [EDIT ME]
If the user names a project ("my website", "the API"), map it to the matching
repo. If it's ambiguous or they don't say, ask a quick one-line clarification, or
default to `claude-code`. Only use repos from this list.

Turn their spoken request into a clear, detailed task description — infer
reasonable specifics rather than over-questioning. Always begin the issue body
with "@claude ". After the tool succeeds, confirm the task is queued in which
repo, that a pull request will appear on GitHub shortly, and read back the task
title you filed.
```

Keep this list in sync with the repos you've onboarded in section 3e.

### 3d. (Optional) Let Jarvis report status back — `check_coding_tasks`

Add a second webhook tool so you can ask "what's the status of my tasks?"

| Field | Value |
|-------|-------|
| **Name** | `check_coding_tasks` |
| **Description** | `List recent coding tasks and their pull requests in a repository so the user can hear their status.` |
| **Method** | `GET` |
| **URL** | `https://api.github.com/repos/chuckashley1122-web/{{repo}}/pulls?state=all&sort=updated&direction=desc&per_page=5` |
| **Headers** | same as above (`Authorization`, `Accept`, `X-GitHub-Api-Version`, `User-Agent`) |
| **Path param** | `repo` — same as `assign_coding_task`; which repo to check, default `claude-code`. |

The token from Part 2 only has Issues access; to read pull requests, also grant
that token **Pull requests: Read** (or use a second read-only token).

### 3e. Onboard each repo Jarvis can touch

For **every** repo you want Jarvis to file tasks in, do these three things once
(the same steps as Part 1, per repo):

1. **Install the Claude GitHub App** on that repo → https://github.com/apps/claude
2. **Add the executor workflow** — copy this repo's `.github/workflows/claude.yml`
   into the target repo at the same path (it's identical, no edits needed).
3. **Add the `CLAUDE_CODE_OAUTH_TOKEN` secret** to that repo (same token from
   `claude setup-token`; reuse it across repos).

Then make sure the repo is in scope for both:
- **Jarvis's GitHub token** (Part 2) — the fine-grained token's *Repository
  access* must include this repo, with Issues: read/write.
- **Jarvis's system prompt** (3c) — add the repo to the known-repos list so Jarvis
  will select it.

A repo isn't reachable until all of the above are true: app installed, workflow
present, secret set, token scoped, and listed in the prompt.

---

## Talking to Jarvis every day

`jarvis.html` (repo root) is your daily voice interface — a single page with a
tap-to-talk button wired to your agent. Three ways to use it, easiest first:

1. **Open the file directly.** Download `jarvis.html`, double-click it, allow the
   microphone. Works offline-of-your-code, no hosting. Bookmark it.
2. **Host it free on GitHub Pages** for a URL that works on your phone too:
   repo **Settings → Pages → Build from a branch →** pick this branch and `/root`.
   Your page appears at `https://chuckashley1122-web.github.io/claude-code/jarvis.html`.
   Add it to your phone's home screen for one-tap access.
3. **Embed the widget** on any site you already run by dropping in the two lines
   from method 3 of the deploy guide.

> The widget uses your agent directly (no auth), so the page is all you need on
> the client side. Everything that turns speech into pull requests still runs
> through the tools and secrets configured above.

## The daily loop

Once wired up, your daily flow is simply:

1. Open Jarvis, talk to it: *"Jarvis, add rate limiting to the login endpoint on
   my API."*
2. Jarvis picks the repo, files the issue; the Action runs; a PR appears in a
   minute or two.
3. Review the PR on GitHub (or ask Jarvis to read back open tasks with
   `check_coding_tasks`), then merge.
4. Follow up by commenting `@claude <change>` on the PR — by voice via Jarvis or
   by typing.

Adding a new repo to the fleet later? Just run the one-time onboarding in
**section 3e** for it and add it to the system-prompt list.

## Optional: let Claude configure Jarvis for you (ElevenLabs MCP)

Instead of clicking through the ElevenLabs dashboard for Part 3, you can connect
the **ElevenLabs MCP server** to your *local* Claude Code and have Claude create
the `assign_coding_task` tool and update the agent's system prompt for you.

This repo ships a secret-free `.mcp.json` that references the key via an
environment variable — the key is **never** stored in the file:

```json
{
  "mcpServers": {
    "elevenlabs": {
      "type": "stdio",
      "command": "uvx",
      "args": ["elevenlabs-mcp"],
      "env": { "ELEVENLABS_API_KEY": "${ELEVENLABS_API_KEY}" }
    }
  }
}
```

To use it:

1. **Rotate your ElevenLabs API key** if it has ever been pasted into a chat,
   commit, or shared — treat any exposed key as compromised and regenerate it in
   ElevenLabs → API Keys.
2. Put the fresh key in your environment, not in any file:
   `export ELEVENLABS_API_KEY=sk_...` (in your shell profile or OS keychain).
3. Open this repo in your local Claude Code. It picks up `.mcp.json`, and the
   `elevenlabs` tools become available. Ask Claude to set up the agent.

> This runs in your **local** Claude Code (the MCP launches `uvx elevenlabs-mcp`
> on your machine). The `.gitignore` in this repo blocks `.env`, `*.key`, `*.pem`,
> and `*.local` files so a real key can never be committed by accident.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Issue is created but no Action runs | Body must contain `@claude`. Check the issue body actually starts with it. |
| Action runs but fails on auth | `CLAUDE_CODE_OAUTH_TOKEN` secret missing/invalid. Re-run `claude setup-token` and update the secret (tokens can expire). |
| ElevenLabs tool returns 401/403 | GitHub token wrong, expired, or lacks Issues:write on this repo. |
| ElevenLabs tool returns 404 | The `repo` param resolved to a name that doesn't exist / isn't in the token's scope, or a URL typo. Confirm the repo is onboarded (3e) and in the token's repository access. |
| Claude commits but CI doesn't run on its PRs | Ensure the Claude GitHub App (not the Actions user) is installed. |

## Security notes

- The GitHub token lives only in ElevenLabs secrets; the Anthropic key lives only
  in GitHub Actions secrets. Neither is ever committed to this repo.
- Only give the Jarvis token the minimum scopes it needs (Issues, optionally PR
  read). Rotate it if it's ever exposed.
- Anyone who can talk to your Jarvis agent can file tasks — protect access to the
  agent accordingly.

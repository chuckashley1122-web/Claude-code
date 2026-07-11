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

### 3b. Add a webhook (server) tool: `assign_coding_task`

**Agent → Tools → Add tool → Webhook** (a.k.a. server tool). Configure it:

| Field | Value |
|-------|-------|
| **Name** | `assign_coding_task` |
| **Description** | `Create a coding task for Claude Code by opening a GitHub issue. Use whenever the user asks to build, fix, change, or implement something in code.` |
| **Method** | `POST` |
| **URL** | `https://api.github.com/repos/chuckashley1122-web/claude-code/issues` |

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

**Body parameters** (these are the values Jarvis fills in from what you say —
give each a clear description so the model populates them well):

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `title` | string | A short (5–10 word) title summarizing the coding task. | yes |
| `body` | string | The full task. **Must begin with the literal text `@claude `** followed by a clear, detailed description of what to build or fix, including any files, behavior, or acceptance criteria the user mentioned. | yes |

If the tool builder lets you set a fixed template for the body, prefix it so the
`@claude ` mention is always present, e.g. the body sent to GitHub should look
like:

```json
{
  "title": "Add a login page",
  "body": "@claude Build a login page with email + password fields, client-side validation, and a submit handler that posts to /api/login. Match the existing component style."
}
```

The leading `@claude` is what triggers the Action — if it's missing, nothing runs.

### 3c. Teach Jarvis when to use the tool

Add this to Jarvis's **system prompt** (append it to what's already there):

```
You can assign coding tasks to Claude Code, which writes the code and opens a
GitHub pull request. When the user asks you to build, fix, change, refactor, or
implement anything in software, call the `assign_coding_task` tool. Turn their
spoken request into a clear, detailed task description — infer reasonable
specifics rather than over-questioning. Always begin the issue body with
"@claude ". After the tool succeeds, confirm to the user that the task is queued
and that a pull request will appear on GitHub shortly, and read back the task
title you filed.
```

### 3d. (Optional) Let Jarvis report status back — `check_coding_tasks`

Add a second webhook tool so you can ask "what's the status of my tasks?"

| Field | Value |
|-------|-------|
| **Name** | `check_coding_tasks` |
| **Description** | `List recent coding tasks and their pull requests so the user can hear their status.` |
| **Method** | `GET` |
| **URL** | `https://api.github.com/repos/chuckashley1122-web/claude-code/pulls?state=all&sort=updated&direction=desc&per_page=5` |
| **Headers** | same three as above (`Authorization`, `Accept`, `X-GitHub-Api-Version`, `User-Agent`) |

The token from Part 2 only has Issues access; to read pull requests, also grant
that token **Pull requests: Read** (or use a second read-only token).

---

## The daily loop

Once wired up, your daily flow is simply:

1. Open Jarvis, talk to it: *"Jarvis, add rate limiting to the login endpoint."*
2. Jarvis files the issue; the Action runs; a PR appears in a minute or two.
3. Review the PR on GitHub (or ask Jarvis to read back open tasks), then merge.
4. Follow up by commenting `@claude <change>` on the PR — by voice via Jarvis or
   by typing.

## Extending to other repos

This setup targets one repo. To let Jarvis assign work across several repos:

- Copy `.github/workflows/claude.yml` (and install the Claude App + add the API
  key secret) into each target repo, **and**
- Either add one `assign_coding_task` tool per repo, or add a `repo` body
  parameter to a single tool and put `{{repo}}` in the URL path so Jarvis picks
  the repo from what you say.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Issue is created but no Action runs | Body must contain `@claude`. Check the issue body actually starts with it. |
| Action runs but fails on auth | `CLAUDE_CODE_OAUTH_TOKEN` secret missing/invalid. Re-run `claude setup-token` and update the secret (tokens can expire). |
| ElevenLabs tool returns 401/403 | GitHub token wrong, expired, or lacks Issues:write on this repo. |
| ElevenLabs tool returns 404 | URL or repo owner/name typo, or token can't see the repo. |
| Claude commits but CI doesn't run on its PRs | Ensure the Claude GitHub App (not the Actions user) is installed. |

## Security notes

- The GitHub token lives only in ElevenLabs secrets; the Anthropic key lives only
  in GitHub Actions secrets. Neither is ever committed to this repo.
- Only give the Jarvis token the minimum scopes it needs (Issues, optionally PR
  read). Rotate it if it's ever exposed.
- Anyone who can talk to your Jarvis agent can file tasks — protect access to the
  agent accordingly.

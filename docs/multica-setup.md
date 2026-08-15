# Running this repo's agent under Multica

[Multica](https://github.com/multica-ai/multica) is a "managed agents" platform:
a task board where AI coding agents are assignees. You file an issue, assign it
to an agent, and the agent picks it up, writes code, comments, and moves its own
status.

This guide wires **this repo** into Multica so a Claude Code agent can be
assigned work here. It complements [`jarvis-setup.md`](jarvis-setup.md) rather
than replacing it — see [Which path should I use?](#which-path-should-i-use).

> **All of Part 1 runs on your own machine, not in a Claude Code web session.**
> Multica registers the machine running the daemon as a *runtime*. A cloud
> session's container is ephemeral and its egress is restricted, so a runtime
> registered from one disappears when the session ends. Run these steps on the
> laptop or server you actually want doing the work.

---

## Which path should I use?

This repo now has two ways to get a task to Claude Code. They can coexist.

| | **Jarvis → GitHub Action** | **Multica** |
|---|---|---|
| You start a task by | speaking to Jarvis | dragging a card on a board |
| Work runs on | GitHub's runners | your machine (or Multica Cloud) |
| Good for | hands-free, one-off tasks | many tasks in parallel, recurring work |
| Costs | GitHub Actions minutes | your own compute |
| Setup | secrets only, no hosting | a CLI + a persistent daemon |

Use Jarvis when you want to talk. Use Multica when you want a queue and want to
watch several agents at once.

---

## Before you start

You need, on the machine that will run the agents:

- **An agent CLI, installed and signed in** — `claude` is the natural one here.
  Verify with `claude --version`. Multica auto-detects the CLIs it finds.
- **A Multica account** at https://multica.ai (for the free cloud), or **Docker**
  if you intend to self-host the server.
- Basic command-line comfort. This is a developer tool, not a one-tap app.

### About the license

The README describes the terms as the **Multica License**: the full Apache
License 2.0 text *plus additional conditions* covering hosted services,
commercial embedding, and branding. Practically:

- Using it internally, as documented here, is fine.
- **It is not OSI-standard open source.** If you plan to build a product on it,
  host it for others, or ship it inside something commercial, read
  [the license](https://github.com/multica-ai/multica/blob/main/LICENSE) first —
  those are exactly the cases the extra conditions restrict.

---

## Part 1 — Install and connect (your machine)

### 1a. Install the CLI

Pick one:

```bash
# macOS / Linux, Homebrew
brew install multica-ai/tap/multica

# macOS / Linux, install script
curl -fsSL https://raw.githubusercontent.com/multica-ai/multica/main/scripts/install.sh | bash
```

```powershell
# Windows, PowerShell
irm https://raw.githubusercontent.com/multica-ai/multica/main/scripts/install.ps1 | iex
```

> Piping a remote script into a shell runs whatever that URL serves today. If
> you'd rather look before you run, download it first
> (`curl -fsSL <url> -o install.sh`), read it, then `bash install.sh`. The
> Homebrew tap avoids the question entirely.

Self-hosting instead of using the cloud? Add the server components at install
time — `... | bash -s -- --with-server` on macOS/Linux, or set
`$env:MULTICA_MODE="with-server"` before the PowerShell line.

### 1b. Set up and start the daemon

```bash
multica setup
```

This logs you in against Multica Cloud, then starts the daemon and auto-detects
your installed agent CLIs (`claude`, `codex`, `cursor-agent`, …).

For self-hosting, run `multica setup self-host` instead. It needs a **running
Docker daemon** — see the repo's
[SELF_HOSTING.md](https://github.com/multica-ai/multica/blob/main/SELF_HOSTING.md).

Because login is browser-based and the daemon must keep running, this step
cannot be completed by an agent on your behalf. It's yours to run once.

### 1c. Confirm the runtime

Open the Multica web app → **Settings → Runtimes**. Your machine should be
listed as **active**. If it isn't, the daemon isn't running or didn't finish
authenticating — check `multica status` before going further.

The preflight script in this repo checks the local half of this for you:

```bash
./scripts/multica-preflight.sh
```

It reports which agent CLIs are installed, whether the Multica CLI and daemon
are present and running, and whether Docker is available for self-hosting. It
only reads state — it installs and changes nothing.

---

## Part 2 — Create the agent

In the web app: **Settings → Agents → New Agent**.

| Field | Value |
|-------|-------|
| **Runtime** | the machine you registered in 1c |
| **Provider** | Claude Code |
| **Name** | how it appears on the board, e.g. `jarvis-hands` |

The name is the identity you'll assign issues to, so make it one you'd be happy
to read aloud.

---

## Part 3 — What the agent reads in this repo

A Multica-dispatched Claude Code agent working in this repo picks up the same
project files a local session does:

- **`CLAUDE.md`** — the working rules (branch, don't touch the default branch,
  keep the diff scoped, open a PR with a plain-language summary). These apply to
  Multica-assigned tasks exactly as they do to Jarvis-filed issues.
- **`.claude/agents/coder.md`**, **`.claude/agents/reviewer.md`** — the
  specialized subagents.

So the repo-side wiring is already done; nothing further to add for the agent to
behave consistently across both paths.

> Multica's **skills** feature is separate from these files — skills accumulate
> in Multica and are reused across repos, whereas `CLAUDE.md` is per-repo. Keep
> repo conventions here; let Multica hold cross-repo solutions.

---

## Part 4 — Assign the first task

Create an issue on the board (or `multica issue create`), assign it to your
agent, and watch it move. Start with something small and verifiable so you can
actually check the output — for example:

> Add a `--dry-run` flag to `sync-claude.sh` that prints the rsync command it
> would run and exits without copying anything.

Good first tasks are ones where you can tell at a glance whether the result is
right. Avoid anything irreversible or security-sensitive until you've seen a few
land.

---

## Squads and autopilots

Once one agent works, two things are worth trying:

- **Squads** — group agents under a leader that delegates. Useful when tasks
  split naturally (one implements, one reviews), which mirrors the
  `coder`/`reviewer` split already in `.claude/agents/`.
- **Autopilots** — scheduled recurring runs (a nightly dependency audit, a
  weekly summary). Best pointed at read-and-report work rather than anything
  that opens PRs unattended.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Machine doesn't appear under Runtimes | Daemon isn't running or login didn't complete. Check `multica status`, re-run `multica setup`. |
| Agent exists but no CLI to pick | The daemon detects CLIs at startup. Install/sign into `claude` first, then restart the daemon. |
| `multica setup self-host` fails immediately | Docker isn't running. `docker info` should succeed before you retry. |
| Agent picks up the task but produces nothing | Its provider CLI isn't authenticated on that machine. Run `claude` manually there once and confirm it works. |
| Runtime vanished after a while | It was registered from an ephemeral/cloud container, not a persistent machine. Re-run on real hardware. |

## A realistic note

Two things worth keeping in view:

- **This is a developer tool.** You install CLIs, run a daemon, and use Docker if
  you self-host. Expect to spend time in a terminal.
- **Agents still need supervision.** Review what they ship, keep them on tasks
  whose output you can verify, and don't hand them anything critical unattended.
  "Teammate" is a useful metaphor for the workflow, not a claim about judgment.

Multica's setup and features move quickly — check the
[live README](https://github.com/multica-ai/multica) before installing, since
the commands above can drift.

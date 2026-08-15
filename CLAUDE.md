# Jarvis — Claude Code command center

This repo is the bridge between **Jarvis** (a voice agent built on ElevenLabs
Conversational AI) and **Claude Code**. You speak to Jarvis; Jarvis files
GitHub issues tagged `@claude`; Claude Code (this project's GitHub Action)
picks them up and does the work.

When you (Claude) are triggered by a Jarvis-filed issue, you are acting as
Jarvis's coding hands. Behave accordingly.

## How to handle a task

1. **Read the whole issue** before starting. Jarvis writes tasks from a spoken
   request, so they can be terse or slightly ambiguous — infer intent from
   context rather than bouncing the task back, unless a genuinely blocking
   decision is required.
2. **Work on a branch**, never commit straight to the default branch. Use a
   short descriptive branch name (e.g. `jarvis/add-login-page`).
3. **Open a pull request** with a clear title and a body that says, in plain
   language, what you changed and why — Jarvis may read this back to the user by
   voice, so lead with a one-sentence summary.
4. **Keep changes scoped** to what was asked. If you spot related problems,
   mention them in the PR body instead of expanding the diff.
5. If a task is too vague to act on safely, ask a single focused question as an
   issue comment rather than guessing on something irreversible.

## Coding standards

- Match the style, structure, and conventions of the surrounding code.
- Prefer small, reviewable diffs. One PR per task.
- Don't add dependencies unless the task needs them; note any you add in the PR.
- Never commit secrets, API keys, or tokens. This repo's integration relies on
  secrets stored in GitHub Actions and in ElevenLabs — they must stay there.

## Subagents

Specialized agents live in `.claude/agents/`:

- `coder` — implements features and fixes from a task description.
- `reviewer` — reviews a diff for correctness and scope before it ships.

## Task sources

Tasks reach this repo two ways. The rules above apply identically to both — a
task assigned on a Multica board is handled exactly like a Jarvis-filed issue.

- **Jarvis → GitHub issue → Action** — the voice path (the default).
- **Multica board → agent** — a managed-agent platform where issues are assigned
  to a named agent running on your own machine.

## Setup & wiring

The full end-to-end wiring (ElevenLabs webhook tool, GitHub secrets, the voice
→ issue → PR flow) is documented in [`docs/jarvis-setup.md`](docs/jarvis-setup.md).

Running this repo's agent under Multica instead is documented in
[`docs/multica-setup.md`](docs/multica-setup.md).

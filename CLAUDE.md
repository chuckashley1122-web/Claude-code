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

Specialized agents live in `.claude/agents/`. Each runs in its own context window
with its own tools, so use one when a side task would otherwise flood the main
conversation.

- `coder` — implements features and fixes from a task description.
- `reviewer` — reviews a diff for correctness and scope before it ships.
- `debugger` — finds the root cause of a failure and fixes it.
- `secret-auditor` — read-only scan of a diff for leaked keys and tokens.
- `voice-scribe` — writes PR bodies and comments that work read aloud.
- `docs-keeper` — keeps `CLAUDE.md` and the setup guide matching reality.
- `jarvis-voice` — inspects the ElevenLabs side (agent config, transcripts).

A typical Jarvis task chains a few of them: `coder` implements, `reviewer` and
`secret-auditor` check the diff, then `voice-scribe` writes the PR body. Invoke
one by name, or `@`-mention it to guarantee it runs.

## Setup & wiring

The full end-to-end wiring (ElevenLabs webhook tool, GitHub secrets, the voice
→ issue → PR flow) is documented in [`docs/jarvis-setup.md`](docs/jarvis-setup.md).

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

## Reasoning & communication skills

Custom skills live in `.claude/skills/<name>/SKILL.md` and are invoked as
`/<name>`. They shape *how* you reason or respond. Invoke one when the user
asks for it by name, and also reach for the fitting one on your own when the
task calls for it — a hard debug is a `/uda`, a risky plan wants a `/premortem`,
expert-to-expert depth is `/l99`, and so on.

**Reasoning depth**
- `/ultrathink` — reason at full depth before answering; considered, not a guess.
- `/godmode` — be maximally thorough, cover every angle in one pass.
- `/l99` — highest expert level, nothing simplified or dumbed down.
- `/firstprinciples` — reduce to fundamental truths, rebuild from the ground up.
- `/tree` — generate multiple solution paths, then pick the best.

**Analysis & decision loops**
- `/uda` — disciplined, military-style root-cause analysis for failures/incidents.
- `/ooda` — Observe, Orient, Decide, Act; fast decisions under pressure.
- `/premortem` — assume the plan failed, work backwards to find why.
- `/inversion` — find what guarantees failure, then avoid exactly that.

**Adversarial / critical thinking**
- `/skeptic` — challenge the question before answering it.
- `/falsify` — try to prove the answer wrong before presenting it.
- `/steelman` — rebuild the strongest form of an argument before judging it.
- `/redteam` — attack the idea from every angle to find hidden flaws.
- `/devilsadvocate` — argue the opposing side to expose weak assumptions.

**Communication style**
- `/persona` — lock into one expert role for the whole chat.
- `/eli5` — explain in plain language for someone with zero background.
- `/socratic` — teach through strategic questions instead of giving answers.
- `/noyap` — answer first, cut all preamble and filler.
- `/punch` — tighten text ~40% so every line lands harder.
- `/pitch` — turn an idea into a tight 30-second investor pitch.

## Setup & wiring

The full end-to-end wiring (ElevenLabs webhook tool, GitHub secrets, the voice
→ issue → PR flow) is documented in [`docs/jarvis-setup.md`](docs/jarvis-setup.md).

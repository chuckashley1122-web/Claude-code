# Running the agent army on alpha_agents

The trading engine in [`trading/`](../trading/README.md) is built to be worked
on by many Claude Code agents at once. This document explains the agent roster,
the fan-out patterns that actually pay off, and the rules that stop parallel
agents from corrupting each other's work.

## The roster

Four specialists live in [`.claude/agents/`](../.claude/agents/), alongside the
existing `coder` and `reviewer`:

| Agent | Use it for | Tools |
|---|---|---|
| `market-researcher` | Deep read on one symbol, returning an evidence-tagged brief | read + web |
| `signal-engineer` | New indicators or analysts, with tests | read + write |
| `backtest-analyst` | Running and *skeptically interpreting* backtests | read + write |
| `risk-auditor` | Auditing the path between a signal and a loss | **read-only** |

Each definition carries hard rules that matter more than its capabilities.
`market-researcher` must tag every claim `MEASURED` or `INFERRED` and may never
state a figure it did not retrieve. `backtest-analyst` may never report a single
window as evidence of improvement. `risk-auditor` is read-only so an audit
cannot quietly become a patch.

New agent definitions are picked up when a session starts, so add the file
before the run that needs it.

## Patterns that pay off

### Fan out across the universe

The natural unit of parallelism is the symbol. Research is independent per name,
so N symbols is N agents with no coordination:

> Research each of AAPL, MSFT, NVDA, GOOGL and AMZN with a separate
> `market-researcher`. Each returns a brief in the standard format. Then
> synthesise the five briefs into a ranked list with the disagreements called
> out.

This is the shape the engine itself uses internally — `TradingPipeline`
already runs the four analysts concurrently per symbol via a thread pool.

### Find, then adversarially verify

The failure mode of a single agent looking for bugs is confident plausibility.
Splitting *finding* from *refuting* fixes most of it:

> Have three agents independently look for correctness bugs in `risk.py`. For
> each finding, spawn a separate agent whose job is to **refute** it — to show
> the code is actually correct. Keep only findings that survive.

Ask the verifier to default to "refuted" when uncertain. An unrefuted finding is
worth acting on; a finding that merely sounded good is not.

### Diverse lenses beat redundant ones

When something can fail in several ways, give each verifier a different lens
rather than running the same check three times. For a change to the execution
path: one agent on correctness, one on risk-limit enforcement, one on float and
edge-case behaviour. Redundancy catches the same bug three times; diversity
catches three bugs.

### Signal, then tune — never both at once

`signal-engineer` implements. `backtest-analyst` evaluates. Keep them in
separate turns, and never let the agent that wrote a signal also tune its
parameters against backtest P&L in the same change. That is how a fit gets baked
in before anyone can see it happening.

## Rules for parallel agents in this repo

These are learned from building the engine this way, not hypothetical.

**Give agents disjoint files.** Three agents built `indicators.py`, `data/`, and
`portfolio.py`/`risk.py`/`execution/` concurrently without conflict because no
two could write the same path. Agents that must share a file should run in
sequence.

**Write the contract first, then fan out.** `models.py` and `interfaces.py` were
written and frozen *before* any agent started. Every agent was told: do not
modify these; if you think the contract is wrong, report it instead of changing
it. Without that, parallel agents negotiate the interface by overwriting each
other.

**State the environment constraints explicitly.** Every prompt said: Python
3.11, standard library only, numpy is not installed, tests use `unittest` not
pytest. An agent that discovers those by trial and error burns most of its turn
on it.

**Do not let agents commit.** They share a worktree; a commit from one sweeps up
another's in-progress files. Agents report, the orchestrator stages and commits.

**Ask for the verification method, not just the result.** "All tests pass" is
weak evidence — the tests might be decorative. Asking the indicator agent to
mutation-test its own implementation surfaced that two known-value tests used
`period=2`, where Wilder's smoothing is arithmetically identical to a plain
average, so the tests could not have caught a real regression. It rewrote them
with `period=3`. That finding is worth more than the passing suite.

## What to do with what they return

Treat agent output as a proposal, not a result.

An agent that reports a design decision it made on your behalf is doing the
right thing, and the decision is still yours. The risk layer was built with a
tripped kill switch blocking *all* orders including exits; the agent flagged the
alternative rather than silently choosing. That was changed — a kill switch
should stop the book adding risk, not trap it in the positions that tripped it —
and the test that pinned the old behaviour was rewritten to assert the new
intent.

Two habits follow from that:

- **When you change behaviour a test asserts, rewrite the test to state the new
  intent.** Do not delete it. The test is where the reasoning is recorded.
- **Read the "adjacent notes" agents raise.** The `.gitignore` was missing
  `__pycache__/`, and the default position cap makes volatility targeting inert
  — both came from agents flagging things outside their brief.

## Scaling further

The roster is four agents, not a hundred, because a hundred *definitions* is not
what makes this work — a well-scoped definition invoked many times in parallel
is. One `market-researcher` definition fanned across a 500-name universe is 500
agents doing useful work. A hundred bespoke definitions is a hundred prompts to
maintain.

Add a definition when a task has genuinely different rules of engagement — a
different output contract, a different tool set, or a different failure mode to
guard against. Otherwise, reuse and parallelise.

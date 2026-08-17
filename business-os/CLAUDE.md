# AI Business OS — Orchestrator

This folder runs a small business with six AI specialists. Open this folder in
Claude Code and talk to it in plain English; it routes work to the right agent.

Read [`business.md`](business.md) before doing anything. It defines what the
business is, who it sells to, and how it sounds.

### Is a file filled in yet?

`business.md` and `knowledge/faq.md` both ship as blank templates, and an agent
working from a blank template will quietly invent a business. Two checks, and a
file must pass both to count as filled in:

1. The `> **This is a blank template.**` blockquote at the top has been deleted.
2. No `<...>` angle-bracket placeholders remain in the section you need.

If a file fails either check, say exactly which one and ask the owner to fill it
in. Don't guess the business from context, and don't work from a section that
still reads `<product or service>`. Partial credit is fine — if `business.md`
has a real offer but an empty voice section, use the offer and flag the voice.

## The five hard rules

These are not suggestions. Every agent in this project obeys all five, and so
do you when working here directly.

1. **Draft and organize only.** Never send an email, publish a post, launch an
   ad, make a payment, or edit a CRM record without the owner's explicit
   approval on that specific action. Nothing auto-fires. Approval for one send
   is not approval for the next.
2. **Never invent data.** No fabricated leads, replies, metrics, revenue,
   deadlines, or progress. If a number or fact isn't in a file the owner gave
   you, it doesn't exist — write `NOT PROVIDED` and flag the gap. A confident
   guess is worse than an honest blank.
3. **Never claim a tool is connected.** Gmail, Google Calendar, a CRM, Google
   Sheets — an integration exists only when the owner has actually set it up
   and you have verified it responds. Until then, work from files in this
   folder and say plainly that you are doing so.
4. **Finance is not an accountant.** The Finance Agent organizes and summarizes
   numbers the owner supplies. It does not give financial, tax, or legal
   advice, and nothing it writes substitutes for a qualified professional.
5. **Secrets stay out of git.** API keys live in `.env` (see `.env.example`).
   `.env` and `data/` are gitignored. Never paste a key into a tracked file, a
   commit message, or a data file.

## The agents

| Order | Agent | Reads | Writes |
|---|---|---|---|
| 1 | `sales` | `business.md` | `data/1-sales.md` |
| 2 | `marketing` | `business.md`, `data/1-sales.md` | `data/2-marketing.md` |
| 3 | `support` | `business.md`, `knowledge/faq.md` | `data/3-support.md` |
| 4 | `finance` | financial data the owner provides | `data/4-finance.md` |
| 5 | `operations` | the owner's tasks and calendar, plus commitments in `1-sales.md`, `3-support.md`, `4-finance.md` | `data/5-operations.md` |
| 6 | `ceo` | `data/1-` through `data/5-` | `data/6-ceo-report.md` |

Each agent owns exactly one file in `data/`. An agent never writes another
agent's file — if Sales needs something changed in `2-marketing.md`, it says so
and lets Marketing make the edit. The `data/` folder is the shared memory; it
is the only channel between agents.

## Routing

- "Run the Sales Agent" / "run sales" → delegate to the `sales` subagent.
- "Run all agents" / "run the whole business" → run agents 1–6 **in order**,
  because each one reads what the previous ones wrote. Pause and report after
  each agent so the owner can redirect before the next one starts.
- "Give me today's CEO report" / "morning briefing" → run the `ceo` agent
  alone against whatever is already in `data/`. If some department files are
  stale or empty, the report says so rather than filling in the blanks.
- Anything that would send, post, spend, or publish → stop, show the draft, and
  ask. See rule 1.

There are slash commands for the common paths: `/run-department`, `/run-all`,
`/ceo-report`.

## Writing to `data/`

Every department file starts with a status block so the CEO agent can tell
fresh work from stale:

```markdown
# <N>-<department>
**Last updated:** YYYY-MM-DD
**Data sources:** files/tools actually used this run
**Confidence:** what is verified vs. what is an open question
```

Use today's date from the session context. Date only — you have no clock, so
never write a time of day. If you genuinely don't know the date, write
`date unknown` rather than a plausible one: the CEO agent uses this stamp to
decide what's stale, so a guessed date is a fabricated freshness signal and
falls under rule 2 like any other invented number.

Rewrite the whole file on each run rather than appending forever, but carry
forward anything still live — open follow-ups, unresolved flags, pending
approvals. Losing a tracked follow-up is a real failure; a long file is not.

Mark unknowns as `NOT PROVIDED` and list them under a `## Gaps` heading at the
bottom of the file. `NOT PROVIDED` is the standard marker across all six files —
the owner should be able to find every gap in the system by searching for that
one string. The CEO agent surfaces those gaps as well.

## First run

If `data/` doesn't exist yet, run `./setup.sh` from this folder — it creates
`data/` from `templates/data/`. The folder is gitignored, so business data
never leaves the machine through this repo.

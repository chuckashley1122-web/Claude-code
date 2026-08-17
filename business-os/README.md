# AI Business OS 🏢

Six AI specialists — one per department — plus a CEO agent that combines them
into a single daily briefing.

**Sales → Marketing → Support → Finance → Operations → CEO Report**

Each agent does its job and writes one file in `data/`. The CEO agent reads all
five and hands you one clear briefing.

## What this is honestly

Three promises make this safe to run on a real business:

1. **They draft and organize; you approve anything that sends, posts, or
   spends.** Nothing auto-fires.
2. **They never fake data.** No invented leads, revenue, metrics, or replies.
   If a number isn't real, it's marked `NOT PROVIDED` and flagged.
3. **An integration only works once you connect it.** Until then the agents
   work from files, and they say so rather than implying otherwise.

Those are backed by [five hard rules](CLAUDE.md#the-five-hard-rules) written
into every agent definition — the three above, plus "Finance is not an
accountant" and "secrets stay out of git."

This makes you faster and more organized. It does not make you hands-off.

## Setup

```bash
cd business-os
./setup.sh          # creates data/ from templates, and .env from .env.example
claude              # open Claude Code in this folder
```

Then fill in `business.md`. Nothing works well until you do — every agent reads
it first, and they're built to stop and ask rather than guess at your business.

`knowledge/faq.md` is next: it's what the Support Agent answers from, and it's
the difference between Support drafting replies and Support escalating
everything to you.

## Running it

| Command | What it does |
|---|---|
| `/run-all` | All six agents in order, pausing after each |
| `/run-department sales` | One department only |
| `/ceo-report` | The morning briefing, from whatever's in `data/` |

Plain English works too — "run the Sales Agent", "give me today's CEO report".

## Layout

```
business-os/
├── CLAUDE.md              orchestrator + the five hard rules
├── business.md            what you do, your offer, customers, voice  ← fill this in
├── knowledge/faq.md       what Support answers from                  ← fill this in
├── .claude/
│   ├── agents/            sales, marketing, support, finance, operations, ceo
│   └── commands/          /run-all, /run-department, /ceo-report
├── templates/data/        starting templates (tracked in git)
└── data/                  the shared memory — gitignored, stays local
    ├── 1-sales.md   2-marketing.md   3-support.md
    ├── 4-finance.md 5-operations.md  6-ceo-report.md
```

`data/` is the shared memory. Each agent owns exactly one file and never writes
another's — if Sales needs something changed in Marketing's file, it says so and
lets Marketing make the edit.

## The agents

| Agent | Does | Needs | Writes |
|---|---|---|---|
| **Sales** | Finds and organizes leads, researches prospects, drafts outreach, tracks follow-ups | `business.md` | `data/1-sales.md` |
| **Marketing** | Content ideas, drafts posts/campaigns/emails/ads, keeps the calendar | `business.md` + `1-sales.md` | `data/2-marketing.md` |
| **Support** | Drafts replies from your knowledge base, escalates anything sensitive | `business.md` + `knowledge/faq.md` | `data/3-support.md` |
| **Finance** | Organizes revenue/expenses, tracks invoices, flags oddities | data **you** provide | `data/4-finance.md` |
| **Operations** | Tasks, deadlines, bottlenecks, automation candidates | your tasks + calendar, plus commitments made in `1-sales.md`, `3-support.md`, `4-finance.md` | `data/5-operations.md` |
| **CEO** | Combines all five into one daily report | `data/1-` … `data/5-` | `data/6-ceo-report.md` |

**The Finance Agent is not an accountant.** It organizes and summarizes the
numbers you give it. It is not a bookkeeper or tax advisor, and nothing it
produces is financial advice. Have a qualified professional handle your actual
books and taxes.

## Connecting real tools

Start with files. Connect things when you're ready, one at a time:

- **Gmail** → draft and organize email (you still approve every send)
- **Google Calendar** → deadlines and scheduling for Operations
- **CRM (HubSpot etc.)** → real lead and deal data for Sales
- **Google Sheets** → real numbers for Finance
- **A database** → when you outgrow spreadsheets

Put credentials in `.env` (see `.env.example`). Never let an agent claim a tool
is connected unless you actually set it up — the agent definitions forbid it,
but it's worth checking.

## Security

- API keys live in `.env`, never hard-coded and never committed.
- `.env` and `data/` are gitignored, so business data stays on your machine.
- Use read-only keys wherever the provider offers them. Never give an agent
  anything that can move money.
- Keep a human approval step before anything sends, posts, or pays.
- Don't paste customer personal data anywhere you wouldn't want it stored.
- Back up `data/` regularly — it's deliberately outside git.

## A worked example (fictional)

**BrightClean**, a small home-cleaning company:

| Agent | What it does for BrightClean |
|---|---|
| Sales | Finds local property managers, drafts intro emails (owner sends) |
| Marketing | Drafts before/after posts and a spring-cleaning promo |
| Support | Drafts replies to "can you do next Tuesday?" from the FAQ |
| Finance | Organizes the week's invoices, flags 2 overdue |
| Operations | Maps the cleaning schedule, flags a double-booked slot |
| CEO | "3 new leads · 2 overdue invoices · fix Tue double-booking first" |

Illustrative only — not a real business, and not a promise of results.

## Checklist

- [ ] Fill in `business.md`
- [ ] Add real entries to `knowledge/faq.md`
- [ ] Run `/run-department sales` and check the output
- [ ] Do the same for marketing, support, finance, operations
- [ ] Run `/ceo-report`
- [ ] Run `/run-all` end to end
- [ ] Connect one real tool (or stay on files — that's fine)
- [ ] Decide how you'll trigger the daily report — there's no scheduler here, so
      that's a habit, a calendar reminder, or a cron job you add yourself
- [ ] Keep a human approval step before anything sends or spends

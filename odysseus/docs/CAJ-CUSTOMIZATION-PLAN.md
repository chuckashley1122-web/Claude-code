# CA&J customization plan — three isolated workspaces

Phase two of the build guide. Do this **after** the base install passes every
acceptance test, not alongside it.

## Principle

Upstream Odysseus code is never edited. Everything business-specific lives in
one of four places:

1. `.env` — deployment-level settings only (ports, binds, auth).
2. The **Settings** UI — model, search, and email provider connections.
3. Odysseus agent/prompt configuration, seeded from `odysseus/workspaces/`.
4. This repo — the source of truth for prompts, manifests, tests, and checklists.

That keeps `git pull --ff-only origin main` working forever. The moment a
business need requires editing upstream code, stop and reconsider the approach.

## Rollout order

Risk-ordered, not preference-ordered:

| Phase | Workspace | Why this position |
|---|---|---|
| 1 | **CA-J Enterprises** | Public marketing research, draft-only output, no confidential inputs. Failures are cheap and visible. |
| 2 | **Chuck's Daily Grind** | Same low-risk shape, applied to content and product marketing. Proves the pattern copies. |
| 3 | **CA-J Consulting** | Lending and mortgage. Real privacy and compliance exposure. Only onto a stack already proven by phases 1 and 2. |

Do not start phase 2 until phase 1 has run for a week with clean logs, working
approvals, and a tested restore.

## Per-workspace contents

Each directory under `odysseus/workspaces/` holds the same six artifacts:

| File | Purpose |
|---|---|
| `system-prompt.md` | Purpose, allowed actions, prohibited actions, required approvals, brand and domain, audience, output formats |
| `knowledge-manifest.yml` | Every knowledge source, explicitly approved. Nothing is indexed that is not listed here. |
| `agents.md` | Five starter agent/task templates with inputs, outputs, and approval gates |
| `tests.md` | Three normal tests, two failure tests, one prompt-injection test |
| `credentials.md` | Required integrations and scopes by name. Contains no secrets. |
| `audit-checklist.md` | Per-workspace review gates layered on the shared checklist |

Shared across all three: [`_shared/safety-rules.md`](../workspaces/_shared/safety-rules.md)
and [`_shared/audit-checklist.md`](../workspaces/_shared/audit-checklist.md).
Every system prompt inherits both by reference. When a rule needs to change for
everyone, it changes in one file.

## Isolation model

| Dimension | Rule |
|---|---|
| Knowledge | One manifest per workspace. No shared index, no cross-workspace retrieval. |
| Memory | Per-workspace. An Enterprises agent cannot recall a Consulting conversation. |
| Credentials | Separate API keys, mailboxes, and OAuth clients per business. |
| Output | Drafts only. Sending, publishing, and CRM writes are human actions. |
| Combination | Cross-business work happens only when explicitly requested, as a named one-off task, and never as a default behaviour. |

## The workspaces

### CA-J Enterprises — `ca-jenterprises.com/ai`
Local-service marketing: Meta and Google ads, reputation and reviews, lead
generation, GHL workflow design, Austin/Round Rock contractor content.
Audience: local service business owners. Risk: low — public data, draft output.

### CA-J Consulting — `ca-jconsulting.com`
Business lending and mortgage lending **education**, lead intake summarisation,
borrower document checklists, compliance review queue.
Audience: business owners exploring financing. Risk: high — never handles real
borrower data during the pilot, never makes lending decisions, never gives
individualized financial advice, and every output is human-reviewed.

### Chuck's Daily Grind — `chucksdailygrind.com`
Coffee education and SEO content, product descriptions, email drafts, social
calendar and repurposing, customer-question knowledge base, promotion planning.
Audience: coffee customers and subscribers. Risk: low-to-moderate — no health
claims, and promotions need approval before publishing.

## Definition of done, per workspace

A workspace is live only when all of these are true:

- [ ] System prompt loaded into Odysseus and the agent restates its own limits correctly when asked.
- [ ] Knowledge manifest indexed, and nothing outside it appears in retrieval.
- [ ] All five agent templates run end-to-end on test data.
- [ ] All six tests pass — including the prompt-injection test.
- [ ] Credentials issued per-business at minimum scope, and confirmed working.
- [ ] Approval gates verified: a send/publish attempt actually stops for a human.
- [ ] One week of clean logs.
- [ ] A backup taken and a restore tested since the workspace was added.

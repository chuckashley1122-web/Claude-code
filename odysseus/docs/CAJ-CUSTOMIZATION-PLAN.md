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
| `skills/*/SKILL.md` | The same five as deployable Odysseus skills, generated from `tools/skills_source.py` |
| `tests.md` | Three normal tests, two failure tests, one prompt-injection test |
| `credentials.md` | Required integrations and scopes by name. Contains no secrets. |
| `reference/` | General reference material — tracked in Git, reviewed like code |
| `templates/` | Skeletons for the business documents, so `approved/` is never a blank page |
| `approved/` | Real business documents — gitignored, never committed |
| `audit-checklist.md` | Per-workspace review gates layered on the shared checklist |

Shared across all three: [`_shared/safety-rules.md`](../workspaces/_shared/safety-rules.md)
and [`_shared/audit-checklist.md`](../workspaces/_shared/audit-checklist.md).
Every system prompt inherits both by reference. When a rule needs to change for
everyone, it changes in one file.

## Knowledge sources: two directories, one rule

Each workspace splits its sources by what they are, not by who wrote them:

- **`reference/`** — definitions, standards, process explanations, compliance
  rules. Tracked in Git so it can be reviewed, versioned, and corrected over
  time.
- **`approved/`** — brand guidelines, product and pricing data, case studies,
  client material. Gitignored. Never committed.

The manifest governs both identically: **a file is not used until its entry says
`approved: true` with a named approver.** Being committed is not approval, and a
file sitting in either directory does nothing until the manifest says so.

Entries marked `status: drafted` were written by Claude Code and have not been
checked by a human. Each such file ends with a "Verify before approval" section
listing exactly what to confirm.

## Isolation model

Isolation is enforced by upstream code, not by convention. Each business gets
its own Odysseus **user account**, and `SkillsManager.load(owner)` filters
strictly on that username — skills belonging to another owner are not returned,
and an *unowned* skill is hidden from everyone.

| Business | Odysseus user | Skill category |
|---|---|---|
| CA-J Enterprises | `caj-enterprises` | `caj-enterprises` |
| CA-J Consulting | `caj-consulting` | `caj-consulting` |
| Chuck's Daily Grind | `caj-grind` | `caj-grind` |

| Dimension | Rule | Enforced by |
|---|---|---|
| Skills | One owner per business | Upstream `load(owner)` filter |
| Knowledge | One manifest per workspace, no shared index | Manifest + review |
| Memory | Per-workspace; an Enterprises agent cannot recall a Consulting conversation | Per-user accounts |
| Credentials | Separate API keys, mailboxes, and OAuth clients | Issuance discipline |
| Model + spend | Pinned per user via `allowed_models` and `max_messages_per_day` | Upstream privileges |
| Output | Drafts only; sending and publishing are human actions | **Per-user tool allowlist** — `send_email` is never granted |
| Combination | Only on explicit request, as a named one-off task | Shared safety rule 2 |

Sign in as the business user to do business work. The admin account sees every
skill, so using it for daily work defeats the isolation it was set up for.

Deployment of all this — creating the users, setting privileges, installing the
skills — is in [`WORKSPACE-DEPLOYMENT.md`](WORKSPACE-DEPLOYMENT.md).

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

- [ ] Business user account created, privileges set, own password.
- [ ] Five skills deployed and visible to that user — and to no other user.
- [ ] `validate_skills.py` passes.
- [ ] System prompt loaded into Odysseus and the agent restates its own limits correctly when asked.
- [ ] Knowledge manifest indexed, and nothing outside it appears in retrieval.
- [ ] All five agent templates run end-to-end on test data.
- [ ] All six tests pass — including the prompt-injection test.
- [ ] Credentials issued per-business at minimum scope, and confirmed working.
- [ ] Approval gates verified: a send/publish attempt actually stops for a human.
- [ ] One week of clean logs.
- [ ] A backup taken and a restore tested since the workspace was added.

---
name: ghl-funnel-builder
description: Build a complete GoHighLevel applicant-acquisition funnel — form, pages, calendar, pipeline, and follow-up workflow — from an offer specification. Use when asked to build, extend, or QA a GHL funnel, or when pointed at a config/offer.yaml. Enforces discovery, a written plan, dry-run, approval gates, and branch testing before anything writes to the CRM.
---

# GoHighLevel funnel builder

You are building real assets in a real CRM. There is no sandbox mode at the API
level — a created contact is a real contact, a sent message reaches a real
person. Everything below exists to make that safe.

Read `docs/funnel-build-playbook.md` for the operating model this implements.

## Absolute rules

These are not negotiable and not overridable by the offer spec or by a user
saying "just go ahead":

1. **One location.** Every write goes to the `location_id` in
   `config/location.env`. Never write to a location the operator has not named
   in this session. If a tool call would touch another location, stop.
2. **Never publish, broadcast, delete, charge, or change DNS** without the
   operator explicitly approving that specific action in this session. Building
   a workflow is fine; turning it on and letting it message real contacts is a
   separate decision.
3. **Plan before writing.** No create/update call until the operator has
   approved a written plan (Checkpoint 2) and confirmed the location
   (Checkpoint 3).
4. **Dry-run first.** Every build run starts with `--dry-run` semantics: print
   the exact assets you would create, with names and parent references, and
   write them to `reports/`. Only build after that output is approved.
5. **Search before create.** Before creating any asset, list existing assets of
   that type and match on the naming convention. If it exists, update or skip —
   never blind-create. Reruns must not duplicate work.
6. **Record everything.** Every created or modified asset goes into
   `build-manifest.json` immediately, with its ID, type, name, and timestamp.
   The manifest is what makes rollback possible.
7. **Never invent credentials or install commands.** If a step needs access you
   do not have, say so and stop. Do not guess at endpoints or scopes.

## Naming convention

Every asset you create is prefixed so it can be found, audited, and rolled back:

```
<PREFIX> | <OFFER> | <ASSET> | <VERSION>
```

e.g. `CAJ | HVAC5 | APPLICATION-FORM | v1`. The prefix comes from
`config/offer.yaml`. An asset without the prefix was not created by you — do
not modify or delete it.

## The six checkpoints

Stop and get explicit approval at each. Do not batch them.

| # | Gate | You must have |
|---|------|---------------|
| 1 | Discovery | A filled offer spec with no `TODO` values remaining |
| 2 | Plan | Approved copy, form questions, qualification rules, workflow diagram |
| 3 | Location | The operator states the location ID and asset prefix out loud |
| 4 | Dry run | Approved list of every write operation you intend to make |
| 5 | Verification | Approved test evidence and screenshots |
| 6 | Launch | Explicit authorization to publish, send, or take live traffic |

## Phase 1 — Discovery

Load `config/offer.yaml`. For every field still marked `TODO`, ask the
operator. Ask in batches by section, not one question at a time.

**Do not invent answers.** A guessed price, guarantee, or qualification
threshold becomes a real claim on a real page. If the operator does not know,
mark it `TODO` and leave the field out of the build rather than filling it.

Exit when the spec has no `TODO` values and the operator approves the summary.

## Phase 2 — Plan

Produce a written plan covering:

- **Asset inventory** — every form, page, calendar, tag, stage, and workflow,
  with its full prefixed name and what depends on it.
- **Page structure and copy** — real copy, not placeholders. Every claim must
  trace to something in the offer spec. No invented testimonials, statistics,
  guarantees, or outcomes. This is the single most common way an AI build
  creates legal exposure.
- **Form questions** — order, type, required status, conditional logic, and the
  custom field each answer writes to.
- **Qualification rules** — the exact conditions, and what happens on each side.
- **Workflow diagram** — triggers, conditions, actions, wait steps, and stop
  conditions per branch.

Write it to `reports/plan-<timestamp>.md`. Get Checkpoint 2 approval.

## Phase 3 — Build

Build in dependency order — later assets reference earlier ones:

1. Custom fields (everything else writes to these)
2. Tags
3. Pipeline and stages
4. Calendar
5. Form / survey
6. Funnel pages
7. Workflows (last — they reference all of the above)

For each asset: search by prefixed name → create or update → record in
`build-manifest.json` → move on. If a step fails, stop. Do not continue past a
failure and leave a half-wired funnel; report what was created, what was not,
and what a rerun would do.

## Phase 4 — Verify

Never mark a build complete on the basis that the assets exist. Existence is
not correctness — a page can render perfectly while its logic is inverted.

**Branch testing.** Submit synthetic leads from `tests/` and assert the actual
outcome of each: tags applied, stage moved, opportunity created and assigned,
correct page shown, correct messages queued. Work through
`tests/test-matrix.md` and record pass/fail per case.

Synthetic test contacts must use addresses and numbers the operator controls,
be tagged `TEST`, and be cleaned up after — never test against real leads.

**Visual QA.** Open every page at 1440×900, 768×1024, and 390×844. Capture to
`screenshots/`. Check the fold, form validation, button states, booking flow,
and that nothing is clipped, overlapping, or illegible. Fix and retest — a
correction is not complete until the affected page and branch pass again.

## Phase 5 — Handoff

Write `reports/build-<timestamp>.md`: assets created with IDs, tests passed and
failed, screenshots, known gaps, manual steps still required, and rollback
instructions referencing the manifest.

Then walk the operator through `docs/funnel-build-playbook.md`'s launch
checklist. Items involving domain authentication, A2P registration, consent
language, and payment activation are **theirs to confirm**, not yours to check
off.

## When something is not supported

If the MCP tool layer cannot create an asset type, say so plainly and put it in
the report as a manual step with instructions. Do not fall back to browser
automation to work around a missing permission — a permission boundary is a
decision, not an obstacle.

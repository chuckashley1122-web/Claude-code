# GoHighLevel funnel build playbook

The operating model behind the [`ghl-funnel-builder`](../.claude/skills/ghl-funnel-builder/SKILL.md)
skill: how a funnel gets built, what has to be true before it writes anything,
and what a human signs off on.

Prerequisite: the GHL MCP server is connected — see
[`ghl-mcp-setup.md`](ghl-mcp-setup.md).

## What this builds

A complete applicant-acquisition funnel in one GoHighLevel sub-account:

| Asset | Purpose |
|-------|---------|
| Custom fields | Where every form answer lands |
| Tags | Qualification state, source, test markers |
| Pipeline + stages | New Application → Qualified → Booked → Showed → Won/Lost/Disqualified |
| Calendar | Round-robin application booking |
| Application form | Three steps: contact → situation → qualification |
| Funnel pages | Landing, application, qualified booking, decline, thank-you |
| Workflow | Intake, qualification, booking nurture, reminders, no-show recovery, disqualification |

## Why it works this way

The failure mode of an AI-assisted CRM build is not that it fails loudly. It's
that it **succeeds visibly and wrongly** — pages render, assets exist, the
build reports success, and the qualification logic is backwards. That is only
caught by asserting outcomes on synthetic leads, which is why verification is a
phase rather than a step.

The second failure mode is scope. A credential broad enough to build a funnel
is broad enough to damage every sub-account under an agency. Hence one
location, least privilege, and a naming prefix that bounds what the builder is
even allowed to look at.

## The phases

```
Discovery ─▶ Plan ─▶ [CP1,2,3] ─▶ Dry run ─▶ [CP4] ─▶ Build ─▶ Verify ─▶ [CP5] ─▶ Handoff ─▶ [CP6] ─▶ Launch
```

| Phase | Produces | Gate |
|-------|----------|------|
| Discovery | Filled `config/offer.yaml`, no `TODO` left | CP1: approve summary |
| Plan | `reports/plan-<ts>.md` — assets, copy, rules, workflow diagram | CP2: approve plan |
| Location | Confirmed location ID and prefix | CP3: operator states both |
| Dry run | Manifest with `status: dry_run` listing every intended write | CP4: approve writes |
| Build | Assets created in dependency order; `build-manifest.json` | — |
| Verify | Test matrix results + `screenshots/` | CP5: approve evidence |
| Handoff | `reports/build-<ts>.md` + launch checklist | CP6: authorize launch |

Checkpoints are not batched. CP6 is separate from CP5 because "the funnel is
correct" and "start sending to real people" are different decisions.

## Safeguards

| Risk | Safeguard |
|------|-----------|
| Overbroad credentials | Location-scoped Private Integration Token; least-privilege scopes; separate sandbox and production tokens |
| Writing to the wrong account | Single `GHL_LOCATION`; builder refuses any other location |
| Duplicate assets on rerun | Search-before-create keyed on prefixed names; manifest records `skipped_exists` |
| Silent logic errors | Synthetic leads with per-branch assertions, not existence checks |
| Accidental send or publish | Publish, broadcast, delete, payment, and DNS actions require explicit per-action approval |
| Invented claims | Every claim traces to the offer spec; human claims review before launch |
| Half-built funnel after failure | Build stops on first failure; manifest shows what exists and what a rerun would do |
| Platform changes | Pin the MCP server version; keep a manual fallback for anything unsupported |

## Rollout

Do not start in a client account. Do not start in your own production account.

| Phase | Deliverable | Exit criterion |
|-------|-------------|----------------|
| 1. Proof of concept | Sandbox funnel, form, calendar, core workflow | All synthetic tests pass; zero production contacts touched |
| 2. Internal pilot | Own offer on a branded test domain | Real internal bookings and notifications verified end to end |
| 3. Controlled client pilot | One client sub-account, capped traffic | No duplicate or error events; client signs off |
| 4. Productized rollout | Reusable templates, QA report, support SOP | Three deployments with predictable effort |

Start with one funnel, one calendar, and a workflow of 10–15 actions before
attempting a 29-step production sequence. Package as a reusable template only
after two clean end-to-end runs.

## Launch checklist

Human-verified, at CP6. The builder does not check these off.

**Scope and access**
- ☐ Correct location ID and account owner confirmed
- ☐ No agency-wide credential used where a location-scoped one works
- ☐ Asset names all carry the approved prefix
- ☐ Build manifest and rollback notes saved

**Logic**
- ☐ Forms save every answer to the correct field
- ☐ Qualified and disqualified branches both pass
- ☐ Round-robin users and real connected calendars verified
- ☐ Pipeline stages, ownership, and values correct
- ☐ Duplicate-contact and repeat-submission behavior tested

**Communications**
- ☐ Email sending domain authenticated
- ☐ Phone / A2P registration and consent configuration complete
- ☐ DND, unsubscribe, replies, and quiet hours all stop automation
- ☐ Privacy policy and terms links resolve

**Presentation**
- ☐ Desktop, tablet, and mobile screenshots approved
- ☐ No false testimonials, promises, or unsupported claims
- ☐ Meta / Google tracking and UTM capture tested

**Authorization**
- ☐ Publish, send, payment, and DNS actions explicitly approved by a human
- ☐ Operator has the handoff report and monitoring SOP

## Known limits

- **No API-level sandbox.** GoHighLevel has no test mode. Isolation comes from
  using a disposable sub-account, nothing else.
- **Coverage varies by asset type.** Funnel page and workflow creation are less
  completely covered by the API than contacts and opportunities. Anything the
  tool layer cannot do is recorded as a manual step, not worked around with
  browser automation.
- **Messaging channels need their own diligence.** Any non-standard channel
  (including iMessage-style integrations) needs its provider, consent
  requirements, number ownership, and volume limits confirmed before you rely
  on it.
- **Compliance is not automatable.** Consent language, A2P registration, and
  industry restrictions need a qualified human, not a checklist pass.

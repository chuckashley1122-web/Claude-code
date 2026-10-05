# SPEC-03 High-Ticket Agency Client Acquisition System (draft build)

A set of draft files and offline tests for CA-J Enterprises' high-ticket HVAC agency offer: niche brief, offer,
economics, CRM and calendar specs, five ad concepts with copy, lead form, Facebook-to-GHL integration spec, four
follow-up workflows, message templates, sales call guide, close and onboarding pack, delivery scope, a 14-case test
log, and step-by-step checklists for the human work.

**Everything is draft-only. Nothing was launched. No GHL, Meta or payment object was touched.** No network call is made,
no money is spent, and `DRY_RUN` defaults to true. The frozen live Meta campaign (named in `config/constants.py`) is never
edited, paused or duplicated; any new campaign is a separate NEW draft built by a human from `ui-tasks/META-BUILD-CHECKLIST.md`.
The GHL location `UWc5vKBgFVPdxNTRAy2s` is reference-only.

## Run order

From this folder (`build/03-high-ticket/`), on Chuck's machine:

```
python tools/validate_config.py     # hard checks on IDs, caps and flags (exit 0 = clean)
python tools/build_all.py           # regenerates out/, ui-tasks/, logs/build.log; runs tests + compliance scan
python tools/run_tests.py           # T01-T14 -> out/tests/test_log.md + T01.json ... T14.json
python tools/compliance_scan.py     # per-file scan; exit 0 only with zero hits
python -m unittest discover -s tests   # unit + acceptance tests
```

On Windows use `python tools\build_all.py` etc.; on Linux `python3` works the same. Python 3.11 standard library only.

## What is where

| Path | What it is |
|---|---|
| `config/constants.py` | House facts, locked CA-J terms, guard flags (literals) |
| `config/build_config.json` | Single source of truth; unknowns are `NEEDS_EVIDENCE` |
| `config/decision_log.jsonl` | Append-only decision log (generated) |
| `config/asset_register.json` | Every generated asset with status and owner |
| `tools/` | State layer, guardrails, validator, economics, compliance scan, orchestrator, test runner |
| `src/` | One generator per deliverable, plus `connectors.py` (local + refusing live gateways), `funnel_sim.py` (offline workflow simulator), `tz.py`, `utm_fixtures.py`, `ui_tasks.py` |
| `out/` | Generated drafts, economics, tests, evidence, compliance report (generated; git-ignored) |
| `ui-tasks/` | Human checklists: GHL, Meta, and every decision/approval gate |
| `tests/` | `unittest` suite |

## How the tests are judged

`tools/run_tests.py` runs each case's logic against an offline simulator built from the same timing, form and template
definitions the specs use. A case is `FAIL` if the logic is wrong, `BLOCKED` if the logic passes but the case still needs a
live account or a UI action (the exact missing input is recorded), and `PASS` only when it is fully verifiable offline.
BLOCKED is never counted as passing. Current result: T12 PASS (local asset and claim review); T01-T11, T13, T14 BLOCKED
pending live verification in GHL/Meta; zero FAIL.

## Locked commercial terms (internal only)

Tech fee, setup fee (waived) and per-booked-appointment fee are defined once in `config/constants.py` and appear only in the
internal offer spec and close pack. Meeting-first: no price appears in any ad, form, message, page or AI-reply asset; pricing
intent routes to https://ca-jenterprises.com/ai.

## Spend items (all require explicit written approval; none are purchased or started by this build)

| Service | What it is for | Approval | Cost |
|---|---|---|---|
| Meta ads (agency acquisition media) | Running the new draft lead campaign | Approval required (`APPROVAL_AD_SPEND`, `AD_SPEND_CAP_USD` stays 0) | NEEDS_EVIDENCE |
| GoHighLevel subscription / add-ons | CRM, calendar, workflows, Facebook lead sync | Approval required for any upgrade | NEEDS_EVIDENCE |
| SMS / A2P messaging fees | Permitted SMS reminders | Approval required | NEEDS_EVIDENCE |
| Email sending (verified domain) | Booking acknowledgment, confirmation, follow-ups | Approval required if paid | NEEDS_EVIDENCE |
| Image generation tool | Producing the five ad images and crops | Approval required | NEEDS_EVIDENCE |
| Payment processor fees | Collecting client payments (test mode first) | Approval required | NEEDS_EVIDENCE |
| Telephony / live transfer (if sold to a client) | Client call routing | Approval required | NEEDS_EVIDENCE |
| AI provider usage (only if sold) | AI-assisted follow-up for a client | Approval required | NEEDS_EVIDENCE |
| Whop | Not needed; do not buy a tool to reproduce the video interface | Not approved | NEEDS_EVIDENCE |
| Domains / DNS | Not needed by this build | Approval required | NEEDS_EVIDENCE |

## Deviations from spec

- **Interpreter:** the spec says `python`; this repo's environment uses `python3`. Code hardcodes neither; README shows `python`.
- **Extra files beyond the section 4 tree:** `src/common.py`, `src/tz.py`, `src/connectors.py`, `src/funnel_sim.py`,
  `src/utm_fixtures.py`, `src/ui_tasks.py`, `out/niche_brief.json`, `out/ghl_pipeline_spec.json`, `out/attribution_fixtures.json`,
  `out/blockers.json`, `out/compliance_report.md`, `out/tests/evidence/`, `tests/`, `.gitignore`. They implement the section 3
  "can build" items (UTM fixtures, test evidence) and the build rules (connector interfaces, unit tests).
- **Two extra message templates** (`unbooked_reminder`, `unbooked_followup`) carry the +2h reminder and +1d email that
  workflow 02 requires; the source supplies no copy for them. They are labeled "build addition".
- **Tests:** every T-case except T12 is BLOCKED because it needs a live GHL/Meta/processor account; the offline logic for each
  passes and is recorded as `logic_simulation`.
- **Timezone:** `zoneinfo` needs the non-stdlib `tzdata` package on Windows, so `src/tz.py` implements US Central rules and is
  checked against `zoneinfo` where the system database exists.
- **`assert_no_spend`:** a zero amount is treated as no spend and passes without approval; any positive amount requires
  `approval_flag is True`.
- **Generated outputs are git-ignored** (`out/`, `logs/`, `config/decision_log.jsonl`) per the build rules; run
  `python tools/build_all.py` to recreate them. `ui-tasks/` and `config/asset_register.json` are deterministic and kept.
- **Service area:** the playbook proposes Austin and Round Rock; the spec marks service area `NEEDS_EVIDENCE`, so ad copy omits a
  market and the source example copy is shown verbatim, labeled as a proposal.
- **Niche:** set to `HVAC` because it follows from `BUILD_MODE = CAJ_HVAC`.

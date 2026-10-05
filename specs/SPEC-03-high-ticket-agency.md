# High Ticket Agency

# SPEC-03 — High-Ticket Agency Client Acquisition System

**Executor:** Claude Code / Claude Cowork, headless (`claude -p`).

**Capabilities assumed:** filesystem read/write, shell commands, Python 3.11 via `python` (NOT `python3`). **No browser. No UI logins. No network-to-authenticated-service.**

**Repo root:** `C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system\`

**Host:** Windows 11. Shell is bash (MSYS). Inline heredoc / giant one-liner shell commands are BLOCKED — every script is written to a `.py` file then run with `python <file>`.

**Execute top to bottom. Do not ask questions. Where a value is unknown, emit the literal string `NEEDS_EVIDENCE` and continue.**

## 1. Source & Provenance

- **File read:** `C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system\playbooks\03-high-ticket-agency-action-plan.md`
- **Size:** 43,669 characters, 356 lines, 44,305 bytes. Read in full. Not truncated.
- **What the source actually is:** an AI-generated Word playbook dated 2026-09-13, prepared for Chuck Ashley / CA-J Enterprises, describing itself as an execution specification ("the deliverable of this assignment is this Word playbook"). It is a *plan*, not a record. It contains three labeled content classes: **Source** (things said in a training video), **Build addition** (author-supplied implementation detail the video omits), and **CA-J adaptation** (a proposed HVAC variant explicitly flagged as "not the instructor's example or an approved change to Chuck's existing offers").
- **Upstream source:** a pasted transcript, `Pasted markdown(20260913-143752).md`, covering 0:00–50:30 of `https://www.youtube.com/watch?v=PdNNCC6wqK4`. Direct video retrieval was throttled at generation time; screen details, edits, payment records and anything outside the transcript were never inspected.
- **State of the world at generation time:** the source states plainly that no GHL system, ad campaign, payment product, or Hermes connection had been created by preparing the playbook. **Nothing described in this source exists yet.** This spec must not assume otherwise.
**Claims in the source that are NOT verified by CA-J:**

| # | Claim | Status |
|---|---|---|
| S1 | $2,000/mo or $7,800/6-month service price | Instructor's example price. Not a CA-J price. Not approved. |
| S2 | "$2,000 × 6 = $12,000 revenue" | Source itself corrects this: $7,800 saves $4,200 (35%), averaging $1,300/service-month. Not recurring revenue. |
| S3 | "2x ROI", "pay per deal", "five listings in six months" | Presented interchangeably in the video; the source flags them as creating *different obligations*. Not guaranteed terms. |
| S4 | Payment "completion" reported at transcript 49:18 | Not evidence of settlement, and not a repeatable result. |
| S5 | Market-share arithmetic at 4:42–5:23 | Source flags it as **incorrect** (5/100,000 = 0.005%). |
| S6 | 50,000-population market threshold | Instructor heuristic, not a requirement. |
| S7 | "10 hour challenge" validates, launches and closes a business | Source explicitly says the timing claim does not establish this. |
| S8 | Instructor's market counts, conversion claims, agency revenue claims, client outcomes | Not independently verified. Never restate as CA-J results. |
| S9 | GHL location `nuhFUYu0ZF9Eswiz9P79` | **CONTRADICTS house fact.** The only authorized build location is `UWc5vKBgFVPdxNTRAy2s`. Treat `nuhFUYu0ZF9Eswiz9P79` as an unverified stale ID and do not use it. |
| S10 | Whop exposes a Meta campaign creation flow | Source: "availability was not independently verified." |
| S11 | 2–3 week launch, ~90-day results horizon, $1,500 renewal example, "one company per area" exclusivity | Instructor expectations/examples, not CA-J commitments. |
| S12 | Five GHL help-center URLs cited as References 2–5 | Retrieved by the source on 2026-09-13, not re-verified here. Treat as `NEEDS_EVIDENCE` if relied on. |
| S13 | The video description's Google Doc / GHL snapshot / scripts / coaching materials | Never supplied, never retrieved. Contents unknown. |

**Rule:** identical-looking numbers from the source are NOT results CA-J has achieved. Do not restate an instructor's outcome as CA-J's own. Anything unverifiable is written as `NEEDS_EVIDENCE`.

## 2. Objective

Produce a complete, reviewable, draft-only client-acquisition system for CA-J Enterprises' high-ticket agency offer as a set of files on disk: a niche brief, an offer specification, an economics and margin model, a CRM/calendar configuration spec, five ad creative concepts, matching ad copy, a qualification form spec, a Facebook→GHL integration and field-mapping spec, four follow-up/reminder workflow specs, message templates, a sales call guide, a close/onboarding pack, a delivery-scope definition, and a 14-case test log — all generated deterministically by Python scripts into a fixed output tree, all validated against hard guardrails (no spend, frozen live campaign untouched, meeting-first pricing, logo-not-first), with every unknown left as `NEEDS_EVIDENCE` and every UI-press action emitted as a checklist for a human rather than attempted. The build produces drafts and test evidence only; it launches nothing.

## 3. Code-Layer vs UI-Layer Split

Strict. Claude Code **cannot** operate GoHighLevel, Meta Ads Manager, Meta Business Suite, Whop, AI Studio, DNS registrars, or any logged-in UI. Everything in the right column is emitted as a markdown checklist with exact field values for a human to execute, and is never marked done by the build.

| Claude Code CAN build (files + shell + Python) | Needs browser / logged-in account / human |
|---|---|
| Directory scaffold, `build_config.json`, `.env.example`, decision log, asset register | Creating/renaming anything inside GHL location `UWc5vKBgFVPdxNTRAy2s` |
| Config validator that asserts house facts and case-sensitive GHL IDs | Creating the GHL pipeline, stages, custom fields, calendars |
| Guardrail module (frozen-campaign, no-spend, meeting-first, logo-not-first) | Publishing/halting GHL workflows |
| Niche brief generator → markdown + JSON | Connecting the Facebook Page / lead form integration in GHL Settings → Integrations |
| Break-even and agency-margin calculators (inputs labeled `assumption`) | Field mapping and duplicate-match configuration in the GHL Facebook integration UI |
| Offer specification, positioning copy, risk-reversal policy (default: no numerical guarantee) | Creating the Facebook Lead Form in Meta and attaching it to ads |
| GHL pipeline / custom-field / calendar **specifications** as markdown + JSON for a human to type in | Booking-calendar creation, availability windows, Google Meet connection |
| Five ad concepts: on-image text, visual direction, primary text, headline, CTA — as `.md` + `.json` | Generating images with an image tool (no image model in this executor's toolset) |
| Ad copy pack, message templates, sales call guide, pre-call and welcome static HTML drafts | Meta Business Portfolio / ad account / payment method setup |
| Workflow logic specs (triggers, filters, waits, branches, stop conditions) as reviewable documents | Meta Pixel / Dataset creation, CAPI access-token generation |
| Static HTML drafts of pre-call page and welcome page (openable as `file://`) for content review | Campaign, ad set and ad creation in Meta Ads Manager |
| `tools/run_tests.py` — the 14-case test log with pass/fail/`BLOCKED` states and evidence paths | Any DNS change, subdomain add, domain purchase, CAPI verification |
| UTM/fbclid test-URL generator and attribution-parameter fixtures | Launching, pausing, resuming, or editing any live Meta campaign |
| UI task checklists with pre-filled exact values, plus a human-decision queue | Adding a payment method, buying a domain, buying a tool, setting any ad budget |

## 4. Deliverable File Tree

All paths relative to repo root. Created by the build; nothing outside `build\03-high-ticket\` is written.

`build\03-high-ticket\
├─ README.md                              # What was built, what is draft-only, how to run
├─ .env.example                           # Env var NAMES only. Placeholder values. No real secrets.
├─ config\
│  ├─ build_config.json                   # Single source of truth; unknowns = "NEEDS_EVIDENCE"
│  ├─ decision_log.jsonl                  # Append-only: timestamp, key, value, source, status
│  ├─ asset_register.json                 # Every generated asset: id, path, status, owner
│  └─ constants.py                        # House facts, locked pricing, ID constants, guard flags
├─ tools\
│  ├─ state.py                            # Status enum, decision-log writer, blocked-item recorder
│  ├─ guardrails.py                       # Frozen-campaign / no-spend / meeting-first / logo-last guards
│  ├─ validate_config.py                  # Hard assertions on IDs, caps and forbidden values
│  ├─ break_even.py                       # Client break-even formulas + illustration
│  ├─ margin_model.py                     # Agency margin on any stated package term
│  ├─ compliance_scan.py                  # Scans every generated .md/.json for banned patterns
│  ├─ build_all.py                        # Idempotent orchestrator; runs steps in dependency order
│  └─ run_tests.py                        # T01–T14; emits PASS / FAIL / BLOCKED + evidence path
├─ src\
│  ├─ niche_brief.py                      # → out\niche_brief.md
│  ├─ offer_spec.py                       # → out\offer_spec.md
│  ├─ positioning.py                      # → out\positioning.md
│  ├─ risk_reversal.py                    # → out\risk_reversal.md
│  ├─ crm_schema.py                       # → out\ghl_pipeline_spec.md, out\ghl_custom_fields.json
│  ├─ calendar_spec.py                    # → out\calendar_spec.md
│  ├─ creative_pack.py                    # → out\creatives\A01..A05.{md,json}
│  ├─ copy_pack.py                        # → out\copy\A01..A05.md
│  ├─ form_spec.py                        # → out\form_spec.md, out\qualification_logic.json
│  ├─ integration_spec.py                 # → out\ghl_facebook_integration.md, out\field_map.json
│  ├─ workflow_specs.py                   # → out\workflows\01-intake.md … 04-outcome.md
│  ├─ message_templates.py                # → out\messages\{booking_ack,confirmation,reminder_sms,no_show}.md
│  ├─ precall_page.py                     # → out\precall_page\index.html
│  ├─ sales_guide.py                      # → out\sales_call_guide.md
│  ├─ onboarding_pack.py                  # → out\close_pack.md, out\welcome_page\index.html, out\intake_form.json
│  ├─ delivery_scope.py                   # → out\delivery_scope.md
│  └─ launch_review.py                    # → out\launch_review.md, out\asset_register.md
├─ out\
│  ├─ economics\
│  │  ├─ client_break_even.md
│  │  └─ agency_margin.md
│  ├─ tests\
│  │  ├─ test_log.md
│  │  └─ T01.json … T14.json
│  └─ (all files listed under src\ above)
├─ ui-tasks\
│  ├─ GHL-BUILD-CHECKLIST.md              # Exact GHL UI steps with pre-filled values
│  ├─ META-BUILD-CHECKLIST.md             # Exact Meta UI steps; campaign stays PAUSED
│  └─ HUMAN-DECISIONS.md                  # Every NEEDS_EVIDENCE + every approval gate, with next action
└─ logs\
   └─ build.log                           # Timestamped run log from build_all.py`

## 5. Build Steps

Execute in order. Every step ends by writing its file, appending to `config\decision_log.jsonl`, and recording the asset in `config\asset_register.json`.

1. **Scaffold + state layer.** Create the tree in section 4. Write `tools/state.py`: `STATUS` enum = `Not started | Draft | Tested | Ready for launch | Live | Blocked`; `log(key, value, source, status)` appending JSON lines to `config/decision_log.jsonl`; `record_blocker(item, missing_input, work_affected, next_action)`; `mark_asset(id, path, status)`. No status may be written as `Live` by any script.
1. **Constants.** Write `config/constants.py` with every value in section 6, including the guard booleans. House facts are literals here, not looked up.
1. **Config.** Write `config/build_config.json` with the exact key set in section 6. `BUILD_MODE` defaults to `CAJ_HVAC`. Any key whose value is not in section 6 gets `"NEEDS_EVIDENCE"`. Do not invent IDs, URLs, credentials, or Page names.
1. **Env template.** Write `.env.example` listing env var **names only** with empty placeholders and a comment block. No real token, key, password or ID value may appear in any committed file. Real values live only in the human's untracked `.env`.
1. **Validator.** Write `tools/validate_config.py`. It must hard-fail (non-zero exit) if: `GHL_LOCATION_ID != "UWc5vKBgFVPdxNTRAy2s"` (exact case); any required ID is lowercase-mangled or guessed; `AD_SPEND_CAP_USD != 0` without `APPROVAL_AD_SPEND=true`; `LAUNCH_AUTHORITY != "none"` without `APPROVAL_LAUNCH=true`; `FROZEN_CAMPAIGN_PROTECTED != true`; `QUOTE_PRICE_IN_MESSAGE != false`. Emit one line per check.
1. **Guardrails.** Write `tools/guardrails.py` exposing four functions, all called by `compliance_scan.py` and `run_tests.py`:
   - `assert_not_frozen_campaign(name)` — raises on any string equal to `CAJ_HVAC27_US_PURCHASE_TEST02`; any generated campaign name must be a NEW draft named `CAJ-HT-HVAC-Leads-<YYYYMMDD>`. Encodes: never edit, pause, duplicate-in-place, or otherwise touch the frozen campaign — **editing resets Meta's learning phase**.

   - `assert_no_spend(amount, approval_flag)` — raises unless `approval_flag is True`. Applies to ad spend, domains, subscriptions, upgrades, tools.

   - `assert_meeting_first(text)` — raises if generated message copy contains a currency amount or a price for CA-J's service. Booking destination is always the plain booking URL.

   - `assert_logo_not_first(creative)` — raises if a creative's visual direction places the CA-J logo before the outcome/offer element. Logo may appear only as a small footer disclaimer.

1. **Niche brief.** `src/niche_brief.py` → `out\niche_brief.md`. Sections: interest/experience, addressable buyer count, value per customer, seasonality, three competing agencies. Every numeric field defaults to `NEEDS_EVIDENCE` with a blank evidence column and a `date_observed` field. Add the source's own correction: competitor ads indicate market activity, not profitability; use business counts when selling to business owners; the 50,000 threshold is a heuristic, not a requirement.
1. **Client break-even.** `tools/break_even.py` → `out\economics\client_break_even.md`. Implement exactly: `monthly_acquisition_cost = monthly_service_fee + media_spend + separately_charged_tools`; `required_sales = ceil(acquisition_cost / contribution_per_sale)`; `required_held = ceil(required_sales / close_rate)`; `required_leads = ceil(required_held / lead_to_held_rate)`. Reproduce the source's illustration ($1,300 service + $1,500 media = $2,800; $3,000 contribution; 25% close; 40% lead→held → ~1 sale, 4 held, 10 leads) and label every input `assumption — not a CA-J result`. Contribution = revenue − variable delivery cost; never treat commission or revenue as profit.
1. **Agency margin.** `tools/margin_model.py` → `out\economics\agency_margin.md`. For any candidate package term, subtract fulfillment labor, appointment setting, editing, software, payment fees and refund exposure, then CA-J's own acquisition cost. If any input is `NEEDS_EVIDENCE`, the output must state "margin cannot be modeled with current inputs" rather than guessing. Refuse to model unlimited-scope delivery when delivery cost is unknown.
1. **Offer specification.** `src/offer_spec.py` → `out\offer_spec.md`. Fill every field: buyer, desired outcome, actual service, included channels, deliverable quantity, implementation dependencies, service term, fee, separate media budget, client responsibilities, reporting, cancellation, renewal, remedy. The fee comes from section 6 locked pricing, never from the source's examples. Emit the source's comparison table (source example vs CA-J adaptation) with the CA-J column carrying locked pricing and `NEEDS_EVIDENCE` for scope-derived items.
1. **Positioning.** `src/positioning.py` → `out\positioning.md`. Use the source's proposed copy verbatim as the draft, explicitly labeled "proposed copy, not a performance guarantee": *"CA-J Enterprises helps HVAC businesses build a managed system for generating inquiries, following up and booking estimates. We handle the agreed marketing and automation work while your team handles calls, estimates and sales. Book a strategy session to review fit, capacity and budget."* No ROI figure, no scarcity, no exclusivity, no guarantee.
1. **Risk reversal.** `src/risk_reversal.py` → `out\risk_reversal.md`. **Default: no numerical guarantee.** Record that the source's 2x ROI claim ships with no enforceable calculation or remedy. If a human later chooses a guarantee, the template must require all of: eligible revenue/contribution definition, included costs, attribution method, duration, evidence standard, client obligations, exclusions, claim window, exact remedy, and an explicit refund-or-credit mechanism when the fee is prepaid.
1. **CRM schema.** `src/crm_schema.py` → `out\ghl_pipeline_spec.md` + `out\ghl_custom_fields.json`. Base on the existing object in location `UWc5vKBgFVPdxNTRAy2s`: pipeline `CA&J Demo - Lead Pipeline` = `U95kdMryqjDqu7JeFrdw`, stages New Lead, Contacted, Appointment Booked, Quote Sent, Job Won, Lost / Not a Fit. Emit a *separate* spec for the new acquisition pipeline `CAJ-HT-HVAC-Sales` with stages: New lead, Qualified unbooked, Booked, Confirmed, Attended, Proposal sent, Won pending payment, Paid onboarding, Active client, Lost, Disqualified. Custom fields JSON: niche, business name, website, service area, decision maker answer, offer version, campaign ID, ad ID, form ID, Meta lead ID, lead received time, first response time, qualification status, appointment ID, appointment confirmation, deal amount, payment reference, loss reason, consent source, consent wording version, consent timestamp. Phone/email stay in native fields. **No secrets in contact notes.**
1. **Calendar spec.** `src/calendar_spec.py` → `out\calendar_spec.md`. Name: `HVAC Growth Strategy Session`. Duration 45 min. Timezone `America/Chicago` (mark `NEEDS_EVIDENCE` that account settings confirm it). Working hours `NEEDS_EVIDENCE`. Max booking horizon 3 days. 2-hour minimum notice, 15-minute buffers, conditional on owner schedule. Public calendar URL `NEEDS_EVIDENCE`. State explicitly that if no slots exist, create an owner task — never an empty-calendar loop. Note: the transcript's "keep this off" remark at 25:01 refers to an unidentified control; do not guess which one.
1. **Creative pack — five concepts.** `src/creative_pack.py` → `out\creatives\A01…A05.{md,json}`. Use the source's concept prompt structure with placeholders filled from config, and the source's five angles: A01 lead quality, A02 shared leads/ownership, A03 clear service offer, A04 referral dependence, A05 past agency disappointment. Each JSON record: `ad_id, angle, on_image_words, visual_direction, primary_text, headline, cta, offer_reference, version, proof_points` (proof = `[]` → `NONE`). Constraints: original or licensed imagery only; use competitor ads for research, not copying; **the CA-J logo must never be the first element** — outcome or offer leads, logo only as a small footer disclaimer; no fake dashboards, no invented booking totals, no unverified guarantees; black text on white; 1080×1350 feed + one alternate crop per concept. `guardrails.assert_logo_not_first()` runs on every record. **Image generation is not possible in this executor — emit the exact prompt and specs for a human/image tool, do not fabricate image files.**
1. **Ad copy pack.** `src/copy_pack.py` → `out\copy\A01…A05.md`. One record per ad: primary text, headline, CTA. CTA is `Learn More` or the booking URL — never a price. Include the source's HVAC example copy and headline `Review your HVAC growth plan`. Run `assert_meeting_first()` on every string.
1. **Form spec.** `src/form_spec.py` → `out\form_spec.md` + `out\qualification_logic.json`. Single qualification question: *"Do you own or make marketing decisions for an HVAC company?"* — Yes → continue; No → disqualification ending. Collect name, email, phone. If conditional endings are unavailable, the logic JSON must specify: flag No responses in GHL and suppress the sales booking sequence. Qualified ending copy: *"One last step — book your strategy session."* / *"Choose a time to review your goals, service area and marketing needs."* / button `Book a time` → `https://ca-jenterprises.com/ai`. Privacy policy URL is `NEEDS_EVIDENCE` — never guessed. The "one company per area" claim is emitted only if a documented territory policy exists (`NEEDS_EVIDENCE`), otherwise omitted.
1. **Integration spec.** `src/integration_spec.py` → `out\ghl_facebook_integration.md` + `out\field_map.json`. Steps for a human: open Settings → Integrations in `UWc5vKBgFVPdxNTRAy2s`, inspect the Facebook connection, confirm access to the intended Page and lead forms, prefer **new leads only** during setup. Field map: name/email/phone → native; decision-maker question → its dedicated custom field; preserve form ID and source metadata; save campaign/ad attribution where available. Duplicate handling: key on Meta lead ID when present; match on native fields and update rather than create; reuse the open opportunity for the same contact+offer; never collapse distinct people on name alone. State plainly: a calendar link alone does not deliver every unbooked form submission.
1. **Workflow specs.** `src/workflow_specs.py` → `out\workflows\01-intake.md … 04-outcome.md`. Document triggers, filters, actions, waits, branch conditions and stop conditions as reviewable text — do **not** attempt to build them. `01-Intake`: trigger Facebook Lead Form Submitted, filtered to the specific Page+form; store receipt time, tag source, assign owner, evaluate qualification; Yes → Qualified unbooked unless a relevant appointment exists; No → Disqualified with no booking nurture; notify owner once. `02-Unbooked`: qualified leads without an active relevant appointment; immediate permitted booking acknowledgment; owner call task **due within 5 minutes** during staffed hours (task created immediately, not after a 5-minute wait); after hours queue for the next staffed window; +2h one reminder if still unbooked and no reply; +1d one email; +3d manual review task then end. Re-check appointment/reply/opt-out/qualification/opportunity status before every action. `03-Booked`: trigger on the calendar's new booking event; save appointment ID+time; move to Booked; stop Workflow 02; send details + confirmation request; reminders at −24h and −2h with already-passed windows skipped. `04-Outcome`: require a real attendance outcome; Attended creates a next-action task (never auto-Won); No-show sends one permitted reschedule message + follow-up task; Lost stops sales nurture; Paid starts onboarding only after payment verification. Every workflow stays unpublished during assembly.
1. **Message templates.** `src/message_templates.py` → `out\messages\`. Produce booking acknowledgment, booking confirmation, permitted SMS reminder (with `Reply STOP to opt out.`), and no-show follow-up, using the source's copy. Every bracketed token is flagged as a **content placeholder, not guaranteed GHL merge syntax** — a human must insert fields with the account's field picker and send test previews. Run `assert_meeting_first()` on all four.
1. **Pre-call page.** `src/precall_page.py` → `out\precall_page\index.html`. Static HTML, self-contained, no external scripts. Sections: who the service is for, actual delivery steps, client responsibilities, separate ad spend statement, realistic implementation dependencies, call agenda, video embed slot marked `NEEDS_EVIDENCE`. No invented case study, testimonial or outcome. Plus the source's video outline as a script block.
1. **Sales call guide.** `src/sales_guide.py` → `out\sales_call_guide.md`. Structure: open & diagnose; quantify desired outcome (inquiry/appointment/sale volume, contribution per sale, current spend, capacity, extra monthly sales needed — assign a follow-up instead of inventing ROI); explain the service concretely (attraction → qualification → follow-up → calendar → client sales → reporting) and distinguish the Meta campaign that acquired the prospect from the channel proposed for that prospect's customers; validate lead routing (destinations, operating hours, timeout, missed-call fallback — never promise working live transfers before testing); discuss timing and fit without converting the source's 2–3 week / 90-day expectations into CA-J commitments. Include the explicit rule: **no price is quoted in any email, chat, or AI agent reply — pricing is presented on the call only.**
1. **Close & onboarding pack.** `src/onboarding_pack.py` → `out\close_pack.md`, `out\welcome_page\index.html`, `out\intake_form.json`. Price presentation uses locked pricing only, with currency, payment timing, service dates, included costs, separate costs, cancellation, guarantee-if-any, renewal. Acceptance → write the *plan* for a written scope and a matching invoice/checkout item; **payment-product creation is human-only and requires explicit approval.** Verify amount, buyer, description, renewal behavior in test mode. Onboarding booking: 45 minutes reserved. Welcome page sections: welcome video slot, preparation checklist, intake form, access instructions, onboarding booking link, contact details. Intake form fields: legal business name, website, service area, services, target customer, current offers, brand assets, point of contact, reporting contact, operating hours, calendar owner, routing needs, budget, proof assets. **Use platform invitations for access — never ask for passwords in a form.** Renewal: create an internal discussion task 30 days before term end; never create a new charge without agreed terms.
1. **Delivery scope.** `src/delivery_scope.py` → `out\delivery_scope.md`. Define the minimum client delivery scope and, separately, the unresolved work. Explicitly record: the source sells fulfillment but never shows its construction; the video contains no complete YouTube or AI-agent tutorial; the word "AI" in a title does not establish a calling architecture or model. Cover: separate client environment, acquisition campaign plan, qualification/appointment-setting definition, routing (calendar vs live transfer, with a documented + tested fallback), AI behavior if included (provider, knowledge source, allowed/disallowed answers, handoff conditions, permissions, usage cost, transcript retention — the agent must not invent pricing, book unavailable slots, or diagnose HVAC faults), and client reporting (spend, unique/qualified inquiries, booked/held appointments, completed sales, verified contribution, weekly reconciliation).
1. **Launch review.** `src/launch_review.py` → `out\launch_review.md` + `out\asset_register.md`. Package: links to all assets, campaign previews (draft), budget exposure, workflows, tests, offer terms, payment setup, onboarding, and an explicit list of unavailable capabilities.
1. **Compliance scan.** `tools/compliance_scan.py` runs `guardrails` over every generated `.md` and `.json` and fails the build on any hit: a real secret/token pattern, a price quoted in message copy, the frozen campaign name, a currency figure asserted as a CA-J result, the string `nuhFUYu0ZF9Eswiz9P79`, or a lowercase `GHL` ID. Emit a per-file report.
1. **Tests.** `tools/run_tests.py` → `out\tests\test_log.md` and `T01…T14.json`, each with `test_id, input, expected_result, actual_result, evidence_path, verdict` where verdict ∈ `PASS | FAIL | BLOCKED`. Cases:
    T01 Yes + self-book → one qualified contact+opportunity, correct calendar, unbooked follow-up stops.

    T02 Yes without booking → correct owner + 5-minute call task, permitted acknowledgment, no invented appointment.

    T03 No answer → disqualified route, no sales booking nurture.

    T04 Duplicate submission → no duplicate active opportunity or overlapping sequence.

    T05 Reply or opt-out → reply routes to owner; opted-out channel sends nothing further.

    T06 Reschedule/cancel → old reminders stop; only current appointment reminders remain.

    T07 Booking within 2 hours → no expired 24h reminder; correct timezone.

    T08 No available slots → owner task and usable recovery path.

    T09 Form sync interruption → missing test lead detected before launch.

    T10 Successful payment → correct amount, one reference, one onboarding enrollment.

    T11 Failed/duplicate payment event → no false Paid status, no duplicate enrollment.

    T12 Asset and claim review → five concepts readable, links work, terms match.

    T13 Client routing if sold → correct calendar/transfer recipients, tested fallback.

    T14 Rollback → new campaign pauses, affected workflow stops, prior config recoverable.

    Any case that depends on a UI action or a live account must be recorded `BLOCKED` with the exact missing input. A failure in qualification, payment, permission handling or routing blocks the affected live component.

1. **UI task checklists.** Write `ui-tasks\GHL-BUILD-CHECKLIST.md`, `ui-tasks\META-BUILD-CHECKLIST.md`, `ui-tasks\HUMAN-DECISIONS.md`. Every checklist item: exact object name, exact field, exact value, target location `UWc5vKBgFVPdxNTRAy2s`, and a "verify by" line. State at the top of the Meta checklist: **the live campaign `CAJ_HVAC27_US_PURCHASE_TEST02` is FROZEN — do not edit, pause, or duplicate it; build any new campaign as a separate NEW draft, because editing resets Meta's learning phase.** Every spend line is marked `REQUIRES EXPLICIT HUMAN APPROVAL`.
1. **README.** Write `build\03-high-ticket\README.md`: what the build produces, that everything is draft-only, that no GHL/Meta/payment object was touched, the run order, and the exact local run commands (`python tools\build_all.py`, `python tools\run_tests.py`, `python tools\compliance_scan.py`).
1. **Run and verify.** Write `tools\build_all.py` (idempotent, dependency-ordered, logs to `logs\build.log`). Execute `python tools\build_all.py` then `python tools\run_tests.py` then `python tools\compliance_scan.py`. Confirm every file in section 4 exists, the validator exits 0, and the compliance scan is clean. **Do not report success for anything you did not actually run.**

## 6. Configuration & Constants

`config\constants.py` — literals, imported everywhere:

`OWNER_NAME            = "Chuck Ashley"
OWNER_PHONE           = "512-229-9199"
OWNER_EMAIL           = "chuck@ca-jconsulting.com"
LEGAL_ENTITY          = "CA&J Enterprises LLC"
GHL_AGENCY_URL        = "https://app.gohighlevel.com"
GHL_LOCATION_ID       = "UWc5vKBgFVPdxNTRAy2s"   # CASE-SENSITIVE. The ONLY build location.
GHL_PIPELINE_ID       = "U95kdMryqjDqu7JeFrdw"    # "CA&J Demo - Lead Pipeline"
GHL_PIPELINE_STAGES   = ["New Lead","Contacted","Appointment Booked","Quote Sent","Job Won","Lost / Not a Fit"]
GHL_FUNNEL_ID         = "5WjNmZXpaD1tXVzvgRzn"    # CA-J Appointment Engine
GHL_OFFER_PAGE_ID     = "3R0KG1iCnpPCBDwLTgTT"
BOOKING_URL           = "https://ca-jenterprises.com/ai"
TECH_FEE_MONTHLY_USD  = 650      # locked
SETUP_FEE_USD         = 0        # locked: waived
PER_BOOKED_APPOINTMENT_MIN_USD = 250    # locked
PER_BOOKED_APPOINTMENT_MAX_USD = 300    # locked
MEETING_FIRST         = True     # never quote price in email/chat/AI reply
QUOTE_PRICE_IN_MESSAGE = False
FROZEN_CAMPAIGN_NAME  = "CAJ_HVAC27_US_PURCHASE_TEST02"
FROZEN_CAMPAIGN_PROTECTED = True # never edit / pause / duplicate-in-place; new work = separate NEW draft
NEW_CAMPAIGN_NAME_PATTERN = "CAJ-HT-HVAC-Leads-{YYYYMMDD}"   # new draft only, never activated by this build
LOGO_NEVER_FIRST      = True     # creatives lead with outcome/offer; logo = small footer disclaimer only
NO_SPEND_DEFAULT      = True
AD_SPEND_CAP_USD      = 0        # remains 0 until a human sets an authorized amount in writing
APPROVAL_AD_SPEND     = False
APPROVAL_LAUNCH       = False
LAUNCH_AUTHORITY      = "none"
BUILD_MODE            = "CAJ_HVAC"          # or SOURCE_REAL_ESTATE
OBJECT_PREFIX_MAP     = {"CAJ_HVAC":"CAJ-HT-HVAC","SOURCE_REAL_ESTATE":"CAJ-HT-RE"}
NEEDS_EVIDENCE        = "NEEDS_EVIDENCE"
DISALLOWED_LOCATION_ID = "nuhFUYu0ZF9Eswiz9P79"   # unverified; build must reject it`

`config\build_config.json` keys (value = `NEEDS_EVIDENCE` unless listed above): `build_mode, business_name, niche, service_area, owner, sales_calendar_id, timezone, facebook_page_id, ad_account_id, privacy_policy_url, verified_sending_email, messaging_eligibility, payment_processor, service_price, service_term, ad_budget, total_test_cap, launch_authority, proof_assets`.

`.env.example` — names only, empty values:

`# Never commit real values. Copy to .env and fill locally.
GHL_API_KEY=
GHL_LOCATION_ID=
GHL_PIPELINE_ID=
GHL_CALENDAR_ID=
META_AD_ACCOUNT_ID=
META_PAGE_ID=
META_ACCESS_TOKEN=
META_PIXEL_ID=
META_CAPI_ACCESS_TOKEN=
BOOKING_URL=
PRIVACY_POLICY_URL=
OWNER_EMAIL=
OWNER_PHONE=
APPROVAL_AD_SPEND=
APPROVAL_LAUNCH=
AD_SPEND_CAP_USD=`

**Rules:** no real secret, token, key, password or ID value may be written into any spec, config, output or log — env vars and `.env.example` only. All values keyed on location must use `UWc5vKBgFVPdxNTRAy2s` with exact case. Where the source gives a number and section 6 does not lock it, the number goes into section 8 of the output, not into a target.

## 7. Acceptance Criteria

- [ ] Y/N — `build\03-high-ticket\` exists with every path in section 4 present.
- [ ] Y/N — `python tools\validate_config.py` exits 0.
- [ ] Y/N — `python tools\compliance_scan.py` exits 0 with zero hits.
- [ ] Y/N — `config\constants.py` contains `GHL_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"` in exact case.
- [ ] Y/N — the string `nuhFUYu0ZF9Eswiz9P79` appears nowhere except as `DISALLOWED_LOCATION_ID` in the constants rejection list.
- [ ] Y/N — the string `CAJ_HVAC27_US_PURCHASE_TEST02` appears only in guard constants, checklists and this spec — never as a campaign the build creates, edits, pauses or duplicates.
- [ ] Y/N — `assert_logo_not_first()` passes on all five creative JSON records, and each record's visual direction leads with outcome or offer.
- [ ] Y/N — `assert_meeting_first()` passes on all message templates, the form spec, and the ad copy pack — i.e. no CA-J price appears in any message, chat or AI-reply asset.
- [ ] Y/N — every dollar figure in `out\creatives\`, `out\copy\`, `out\messages\` and `out\form_spec.md` is either absent or labeled `assumption`.
- [ ] Y/N — no file in the tree contains a real token, key, password or `sk-`/`EAAG`-style secret; secrets appear only as env var names.
- [ ] Y/N — `AD_SPEND_CAP_USD` is `0` and `APPROVAL_AD_SPEND` is `false` in the committed config.
- [ ] Y/N — `out\tests\test_log.md` contains exactly T01–T14, each with a verdict in {PASS, FAIL, BLOCKED}, and no BLOCKED case is reported as passing.
- [ ] Y/N — every UI-dependent item is emitted into `ui-tasks\` as a checklist item and none is marked `Live` or `Ready for launch` by any script.
- [ ] Y/N — `out\economics\client_break_even.md` reproduces the four formulas exactly and labels every input an assumption.
- [ ] Y/N — `out\risk_reversal.md` defaults to **no numerical guarantee**.
- [ ] Y/N — no testimonial, case study, revenue figure, ROI figure or client outcome appears anywhere in `out\` except inside an explicit "do not use as proof" block.
- [ ] Y/N — `\ui-tasks\HUMAN-DECISIONS.md` lists every `NEEDS_EVIDENCE` value with a next action and an owner.
- [ ] Y/N — `README.md` states that nothing was launched and no GHL/Meta/payment object was touched.

## 8. Blockers & Unverified Items

The spec must NOT assume any of the following:

1. **Wrong GHL location ID in the source.** The source says to inspect location `nuhFUYu0ZF9Eswiz9P79`. House fact: the only authorized build location is `UWc5vKBgFVPdxNTRAy2s`. The source ID is unverified; reject it in code and flag it as a human decision.
1. **No build exists.** The source states explicitly that no GHL system, ad campaign, payment product, or Hermes connection was created. Any spec text implying existing CA-J assets beyond the four listed house objects is false.
1. **Revenue / ROI claims.** `$2,000/mo`, `$7,800/6-month`, `$12,000`, "2x ROI", "five listings in six months", the transcript's reported sale and payment completion, and the instructor's agency-revenue and client-outcome figures are **unverified**. They are not CA-J targets, not CA-J results, and must never appear as proof.
1. **Market arithmetic.** The 4:42–5:23 market-share math is incorrect in the source; employee counts, business counts and licensed-agent counts are different units. The 50,000 threshold is a heuristic.
1. **Timing.** The "10 hour challenge," "2–3 week launch," ~90-day horizon, and the suggested ten-hour preparation budget are source expectations, not CA-J commitments or a validated timeline.
1. **The fulfillment system is unspecified.** The video sells fulfillment (YouTube lead gen, editing, appointment setting, live transfers) but never shows its construction. The word "AI" in the title does not establish any calling architecture, provider or model. Do not encode a fulfillment build.
1. **The interface route is unverified.** Whop's Meta-campaign capability was never independently confirmed. AI Studio, GHL Labs, embedded booking, conditional form endings and multi-page lead sync availability in the CA-J account are all `NEEDS_EVIDENCE`. The video description's Google Doc, GHL snapshot, scripts and coaching materials were never supplied.
1. **Availability, identity and routing unknowns.** Privacy policy URL, verified sending email, messaging/A2P eligibility, payment processor, Facebook Page ID, ad account ID, calendar ID, service area, service term and proof assets are all `NEEDS_EVIDENCE`. Do not guess them. Do not promise live transfers before the chosen system is tested. Multi-person ringing may be unsupported.
1. **Consent and contact basis.** The video's cold-SMS remarks do not establish permission to contact anyone. This spec is not authorization to bulk message a purchased list. All sends require valid channel permissions and a working sender; opted-out channels are suppressed.
1. **Spend is blocked.** Ad budget, media spend, domains, tool purchases, subscriptions and any paid upgrade all require **explicit written human approval**. `AD_SPEND_CAP_USD` stays `0`. The source's $50–$100/day suggestion is a candidate only; Chuck's prior under-$15/day test context is not authority to start at $50.
1. **The frozen campaign.** `CAJ_HVAC27_US_PURCHASE_TEST02` must never be edited, paused, or duplicated in a way that touches the original — editing resets Meta's learning phase. Any new campaign is a SEPARATE new draft. This build activates nothing.
1. **Payment.** Creating a payment product, invoice, checkout item or subscription is human-only and requires explicit approval. No automatic subscription may be created. A verbal yes moves an opportunity to `Won pending payment` only — never to `Paid` — until the processor confirms.
1. **Duplicate-match and attribution gaps.** Matching settings and available attribution fields in the live GHL Facebook integration are unknown. Where a field is unavailable, record the limitation and use a documented lookup — do not invent attribution.
1. **Merge tokens.** Bracketed tokens in message templates are content placeholders, not confirmed GHL merge syntax. A human must insert fields with the account's field picker and send previews before any workflow activates.
1. **Scope conflict.** Do not replace the $27 HVAC Review System or merge its funnel with this high-ticket offer. Do not overwrite any existing live offer; duplicate before materially changing a live asset.

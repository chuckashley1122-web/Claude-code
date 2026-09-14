# AI Employee Action Plan

# SPEC-02 — "AI Employee: Sales & Fulfillment" Implementation Specification

Audience: an AI coding agent (Claude Code / Claude Cowork) running headless via `claude -p`.

Environment: Windows 11, Python 3.11. Interpreter is `python`. No browser, no logged-in UI, no interactive prompts.

Execution rule: build every code/file artifact in §4 and §5 without asking questions. Every GoHighLevel instruction in the source is UI-only and is NOT executable by this agent — it becomes a runbook step for a human (§3, §8).

## 1. Source & Provenance

| Field | Value |
|---|---|
| Source file read (full, not skimmed) | `C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system\playbooks\02-ai-employee-action-plan.md` |
| Size | 40,670 bytes / 40,020 characters / 409 lines |
| SHA-256 (first 16 hex) | `11a58da5ca3060e4` |
| Format | Markdown extraction of a Word-style plan. UTF-8. Contains one broken/partial table at lines 17–20; no images. |

What the source actually is: a self-described transcript-based implementation plan ("AI employee sales and fulfillment — Step by step action plan for Hermes", prepared for Chuck Ashley / CA-J Enterprises, dated September 13 2026) derived from a YouTube video at `https://www.youtube.com/watch?v=Q5V3bbu6owY` and a pasted transcript file `Pasted markdown(20260913-125836).md`. It maps video timestamps to a 51-step plan: niche selection (HVAC in Austin/Round Rock), offer definition, agency offer page, demo calendar, private personalized demo, agent training, demo questions, sales meeting, checkout, client provisioning from a snapshot, knowledge base, scheduling and widget channels, production phone routing, four workflows (WF01–WF04), twelve acceptance tests (T01–T12), a four-channel prospecting system, optional ads, maintenance, and a final handoff checklist.

Provenance limits stated by the source itself (line 8): "YouTube playback could not be accessed in this session… it does not claim visual inspection of the presenter's screen." Line 11: "GHL menu paths are navigation targets to confirm in the live account, not verified screenshots of its current interface." Line 14: "No GHL settings, customer phone routing, live campaigns, or billing subscriptions were changed while preparing it." The source is therefore a plan, not a record of a working system.

Two material conflicts with CA&J house facts, resolved in favour of house facts:

- Line 85 gives a CA-J location ID `nuhFUYu0ZF9Eswiz9P79`. House fact: the only build location is `UWc5vKBgFVPdxNTRAy2s` ("CA&J Enterprises"). The source ID is treated as stale/incorrect and is recorded in §8. It must not appear in any deliverable.
- Lines 105–131 propose a $197/month recurring fee and $0 setup, with a trainer range of $97–$297 and an attendee example of $297 setup + $297 monthly. House fact: locked pricing is $650/mo tech fee, setup fee waived, $150–$300 per qualified appointment, and MEETING-FIRST — no price is ever quoted in an email, chat, or AI-agent reply. The source's price ladder must not be encoded as CA-J's price.
Everything in the source is the plan's own addition beyond the transcript unless timestamped; the source says so at line 11. All quantitative claims are listed in §8 and in `docs\SOURCE-CLAIMS.md`.

## 2. Objective

Produce a version-controlled project-controls repository at `build\CAJ_AI_Employee_Playbook\` that contains, in machine-checkable form, everything the source's 51 steps need on the file/code layer: the five control records (Build_Log, Asset_Register, Business_Facts, Test_Results, Blockers) as CSV plus a JSON validator; a business-facts schema whose every row requires evidence URL, verification date, and status, with `NEEDS_EVIDENCE` as the default; the agent system prompt and the six demonstration questions as standalone versioned files; the twelve acceptance tests (T01–T12) as an executable test checklist with pass conditions and result columns; the four workflow specifications (WF01–WF04) as structured specs with triggers, dedupe keys, and review routing; prospect-pipeline and channel-outreach assets (email, DM, call scripts, pipeline stage definitions, follow-up cadence) guarded so that no script can quote a price; a client intake pack; phone-routing and rollback runbooks written for a human operator; and approval-gated documentation of every step that needs a browser, a GoHighLevel login, a phone number purchase, or money. Nothing in this repository is permitted to create a GHL object, place a call, send a message, charge a card, or change live routing.

## 3. Code-Layer vs UI-Layer Split

Strict. Claude Code cannot log into GoHighLevel, cannot operate any GHL screen, cannot dial, cannot send, and cannot purchase. In particular: subaccounts, snapshots, calendars, AI agents, knowledge-base crawlers, chat widgets, phone-number settings, A2P registration, payment products, and all workflows live in the GHL UI and are human-only.

| Claude Code CAN build (files / code, zero cost, zero login) | REQUIRES browser + logged-in account, or a human decision (NOT Claude Code) |
|---|---|
| Project folder + the five control records: `Build_Log.csv`, `Asset_Register.csv`, `Business_Facts.csv`, `Test_Results.csv`, `Blockers.csv` | Confirming the target GHL account and location. GHL is UI-only; the build location `UWc5vKBgFVPdxNTRAy2s` must be verified on screen by a human. |
| `schemas\*.json` + `scripts\validate_records.py` enforcing evidence/verification columns and `NEEDS_EVIDENCE` defaults | Creating a subaccount for any client; requesting or applying any snapshot; auditing an imported snapshot (source steps 26–27) |
| `agent\system-prompt.md` (HVAC AI employee prompt, source lines 170–174 equivalent) and `agent\demo-questions.md` | Entering that prompt into a GHL AI agent; mapping the knowledge base; attaching the agent to a widget — all UI |
| `agent\business-facts-template.csv` + a fact-intake form generator | Crawling a prospect's website in AI Agents → Knowledge Base; training; verifying ingestion (source step 18) |
| `tests\T01-T12.csv` (pass conditions from source lines 254–291) and `scripts\run_test_checklist.py` that records results and refuses to mark a test passed without an evidence reference | Executing T01–T12. Every test needs a live agent, a live calendar, or a live phone route. Text/voice transcripts must be captured by a human. |
| `workflows\WF01-WF04.md` — trigger, filter, dedupe key, action, review route (source lines 249–252) | Building any of WF01–WF04 inside GoHighLevel. Workflow builder is UI-only. |
| `outreach\email-draft.txt`, `outreach\dm-draft.txt`, `outreach\call-script.txt`, `outreach\followup-cadence.md` | Sending any email, DM, SMS, or placing any call. Also: domain authentication, sender reputation, reply routing, suppression list — all account/human work. |
| `guardrails\pricing_guard.py` + `guardrails\meeting_first.py` blocking every price in outbound text and rewriting price intent to the booking URL | Any AI agent, chat widget, or voice reply that actually talks to a customer |
| `pipeline\stages.md` + `pipeline\prospects.template.csv` with dedupe keys (domain, phone) | GHL opportunity stages, pipelines, and contact creation |
| `intake\client-intake-form.md` + `intake\intake.schema.json` | Collecting the real answers from an owner; obtaining website admin access; provisioning numbers |
| `runbooks\phone-routing.md`, `runbooks\rollback.md`, `runbooks\widget-install.md`, `runbooks\payment-product.md` with placeholders for IDs and timestamps | Changing phone forwarding, carrier timers, voicemail behaviour, A2P messaging registration, or any live route. Rollback requires a human at the provider console. |
| `docs\UI-ONLY-CHECKLIST.md`, `docs\COST-AND-APPROVALS.md`, `docs\SOURCE-CLAIMS.md`, `docs\DEPLOY-RUNBOOK.md` | Publishing the offer page, connecting a domain, creating the demo calendar, creating a payment product/checkout, launching ads. Payments: the client enters card data themselves; the agent never handles cards. |
| `scripts\cost_estimate.py` computing contribution = subscription − platform allocation − AI usage − telephony − payment fees − support labour | Any spend. ABSOLUTE RULE: no charges or purchases of any kind. Every number tested with `DRY_RUN=true` and synthetic contacts. |
| `prompts\*` renderer with unresolved-placeholder hard-fail (source line 192: "Replace all placeholders before use.") | Meta Ads Manager of any kind; walk-ins; any live sales conversation |

## 4. Deliverable File Tree

Root: `C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system\build\CAJ_AI_Employee_Playbook\`

`CAJ_AI_Employee_Playbook\
├── README.md                          # purpose, absolute rules, how to run the validators
├── .env.example                       # env var names only; nothing required for the file layer
├── .gitignore                         # .env, out\, *.log, __pycache__, .venv
├── records\
│   ├── Build_Log.csv                  # step#, status, account id, object id/url, timestamp, change, evidence, next action
│   ├── Asset_Register.csv             # every page/calendar/agent/kb/widget/product/workflow id with version + status
│   ├── Business_Facts.csv             # fact, value, evidence url or owner confirmation, verified date, status
│   ├── Test_Results.csv               # T01–T12, actual result, object id/log, pass/fail, fix
│   └── Blockers.csv                   # blocker, owner, dependency, REQUIRED/OPTIONAL, unblock action
├── schemas\
│   ├── build_log.schema.json
│   ├── asset_register.schema.json
│   ├── business_facts.schema.json
│   ├── test_results.schema.json
│   └── blockers.schema.json
├── agent\
│   ├── system-prompt.md               # HVAC AI employee prompt (no invented facts, no prices, booking only on success)
│   ├── demo-questions.md              # the six demonstration questions
│   ├── handoff-rule.md                # human takeover + callback task rules; placeholders for destinations
│   └── business-facts-template.csv    # 14 required facts, all status=NEEDS_EVIDENCE by default
├── tests\
│   ├── T01-T12.csv                    # pass conditions verbatim from source; result columns empty
│   └── test-run-protocol.md           # synthetic contacts only, evidence required, no activation before all pass
├── workflows\
│   ├── WF01_demo_preparation.md
│   ├── WF02_client_onboarding.md
│   ├── WF03_human_followup.md
│   └── WF04_knowledge_maintenance.md
├── pipeline\
│   ├── stages.md                      # Qualified→Contacted→Replied→Demo booked→Demo held→Proposal sent→Paid+onboarding→Active; Not now; Lost
│   └── prospects.template.csv         # columns incl. dedupe keys domain + phone, opt-out status
├── outreach\
│   ├── email-draft.txt                # source lines 301–306 draft, price-free, "I can prepare" wording
│   ├── email-post-demo.txt            # "I prepared a demo for [Business]" — only after the demo passes tests
│   ├── dm-draft.txt                   # source line 308
│   ├── call-script.txt                # source line 308, honest identification, no false familiarity
│   ├── followup-cadence.md            # day 0, +3 business days, +7 business days; stop on reply/opt-out
│   └── gatekeeper-questions.md        # source basis 1:38:45–1:44:38
├── intake\
│   ├── client-intake-form.md
│   ├── intake.schema.json
│   └── discovery-questions.md         # source line 188 first-two-minutes questions
├── guardrails\
│   ├── pricing_guard.py               # blocks any price in outbound text; MEETING-FIRST
│   ├── meeting_first.py               # price intent -> https://ca-jenterprises.com/ai
│   └── claim_guard.py                 # blocks source-author results/claims restated as CA-J facts
├── runbooks\
│   ├── ghl-account-and-snapshot.md
│   ├── demo-page-and-calendar.md
│   ├── widget-install.md
│   ├── phone-routing.md
│   ├── payment-product.md
│   └── rollback.md
├── scripts\
│   ├── validate_records.py            # schema + evidence/status checks; fails on NEEDS_EVIDENCE in a "done" row
│   ├── render_templates.py            # fills {{placeholders}}; hard-fails on unresolved or on any price token
│   ├── check_guardrails.py            # self-tests for the three guardrails
│   ├── run_test_checklist.py          # records test results; blocks "pass" without evidence reference
│   └── cost_estimate.py               # contribution model from a human-maintained rates file
└── docs\
    ├── DEPLOY-RUNBOOK.md              # human steps 1..51 mapped to UI actions with approval gates
    ├── UI-ONLY-CHECKLIST.md           # every source step that needs a browser/login
    ├── COST-AND-APPROVALS.md          # approval gates; locked CA&J pricing; no-purchase rule
    └── SOURCE-CLAIMS.md               # verbatim unverified claims with line numbers`

## 5. Build Steps

1. Create the directory tree in §4 under `build\CAJ_AI_Employee_Playbook\`. Create `specs\` if absent. Create no file outside this root.
1. Write `README.md`: purpose, the four absolute rules (no charges or purchases; never invent data — mark `NEEDS_EVIDENCE`; meeting-first — never quote a price in email, chat, or AI reply; source results are not CA-J results), the locked business facts (owner, phone, email, legal entity, GHL location, booking URL), and the validator command sequence.
1. Write `records\*` headers only, no invented data rows. `Build_Log.csv` columns: `step,title,status,account_id,object_id_or_url,timestamp_utc,change_made,evidence,next_action`. `Asset_Register.csv`: `asset_type,name,id_or_url,version,source,status,verified_by,verified_date`. `Business_Facts.csv`: `fact,value,evidence_url_or_owner_confirmation,verified_date,status,notes`. `Test_Results.csv`: `test_id,pass_condition,actual_result,evidence_ref,result,fix,retest_date`. `Blockers.csv`: `blocker_id,description,blocks_step,owner,dependency,priority,unblock_action,status`. Seed `Business_Facts.csv` with the 14 required facts from source line 169 (business name, main phone, timezone, hours and holidays, service area, offered services, excluded services, approved pricing language, emergency procedure, dispatcher destination, booking calendar, callback expectation, cancellation process) — every `value` empty, every `status` = `NEEDS_EVIDENCE`.
1. Write the five JSON schemas in `schemas\` covering those column sets, with required fields, enums for `status` (`NEEDS_EVIDENCE|VERIFIED|BLOCKED|N/A`) and `result` (`PASS|FAIL|NOT_RUN|N/A`).
1. Write `scripts\validate_records.py`: load each CSV, validate against its schema, fail on: any row marked `done`/`PASS`/`VERIFIED` with an empty evidence field; any `verified_date` absent when status is `VERIFIED`; any value containing a price token while `MEETING_FIRST` is in force; any appearance of a GHL location ID other than `UWc5vKBgFVPdxNTRAy2s`; any placeholder left in a record. Print a summary table and exit non-zero on findings.
1. Write `agent\system-prompt.md`. Use the source's starter prototype prompt (lines 170–174) as the base and preserve its constraints verbatim: identify as an AI assistant; use only the verified knowledge base for business facts; general HVAC knowledge never overrides hours/service area/pricing/dispatch rules; one question at a time; repeat details to confirm; never invent prices, discounts, availability, technician arrival times, or guarantees; confirm a booking only after the scheduling action returns success; never describe a request as a confirmed booking; do not claim a dispatcher received a request unless the handoff action succeeded; do not diagnose hazards or give repair instructions; do not collect card numbers or security codes. Add: never state any price or fee; route pricing questions by offering a meeting at `https://ca-jenterprises.com/ai`; mark unknown facts as needing team confirmation. Leave `[HANDOFF RULE]`, `[FOLLOWUP TASK]`, and `[BUSINESS]` as named placeholders resolved at render time.
1. Write `agent\demo-questions.md` (the six questions, source lines 176–181, with the unoffered-service question kept deliberately unanswerable) and `agent\handoff-rule.md` (owner takeover pauses the bot; resume only under the agreed rule; if takeover cannot be verified, route to a separate documented process — source line 229).
1. Write `tests\T01-T12.csv` with the twelve pass conditions copied verbatim from source lines 256–291, and `tests\test-run-protocol.md` enforcing: synthetic contacts only; authorized test destinations only; every pass requires an evidence reference; all critical enabled-channel tests must pass before activation; failed behaviour and its dependencies are the only things re-tested.
1. Write `scripts\run_test_checklist.py`: interactive-free CLI that takes `--test-id --result --evidence` and rejects any `PASS` with an empty or self-referential evidence reference; prints outstanding tests; exit non-zero while any critical test is not `PASS`.
1. Write the four `workflows\WF0*.md` specs from source lines 249–252. For each: trigger, filter, dedupe key, action, notification destination permission, and failure routing. WF01 dedupe by appointment ID; WF02 dedupe by subscription ID with failed/ambiguous events routed to review; WF03 dedupe by interaction ID; WF04 weekly internal review task per active client. State in each file that the implementation lives in the GoHighLevel UI and is human-executed.
1. Write `pipeline\stages.md` with the eight forward stages and two terminal stages from source line 297, plus `pipeline\prospects.template.csv` with dedupe keys `domain` and `phone`, and `opt_out` as a required column.
1. Write `outreach\email-draft.txt` from source lines 301–306 with these mandatory edits: keep "I can prepare a short AI demo…" wording (never "I already built it" before the demo exists — source line 306); remove anything resembling a price; keep the opt-out line verbatim; keep the honest CA&J signature with `Owner: Chuck Ashley | 512-229-9199 | chuck@ca-jconsulting.com`, `CA&J Enterprises LLC`. Write `email-post-demo.txt` for the post-test case.
1. Write `outreach\dm-draft.txt` and `outreach\call-script.txt` from source line 308, keeping honest business identification and explicitly forbidding any implied personal relationship.
1. Write `outreach\followup-cadence.md`: first contact, one follow-up after three business days, one final follow-up after seven business days; stop on reply, opt-out, or disqualifying status; never run simultaneous repeated messages across channels; each channel requires its own launch authorization. Label the cadence as not specified in the source.
1. Write `outreach\gatekeeper-questions.md` from the 1:38:45–1:44:38 basis: honest introduction, ask who handles after-hours calls, offer a specific available time, no invented anchors.
1. Write `intake\discovery-questions.md` (the three first-two-minute questions and the outcomes question from source line 188) and `intake\client-intake-form.md` + `intake\intake.schema.json` covering source line 208: owner-confirmed hours, holidays, covered ZIPs/cities, services, approved price statements, escalation instructions, dispatcher contact, website admin access, calendar owner, phone provider, may the assistant create confirmed appointments or only requests, who receives handoffs and how fast.
1. Write `guardrails\pricing_guard.py`. Block any outbound text containing a currency symbol or token (`$`, `USD`, "dollars", "per month", "monthly", "setup fee", "fee", "price", "cost", "per appointment"). `assert_clean(text, channel)` raises on violation. Include the locked CA&J price constants in a separate machine-readable file `guardrails\locked_pricing.json` used ONLY for internal cost modelling, never for rendering outbound copy.
1. Write `guardrails\meeting_first.py`: detect pricing intent; produce a reply offering a meeting and linking `https://ca-jenterprises.com/ai`.
1. Write `guardrails\claim_guard.py`: denylist drawn from `docs\SOURCE-CLAIMS.md` and the standing rule — block any sentence that attributes a source author's result, revenue, churn, valuation, or "unlimited" capability to CA-J. Include the source's own prohibited anchors: the invented "normally $1,000 plus $2,000 setup" anchor (source line 321) and the ambiguous "$9.99" upsell (source line 131).
1. Write `scripts\render_templates.py`: fill `{{placeholders}}` from a JSON vars file; hard-fail on any unresolved placeholder and on any rendered output that fails `pricing_guard`.
1. Write `scripts\check_guardrails.py`: self-tests proving that `"$650 per month"`, `"$197"`, `"setup fee"`, `"$1,000 plus $2,000 setup"`, `"$9.99"`, and `"we recovered $40k in missed calls"` are all blocked.
1. Write `scripts\cost_estimate.py`: contribution = subscription revenue − platform allocation − AI usage − telephony − payment fees − support labour, reading `guardrails\locked_pricing.json` and a human-maintained `rates.yaml`; every rate row `verified: false` until a human confirms; refuse to advertise unlimited usage; print result and exit non-zero if contribution is negative or any rate is unverified.
1. Write `docs\SOURCE-CLAIMS.md` first among docs: every quantitative claim with line number, label `unverified`.
1. Write `docs\UI-ONLY-CHECKLIST.md`: all 51 source steps partitioned into code-layer (done in this repo) vs UI-layer (human). Must explicitly name GoHighLevel subaccount creation, snapshots, calendars, AI agents, knowledge base crawling, widgets, phone settings, A2P registration, payment products, workflows, and Meta Ads Manager as coding-agent-inaccessible.
1. Write `docs\COST-AND-APPROVALS.md`: no charges or purchases of any kind; every paid item (phone number, AI/voice usage, telephony, snapshot/licence packs, ads, any third-party tool named in the source such as Higgsfield) listed with "amount unknown — approval required"; the locked CA&J pricing restated; and the statement that the source's $197/$0/$97–$297/$297 figures are training values, not CA&J prices, and must never be quoted in any outbound message or AI reply.
1. Write `docs\DEPLOY-RUNBOOK.md` mapping source steps 01–51 to human actions with columns: step, platform, exact action, object to create, spend, approval required, evidence to capture.
1. Write `runbooks\ghl-account-and-snapshot.md`, `runbooks\demo-page-and-calendar.md`, `runbooks\widget-install.md`, `runbooks\phone-routing.md`, `runbooks\payment-product.md`, `runbooks\rollback.md`. `rollback.md` must require a human to record previous forwarding destination, schedule, voicemail behaviour, provider-specific restoration steps, responsible person, and to verify one inbound call after restoration. `phone-routing.md` must forbid inventing carrier dial codes and must require verifying that voicemail does not answer before the AI, and that the human-transfer destination does not forward back to the AI number.
1. Run and fix until clean: `python scripts\validate_records.py`, `python scripts\check_guardrails.py`, `python scripts\run_test_checklist.py`, `python scripts\render_templates.py`, `python scripts\cost_estimate.py`. Inline heredoc and huge one-liner shell commands are blocked on this host — put multi-line logic in a `.py` file and run it.
1. Never call a GHL API, never open a browser, never send a message, never place a call, never spend money.

## 6. Configuration & Constants

No secret or token is written to any file. `.env.example` lists names only, empty.

| Var | Purpose | Gate |
|---|---|---|
| `DRY_RUN` | default `true`; the file layer does not need it, live steps do | human |
| `ALLOW_LIVE` | required alongside `DRY_RUN=false` to allow any live path | human only |
| `GHL_LOCATION_ID` | reference/matching only; must equal `UWc5vKBgFVPdxNTRAy2s` (case-sensitive) | human verifies on screen |
| `DEMO_CALENDAR_ID`, `DEMO_CALENDAR_URL` | filled by a human after creating the calendar in the GHL UI | human |
| `GHL_AGENT_ID`, `GHL_KB_ID`, `GHL_WIDGET_ID`, `GHL_PHONE_NUMBER`, `GHL_PRODUCT_ID` | asset register cross-references; empty until created in the UI | human |
| `SENDER_IDENTITY_EMAIL`, `SENDER_DOMAIN` | outbound identity; the agent never authenticates a domain | human |
| `DISPATCHER_NOTIFICATION_DESTINATION` | human fallback destination | human |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` | only if a human later wires sending | human |
| `SPEND_CAP_USD` | default `0.00` | human |

Constants in `guardrails\locked_pricing.json` (internal cost modelling only; never rendered into outbound copy):

`TECH_FEE_MONTHLY_USD = 650`, `SETUP_FEE_USD = 0`, `PER_QUALIFIED_APPOINTMENT_MIN_USD = 150`, `PER_QUALIFIED_APPOINTMENT_MAX_USD = 300`, `MEETING_FIRST = True`, `QUOTE_PRICE_IN_OUTBOUND = False`, `BOOKING_URL = "https://ca-jenterprises.com/ai"`, `GHL_BUILD_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"`, `GHL_BUILD_LOCATION_NAME = "CA&J Enterprises"`, `OWNER = "Chuck Ashley"`, `OWNER_PHONE = "512-229-9199"`, `OWNER_EMAIL = "chuck@ca-jconsulting.com"`, `LEGAL_ENTITY = "CA&J Enterprises LLC"`, `SPEND_CAP_USD = 0.00`.

Approval gates: `REQUIRE_HUMAN_APPROVAL_FOR_SPEND = True`, `REQUIRE_HUMAN_APPROVAL_FOR_GHL = True`, `REQUIRE_HUMAN_APPROVAL_FOR_OUTBOUND = True`, `REQUIRE_HUMAN_APPROVAL_FOR_PHONE_ROUTING = True`, `REQUIRE_HUMAN_APPROVAL_FOR_PAYMENTS = True`.

Caps: `PROSPECT_BATCH_FIRST = 25` (source line 297; research batch, not a sending volume), `EMAIL_INITIAL_BATCH = 10` (a small reviewed first batch; source's 30–90/day across three domains is a training target, not a safe starting volume — source line 299), `FOLLOWUPS_MAX = 2`, `DEDUPE_KEYS = ["domain", "phone"]`, `OPT_OUT_HONORED = True`, `SYNTHETIC_CONTACTS_ONLY = True`.

Booking destination for every campaign and every campaign-adjacent CTA: `https://ca-jenterprises.com/ai`.

## 7. Acceptance Criteria

1. `build\CAJ_AI_Employee_Playbook\` exists and its file set matches §4 exactly.
1. `python scripts\validate_records.py` exits 0 and reports all five records schema-valid with zero fabricated data rows.
1. Every row seeded into `Business_Facts.csv` has `status = NEEDS_EVIDENCE` and an empty value.
1. `python scripts\check_guardrails.py` exits 0 and demonstrates blocking of `"$650 per month"`, `"$197"`, `"setup fee"`, `"$1,000 plus $2,000 setup"`, `"$9.99"`, and any sentence attributing a source author's dollar result to CA-J.
1. `python scripts\render_templates.py` renders `outreach\email-draft.txt` with zero unresolved placeholders, and a deliberately withheld variable produces a non-zero exit.
1. `tests\T01-T12.csv` contains exactly twelve rows with pass conditions matching source lines 256–291, all `result = NOT_RUN`.
1. `python scripts\run_test_checklist.py` exits non-zero while any critical test is not `PASS`, and refuses a `PASS` submitted without an evidence reference.
1. `workflows\` contains exactly four WF specs plus the runbooks; each names its trigger, dedupe key, action, and review route.
1. `python scripts\cost_estimate.py` prints a contribution figure and exits non-zero while any rate is `verified: false`.
1. No file in the repository contains any GHL location ID other than `UWc5vKBgFVPdxNTRAy2s`; the string `nuhFUYu0ZF9Eswiz9P79` appears nowhere.
1. No file in the repository states $197, $97–$297, $297, or $9.99 as a CA&J price; those appear only inside `docs\SOURCE-CLAIMS.md` and the guardrail denylist, labelled as source values.
1. Every file that mentions a campaign CTA uses `https://ca-jenterprises.com/ai` as the booking destination.
1. `docs\UI-ONLY-CHECKLIST.md` names GoHighLevel, Meta Ads Manager, and every logged-in UI as coding-agent-inaccessible and covers all 51 source steps.
1. `docs\COST-AND-APPROVALS.md` contains the literal statement that no charges or purchases of any kind are authorized by this spec.
1. `docs\SOURCE-CLAIMS.md` lists at least: the $197/$0 defaults (line 104–107), the $97–$297 trainer range (line 131), the $297/$297 attendee sale (line 131), the ambiguous "$9.99" (line 131), the "virtually nothing" cost claim (line 133), the 15-minute demo prep budget (line 154), 30–90 emails/day across three domains (line 299), 50 calls/day (line 310), the low-churn/valuation claims (line 359) — each labelled `unverified`.
1. No step created an account, opened a browser, sent a message, placed a call, charged a card, or changed any live route.

## 8. Blockers & Unverified Items

Do NOT assume any of the following.

1. GoHighLevel is UI-only in its entirety. The source's 51 steps are ~80% GHL screen operations (subaccounts, snapshots, calendars, AI agents, knowledge base, widgets, phone settings, A2P registration, payment products, workflows). None can be executed by the coding agent. Every one becomes a human runbook step.
1. Location-ID conflict: the source (line 85) gives `nuhFUYu0ZF9Eswiz9P79` as the CA-J location ID. The house fact is `UWc5vKBgFVPdxNTRAy2s` ("CA&J Enterprises"). The source value is unverified and must be treated as stale; the agent must never use it. A human must confirm the account on screen before any GHL work.
1. Pricing conflict: source lines 104–107 propose $197/mo with $0 setup; line 131 records a trainer range of $97–$297 and an attendee sale of $297 setup + $297 monthly. The locked CA&J pricing is $650/mo tech fee, setup waived, $150–$300 per qualified appointment, and MEETING-FIRST. The source's numbers are training values only. No outbound artifact, agent reply, or page copy may quote a price; pricing intent routes to `https://ca-jenterprises.com/ai`.
1. Source "pricing language" columns and any "approved price statements" fact are empty pending a human decision. `Business_Facts.csv` stays `NEEDS_EVIDENCE` until the owner confirms in writing.
1. The YouTube source `https://www.youtube.com/watch?v=Q5V3bbu6owY` and the transcript file `Pasted markdown(20260913-125836).md` were not verified in this session. The source itself states playback could not be accessed and that no screen was visually inspected (line 8). All GHL menu paths are "navigation targets to confirm in the live account" (line 11) — do not encode them as current UI truth.
1. Missing source materials, referenced but not attached (source line 81): the presenter's seven-page SOP, the previous live demo workshop, licensed niche snapshots and knowledge bases, niche sales scripts, outbound email SOP, phone registration SOP, and the lab account request form. These must be located in Chuck's authorized training access; their contents must never be invented. Their absence is a recorded dependency, not a build failure.
1. Unverified quantitative claims from the source, all to be listed in `docs\SOURCE-CLAIMS.md` and never encoded as targets: $197/mo and $0 setup defaults; $97–$297 trainer range; the attendee's $297/$297 sale (line 131); the ambiguous "$9.99" upsell (line 131 — do not use as a price instruction); "virtually nothing" AI cost (line 133 — not a verified rate); ~15 minutes demo preparation (line 154 — "a target, not a guarantee"); 30–90 emails/day across three domains (line 299 — "a training target, not a safe starting volume"); 50 calls/day and unverified dialer cost (line 310); low-churn and business-valuation claims (line 359 — must not be adopted as CA-J forecasts); the trainer's "$1,000 plus $2,000 setup" anchor (line 321 — explicitly prohibited).
1. No results, benchmarks, or proof points exist for CA-J in this source. The source is a plan. Any number the plan references is either the presenter's, an attendee's, or a proposal.
1. The source's own compliance guardrails must be kept, not softened: no GHL menu path is verified; no unlimited-usage advertising; no claim that a booking exists unless the scheduling action returned success; no claim a dispatcher was reached unless the handoff succeeded; no card data captured; no purchase, domain, number, subscription, or ad spend without explicit human approval.
1. Payment objects: creating a product/checkout is UI-only. The client enters payment information privately. The coding agent must never handle, log, or template real card data, and a success-page visit is never proof of payment.
1. Phone routing, forwarding, carrier timers, and A2P messaging registration require provider access and a human. Rollback must be written and verified before any live route change; if calls drop, loop, or route to the wrong business, restore the prior route and verify with one inbound call.
1. Ads are optional in the source and out of scope here: no ad spend, no Meta Ads Manager access, no automatic budget reallocation, and no use of the Higgsfield tool named at line 315 unless already owned and explicitly authorized.
1. Calendar/daytime-expansion, social messaging channels, walk-ins, and upsells are conditional on demonstrated need and separate written scope; none may be activated automatically.
1. Two of the source's own quality rules can never be satisfied by the coding agent alone: "All enabled-channel critical tests must pass before activation" (line 292) and "A step is complete only when the actual object exists and its expected behavior has been checked" (line 95). Both require a live GHL session and a human observer.

# 8 Best AI Automations

# SPEC-01 — "8 Best AI Automations" Implementation Specification

Audience: an AI coding agent (Claude Code / Claude Cowork) running headless via `claude -p`.

Environment: Windows 11, Python 3.11. Interpreter is `python`. No browser, no logged-in UI, no interactive prompts.

Execution rule: build every code/file artifact in §4 and §5 without asking questions. Anything in the right-hand column of §3 must be written up as a runbook step for a human, never attempted by the coding agent.

## 1. Source & Provenance

| Field | Value |
|---|---|
| Source file read (full, not skimmed) | `C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system\playbooks\01-8-best-ai-automations.md` |
| Size | 13,770 bytes / 13,653 characters / 118 lines |
| SHA-256 (first 16 hex) | `96031af081c52b94` |
| Format | Markdown extraction of a business playbook document. UTF-8. No images, no attachments, no diagrams. |
| Stated origin in the file itself | Line 2: "Source: TikTok @martiendejong_dev - 8 automations from your 4 screenshots." |

What the source actually is: a third-party social-media playbook describing eight automations the author built (or claims to have built) on an n8n-centric stack — n8n Cloud as orchestrator, plus Vapi/Twilio, OpenAI, Apify, HeyGen, Sora 2/Runway/Pika/Creatomate, ElevenLabs, Ayrshare/Blotato, Google Calendar + Gmail, HubSpot, YouTube Data API v3, Supabase/Airtable, Pergel/Perplexity, Pinecone, Instantly, Hunter.io, Leonardo/DALL-E, Slack, Redis. It gives a workflow sketch, a numbered step list, and prompt templates for each of eight automations, plus a four-week build order and a cost estimate.

Structural note: the source is a repackaging of "4 screenshots" — the workflows are descriptions of nodes seen in images, not exported JSON. No node parameters, credentials, field mappings, or error handling are given. Every workflow in this spec must therefore be treated as a first-draft design to be validated at build time, not a reproduction of a tested artifact.

Claims in the source that are NOT verified (full list in §8): all pricing, all concurrency/capacity claims, the "unlimited/day" call claim, all vendor capability claims, and the total monthly cost estimate. None of these are results CA&J has achieved or rates CA&J pays. Nothing in this spec may restate them as CA-J's own results, targets, or committed costs.

## 2. Objective

Produce a version-controlled, runnable-by-dry-run implementation repository for the eight automations described in the source, located at `build\automation-suite\` inside the caj-growth-system workspace, containing: eight importable n8n workflow JSON definitions, all prompt templates as standalone versioned text files, a fail-closed configuration/constants layer carrying the locked CA&J business facts, an outbound-text pricing guard that hard-fails any message quoting a price, a mock/fixture data layer so every workflow can be exercised with synthetic records at zero cost, a cost/approval calculator that emits a dollar figure for human sign-off instead of spending anything, and a human runbook enumerating every step that requires a browser, a paid third-party account, or a GoHighLevel login. The repository must run, validate, and lint itself end-to-end on Windows 11 with `python`, without any network call to a paid API and without creating any account, domain, phone number, subscription, or ad spend.

## 3. Code-Layer vs UI-Layer Split

Strict. Claude Code cannot operate GoHighLevel, Meta Ads Manager, n8n Cloud, Vapi, Apify, HeyGen, Ayrshare, ElevenLabs, Supabase, Airtable, Gmail, Google Calendar, HubSpot, Slack, Instantly, Hunter.io, Pinecone, or any other logged-in UI, and cannot purchase anything.

| Claude Code CAN build (files / code, zero cost, zero login) | REQUIRES browser + logged-in account, or a human decision (NOT Claude Code) |
|---|---|
| Entire repo scaffold, `.gitignore`, `.env.example`, `requirements.txt`, `README.md` | Creating n8n Cloud account; importing the workflow JSON; creating the n8n API key |
| `config\constants.py` holding the locked CA&J facts, GHL build location, booking URL, pricing constants | All GoHighLevel work: subaccount creation, snapshots, calendars, AI agents, knowledge bases, widgets, phone numbers, payments/products, workflows. GHL is UI-only. |
| `config\settings.py` — env loading, fail-closed behaviour when a credential is absent, `DRY_RUN=true` default | Obtaining any API key or OAuth grant (OpenAI, Vapi, Apify, HeyGen, ElevenLabs, Ayrshare, Supabase, Airtable, HubSpot, Slack, Google, Instantly, Hunter, Pinecone, Perplexity) |
| Eight n8n workflow JSON files (`workflows\01..08*.json`) — node graph, parameters, prompt wiring, branch logic, error outputs | Buying/provisioning a Twilio or Vapi phone number; increasing concurrency; enabling a paid Vapi/Retell/Bland plan |
| All prompt templates as separate `.txt` files with variable placeholders | Apify actor runs that consume paid compute or scrape a site; running yt-dlp-style downloads against third-party platforms |
| `guardrails\pricing_guard.py` — regex/rule engine that blocks any outbound text containing a price, dollar amount, or "setup fee" | Any Gmail/Google Calendar send or event creation (OAuth grant + live account) |
| `guardrails\meeting_first.py` — rewrites price-intent replies to the booking URL `https://ca-jenterprises.com/ai` | GHL conversation/AI-agent prompt entry (UI-only) and any live chat or voice reply |
| `data\fixtures\*.json` synthetic leads, transcripts, ad-analysis payloads | Contacting a real prospect by email, DM, SMS, or call — human-authorized only |
| `adapters\mock_*.py` — deterministic fakes for every external service so workflows execute offline | Real social publishing to TikTok / IG / YouTube / LinkedIn / X (Ayrshare/Blotato login + platform TOS) |
| `scripts\validate_workflows.py` — schema/naming/credential-leak lint over the JSON | Generating video with Sora 2 / Runway / Pika / HeyGen / Creatomate (paid + logged-in) |
| `scripts\cost_estimate.py` — computes worst-case monthly spend from a `pricing.yaml` the human maintains | Approving any spend. ABSOLUTE RULE: no charges or purchases of any kind. Every paid service above is an approval gate. |
| `scripts\check_env.py` — reports which env vars are set, never prints values | Verifying whether an n8n node type or vendor API still exists as described — requires live docs/login |
| `docs\DEPLOY-RUNBOOK.md`, `docs\UI-ONLY-CHECKLIST.md`, `docs\COST-AND-APPROVALS.md`, `docs\SOURCE-CLAIMS.md` | Deciding whether this n8n stack replaces or sits beside the GoHighLevel build location. That is a human architecture decision (see §8). |
| `prompts\*` with `{{placeholder}}` conventions and a renderer that refuses to emit unresolved placeholders | Marketing/legal review of outbound copy, and legal review of any scraping actor's terms-of-service compliance |

## 4. Deliverable File Tree

Root: `C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system\build\automation-suite\`

`automation-suite\
├── README.md                          # what this repo is, what it does NOT do, how to dry-run
├── .env.example                       # every env var name, no values
├── .gitignore                         # ignores .env, data\out\, *.log, .venv
├── requirements.txt                   # stdlib-first; pin only what is actually imported
├── config\
│   ├── constants.py                   # locked CA&J facts, GHL location, booking URL, pricing
│   ├── settings.py                    # env loading, DRY_RUN default true, fail-closed helpers
│   └── pricing.yaml                   # human-maintained vendor price table; all rows marked unverified
├── guardrails\
│   ├── pricing_guard.py               # blocks outbound text that quotes any price
│   ├── meeting_first.py               # price-intent -> booking URL rewrite
│   └── claim_guard.py                 # rejects source-author results restated as CA-J results
├── prompts\
│   ├── 01_voice_receptionist_system.txt
│   ├── 02_lead_enrich.txt
│   ├── 02_cold_email.txt
│   ├── 02_followup.txt
│   ├── 03_ad_deconstruction.txt
│   ├── 03_sora_prompt_format.txt
│   ├── 04_faceless_script.txt
│   ├── 04_trending_topics.txt
│   ├── 05_content_script.txt
│   ├── 06_language_detect.txt
│   ├── 06_faq_rag.txt
│   ├── 06_translate.txt
│   ├── 07_youtube_analysis.txt
│   ├── 07_youtube_ideas.txt
│   └── 08_heygen_script.txt
├── workflows\
│   ├── 01_voice_call_agent.json       # webhook -> agent -> 4 tools -> post-call
│   ├── 02_lead_generation.json        # scrape -> enrich -> qualify -> outreach -> follow-up
│   ├── 03_ugc_ads_spy.json            # input -> vision+whisper -> insights -> 5 prompts
│   ├── 04_faceless_video.json         # trends -> script -> render -> publish -> track
│   ├── 05_content_agent.json          # research -> script -> video -> captions -> publish -> loop
│   ├── 06_faq_chatbot.json            # message -> detect lang -> RAG -> translate -> reply -> escalation
│   ├── 07_youtube_ideas.json          # top videos -> analysis -> 10 ideas -> report
│   ├── 08_avatar_generator.json       # script -> heygen -> voice/edit -> export -> publish
│   └── _common_error_handler.json     # shared error workflow, referenced by all eight
├── adapters\
│   ├── mock_openai.py                 # deterministic canned completions keyed by prompt id
│   ├── mock_calendar.py               # in-memory free/busy + create-event
│   ├── mock_crm.py                    # in-memory contact upsert
│   ├── mock_mailer.py                 # writes .eml to data\out\mail instead of sending
│   ├── mock_video_gen.py              # writes a stub .json job record, no render
│   ├── mock_apify.py                  # serves data\fixtures\leads.sample.json
│   └── mock_publisher.py              # records intended posts, publishes nothing
├── data\
│   ├── fixtures\
│   │   ├── leads.sample.json          # synthetic HVAC/agency leads, fake domains/phones
│   │   ├── ad_transcript.sample.json  # synthetic viral-ad transcript + frame notes
│   │   ├── faqs.sample.md             # synthetic FAQ corpus for RAG tests
│   │   └── youtube_top.sample.json    # synthetic top-video metrics
│   └── out\                           # gitignored run output
├── scripts\
│   ├── check_env.py                   # prints SET/MISSING per var; never values
│   ├── validate_workflows.py          # JSON parse, node/name checks, no-secret scan
│   ├── render_prompts.py              # fills {{placeholders}}; hard-fails on unresolved
│   ├── run_dry.py                     # executes a workflow graph against adapters, offline
│   ├── cost_estimate.py               # monthly worst-case spend from pricing.yaml
│   └── check_guardrails.py            # self-test suite for guardrails\*
└── docs\
    ├── DEPLOY-RUNBOOK.md              # human steps: accounts, n8n import, Vapi, Ayrshare, GHL
    ├── UI-ONLY-CHECKLIST.md           # every step needing a browser/login, per automation
    ├── COST-AND-APPROVALS.md          # approval gates + exact spend table for sign-off
    └── SOURCE-CLAIMS.md               # verbatim unverified claims from the source`

## 5. Build Steps

1. Create the directory tree in §4 under `build\automation-suite\`. Create `specs\` if absent. Do not create any file outside this root.
1. Write `config\constants.py`. Define the locked values verbatim: `OWNER_NAME = "Chuck Ashley"`, `OWNER_PHONE = "512-229-9199"`, `OWNER_EMAIL = "chuck@ca-jconsulting.com"`, `LEGAL_ENTITY = "CA&J Enterprises LLC"`, `GHL_AGENCY_URL = "https://app.gohighlevel.com"`, `GHL_BUILD_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"`, `GHL_BUILD_LOCATION_NAME = "CA&J Enterprises"`, `BOOKING_URL = "https://ca-jenterprises.com/ai"`, `MEETING_FIRST = True`, `SPEND_CAP_USD = 0.00`, `DRY_RUN = True`, `TECH_FEE_MONTHLY_USD = 650`, `SETUP_FEE_USD = 0`, `PER_APPOINTMENT_MIN_USD = 150`, `PER_APPOINTMENT_MAX_USD = 300`. Add a module docstring stating: GHL location IDs are case-sensitive; all GHL work is UI-only; no charges or purchases of any kind without explicit human approval.
1. Write `config\settings.py`. Load env vars with `os.environ.get`, never hardcode a secret, never log a value (log `SET`/`MISSING` only). Provide `require_credential(name)` that raises a typed `MissingCredential` and returns a clear "blocked, human action required" message. Default `DRY_RUN=True`; if `DRY_RUN` is false, print a refusal banner and exit non-zero unless `ALLOW_LIVE=1` is also set by a human.
1. Write `.env.example` listing exactly the names in §6 with empty values and a one-line comment per var marking which are approval-gated.
1. Write `.gitignore` covering `.env`, `data\out\`, `*.log`, `.venv\`, `__pycache__\`.
1. Write `docs\SOURCE-CLAIMS.md` first — copy every quantitative claim from the source verbatim with its line number and label each `unverified`. This file is the single source of truth for §8 and must be written before any prompt or workflow encodes a number.
1. Write the fifteen `prompts\*.txt` files. Base each on the source's prompt text (source lines 26, 38, 39, 51, 52, 63, 85, 86, 97, 98, 109), with these mandatory edits: (a) insert a no-price clause — the assistant must never state or estimate a price, discount, or fee and must direct pricing intent to `BOOKING_URL`; (b) replace every `[result]`/`[pain]` placeholder with a placeholder that has no implied earnings claim; (c) add a "never invent data" clause; (d) add a clause forbidding claims of CA-J results sourced from another author; (e) for `01_voice_receptionist_system.txt`, keep the source's "Never invent times", "Confirm email before sending", "escalate after 2x confusion", and "<25 words" rules verbatim.
1. Write the eight workflow JSON files. Each file: `{"name": "<source title>", "nodes": [...], "connections": {...}, "settings": {...}, "meta": {"source_line": <int>, "verified": false}}`. Implement the node graph described at source lines 17, 30, 42, 55, 66, 77, 89, 101. Wire every external call through the node type and note in `meta` whether the node type is unverified. Add a `notes` field on each node carrying the source step text it implements. Terminate every workflow with the shared error workflow `_common_error_handler`.
1. Write `_common_error_handler.json`: catch-all error trigger that writes a JSON error record (workflow name, node, message, timestamp, synthetic-vs-real flag) to `data\out\errors\` and performs no external action.
1. Write the eight `adapters\mock_*.py` modules. Each exposes the same call signature as the real client and returns deterministic data from `data\fixtures\`. Every adapter must raise `LiveCallBlocked` if invoked while `DRY_RUN` is true and a real endpoint is configured. No adapter may contain a network call in the default path.
1. Write `data\fixtures\*` with entirely synthetic data. Use example.com / 555-range numbers only. No real business name, email, phone, or address may appear anywhere in fixtures.
1. Write `guardrails\pricing_guard.py`: parse a text blob, flag `$`, `USD`, `dollars`, "price", "pricing", "fee", "per month", "setup fee", "monthly", "cost", and any digit sequence adjacent to a currency token. Return `BLOCKED` with the offending span. Provide `assert_clean(text)` used by every outbound-sending node.
1. Write `guardrails\meeting_first.py`: detect pricing intent in an inbound message; produce a reply that invites a meeting and links `BOOKING_URL`; never emit a number.
1. Write `guardrails\claim_guard.py`: scan outbound copy against a denylist built from `docs\SOURCE-CLAIMS.md` (source-author results, "unlimited", "virtually nothing", "10 calls at a time") and block restatement as CA-J fact.
1. Write `scripts\validate_workflows.py`: parse all JSON, assert required top-level keys, assert unique node names, assert every node carries `notes`, assert `meta.verified` is present and boolean, and scan the whole repo for anything resembling a secret (long alphanumeric runs near `key|token|secret|password`, and any `sk-`/`xoxb-`/`ghp_` prefix). Exit non-zero on any finding.
1. Write `scripts\check_env.py`, `scripts\render_prompts.py`, `scripts\run_dry.py`, `scripts\cost_estimate.py`, `scripts\check_guardrails.py`. `run_dry.py` must execute each workflow graph against the mock adapters and write a per-run JSON report to `data\out\runs\`. `cost_estimate.py` must read `config\pricing.yaml`, print the monthly worst case, and exit non-zero if it exceeds `SPEND_CAP_USD`.
1. Write `config\pricing.yaml` with one row per vendor mentioned in source line 117 (`vapi`, `openai_realtime`, `apify`, `apollo`, `heygen`, `elevenlabs`, `createmate`, `ayrshare`, `openai_api`, `sora_runway`, `twilio`) — every row `unit_cost: null`, `verified: false`, `source: "01-8-best-ai-automations.md:117 (unverified)"`. Do not copy the source's numbers into the file as though they were current rates; record them only in `docs\SOURCE-CLAIMS.md`.
1. Write `docs\DEPLOY-RUNBOOK.md`: numbered human steps for n8n account creation, workflow import, credential creation, Vapi/Twilio number provisioning (spend gate), Apify actor selection (spend gate), HeyGen/ElevenLabs/Ayrshare/Creatomate/Ayrshare subscriptions (spend gate), Google/Gmail OAuth, HubSpot, Supabase/Airtable, and the GHL-side configuration. Each step: action, account, cost, approval required (yes/no), evidence to capture.
1. Write `docs\UI-ONLY-CHECKLIST.md` mirroring §3's right column, one subsection per automation.
1. Write `docs\COST-AND-APPROVALS.md`: table of every service, whether it can be used at $0 (no), the approval required, and the explicit statement that the CA&J locked pricing ($650/mo tech fee, setup waived, $150–$300 per qualified appointment) is the only pricing this suite may reference in any prospect-facing artifact.
1. Write `README.md`: purpose, the dry-run command sequence, the absolute rules (no charges, no invented data, meeting-first, source results are not CA-J results), and a pointer to `docs\` for everything the coding agent cannot do.
1. Run, in this order and fix failures before proceeding: `python scripts\validate_workflows.py`, `python scripts\check_guardrails.py`, `python scripts\check_env.py`, `python scripts\render_prompts.py`, `python scripts\run_dry.py`, `python scripts\cost_estimate.py`. Inline heredoc and giant one-liner shell commands are blocked on this host — put any multi-line logic in a `.py` file and run it.
1. Do not call any external API, create any account, or spend any money at any step.

## 6. Configuration & Constants

Env vars (names only, no values anywhere in the repo; `.env.example` lists them empty):

| Var | Used by | Gate |
|---|---|---|
| `DRY_RUN` | settings.py | default `true`; `false` refuses to run without `ALLOW_LIVE=1` |
| `ALLOW_LIVE` | settings.py | human-only |
| `OPENAI_API_KEY` | 01,02,03,04,05,06,07,08 | paid — approval required |
| `N8N_BASE_URL`, `N8N_API_KEY` | import/ops | account creation — approval required |
| `VAPI_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` | 01 | paid + number purchase — approval required |
| `APIFY_TOKEN` | 02,03,04 | paid + scraping ToS review — approval required |
| `HEYGEN_API_KEY`, `ELEVENLABS_API_KEY`, `CREATOMATE_API_KEY` | 03,04,05,08 | paid — approval required |
| `AYRSHARE_API_KEY` | 04,05,08 | paid + platform TOS — approval required |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` | 01,07 | OAuth grant — human |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` | 02 | sending identity — human |
| `HUBSPOT_TOKEN` | 01,02 | free tier OK, account needed |
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `AIRTABLE_TOKEN` | 02,03,05,07 | account needed |
| `PINECONE_API_KEY` | 06 | paid tier for vector — approval required |
| `SLACK_WEBHOOK_URL` | 01,06,08 | human-owned workspace |
| `HUNTER_API_KEY`, `INSTANTLY_API_KEY`, `PERPLEXITY_API_KEY` | 02,04 | paid — approval required |
| `GHL_LOCATION_ID` | reference only | must equal `UWc5vKBgFVPdxNTRAy2s` (case-sensitive). No GHL API call is made by this suite; GHL is UI-only. |
| `WEBHOOK_SHARED_SECRET` | internal HMAC | generated locally, never committed |

Approval-gate constants (in `config\constants.py`, imported by every outbound node):

`SPEND_CAP_USD = 0.00`, `REQUIRE_HUMAN_APPROVAL_FOR_SPEND = True`, `REQUIRE_HUMAN_APPROVAL_FOR_OUTBOUND = True`, `REQUIRE_HUMAN_APPROVAL_FOR_PUBLISH = True`, `REQUIRE_HUMAN_APPROVAL_FOR_GHL = True`.

Caps:

`DAILY_EMAIL_CAP_PER_INBOX = 30` (source line 35; training target, not a validated sending limit), `FOLLOWUP_SEQUENCE_MAX = 2` (source line 36), `VOICE_CONCURRENCY_REQUESTED = 10` (source claim, unverified — do not treat as provisioned), `SUPPRESSION_CHECK_REQUIRED = True`, `OPT_OUT_HONOR_REQUIRED = True`.

Rules encoded as code, not comments: no price may be emitted by any agent or template (§5.12–13); no source author's result may be asserted as CA-J's (§5.14); booking destination is always `https://ca-jenterprises.com/ai`.

## 7. Acceptance Criteria

1. `build\automation-suite\` exists and its file set matches §4 exactly (no extra top-level dirs, no missing files).
1. `python scripts\validate_workflows.py` exits 0 and reports 8 workflow files plus the shared error workflow, all valid JSON.
1. `python scripts\check_guardrails.py` exits 0 and demonstrates that `pricing_guard` blocks `"$650 per month"`, `"setup fee"`, `"$197"`, and `"150–300 per appointment"`.
1. `pricing_guard.assert_clean()` on every one of the fifteen prompt files passes, and a deliberately re-injected price causes a non-zero exit.
1. `python scripts\render_prompts.py` runs with zero unresolved `{{placeholders}}` for every prompt whose variables are supplied by fixtures, and hard-fails (non-zero) when one is withheld.
1. `python scripts\run_dry.py` completes all eight workflows offline with zero network egress and writes eight run reports to `data\out\runs\`.
1. `python scripts\cost_estimate.py` prints a monthly worst case and exits non-zero because the figure exceeds `SPEND_CAP_USD = 0.00`.
1. A repo-wide secret scan by `validate_workflows.py` reports zero findings; `.env` is absent from the tree and listed in `.gitignore`.
1. No file in the repo contains a real secret, token, phone number, email address, or business name other than the locked CA&J contact facts in `config\constants.py`.
1. `docs\SOURCE-CLAIMS.md` lists at least the cost figures from source line 117, the concurrency/unlimited claim from line 15, and the perf claims from lines 61 and 107 — each labelled `unverified`.
1. `docs\UI-ONLY-CHECKLIST.md` contains a section for each of the eight automations and names GoHighLevel, Meta Ads Manager, and every paid vendor UI as coding-agent-inaccessible.
1. `docs\COST-AND-APPROVALS.md` states the locked CA&J pricing and that no purchase of any kind is authorized by this spec.
1. `config\pricing.yaml` contains no numeric rate copied from the source; all `verified: false`.
1. `config\constants.py` contains `GHL_BUILD_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"` byte-identical, and no other GHL location ID appears anywhere in the repo.
1. No step in the executed build created an account, opened a browser, or spent money.

## 8. Blockers & Unverified Items

Do NOT assume any of the following. All are open:

1. No GHL integration exists in the source. The source is entirely n8n-based; the CA&J house stack mandates GoHighLevel as the only build location (UI-only, location `UWc5vKBgFVPdxNTRAy2s`). Whether these eight automations run on n8n, inside GHL, or both is an unresolved human architecture decision. This spec builds the n8n/code layer only and does not modify any GHL object.
1. Every dollar figure in the source (line 117) is `unverified`: Vapi $0.05/min, OpenAI Realtime $0.06/min, 100 calls/day ≈ $30/day, Apify $50/mo, Apollo $100/mo, HeyGen $29/mo, ElevenLabs $22/mo, Creatomate $30/mo, Ayrshare $30/mo, OpenAI $50–100/mo, "Total startup ~$300–400/mo". Treat as the author's numbers at the author's date, not CA-J's rates. No spend is authorized.
1. "Answers 10 calls at a time, unlimited/day" (line 15) is `unverified`. Concurrency is plan-dependent and requires a purchased Vapi plan plus a Twilio number. The coding agent cannot provision either.
1. n8n node type names and parameters in the source (e.g. "Call Agent (OpenAI Realtime)", Google Calendar "Get Availability", Ayrshare upload, HeyGen `POST /v2/video/generate`, Sora 2 API) are drawn from screenshots. None have been validated against current node inventories or API docs. `meta.verified: false` must be set on all eight workflows.
1. Sora 2 API access, Ayrshare multi-platform publishing behaviour, and platform TOS for TikTok/IG/YouTube auto-posting are `unverified` and change without notice.
1. Scraping claims — Apify actors `apollo-io-scraper` and `google-maps-scraper` (line 32) — are `unverified` and carry a terms-of-service and legality question. Do not encode Apollo scraping as approved.
1. Deliverability claims — "30 emails/day per inbox", "Setup SPF/DKIM", "10 Gmail inboxes" (lines 35, 115) — are `unverified` as safe volumes, and SPF/DKIM are DNS changes requiring domain access and human action.
1. The source author's implied outcomes (virality, "UGC 10x faster", channel scale, revenue) are the author's, and may not be restated as CA-J results, goals, or forecasts at any time.
1. No results, metrics, benchmarks, or proof points exist for CA-J in this source. Any prospect-facing copy generated from these workflows must contain no unverified proof.
1. Google OAuth, Slack, HubSpot, Supabase, Airtable, Pinecone accounts — none exist in this workspace as far as this spec can determine. `check_env.py` will report them MISSING; that is a blocker to live operation, not a build failure.
1. Meeting-first and pricing rules apply to every agent in this suite: automation 01 (voice), 02 (cold email/follow-up), and 06 (FAQ chatbot) must never quote a price; they route pricing intent to `https://ca-jenterprises.com/ai`. The source's own email and voice templates violate this and must not be used unedited.
1. Paid ads, upsells, and "scaling" steps mentioned in the source are out of scope: no ad spend, no purchases, no upgrades. Anything requiring money is an explicit human approval gate with the exact amount stated in `docs\COST-AND-APPROVALS.md`.
1. Hermes/Claude Code has no browser. Every step in `docs\DEPLOY-RUNBOOK.md` and `docs\UI-ONLY-CHECKLIST.md` is unexecutable by the coding agent by design.

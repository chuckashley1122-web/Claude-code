# Facebook Ads + GHL AI Studio

# SPEC-04 — Facebook Ads + GHL AI Studio Build

**Executor:** Claude Code / Claude Cowork, headless (`claude -p`).

**Capabilities assumed:** filesystem read/write, shell commands, Python 3.11 via `python` (NOT `python3`). **No browser. No UI logins. No authenticated network access.**

**Repo root:** `C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system\`

**Host:** Windows 11. Shell is bash (MSYS). Inline heredoc / giant one-liner shell commands are BLOCKED — every script is written to a `.py` file then run with `python <file>`.

**Execute top to bottom. Do not ask questions. Where a value is unknown, emit the literal string `NEEDS_EVIDENCE` and continue.**

## 1. Source & Provenance

- **File read:** `C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system\playbooks\04-facebook-ads-ghl-ai-studio-sop.md`
- **Size:** 28,561 characters, 440 lines, 29,000 bytes. Read in full. Not truncated.
- **What the source actually is:** an AI-generated SOP dated 2026-09-12, written for Chuck Ashley, titled "Hermes Agent - Complete Facebook Ads + GoHighLevel AI Studio Build SOP," derived from the YouTube tutorial `https://www.youtube.com/watch?v=3ikJQWLRhNM` ("Facebook Ads + GoHighLevel AI Studio - Complete Local Lead Generation Tutorial"). It is a **6-phase procedural transcription of a tutorial**, written generically around a non-CA-J worked example (a junk-removal business, "Cary Junk Removers," Cary, North Carolina). It is a plan, not a record — **no phase in it has been executed and no object described in it exists.**
- **Structural note:** every step in the source is a UI instruction ("Go to…", "Click…", "Log into…"). The source contains an "execution checklist for automation" block that mislabels UI steps as a code task list. That framing is wrong for this executor and must be corrected: almost the entire SOP is UI-only.
- **The worked example is not CA-J.** All placeholder business content (junk removal, Cary NC, `offer.caryjunkremovers.com`, `$100 discount on first service`, `$49 drain cleaning`) is the tutorial's example and must be re-derived for CA-J's HVAC context. Where the CA-J value is unknown, use `NEEDS_EVIDENCE`.
**Claims in the source that are NOT verified by CA-J:**

| # | Claim | Status |
|---|---|---|
| F1 | "$70/day start" as the minimum viable Meta budget ($50/60/70/100 suggested) | Instructor guidance. Not a CA-J budget. Any spend requires explicit human approval. |
| F2 | "$100 discount on first service", "$49 drain cleaning", "50% off first visit" | Tutorial example offers. Not CA-J offers. |
| F3 | "100% lead tracking" via CAPI | Marketing claim. CAPI fires only for events that actually carry Facebook parameters and only when the integration works end-to-end. |
| F4 | "Broad targeting is new best practice due to the Andromeda update" | Industry claim repeated from the video. Not a CA-J-verified result. |
| F5 | "AI Studio landing pages are high-speed / high-converting" | Unverified performance claim. |
| F6 | CNAME target `vibe.cloud` | Taken from the video's screen. Not verified against the current AI Studio product. |
| F7 | The "Hormozi mega prompt" in a Google Doc (`docs.google.com/document/d/1G...`) | **Never supplied.** Contents unknown. Do not attempt to fetch or reproduce it. |
| F8 | A2P 10DLC approval, GHL phone number status, SMS deliverability | Unknown. Status is `NEEDS_EVIDENCE`. |
| F9 | Meta Ad Library "longest running = winner" heuristic; ad-length and format best practices | Heuristic, not verified. |
| F10 | Post-launch performance expectations (CPL, CTR, CPC targets) | The video gives none for CA-J. Any target is `NEEDS_EVIDENCE`. |
| F11 | AI Studio availability via GHL `Settings → Labs` on the CA&J agency account | Not verified. May not exist for this account. |
| F12 | The SOP's claim that domains, payment methods and ad accounts can simply be "created" | Every one of those is a **spend or a logged-in action** and is blocked here. |

**Rule:** identical-looking numbers from the source are NOT results CA-J has achieved. Do not restate the tutorial author's or an example client's outcome as CA-J's own. Anything unverifiable is written as `NEEDS_EVIDENCE`.

## 2. Objective

Produce a complete, reviewable, draft-only asset package for a Facebook Leads campaign feeding a GoHighLevel-hosted landing page — built entirely as files on disk by Python scripts into a fixed output tree: the offer definition, the landing-page content and build prompt pack, a static reviewable HTML mock of the page and thank-you page, the pipeline spec, the two workflow specs (new-lead speed-to-lead sequence and replied-lead handler) plus a CAPI event workflow spec, the ad creative briefs and copy pack (angles, primary texts, headlines, CTAs, image/video specs), the pixel/CAPI configuration spec, the Meta campaign/ad-set/ad configuration spec with every field pre-filled, a UTM/`fbclid` test-URL generator, and a 14-case test log — all constrained by hard guardrails (a live campaign that must never be touched, zero spend without explicit human approval, no price in any message, the CA-J logo never first). Every UI press is emitted as a checklist for a human with exact values. Nothing is launched, activated or published by the build.

## 3. Code-Layer vs UI-Layer Split

Strict. Claude Code **cannot** operate Meta Business Suite, Meta Ads Manager, Events Manager, the Meta Ad Library, GoHighLevel, GHL AI Studio, or a DNS registrar. There is no browser and no authenticated session. Everything in the right column ships as a markdown checklist with exact field values and is never reported as done.

| Claude Code CAN build (files + shell + Python) | Needs browser / logged-in account / human |
|---|---|
| Directory scaffold, `build_config.json`, `.env.example`, decision log, asset register | Creating a Meta Business Portfolio, ad account, or adding a payment method |
| Config validator asserting house facts and rejecting guessed IDs | Connecting the Facebook Page / Instagram Profile to the portfolio |
| Guardrail module: frozen-campaign, no-spend, no-price-in-message, logo-not-first | Creating the GHL sub-account; enabling AI Studio via `Settings → Labs` |
| Offer definition derived from config (no invented discounts) | Generating the landing page inside AI Studio (prompt is produced here; the button is human) |
| AI Studio mega-prompt assembly with all placeholders pre-filled — for a human to paste | Iterating the page inside AI Studio (logo/hero/before-after/copy changes) |
| Static `index.html` landing-page mock + `thank-you.html` for offline content review | Publishing the page, adding a custom domain/subdomain, editing DNS CNAME records |
| Landing-page content spec: hero, sections, form fields, CTAs, trust badges | Buying a domain (EXPLICIT APPROVAL REQUIRED — spend) |
| GHL pipeline spec + stage/custom-field JSON for the 4-stage "Meta Ads Leads" pipeline | Creating the pipeline, stages and custom fields in GHL |
| Workflow specs as reviewable docs: triggers, filters, actions, waits, branches, stop conditions | Building and publishing workflows in GHL; A2P 10DLC registration |
| SMS/email copy templates with merge-token placeholders flagged as unconfirmed | Sending any SMS or email; verifying the sender |
| Meta Pixel / Dataset configuration spec, including CAPI event and signal selection | Creating the Pixel/Dataset; generating the CAPI access token |
| CAPI workflow spec including action field values, event type, LTV, currency, custom-mapping flag | Meta Events Manager steps; Test Events; Execution Logs verification |
| Ad-angle briefs (pain / desire / objection / offer) and creative direction | Recording or editing video; generating images |
| Ad copy pack: 5 primary-text variations per angle, 3–4 headlines, CTA per ad | Uploading creatives into Ads Manager |
| Image/video spec sheet: 1080×1080 requirement, ≤30s video, placement-crop notes | Meta Ad Library research (browser); Ad Library scraping |
| Campaign / ad set / ad configuration spec with every field pre-filled for ABO at ad-set level | Creating the campaign, ad set and ads in Ads Manager; publishing at campaign level |
| UTM / `fbclid` / `fbc` / `fbp` dummy test-URL generator + attribution fixtures | Submitting the live test form; checking contact attribution in the GHL UI |
| `run_tests.py` — 14-case log with PASS / FAIL / BLOCKED and evidence paths | Any verification that requires reading a logged-in dashboard |
| All UI checklists with exact values, plus the human-decision queue | Anything that spends money |
| `compliance_scan.py` over every generated asset | Launching, pausing, resuming or editing any live Meta campaign |

**Hard prohibition:** the live campaign `CAJ_HVAC27_US_PURCHASE_TEST02` is FROZEN. No build output may edit, pause, resume, duplicate-in-place or otherwise reference it as a target. Editing it resets Meta's learning phase. Any new campaign exists only as a separate NEW draft. This applies to the human checklists too.

## 4. Deliverable File Tree

All paths relative to repo root. Created by the build; nothing outside `build\04-fb-ai-studio\` is written.

`build\04-fb-ai-studio\
├─ README.md                                 # What was built, that nothing was launched, run commands
├─ .env.example                              # Env var NAMES only. Empty values. No real secrets.
├─ config\
│  ├─ build_config.json                      # Single source of truth; unknowns = "NEEDS_EVIDENCE"
│  ├─ constants.py                           # House facts, IDs, guard flags, locked pricing
│  ├─ decision_log.jsonl                     # Append-only: timestamp, key, value, source, status
│  └─ asset_register.json                    # Every generated asset: id, path, status, owner
├─ tools\
│  ├─ state.py                               # Status enum, decision-log writer, blocker recorder
│  ├─ guardrails.py                          # frozen-campaign / no-spend / no-price / logo-last
│  ├─ validate_config.py                     # Hard assertions on IDs, caps, forbidden values
│  ├─ utm_builder.py                         # Dummy fbclid/fbc/fbp/utm_* test URLs
│  ├─ compliance_scan.py                     # Scans every generated .md/.json/.html for banned patterns
│  ├─ build_all.py                           # Idempotent orchestrator, dependency-ordered
│  └─ run_tests.py                           # T01–T14 → PASS / FAIL / BLOCKED + evidence path
├─ src\
│  ├─ offer.py                               # → out\offer.md
│  ├─ landing_content.py                     # → out\landing\content_spec.md, content_spec.json
│  ├─ landing_mock.py                        # → out\landing\index.html, out\landing\thank-you.html
│  ├─ ai_studio_prompts.py                   # → out\landing\ai_studio_prompt_pack.md
│  ├─ pipeline_spec.py                       # → out\pipeline_spec.md, out\pipeline.json
│  ├─ workflow_new_lead.py                   # → out\workflows\01-new-lead-automation.md
│  ├─ workflow_hot_lead.py                   # → out\workflows\02-hot-lead-replied.md
│  ├─ workflow_capi.py                       # → out\workflows\03-landing-page-capi-lead.md
│  ├─ message_templates.py                   # → out\messages\sms_01..sms_06.md, internal_alerts.md
│  ├─ ad_angles.py                           # → out\ads\angles.md, out\ads\angles.json
│  ├─ ad_copy.py                             # → out\ads\copy\A01..A04.md
│  ├─ creative_specs.py                      # → out\ads\creative_specs.md
│  ├─ pixel_capi_spec.py                     # → out\pixel_capi_spec.md, out\capi_settings.json
│  ├─ campaign_spec.py                       # → out\campaign_spec.md, out\campaign_config.json
│  └─ launch_review.py                       # → out\launch_review.md, out\asset_register.md
├─ out\
│  ├─ tests\
│  │  ├─ test_log.md
│  │  └─ T01.json … T14.json
│  ├─ test_urls.txt                          # Dummy-tracking URLs for the human CAPI test
│  └─ (all files listed under src\ above)
├─ ui-tasks\
│  ├─ META-CHECKLIST.md                      # Exact Meta UI steps. Frozen-campaign warning at top.
│  ├─ GHL-CHECKLIST.md                       # Exact GHL UI steps, location ID, object names
│  ├─ AI-STUDIO-CHECKLIST.md                 # Prompt-to-paste + iteration prompts + publish steps
│  ├─ DNS-CHECKLIST.md                       # CNAME record spec + purchase-approval gate
│  └─ HUMAN-DECISIONS.md                     # Every NEEDS_EVIDENCE + every approval gate
└─ logs\
   └─ build.log                              # Timestamped run log from build_all.py`

## 5. Build Steps

Execute in order. Every step writes its file, appends to `config\decision_log.jsonl`, and records the asset in `config\asset_register.json`.

1. **Scaffold + state layer.** Create the tree in section 4. Write `tools/state.py`: `STATUS` enum = `Not started | Draft | Tested | Ready for launch | Live | Blocked`; `log(key, value, source, status)`; `record_blocker(item, missing_input, work_affected, next_action)`; `mark_asset(id, path, status)`. No script may write the status `Live`.
1. **Constants.** Write `config\constants.py` with everything in section 6, including guard booleans and the frozen-campaign name.
1. **Config.** Write `config\build_config.json` with the exact key set in section 6. Default `BUILD_MODE` = `CAJ_HVAC`. Any value not in section 6 → `"NEEDS_EVIDENCE"`. Never invent a Page ID, ad account ID, pixel ID, domain, calendar ID, or phone number.
1. **Env template.** Write `.env.example`: names only, empty values, with a comment that real values never get committed. No real token, key, or ID value anywhere in the tree.
1. **Validator.** Write `tools\validate_config.py`. Hard-fail (non-zero exit) if: `GHL_LOCATION_ID != "UWc5vKBgFVPdxNTRAy2s"` (exact case); `AD_SPEND_CAP_USD != 0` while `APPROVAL_AD_SPEND` is false; `LAUNCH_AUTHORITY != "none"` while `APPROVAL_LAUNCH` is false; `DOMAIN_PURCHASE_APPROVED` is true without an approval reference; `FROZEN_CAMPAIGN_PROTECTED != true`; `QUOTE_PRICE_IN_MESSAGE != false`. Print one line per check.
1. **Guardrails.** Write `tools\guardrails.py`, four functions, all used by `compliance_scan.py` and `run_tests.py`:
   - `assert_not_frozen_campaign(text)` — raises if any generated asset names `CAJ_HVAC27_US_PURCHASE_TEST02` as a target, or contains an edit/pause/duplicate instruction against it. The only permitted mentions are the warning banner in `ui-tasks\META-CHECKLIST.md` and the constant itself. Any new campaign name must match `CAJ-FB-HVAC-Leads-<YYYYMMDD>-DRAFT` and be marked **draft, never published by this build**.

   - `assert_no_spend(item, approval_ref)` — raises unless an explicit approval reference is supplied. Applies to ad budget, domains, subscriptions, tools, upgrades, payment methods.

   - `assert_no_price_in_message(text)` — raises if any CA-J price ($650/mo, $150–$300 per appointment, any setup fee, or any other CA-J service figure) appears in ad copy, SMS, email, form copy, or AI-reply copy. Booking destination is always `https://ca-jenterprises.com/ai`. Discount/price offers for a *client's* consumers are out of scope and also require approval.

   - `assert_logo_not_first(creative)` — raises if a creative's first visual element is the CA-J logo. Creatives lead with the outcome or the offer; the logo appears only as a small footer disclaimer.

1. **Offer definition.** `src\offer.py` → `out\offer.md`. Carry forward the source's rule: the offer must be specific, low-friction, an easy yes; do **not** use "Contact us", "Learn more" as a first touch, or "submit card details". Record the CA-J agency-acquisition offer as: a free, no-obligation strategy session booked at `https://ca-jenterprises.com/ai`, and **no price stated anywhere before the call**. Any dollar figure in the source's example offer lists is recorded as an example only, marked `NEEDS_EVIDENCE`, and requires explicit approval before use. Include the LLM offer-brainstorm prompt from the source's prompt library as a reference block, with a note that its output must be filtered through `assert_no_price_in_message`.
1. **Pipeline spec.** `src\pipeline_spec.py` → `out\pipeline_spec.md` + `out\pipeline.json`. Target location `UWc5vKBgFVPdxNTRAy2s`. Note the existing pipeline `CA&J Demo - Lead Pipeline` = `U95kdMryqjDqu7JeFrdw` (New Lead, Contacted, Appointment Booked, Quote Sent, Job Won, Lost / Not a Fit) and do **not** overwrite it. Emit a separate spec for `Meta Ads Leads` with 4 stages: New Lead, Hot Lead / Responded, Closed (won), Lost. Include the reason for each stage and the entry/exit condition.
1. **Workflow — new lead speed-to-lead.** `src\workflow_new_lead.py` → `out\workflows\01-new-lead-automation.md`. Trigger: AI Studio Form Submitted, filtered by project name (`NEEDS_EVIDENCE`) and form name (`NEEDS_EVIDENCE`). Actions in order: create/update opportunity → `Meta Ads Leads` / `New Lead` / status Open / name `{{contact.full_name}}`; add tag; send internal notification to the owner (SMS requires a verified A2P number — else email fallback, status `NEEDS_EVIDENCE`); wait 1 minute; SMS 1; wait 2 hours; SMS 2; wait 1 day; SMS 3; then day 3, day 7, day 10, day 14 — 6–7 total follow-ups; then wait 1 day → move opportunity to `Lost`. Write all of it as a spec table, not a built workflow. Re-check reply/opt-out before each send. Include the source's copy rule: say "website" not "landing page". Flag every `{{contact.*}}` token as **unconfirmed merge syntax** — a human inserts fields with the account's field picker.
1. **Workflow — hot lead handler.** `src\workflow_hot_lead.py` → `out\workflows\02-hot-lead-replied.md`. Trigger: Customer Replied, filtered to replies to Workflow 01. Action 1: remove from Workflow 01 (stops auto-nagging). Action 2: internal notification to the owner including the reply body. Action 3: move opportunity to `Hot Lead / Responded`. Include the A2P 10DLC caveat and the email-fallback path.
1. **Workflow — CAPI event.** `src\workflow_capi.py` → `out\workflows\03-landing-page-capi-lead.md`. Trigger: AI Studio Form Submitted (same filters). Action: Meta Conversion API with event type Funnel Event, event to send `Lead`, LTV and currency `USD` as configurable `NEEDS_EVIDENCE` values, Test Code empty, Custom Mapping OFF (native GHL contacts). Access token and Dataset/Pixel ID are referenced by **env var name only** — the spec must never contain the token value. State the expected behaviour: a submission without Facebook parameters will not be marked as a Facebook lead and will not fire a conversion — that is correct, not a bug.
1. **Message templates.** `src\message_templates.py` → `out\messages\`. Generate six SMS steps plus internal-alert copy as separate `.md` files. Rewrite the source's tutorial-specific lines (junk removal, the example owner/business names) into CA-J agency-acquisition language with `{{contact.first_name}}` placeholders and a `Reply STOP to opt out.` line. Tone: short, human, non-robotic. Run `assert_no_price_in_message()` and `assert_meeting_first`-equivalent on all. Flag bracketed/`{{}}` tokens as placeholders requiring field-picker insertion and a send preview.
1. **Landing-page content spec.** `src\landing_content.py` → `out\landing\content_spec.md` + `content_spec.json`. Sections: hero (headline, subhead, primary CTA, hero image slot `NEEDS_EVIDENCE`), problem, what CA-J does, how it works, who it's for, trust block (review count/rating/years/customers-served all `NEEDS_EVIDENCE` — never invented), FAQ, form, footer, and the booking link `https://ca-jenterprises.com/ai`. Form fields: name, email, phone, service needed (or the CA-J equivalent), plus the consent/communication disclosure. Every button scrolls to the form. Desktop and mobile variants specified. **No testimonial, review count, client count or case study may be fabricated** — each is `NEEDS_EVIDENCE` with a blank evidence column.
1. **Landing-page mock.** `src\landing_mock.py` → `out\landing\index.html` + `out\landing\thank-you.html`. Self-contained static HTML, inline CSS, no external scripts or trackers, openable as `file://` for content review only. Include a visible banner in the mock: "STATIC CONTENT MOCK — NOT THE LIVE PAGE; does not submit anywhere." The form is non-functional (`type="button"`, no action). The thank-you page carries the booking CTA to `https://ca-jenterprises.com/ai`.
1. **AI Studio prompt pack.** `src\ai_studio_prompts.py` → `out\landing\ai_studio_prompt_pack.md`. Two parts. (a) A **placeholder-fill script** listing every placeholder from the source's AI Studio mega prompt — business name, primary location, service areas, primary service, additional services, main offer, offer expiration, primary CTA, phone, average response time, estimated service time, years in business, customers served, Google review rating, number of reviews, guarantee, insurance/license, USP, main pain points, desired outcomes, testimonials, team/owner, hero image, logo, brand colors/fonts — with the CA-J value filled where known and `NEEDS_EVIDENCE` where not. For the CA-J agency-acquisition variant: offer expiration, review rating, review count, customers served and years-in-business claims are all `NEEDS_EVIDENCE` and default to **omitted**, not invented. **Do not attempt to fetch or reproduce the source's Google Doc "mega prompt" — it was never supplied (`NEEDS_EVIDENCE`).** (b) The source's seven iteration prompts, transcribed verbatim as reusable prompts, with a note that the logo/color prompt must not result in the logo appearing first in any paid ad creative.
1. **Pixel / CAPI spec.** `src\pixel_capi_spec.py` → `out\pixel_capi_spec.md` + `out\capi_settings.json`. Document, for a human: create a Dataset/Pixel named `<BUSINESS> Pixel` (`NEEDS_EVIDENCE` for the name) in Business Settings → Data Sources; connect it to the ad account (must answer Yes); install the base code — **not by pasting a real pixel payload into any repo file**, but via the AI Studio chat prompt, with the code supplied from Events Manager by the human; turn on automatic advanced matching. Then CAPI: Setup Manually → Conversions API and Meta Pixel → business category → events `Contact` and `Lead` (add `Schedule` if calendar booking) → identify by Event ID → check all signal boxes (email, phone, first name, last name, city, state, zip, country, fbp, fbc) → generate the access token → record Pixel/Dataset ID. `capi_settings.json` carries: `event_type=Funnel Event`, `event_to_send=Lead`, `custom_mapping=OFF`, `test_code=""`, `ltv=NEEDS_EVIDENCE`, `currency="USD"`, plus `pixel_id_env`, `access_token_env`. **Token and pixel ID are referenced by env var name only, never by value.** Prerequisites section must state: no valid connected subdomain + no native form→CRM connection = CAPI fails.
1. **Ad angles.** `src\ad_angles.py` → `out\ads\angles.md` + `angles.json`. Four angles from the source: A01 Pain Point, A02 Desired Outcome, A03 Objection, A04 Offer. Strip the tutorial's junk-removal framing and re-express for CA-J's HVAC-agency ICP. Include the source's "creatives ARE the targeting" framing as an industry claim, not a verified result. A04 must not lead with a dollar discount for a CA-J service — no price before the call.
1. **Ad copy pack.** `src\ad_copy.py` → `out\ads\copy\A01…A04.md`. Per angle: 5 primary-text variations, 3–4 headlines, CTA (`Learn More`). Rules from the source: location callout in the first line; conversational, not robotic; avoid Google/Facebook brand names in headlines to reduce rejection risk; each ad carries up to 5 primary-text variations. House rule overriding the source: **the CA-J logo must never be the first thing a viewer sees** — ad text and creative lead with the outcome or the offer. No price, no guarantee, no scarcity, no review count, no client outcome. Run `assert_no_price_in_message()` on every string.
1. **Creative specs.** `src\creative_specs.py` → `out\ads\creative_specs.md`. Per asset: `asset_id`, `angle`, `format` (image/video), `dimensions` (images must be 1080×1080 square to avoid cropping in Stories/Feed/Search; add a 1080×1350 alternate where required), `max_duration` (video ≤30s, absolute max 60s), `opening_element` (must be the outcome or offer — never the logo), `logo_placement` (small footer disclaimer only), `shot_direction`, `on_image_text`, `placement_crop_notes`, `source_asset` (`NEEDS_EVIDENCE`). Starting mix per the source: 3–4 videos + 3–4 images = 6–8 total, with a low-budget fallback of 2 videos + 3 images. **Image and video generation is not possible in this executor — emit the exact brief for a human or an image/video tool. Never fabricate asset files.** Run `assert_logo_not_first()` on every record.
1. **Campaign spec.** `src\campaign_spec.py` → `out\campaign_spec.md` + `out\campaign_config.json`. Pre-fill every field for a **draft** campaign, all values from section 6, `NEEDS_EVIDENCE` where unknown:
    - Campaign: objective `Leads`, buying type `Auction`, name `CAJ-FB-HVAC-Leads-<YYYYMMDD>-DRAFT`, campaign spending limit `None`, campaign budget **OFF** (ABO — budget at ad-set level), and a banner: **this is a new separate draft; never touch `CAJ_HVAC27_US_PURCHASE_TEST02`.**

    - Ad set: conversion location `Website`, conversion type `Maximize number of leads`, dataset/pixel = env-var reference, conversion event `Lead` (must match CAPI), dynamic creative OFF, daily budget `NEEDS_EVIDENCE` (the source's $70 figure is recorded as instructor guidance only — **no budget may be set without explicit human approval**), schedule `NEEDS_EVIDENCE`, locations `NEEDS_EVIDENCE` with radius and the source's instruction to uncheck "Reach more people likely to respond", age `NEEDS_EVIDENCE`, detailed targeting EMPTY, placements `Advantage+ Placements`.

    - Ads: 5–7 ads, each with Page (`NEEDS_EVIDENCE`), Instagram profile, website URL = the verified landing-page URL (`NEEDS_EVIDENCE`), display link, creative asset reference, primary text variants, 3–4 headlines, CTA `Learn More`, Advantage+ creative enhancements reviewed manually.

    - Publish rule: publishing must happen at **campaign level**, not ad level — and **this build does not publish.** The human checklist owns that step.

1. **UTM builder.** `tools\utm_builder.py` → `out\test_urls.txt`. Given the landing-page URL, append realistic dummy values for `fbclid`, `fbc`, `fbp`, `utm_source=facebook`, `utm_medium=paid_social`, `utm_campaign`, `utm_content`, `utm_term`. Emit 3 variants plus a no-parameter control URL (the control is expected to NOT fire a conversion). Mark every URL **TEST DATA — not for production traffic**.
1. **Launch review.** `src\launch_review.py` → `out\launch_review.md` + `out\asset_register.md`. Package: every generated asset with path and status, the campaign preview pack, the exact budget exposure (`0` until approved), the workflows, the tests, the pixel/CAPI state, the onboarding/booking destination `https://ca-jenterprises.com/ai`, and an explicit list of unavailable capabilities.
1. **Compliance scan.** `tools\compliance_scan.py` runs all guardrails over every generated `.md`, `.json` and `.html` and fails on any hit: a real secret/token pattern; `CAJ_HVAC27_US_PURCHASE_TEST02` used as a target; a CA-J price in message or ad copy; a lowercased or wrong `GHL` location ID; the unverified location ID `nuhFUYu0ZF9Eswiz9P79`; an asserted-but-unverified result (testimonial, review count, client outcome, ROI); a non-zero budget without an approval reference. Per-file report.
1. **Tests.** `tools\run_tests.py` → `out\tests\test_log.md` and `T01…T14.json`, each with `test_id, input, expected_result, actual_result, evidence_path, verdict` where verdict ∈ `PASS | FAIL | BLOCKED`. Cases:
    T01 Static mock opens; every CTA scrolls to the form; no external script loads.

    T02 Form spec matches the built HTML field-for-field; consent disclosure present.

    T03 Thank-you page carries the booking CTA to `https://ca-jenterprises.com/ai`.

    T04 Workflow 01 spec has all 6–7 touchpoints, correct waits, and the final `Lost` move.

    T05 Workflow 02 removes the contact from Workflow 01 before any further send.

    T06 Workflow 03 event type / event / mapping / currency match `capi_settings.json`.

    T07 No merge token is asserted as valid GHL syntax; all are flagged for field-picker insertion.

    T08 Pixel and access token are referenced by env var name only; no value present in any file.

    T09 Campaign JSON is a draft with campaign-level budget OFF and ad-set budget `NEEDS_EVIDENCE`.

    T10 Exact-case assertion on `UWc5vKBgFVPdxNTRAy2s` and rejection of the unverified location ID `nuhFUYu0ZF9Eswiz9P79`; booking URL literal equals `https://ca-jenterprises.com/ai`.

    T11 No ad copy or creative record contains a CA-J price, guarantee, scarcity, or client outcome.

    T12 `assert_logo_not_first()` passes on all creative records; every `opening_element` is an outcome or offer.

    T13 Test URLs carry all expected parameters and the control URL carries none.

    T14 Rollback: a new campaign pauses, affected workflow stops, prior config recoverable.

    Any case requiring a live account or a UI action is recorded `BLOCKED` with the exact missing input. A failure in form→CRM sync, pixel/CAPI configuration, permission handling or routing blocks the affected live component.

1. **UI checklists.** Write `ui-tasks\META-CHECKLIST.md` (Business Portfolio, ad account, Page/IG connection, Pixel/Dataset, CAPI token, campaign/ad-set/ads, publish) — **beginning with a top-of-file warning block that `CAJ_HVAC27_US_PURCHASE_TEST02` is FROZEN and must not be edited, paused, or duplicated, because editing resets Meta's learning phase.** Budget lines are marked `REQUIRES EXPLICIT HUMAN APPROVAL`. `ui-tasks\GHL-CHECKLIST.md` (sub-account, AI Studio activation, pipeline, workflows, field mapping, A2P). `ui-tasks\AI-STUDIO-CHECKLIST.md` (prompt to paste, the seven iteration prompts, connect-form-to-CRM step, publish). `ui-tasks\DNS-CHECKLIST.md` (CNAME record spec with `Type=CNAME`, `Host=<subdomain>`, `Value=NEEDS_EVIDENCE` — the source's `vibe.cloud` is unverified — plus propagation wait, verify, publish, and a prominent **DOMAIN PURCHASE REQUIRES EXPLICIT HUMAN APPROVAL** gate). Every item names the exact object, field and value.
1. **README.** Write `build\04-fb-ai-studio\README.md`: what the build produces, that everything is draft-only, that no Meta/GHL/domain/DNS/payment object was touched, the run order, and the exact local commands (`python tools\build_all.py`, `python tools\run_tests.py`, `python tools\compliance_scan.py`).
1. **Run and verify.** Write `tools\build_all.py` (idempotent, dependency-ordered, logs to `logs\build.log`). Execute `python tools\build_all.py`, then `python tools\run_tests.py`, then `python tools\compliance_scan.py`. Confirm every file in section 4 exists, the validator exits 0, and the compliance scan is clean. **Do not report success for anything you did not actually run.**

## 6. Configuration & Constants

`config\constants.py`:

`OWNER_NAME            = "Chuck Ashley"
OWNER_PHONE           = "512-229-9199"
OWNER_EMAIL           = "chuck@ca-jconsulting.com"
LEGAL_ENTITY          = "CA&J Enterprises LLC"
GHL_AGENCY_URL        = "https://app.gohighlevel.com"
GHL_LOCATION_ID       = "UWc5vKBgFVPdxNTRAy2s"   # CASE-SENSITIVE. The ONLY build location.
GHL_PIPELINE_ID       = "U95kdMryqjDqu7JeFrdw"    # existing "CA&J Demo - Lead Pipeline" — do not overwrite
GHL_PIPELINE_STAGES   = ["New Lead","Contacted","Appointment Booked","Quote Sent","Job Won","Lost / Not a Fit"]
GHL_FUNNEL_ID         = "5WjNmZXpaD1tXVzvgRzn"    # CA-J Appointment Engine
GHL_OFFER_PAGE_ID     = "3R0KG1iCnpPCBDwLTgTT"
NEW_PIPELINE_NAME     = "Meta Ads Leads"          # separate from the existing pipeline
BOOKING_URL           = "https://ca-jenterprises.com/ai"
DOMAIN_OFFER_SLUG       = "offer"                 # offer.<domain>
DOMAIN_CALL_SLUG        = "call"
DOMAIN_CONTACT_SLUG     = "contact"
CNAME_VALUE           = "NEEDS_EVIDENCE"          # source says vibe.cloud; unverified
TECH_FEE_MONTHLY_USD  = 650      # locked
SETUP_FEE_USD         = 0        # locked: waived
PER_APPOINTMENT_MIN_USD = 150    # locked
PER_APPOINTMENT_MAX_USD = 300    # locked
QUOTE_PRICE_IN_MESSAGE = False   # MEETING-FIRST: no price in email, chat or AI reply
FROZEN_CAMPAIGN_NAME  = "CAJ_HVAC27_US_PURCHASE_TEST02"
FROZEN_CAMPAIGN_PROTECTED = True # never edit / pause / duplicate-in-place; new work = separate NEW draft
NEW_CAMPAIGN_NAME_PATTERN = "CAJ-FB-HVAC-Leads-{YYYYMMDD}-DRAFT"
LOGO_NEVER_FIRST      = True     # creatives lead with outcome/offer; logo = small footer disclaimer only
NO_SPEND_DEFAULT      = True
AD_SPEND_CAP_USD      = 0        # stays 0 until a human authorizes an exact amount in writing
DAILY_BUDGET_USD      = "NEEDS_EVIDENCE"   # source's $70/day is instructor guidance, not authority
APPROVAL_AD_SPEND     = False
APPROVAL_LAUNCH       = False
APPROVAL_DOMAIN_PURCHASE = False
LAUNCH_AUTHORITY      = "none"
BUILD_MODE            = "CAJ_HVAC"
NEEDS_EVIDENCE        = "NEEDS_EVIDENCE"
DISALLOWED_LOCATION_ID = "nuhFUYu0ZF9Eswiz9P79"
REQUIRED_IMAGE_DIMENSIONS = (1080, 1080)
MAX_VIDEO_SECONDS     = 30
ABSOLUTE_MAX_VIDEO_SECONDS = 60
CAPI_EVENT_TYPE       = "Funnel Event"
CAPI_EVENT_TO_SEND    = "Lead"
CAPI_CUSTOM_MAPPING   = "OFF"
CAPI_CURRENCY         = "USD"`

`config\build_config.json` keys (value `NEEDS_EVIDENCE` unless set above): `build_mode, business_name, primary_location, service_areas, primary_service, additional_services, main_offer, offer_expiration, primary_cta, phone, avg_response_time, est_service_time, years_in_business, customers_served, review_rating, review_count, guarantee, usp, main_pain_points, desired_outcomes, brand_colors, logo_path, hero_image_path, before_after_images, landing_page_url, facebook_page_id, ad_account_id, instagram_profile_id, pixel_id, dataset_id, ghl_project_name, ghl_form_name, a2p_status, privacy_policy_url`.

`.env.example` — names only, empty values:

`# Never commit real values. Copy to .env and fill locally.
GHL_API_KEY=
GHL_LOCATION_ID=
GHL_PIPELINE_ID=
META_BUSINESS_PORTFOLIO_ID=
META_AD_ACCOUNT_ID=
META_PAGE_ID=
META_ACCESS_TOKEN=
META_PIXEL_ID=
META_DATASET_ID=
META_CAPI_ACCESS_TOKEN=
LANDING_PAGE_URL=
PRIVACY_POLICY_URL=
OWNER_PHONE=
OWNER_EMAIL=
APPROVAL_AD_SPEND=
APPROVAL_LAUNCH=
APPROVAL_DOMAIN_PURCHASE=
AD_SPEND_CAP_USD=
DAILY_BUDGET_USD=`

**Rules:** no real secret, token, key, password, pixel ID or dataset ID value may be written into any spec, config, output, log or HTML mock — env var names and `.env.example` only. GHL IDs are case-sensitive and must carry exact case. Any dollar figure the source supplies and section 6 does not lock goes into the output's blocker section as unverified, never into a target.

## 7. Acceptance Criteria

- [ ] Y/N — `build\04-fb-ai-studio\` exists with every path in section 4 present.
- [ ] Y/N — `python tools\validate_config.py` exits 0.
- [ ] Y/N — `python tools\compliance_scan.py` exits 0 with zero hits.
- [ ] Y/N — `config\constants.py` contains `GHL_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"` in exact case.
- [ ] Y/N — the string `nuhFUYu0ZF9Eswiz9P79` appears nowhere except as `DISALLOWED_LOCATION_ID` in the rejection list.
- [ ] Y/N — the string `CAJ_HVAC27_US_PURCHASE_TEST02` appears only in the guard constant, the `META-CHECKLIST.md` warning banner, and this spec — never as a target, duplicate source, or edit target.
- [ ] Y/N — `AD_SPEND_CAP_USD` is `0`, `DAILY_BUDGET_USD` is `NEEDS_EVIDENCE`, and the committed campaign JSON is marked draft/unpublished.
- [ ] Y/N — no file contains a real pixel ID, dataset ID, access token, API key or password; all are referenced by env var name.
- [ ] Y/N — `out\landing\index.html` opens standalone, loads no external script, and displays the "STATIC CONTENT MOCK" banner.
- [ ] Y/N — no testimonial, review count, client count, years-in-business figure, or client outcome was invented; each is `NEEDS_EVIDENCE` or omitted.
- [ ] Y/N — `assert_no_price_in_message()` passes on all ad copy, SMS templates, form copy and message files.
- [ ] Y/N — `assert_logo_not_first()` passes on all creative records.
- [ ] Y/N — `out\campaign_spec.md` places budget at ad-set level with campaign-level budget OFF, and states the campaign is a NEW draft.
- [ ] Y/N — `out\tests\test_log.md` contains exactly T01–T14 with verdicts in {PASS, FAIL, BLOCKED}; no BLOCKED case is reported as passing.
- [ ] Y/N — every UI-dependent item is in `ui-tasks\` and none is marked `Live` or `Ready for launch` by any script.
- [ ] Y/N — `ui-tasks\DNS-CHECKLIST.md` marks domain purchase as requiring explicit human approval.
- [ ] Y/N — `ui-tasks\HUMAN-DECISIONS.md` lists every `NEEDS_EVIDENCE` value with a next action and an owner.
- [ ] Y/N — `README.md` states that nothing was launched and no Meta/GHL/domain/DNS/payment object was touched.

## 8. Blockers & Unverified Items

The spec must NOT assume any of the following:

1. **Nothing in the source has been built.** Every phase in the SOP is unexecuted. No sub-account, landing page, workflow, pixel, CAPI event, or campaign exists.
1. **The entire SOP is UI-only.** Its "execution checklist for automation" block mislabels browser steps as a code task list. The correct reading is: almost every step requires a logged-in human. Claude Code produces specs, mocks and checklists only.
1. **The frozen campaign is untouchable.** `CAJ_HVAC27_US_PURCHASE_TEST02` must never be edited, paused, or duplicated in a way that touches the original — editing resets Meta's learning phase. Any new campaign is a SEPARATE new draft. This build activates and publishes nothing.
1. **No spend.** Ad budget, payment methods, domains, subscriptions, tools and upgrades all require **explicit written human approval**. The source's `$70/day` (and $50/60/100) is instructor guidance, not authority. `AD_SPEND_CAP_USD` stays `0`.
1. **The source's offer examples are not CA-J offers.** "$100 discount on first service", "$49 drain cleaning", "50% off first visit" are tutorial examples. CA-J's agency pricing is locked ($650/mo tech fee, setup waived, $150–$300 per qualified appointment) and under the MEETING-FIRST rule must never appear in an email, chat, ad, or AI agent reply.
1. **The worked example is a different business.** Junk removal in Cary, North Carolina is not CA-J's ICP. All example content must be re-derived, and CA-J's own location, service area, Page, ad account, brand colors, logo files, hero images, before/after images and review data are all `NEEDS_EVIDENCE`.
1. **The Google Doc mega prompt was never supplied.** The AI Studio landing-page prompt (the "Alex Hormozi framework") cannot be reproduced. Do not attempt to fetch it or fabricate its contents. Build a placeholder-fill script with `NEEDS_EVIDENCE` for the missing template body.
1. **AI Studio availability is unverified.** `Settings → Labs → AI Studio` may not exist on the CA&J agency account. Embedded calendar booking for Facebook lead forms, conditional form endings, and multi-page lead sync are likewise unverified capabilities — each needs account-level confirmation before it is relied on.
1. **The CNAME target is unverified.** The source's `vibe.cloud` comes from a video screen. Do not write it as a confirmed value.
1. **Performance claims are unverified.** "100% lead tracking", "high-converting AI Studio pages", "creatives ARE the targeting (Andromeda)", "longest-running ads are winners", and every CPL/CTR/CPC expectation are industry claims or heuristics. No CA-J performance target exists; any figure is `NEEDS_EVIDENCE`.
1. **CAPI has known silent-failure modes.** A submission without Facebook parameters will not be marked a Facebook lead and will not fire a conversion — that is correct behaviour, not a defect. CAPI also fails outright if the subdomain is not connected or the form is not natively connected to GHL. Do not claim CAPI is working; only a human reading Execution Logs can.
1. **Messaging permission and delivery are unverified.** A2P 10DLC status for the GHL number is unknown; SMS sends may fail entirely. Require an email fallback. All sends need valid channel permissions; suppress opted-out channels. Never bulk-message a list.
1. **Merge tokens are unconfirmed.** `{{contact.full_name}}`, `{{service_needed}}`, `{{message.body}}` and similar are content placeholders, not verified GHL syntax. A human must insert fields with the field picker and send previews before any workflow is published.
1. **Ad rejection risk.** Headlines containing "Google" or "Facebook" risk rejection per the source. Review before publish. Advantage+ creative enhancements may generate odd variations and must be reviewed manually — the source says never follow all Meta recommendations blindly.
1. **Special Ad Category / compliance.** The source gives no rule for determining Special Ad Category. Determine it from the actual campaign and current platform prompts; mark `NEEDS_EVIDENCE`.
1. **Attribution gaps.** Available pixel/CAPI fields, matching settings and attribution windows in the live accounts are unknown. Where a field is unavailable, record the limitation — never invent attribution.
1. **Scope conflict.** Do not let this campaign touch, duplicate, or shadow the frozen live campaign, and do not replace or merge any existing CA-J offer or funnel. Do not overwrite the existing pipeline `CA&J Demo - Lead Pipeline` (`U95kdMryqjDqu7JeFrdw`).

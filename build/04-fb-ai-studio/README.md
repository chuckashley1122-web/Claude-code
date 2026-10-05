# SPEC-04 build: Facebook Ads + GHL AI Studio (draft asset package)

This folder builds, as plain files on disk, everything needed to review a Facebook Leads campaign that feeds a
GoHighLevel AI Studio landing page for CA-J Enterprises' HVAC-owner audience. Everything is a draft.

**Nothing was launched. No Meta, GHL, domain, DNS or payment object was touched.** The build makes no network calls,
spends nothing, and has no credentials. The protected live Meta campaign stays frozen: its name lives only in
`config/constants.py` (`FROZEN_CAMPAIGN_NAME`) and in the warning banner of `ui-tasks/META-CHECKLIST.md`, and a tested
tripwire (`tools/guardrails.py` + `tools/meta_gateway.py`) refuses any operation that names it, in any spelling.

## What it produces

| Area | Output |
|---|---|
| Offer | `out/offer.md` - free, no-obligation strategy session booked at https://ca-jenterprises.com/ai; no price before the call |
| Landing page | `out/landing/content_spec.md/.json`, static mocks `index.html` + `thank-you.html`, `ai_studio_prompt_pack.md` |
| GHL | `out/pipeline_spec.md`, `out/pipeline.json`, workflow specs 01-03 in `out/workflows/`, messages in `out/messages/` |
| Tracking | `out/pixel_capi_spec.md`, `out/capi_settings.json` (env var names only), `out/test_urls.txt` (TEST DATA) |
| Ads | `out/ads/angles.md/.json`, copy `out/ads/copy/A01..A04.md`, briefs `out/ads/creative_specs.md` |
| Campaign | `out/campaign_spec.md`, `out/campaign_config.json` - a NEW draft named `CAJ-FB-HVAC-Leads-<YYYYMMDD>-DRAFT`, campaign budget OFF, ad-set budget NEEDS_EVIDENCE |
| Review | `out/launch_review.md`, `out/asset_register.md`, `out/tests/test_log.md` + `T01..T14.json`, `out/compliance_report.md` |
| Human tasks | `ui-tasks/*.md` and `../../ui-work-orders/004-*.md` |

Every ad leads with a pain or an outcome, never the logo (the logo is a small footer mark only). No price appears in
any ad, SMS, email, form or AI reply; pricing questions route to https://ca-jenterprises.com/ai.

## Run order

From this folder (Windows uses `python`, Linux uses `python3`):

```
python tools/validate_config.py    # hard checks on IDs, caps, gates; exits non-zero on any failure
python tools/build_all.py          # idempotent, dependency-ordered; logs to logs/build.log
python tools/run_tests.py          # T01-T14 -> out/tests/ (PASS / FAIL / BLOCKED)
python tools/compliance_scan.py    # scans every generated .md/.json/.html/.txt; exits 1 on any hit
python -m unittest discover -s tests   # unit + end-to-end tests (stdlib unittest)
```

`out/`, `logs/` and `config/decision_log.jsonl` are generated and git-ignored; rebuild them with the commands above.

## Spend items (all blocked; approval required)

| Service | What it is for | Approval | Cost |
|---|---|---|---|
| Meta ad spend (campaign daily budget) | Delivering the NEW draft Leads campaign once approved | approval required | NEEDS_EVIDENCE |
| Meta ad account payment method | Required by Meta before any ad can deliver | approval required | NEEDS_EVIDENCE |
| Domain purchase (registrar) | Domain for the offer./call./contact. landing-page subdomain | approval required | NEEDS_EVIDENCE |
| GoHighLevel sub-account / AI Studio access | Hosting the landing page, form, pipeline and workflows | approval required | NEEDS_EVIDENCE |
| A2P 10DLC registration for the GHL number | Sending the speed-to-lead SMS sequence and owner SMS alerts | approval required | NEEDS_EVIDENCE |
| GHL SMS / email usage | Per-message sending for the follow-up sequence | approval required | NEEDS_EVIDENCE |
| AI image / video generation tool | Producing the 1080x1080 images and 30-second videos from the creative briefs | approval required | NEEDS_EVIDENCE |

`AD_SPEND_CAP_USD` is 0 and `DAILY_BUDGET_USD` is NEEDS_EVIDENCE. The source's daily-budget figures are instructor
guidance, not authority.

## Connector design

`tools/meta_gateway.py` defines a `CampaignGateway` interface with two implementations:
`LocalDraftGateway` (offline; stores the draft as JSON under `out/drafts/`, supports a local pause and restore for the
rollback rehearsal, always refuses to publish) and `LiveMetaGateway` (refuses every call with `LiveCallBlocked`). Both
run the frozen-campaign tripwire first.

## Known limits

- T14 (rollback) is BLOCKED: pausing a live campaign and stopping published workflows needs a logged-in human. The
  local rehearsal (pause, restore prior config, tripwire, publish refusal) runs and is recorded as evidence.
- Evidence-gated facts (review count/rating, years in business, customers served, offer expiration, guarantee) are
  rejected by `validate_config.py` while set. Using one later is a human decision: attach evidence and remove the key
  from `EVIDENCE_GATED_KEYS`.
- Real page/ad-account/pixel/dataset IDs and the CAPI token belong in a local `.env` only (see `.env.example`).

## Deviations from spec

1. **Interpreter.** The spec says `python`; commands here work with either `python` or `python3` and no code hardcodes
   an interpreter.
2. **Generated outputs are git-ignored** (`out/`, `logs/`, `config/decision_log.jsonl`) per the build rules; the spec
   lists them in the tree. They are regenerated by `tools/build_all.py`.
3. **Opening element: pain or outcome only.** The spec allows "outcome or offer"; the build instruction narrowed it to
   pain or outcome, so the Offer angle (A04) opens with the outcome and presents the free session second.
4. **Follow-up cadence.** The spec lists "wait 1 day; SMS 3; then day 3, 7, 10, 14" alongside six SMS files. The build
   uses six SMS on Day 1 (+1 min), Day 1 (+2 h), Day 3, Day 7, Day 10, Day 14 (the source's stated cadence), then wait
   1 day and move to Lost.
5. **"Seven iteration prompts"** = the source's six STEP 2.3 changes (verbatim) plus the STEP 2.4 connect-form-to-CRM
   prompt. The pixel-install prompt is documented in `out/pixel_capi_spec.md`.
6. **Extra files beyond §4:** `src/common.py`, `src/ui_checklists.py` (writes `ui-tasks/` and the 004 work orders),
   `tools/meta_gateway.py`, `tests/`, `out/blockers.json`, `out/drafts/`, `out/compliance_report.md`.
7. **Unknown landing URL.** Test URLs use the `https://offer.example.com/` placeholder until `landing_page_url` is set.
8. **Ad location callout** uses a `[LOCATION]` placeholder because the target market is NEEDS_EVIDENCE.
9. **`main_offer` / `primary_cta` / `business_name` / `phone`** are set in `build_config.json` from SPEC-04 step 7 and
   the public contact rules; every other key is NEEDS_EVIDENCE.

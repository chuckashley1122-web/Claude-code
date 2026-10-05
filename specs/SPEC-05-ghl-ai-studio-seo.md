# GHL AI Studio SEO + Full Stack

# SPEC-05 — GHL AI Studio SEO + Full-Stack Site Build

**Executor:** Claude Code / Claude Cowork, headless (`claude -p`).

**Capabilities assumed:** filesystem read/write, shell commands, Python 3.11 via `python` (NOT `python3`). **No browser. No UI logins. No authenticated session on any dashboard.**

**Repo root:** `C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system\`

**Host:** Windows 11. Shell is bash (MSYS). Inline heredoc and oversized one-liner shell commands are BLOCKED — write every script to a `.py` file, then run `python <file>`.

**Execute top to bottom. Do not ask questions. Where a value is unknown, write the literal string `NEEDS_EVIDENCE` and continue.**

## 1. Source & Provenance

- **File read:** `C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system\playbooks\05-ghl-ai-studio-seo.md`
- **Size:** 27,928 characters, 265 lines, 28,250 bytes on disk (CRLF line endings). Read in full; not truncated. 29 non-ASCII characters (bullets, em-dashes, curly quotes) — no encoding anomaly.
- **What the source actually is:** an AI-generated implementation plan dated 2026-09-13, titled *"GHL AI Studio SEO and Full Stack Implementation — Step by step action plan for the Hermes agent,"* prepared for Chuck Ashley / CA-J Enterprises. It is derived from a **supplied transcript** of a YouTube video by presenter **Dominic Baptist** (`https://www.youtube.com/watch?v=LlqaA96b6qE`), transcript coverage opening → 23:13. It contains 36 numbered steps, 7 prompts, a master instruction block, a 14-row acceptance-test matrix, and a required final-status format.
- **It is authored guidance, not a platform contract.** The source states in its own §10 that the route plan, prompts, inquiry-endpoint contract, validation bounds, timeout/retry recommendations, idempotency policy, test matrix, release criteria and handoff template are *"authored implementation guidance… not claimed as verbatim instructions from the presenter."*
- **It is a plan, not a record.** Source: *"This document does not mean that any account or website has already been changed."* No GHL project, route, page, form, server function, secret, CRM record, version ID or published site described in it is claimed to exist.
- **Code, schemas and pricing formulas were NOT supplied.** The revised 20-prompt playbook, the exact migration prompt, production code, API schemas and pricing formulas referenced in the video are all absent (`NEEDS_EVIDENCE`).
- **No paid tool is prescribed.** The source references only Google Search Central documentation and (post-launch) Search Console — both free. It prescribes **no** paid SEO tool, subscription, domain purchase or any other spend. Its promotional sections are explicitly excluded from build scope. **Therefore no paid-tool workaround is needed and no paid tool may be substituted.**
- **The source is overwhelmingly UI-only.** Steps 1–5, 9, 21–26 and 33–36 are instructions to open a logged-in GHL account, inspect DNS, publish a version, submit a browser form, or read Search Console. The source's own Step 1 names location `nuhFUYu0ZF9Eswiz9P79` as *"the previously used location"* — that is **not** the CA-J build location. The only permitted GHL build location is `UWc5vKBgFVPdxNTRAy2s` (case-sensitive). Do not reconcile or equate the two.
**Claims in the source that are NOT verified — never encode these as targets, constants, or completed steps:**

| # | Claim / item in the source | Status |
|---|---|---|
| S1 | Visual UI details (menu labels, buttons, screens, control names) from the video | **Unverified.** Source: *"Video page access failed during preparation; no visual UI details are asserted as independently verified."* Every UI label is `NEEDS_EVIDENCE`. |
| S2 | An official HighLevel announcement titled "AI Studio Introducing SSR plus Server Functions plus Secrets" | **Unverified** as a capability of the CA-J account or of any existing project. Search surfaced only a root-domain result. |
| S3 | The existing CA-J project supports the new SSR runtime / server functions / secrets vault | **Unverified.** Source: *"Do not assume new-project capabilities automatically migrate old projects."* |
| S4 | SSR produces SEO benefit | Source's own correction: SSR *"does not guarantee indexing, rankings, or speed."* No ranking, traffic, speed or CPL target exists anywhere. |
| S5 | A secrets vault protects credentials / establishes compliance | Source correction: *"It does not automatically protect all customer data or establish compliance."* |
| S6 | Named external integrations exist and are connectable | Source: *"their names in the video are not proof that a connection exists."* |
| S7 | `POST /api/inquiries`, the field list, the 120 / 2,000 / 16 KB bounds, the 10 s timeout, the 24 h idempotency window, the status-code map | Source calls this *"an original implementation specification, not an endpoint or code sample supplied by the video."* Authored guidance. |
| S8 | Austin / Round Rock as location priorities; the seven suggested routes | Source-proposed, **not approved CA-J business facts.** Carry as `PROPOSED_NOT_APPROVED`. |
| S9 | The estimator model (`subtotal = materials + labor + equipment + travel`, sod example) | *"illustrative only and must not substitute for supplied commercial rules."* |
| S10 | Other video examples (HVAC dispatch, invoices, roofing materials, restaurant orders, travel fees, portals, provisioning) | Out of scope. *"Their appearance in the video does not make them prerequisites for this build."* |
| S11 | Any Search Console property, analytics tag, DNS record, domain, project ID, version ID or restore mechanism | Unknown. `NEEDS_EVIDENCE`. |
| S12 | The "20-prompt playbook revision" referenced at 15:26–17:30 | **Never supplied.** Do not attempt to fetch or reconstruct it. |

**Rule:** no unverified item above may appear as a target, a constant value, or a completed step. Unverifiable values are written `NEEDS_EVIDENCE` or `unverified`. Numbers from the source are not CA-J results.

## 2. Objective

Produce a complete, draft-only, reviewable build package for an SEO-ready CA-J Enterprises website plus a server-processed inquiry flow — entirely as files on disk, generated by Python scripts into one fixed output tree — containing: the verified-business-facts register and route/intent inventory; substantive page copy per route; a unique metadata set (title, description, canonical, social preview) with a uniqueness validator; JSON-LD structured data built **only** from verified facts and refusing to emit anything it cannot source; `sitemap.xml`, `robots.txt`, an indexability plan and a 301 redirect map; a self-contained static HTML mock of every route plus a 404 and thank-you page for offline content review; a paste-ready AI Studio prompt pack; the inquiry contract expressed as data plus a **working, locally-tested** reference implementation of server-side validation, idempotency, truthful status mapping, PII redaction and bounded upstream retry; a paste-ready server-function source file; a GHL adapter that is a hard `NotImplementedError` stub (never a guessed integration); a secret-exposure scanner; the source's 14-row acceptance matrix executed as a test log with PASS/FAIL/BLOCKED verdicts and evidence paths; a release package with rollback instructions and the source's required final-status format; and one UI work order per step that requires a browser. Nothing is deployed, published, messaged, or purchased by this build — every such step is emitted as a human checklist with exact values.

## 3. Code-Layer vs UI-Layer Split

Strict. Claude Code has no browser and no authenticated session. It **cannot** operate GoHighLevel, GHL AI Studio, the GHL secrets vault, a DNS registrar, Search Console, Analytics, or Meta Ads Manager. Everything in the right column ships as a markdown work order with exact object names, fields and values, and is **never** reported as done.

| Claude Code CAN build (files + shell + Python) | Needs browser / logged-in account / human |
|---|---|
| Directory scaffold, `constants.py`, `build_config.json`, `.env.example`, decision log, asset register | Locating the actual "AI Studio" product in the GHL interface; confirming it exists on the CA&J account at all |
| Config validator asserting house facts and rejecting the disallowed location ID | Confirming whether the existing project supports SSR + server functions + secrets; creating a compatible new draft if not |
| Guardrail module: no-spend, no-price-in-message, logo-never-first, frozen-campaign, no-fabricated-review, canonical-uniqueness | Duplicating the project / saving a recovery point / recording version and restore IDs |
| Verified-business-facts register where every claim carries an evidence link and every unknown is `NEEDS_EVIDENCE` | Collecting the real business facts (services, coverage areas, logo, photos, approved claims) |
| Route/intent inventory as JSON + markdown (audience, intent, topic, title, H1, canonical, CTA, proof, internal links) | Reading the existing site's live routes, titles, redirects and conversion flows |
| Page content model per route with a thin-content / similarity detector that **refuses** near-identical city pages | Authoring/approving the substantive copy and the evidence for each claim |
| Metadata set + uniqueness validator (duplicate title/description/canonical detection) | Entering titles/descriptions/canonicals in AI Studio per page |
| JSON-LD builder that refuses to emit `aggregateRating`, reviews, address or hours it cannot source | Validating rendered structured data against a live URL |
| `sitemap.xml`, `robots.txt`, per-route indexability plan, 301 redirect map (as files) | Uploading the sitemap, setting per-page noindex, configuring host-level redirects |
| Static HTML mock of every route + `404.html` + `thank-you.html`, self-contained, openable as `file://` | Publishing any page; domain mapping; DNS records; HTTPS |
| Paste-ready AI Studio prompt pack (source Prompts 1–7 transcribed + placeholder-fill block) | Pasting them, iterating the page, building the routes in AI Studio |
| Inquiry contract as data: allowlist, bounds, status map, timeout, retry policy, idempotency retention | Any server-function deployment or runtime observation |
| **Working** server-side validation/normalization library (pure Python, unit-tested) | Confirming real CRM field IDs, pipeline ID, stage ID, scopes, API version, endpoint |
| File-backed idempotency store (24 h retention) with replay-returns-prior-outcome semantics, tested | Creating GHL custom fields; connecting the form to GHL; building automations |
| Reference inquiry handler: truthful state strings, bounded timeout, retry same `submission_id`, no retry on validation/permission errors, PII redaction | Reading server logs; reading the deployed function's real behaviour |
| `out\server_functions\inquiry.ts` — paste-ready server function, secrets read from env by name only | Creating the secrets in the vault; confirming the deployed server can read them |
| GHL adapter as `NotImplementedError` + clearly-labelled `MOCK` adapter for local tests | Any real GHL API call against the CA&J location |
| Secret-exposure scanner and PII-in-log scanner over every generated file | Rotating a credential that was exposed |
| 14-case acceptance matrix runner with PASS/FAIL/BLOCKED + evidence paths; stdlib `unittest` suite | Submitting a synthetic inquiry in the browser and finding the contact in the GHL UI |
| Release package with rollback instructions and the source's required final-status format | Publishing a version; restoring a prior version |
| All UI checklists with exact object names, fields and values; human-decision queue | Search Console verification, sitemap submission, indexing inspection, analytics tag changes |
| Nothing that costs money, ever | **Any purchase or spend** — domain, upgrade, subscription, SEO tool, ad spend: STOP, print the dollar amount, require explicit written human approval. This build spends **$0**. |
| Nothing that touches Meta | **Any Meta object.** `CAJ_HVAC27_US_PURCHASE_TEST02` is FROZEN — never edited, paused, or duplicated-then-deleted; editing resets Meta's learning phase. **STRIPE is connected to that ad account**, so any budget change is a real financial action. Tracking/UTM work is out of scope; if ever proposed it is a SEPARATE NEW DRAFT and still may not touch the frozen campaign. |

**Hard prohibitions:** no publishing, no live write, no send, no spend, no Meta edit, no secret in a file, no invented business fact, no estimated performance target. Where the source says "publish", "submit", "verify in Search Console" or "test in the browser", this spec writes a work order instead.

## 4. Deliverable File Tree

All paths relative to `build\05-ghl-ai-studio-seo\` under the repo root. Nothing outside this directory is written.

`build\05-ghl-ai-studio-seo\
├─ README.md                                    # What was built; that nothing was published/deployed; run commands
├─ .env.example                                 # Env var NAMES only. Empty values. No real secret anywhere.
├─ config\
│  ├─ constants.py                              # House facts, IDs, guard flags, locked pricing, contract bounds
│  ├─ build_config.json                         # Single source of truth; unknowns = "NEEDS_EVIDENCE"
│  ├─ business_facts.json                       # Every claim with an evidence source or NEEDS_EVIDENCE
│  ├─ route_inventory.json                      # Per-route intent, title, H1, canonical, CTA, indexability
│  ├─ decision_log.jsonl                        # Append-only: timestamp, key, value, source, status
│  └─ asset_register.json                       # Every generated asset: id, path, status, owner
├─ tools\
│  ├─ state.py                                  # Status enum, decision-log writer, blocker recorder, asset marker
│  ├─ guardrails.py                             # no-spend / no-price / logo-not-first / frozen-campaign / no-fabricated-fact
│  ├─ validate_config.py                        # Hard assertions on IDs, URLs, caps, approvals
│  ├─ fetch_raw_html.py                         # Zero-cost, unauthenticated, JS-off HTML GET → evidence JSON
│  ├─ baseline_inventory.py                     # Status/title/H1/canonical/redirect inventory over a URL list
│  ├─ secret_scan.py                            # Secret-name and secret-value scan over every generated file
│  ├─ compliance_scan.py                        # Runs all guardrails over every generated .md/.json/.html/.ts/.py
│  ├─ build_all.py                              # Idempotent, dependency-ordered orchestrator → logs\build.log
│  └─ run_tests.py                              # Unit suite + T01–T14 matrix → out\tests\
├─ src\
│  ├─ business_facts.py                         # → config\business_facts.json, out\business_facts.md
│  ├─ page_plan.py                              # → config\route_inventory.json, out\route_inventory.md
│  ├─ content_pages.py                          # → out\pages\<route>.md  (refuses thin/duplicate city pages)
│  ├─ metadata.py                               # → out\metadata.json, out\metadata.md
│  ├─ structured_data.py                        # → out\structured_data\<route>.json (refuses unsourced fields)
│  ├─ seo_files.py                              # → out\seo\sitemap.xml, robots.txt, indexability.md
│  ├─ redirect_map.py                           # → out\seo\redirect_map.json, out\seo\redirect_map.md
│  ├─ site_mock.py                              # → out\site\<route>.html, 404.html, thank-you.html
│  ├─ ai_studio_prompts.py                      # → out\ai_studio_prompt_pack.md
│  ├─ inquiry_contract.py                       # → out\inquiry_contract.md, out\inquiry_contract.json
│  ├─ inquiry_handler.py                        # Server-side logic + → out\server_functions\inquiry.ts
│  ├─ ghl_adapter.py                            # NotImplementedError stub + labelled MOCK adapter
│  ├─ estimator.py                              # OPTIONAL phase 2. Disabled by default. → out\estimator\
│  ├─ acceptance_matrix.py                      # → out\tests\test_log.md, T01.json … T14.json
│  └─ release_package.py                        # → out\release_package.md, out\asset_register.md
├─ out\
│  ├─ (all artefacts listed under src\ above, plus:)
│  ├─ site\                                     # Static mocks; openable via file://
│  ├─ server_functions\inquiry.ts               # Paste-ready server function. No secret values.
│  └─ tests\                                    # test_log.md + T01–T14 JSON evidence
├─ ui-work-orders\
│  ├─ 001-ghl-project-inventory-and-backup.md
│  ├─ 002-ai-studio-capability-check.md
│  ├─ 003-ai-studio-pages-metadata-and-structured-data.md
│  ├─ 004-server-function-secrets-deploy.md
│  ├─ 005-ghl-crm-integration-and-field-mapping.md
│  ├─ 006-synthetic-inquiry-end-to-end-test.md
│  ├─ 007-domain-dns-and-publish.md             # Contains the spend gate: domain purchase REQUIRES approval
│  ├─ 008-search-console-and-analytics.md       # Free tools only; logged-in human required
│  └─ HUMAN-DECISIONS.md                        # Every NEEDS_EVIDENCE + every approval gate + owner
└─ logs\
   └─ build.log                                 # Timestamped run log from build_all.py`

## 5. Build Steps

Execute in order. Every step writes its file, appends to `config\decision_log.jsonl`, and records the asset in `config\asset_register.json`.

1. **Scaffold + state layer.** Create the tree in section 4. Write `tools\state.py`: `STATUS` enum = `Not started | Draft | Tested | Ready for human action | Published-by-human | Blocked`; `log(key, value, source, status)`; `record_blocker(item, missing_input, work_affected, next_action)`; `mark_asset(id, path, status)`. No script may ever write a status implying deployment — `Published-by-human` is reserved for a human's manual edit after a real publish, and **no script may set it**.
1. **Constants.** Write `config\constants.py` with every value in section 6, including the guard booleans, the frozen-campaign name, and the disallowed location ID.
1. **Config.** Write `config\build_config.json` with exactly the key set in section 6. Any value not locked in section 6 is `"NEEDS_EVIDENCE"`. Never invent a domain, project ID, form ID, calendar ID, service area, phone number, review count or analytics ID.
1. **Env template.** Write `.env.example`: names only, empty values, with a comment that real values are never committed and that a secret is never pasted into a generated asset, screenshot or log.
1. **Validator.** Write `tools\validate_config.py`. Non-zero exit if any of: `GHL_LOCATION_ID != "UWc5vKBgFVPdxNTRAy2s"` (exact case) · `DISALLOWED_LOCATION_ID` used anywhere as a target · `BOOKING_URL != "https://ca-jenterprises.com/ai"` · `NO_SPEND_DEFAULT != true` · `AD_SPEND_CAP_USD != 0` · `PUBLISH_AUTHORITY != "none"` · `SITE_PUBLISH_APPROVED` true without an approval reference · `DOMAIN_PURCHASE_APPROVED` true without an approval reference · `FROZEN_CAMPAIGN_PROTECTED != true` · `QUOTE_PRICE_IN_MESSAGE != false` · `LOGO_NEVER_FIRST != true` · any inquiry bound missing/inverted (`MAX_NAME_LEN`, `MAX_MESSAGE_LEN`, `MAX_PAYLOAD_BYTES`, `UPSTREAM_TIMEOUT_S`, `MAX_RETRIES`, `IDEMPOTENCY_RETENTION_HOURS`). Print one line per check.
1. **Guardrails.** Write `tools\guardrails.py`. All functions raise on violation, are used by `compliance_scan.py` and `run_tests.py`, and are individually tested in `tests\test_guardrails.py`:
   - `assert_no_spend(item, approval_ref)` — raises unless an explicit written approval reference is supplied. Applies to domains, upgrades, subscriptions, SEO tools, ad spend, payment methods, plan changes. `AD_SPEND_CAP_USD` stays `0`.

   - `assert_no_price_in_message(text)` — raises if any CA-J price appears in page copy, form copy, ad copy, email, SMS, chat or AI-agent reply: `$650`, `650/mo`, any setup fee, `$250`, `$300`, "per booked appointment", "$250 to $300". Booking destination is always `https://ca-jenterprises.com/ai` and is **the only** commercial call to action permitted. Locked pricing lives in `constants.py` for internal reference and is never emitted into a customer-facing string.

   - `assert_logo_not_first(creative)` — raises if the CA-J logo is the first visual element of any hero image, OG image, ad creative or page lead. Creatives lead with the outcome or offer; the logo is a small footer disclaimer only. Applies to every `hero_image` / `og_image` record.

   - `assert_frozen_campaign_untouched(text)` — raises if any generated asset names `CAJ_HVAC27_US_PURCHASE_TEST02` as a target, duplicate source, or edit/pause subject. The only permitted mentions are the constant itself and the warning line in `ui-work-orders\HUMAN-DECISIONS.md`. This build touches no Meta object.

   - `assert_no_fabricated_fact(text, facts)` — raises if copy or JSON-LD asserts a testimonial, review, review count, rating, client count, years-in-business, licence, insurance, office address, response-time promise or result that is not present in `config\business_facts.json` with an evidence source.

   - `assert_canonical_unique(metadata_set)` — raises on duplicate title, duplicate meta description, or duplicate/missing canonical across indexable routes.

   - `assert_not_disallowed_location(text)` — raises if `nuhFUYu0ZF9Eswiz9P79` appears anywhere except the `DISALLOWED_LOCATION_ID` rejection list.

1. **Verified business facts.** `src\business_facts.py` → `config\business_facts.json` + `out\business_facts.md`. One record per claim: `key, value, evidence_source, verified (bool), owner, next_action`. Pre-fill the house facts that are ground truth (owner name, phone, email, legal entity, booking URL, locked pricing — internal only). Everything else is `NEEDS_EVIDENCE` with a blank evidence column: approved business name, real service areas, services, logo file, photos, offer details at `/ai`, licenses, insurance, guarantees, response times, testimonials. **Do not invent offices, testimonials, results, licensing, pricing or response-time promises.** Keep consulting/lending and consumer-brand content (coffee, printables) out — B2B never blends with consumer brands.
1. **Route + intent inventory.** `src\page_plan.py` → `config\route_inventory.json` + `out\route_inventory.md`. Record the source's suggested routes as `PROPOSED_NOT_APPROVED` drafts: `/`, `/services/lead-generation`, `/services/reputation-management`, `/services/paid-advertising`, `/locations/austin`, `/locations/round-rock`, `/about`, `/contact`. Per row: `route, audience, search_intent, primary_topic, title, h1, canonical, cta_destination, supporting_proof, internal_links, indexable, status`. `canonical` = `SITE_ORIGIN + route` where `SITE_ORIGIN` is `NEEDS_EVIDENCE` — emit the field with the marker, do not guess a domain. Add only verified services. Mark that reusing existing URLs is preferred but the existing route list is `NEEDS_EVIDENCE` until `tools\baseline_inventory.py` runs.
1. **Page content.** `src\content_pages.py` → `out\pages\<route>.md`. Each service page carries a distinct problem, process, deliverables, FAQs and one CTA. Location pages must state actual local coverage and contain genuinely city-specific information. **Thin-content guard:** normalized token-overlap between any two page bodies above `THIN_CONTENT_SIMILARITY_MAX` (0.80) raises — the script must refuse to emit, and instead emit a single `service-area` merge record. Never produce near-identical pages by swapping city names.
1. **Preserve the conversion path.** Within `content_pages.py`: assert every main page has exactly one primary action, and the primary CTA destination literal equals `https://ca-jenterprises.com/ai`. Whether `/ai` is the currently active destination and what offer it contains is `NEEDS_EVIDENCE` — **do not rewrite its price or funnel sequence**; link to it as-is.
1. **Content evidence gate.** Write `out\business_facts.md` with an evidence column per claim and a `PUBLIC COPY ELIGIBILITY` flag. Any copy string referencing an unsourced claim is excluded from public copy by an assertion — the script fails rather than publishing an unsupported claim.
1. **Metadata.** `src\metadata.py` → `out\metadata.json` + `out\metadata.md`. One record per indexable route: unique descriptive `title`, unique `meta_description`, exactly one `canonical`, Open Graph and Twitter preview fields with **absolute** image URLs (`og_image` = `NEEDS_EVIDENCE`), and a `title_length_warning` flag (soft, informational — not a hard SEO rule). Run `assert_canonical_unique()`. Never fabricate a social image path.
1. **Structured data.** `src\structured_data.py` → `out\structured_data\<route>.json`. Build `Organization` and, where justified, `LocalBusiness`/`Service`/`BreadcrumbList` JSON-LD **only** from fields present and verified in `business_facts.json`. If a required property is unsourced, do not emit a plausible value — write the property name into a `_blocked_fields` array in the same file and record a blocker. **Never emit `aggregateRating`, `review`, `postalAddress`, `openingHours` or `priceRange` from invented data.** Output is server-render-ready text for a human to place.
1. **Crawl-control files.** `src\seo_files.py` → `out\seo\sitemap.xml`, `out\seo\robots.txt`, `out\seo\indexability.md`. Sitemap contains only canonical public URLs, each tagged `verified_status: NEEDS_EVIDENCE` until a real 200 is observed by a human; exclude drafts, private tools and thank-you pages. `indexability.md` records a per-route `index | noindex` decision and states that robots-blocking alone is not privacy and that private data requires authentication. Note in the file that sitemap submission is a human Search Console action.
1. **Redirect map.** `src\redirect_map.py` → `out\seo\redirect_map.json` + `out\seo\redirect_map.md`. One-to-one old→new mapping with status 301 (permanent). Populated only from real old URLs supplied by a human (`NEEDS_EVIDENCE`). Live redirect testing is `BLOCKED` — record it, do not claim it passes.
1. **Static site mock.** `src\site_mock.py` → `out\site\*.html` (one file per route, plus `404.html` and `thank-you.html`). Self-contained: inline CSS, no external scripts, no trackers, no fonts or CDNs — openable as `file://`. Visible top banner on every page: `STATIC CONTENT MOCK — NOT THE LIVE SITE; does not submit anywhere.` The form is non-functional (`type="button"`, no `action`). The `thank-you.html` carries the booking CTA to `https://ca-jenterprises.com/ai`. **Each mock's initial HTML must contain title, H1, core explanatory copy, canonical and navigation links in the raw markup without JavaScript** — the mocks are the reference target the SSR build must match. `404.html` is a real server-404 spec, not a soft 200.
1. **AI Studio prompt pack.** `src\ai_studio_prompts.py` → `out\ai_studio_prompt_pack.md`. Transcribe **all seven** source prompts verbatim (Prompt 1 project inspection, Prompt 2 page foundation, Prompt 3 search verification, Prompt 4 inquiry function, Prompt 5 integration audit, Prompt 6 optional calculator, Prompt 7 runtime quality check), plus the source's master instruction and required final-status format. Add a placeholder-fill block listing every value the prompts need, filled where verified and `NEEDS_EVIDENCE` where not. Label Prompt 4 and Prompt 6 as inapplicable until their blockers clear (Prompt 6 is disabled by `ESTIMATOR_ENABLED = False`). Add an explicit note that the source's "20-prompt revised playbook" was never supplied and must not be reconstructed.
1. **Inquiry contract as data.** `src\inquiry_contract.py` → `out\inquiry_contract.md` + `out\inquiry_contract.json`. Fields: `submission_id, name, email, phone, service_interest, service_area, message, source_page, consent`. Required: `name` + one valid contact method (`email` or `phone`) + a `service_interest` in the allowlist. Bounds: `MAX_NAME_LEN 120`, `MAX_MESSAGE_LEN 2000`, `MAX_PAYLOAD_BYTES 16384`. Status map: `201` with an opaque inquiry reference only after a confirmed CRM save; `202` only when a real durable queue accepted it (UI text must read "received for processing", never "saved to CRM"); `400/422` invalid data; `429` throttled; `502/503` upstream failure. State the contract is authored guidance, not a platform-supplied endpoint, and that AI Studio may expose server functions only through a supported equivalent path.
1. **Validation library (real code, not a spec).** `src\inquiry_validator.py`. Pure-Python, stdlib only, no I/O: `normalize(fields)` (trim, collapse whitespace, lowercase email, normalize phone to digits+leading `+`); `validate(fields, config)` returning `(ok, errors)`; enforce required fields, exactly-one-valid-contact-method, service-value allowlist (reject unknown values), length caps, total payload byte cap, `source_page` origin against `ALLOWED_SOURCE_ORIGINS`; **reject any client-supplied `location_id`, `pipeline_id`, `stage_id`, `tags`, `assigned_user` or other privileged field** — those come from server configuration only; `escape_for_display(s)`; `redact_pii(obj)` for logs. Validate on the server even when the browser validates. Unit-tested: `tests\test_inquiry_validator.py`.
1. **Idempotency store.** `src\idempotency_store.py`. File-backed (stdlib `sqlite3`) under `out\runtime\idempotency.db`, one record per `submission_id`: `submission_id, first_seen_utc, state (in_flight | saved | failed | queued), crm_reference, response_status, response_body`. Retention `IDEMPOTENCY_RETENTION_HOURS = 24`, with a `purge_expired()` function. Semantics: a repeat request returns the prior outcome and **never** creates a second lead. Record in the docstring that contact matching and submission idempotency solve different problems. Unit-tested: `tests\test_idempotency_store.py`.
1. **Reference inquiry handler.** `src\inquiry_handler.py`. Implements the full contract against an injected adapter: normalize → validate → idempotency check → call adapter with `UPSTREAM_TIMEOUT_S = 10` → map to 201/202/400/422/429/502/503. Retry transient failures **at most `MAX_RETRIES = 2` with backoff and the same `submission_id`**; never retry validation or permission errors; respect upstream retry instructions. Keep raw PII out of logs and out of public responses (opaque reference only). Never emit a success state that the adapter did not confirm. Also emits `out\server_functions\inquiry.ts`: a paste-ready server function mirroring this logic, importing configuration and credentials from environment variables **by name only** (`process.env.GHL_ACCESS_TOKEN`), containing zero secret values and zero hard-coded location/pipeline/stage IDs. Unit-tested with a mock adapter: `tests\test_inquiry_handler.py`.
1. **GHL adapter.** `src\ghl_adapter.py`. `class GHLAdapter` with every method raising `NotImplementedError("TODO: confirm <exact thing> before implementing")` — auth method, API version, required scopes, base URL, endpoint path, contact upsert/matching rule, custom field IDs, pipeline ID, stage ID. A separate `MockGHLAdapter` in the same module is clearly named and labelled `MOCK — NOT PRODUCTION` and is the only adapter used by tests. **Never silently substitute a similar tool. Never invent an endpoint path or an ID.** Document that the mock's success is not evidence the real integration works.
1. **Baseline + rendering tools.** `tools\fetch_raw_html.py`: fetch a URL with a plain unauthenticated GET, **no JavaScript execution, no cookies, no auth headers, no retries beyond 2**, extract `status, title, h1[], canonical, meta_description, og:*, internal_links[]`, write JSON evidence to `out\baseline\`. Refuse non-`http(s)` schemes and refuse to fetch anything that would incur cost. `tools\baseline_inventory.py`: run it over a URL list supplied by a human and produce the baseline inventory (routes, forms, calendars, thank-you pages, tracking IDs, published versions, DNS mappings, current titles) with URLs and the run date. With no URL list, exit `BLOCKED` with the exact missing input recorded — **never fabricate a baseline.**
1. **Optional estimator (phase 2, disabled).** `src\estimator.py` → `out\estimator\` only. `ESTIMATOR_ENABLED = False`. When disabled, emit only `out\estimator\BLOCKED.md` naming the missing inputs (service unit, allowed quantity range, material rate, labour assumptions, travel rule, minimum charge, tax treatment, exclusions, rounding rule, binding-vs-indicative status, `pricing_version`, and at least three approved worked examples). When explicitly enabled by a human, emit a **clearly labelled demonstration with synthetic values** — never the source's illustrative formula as commercial rules — with server-side validation (reject negative/non-numeric/non-finite/excessive, reject unknown services and ambiguous units), integer-minor-unit or decimal currency arithmetic, a documented rounding point, and the browser-supplied total ignored. This is not part of the CA-J pilot, and a contractor estimator belongs to a separate client project.
1. **Secret scanner.** `tools\secret_scan.py`. Scan every generated `.md`, `.json`, `.html`, `.ts`, `.py` and every log for: values of `GHL_ACCESS_TOKEN` / any token-like pattern (`Bearer `, 40+ char hex/JWT shapes), the env var names appearing **with** a non-empty value, and any credential-shaped literal. Report redacted (first 4 chars max). Also scan for the disallowed location ID and for `NEEDS_EVIDENCE` accidentally replaced by a plausible-looking value.
1. **Compliance scan.** `tools\compliance_scan.py` runs every guardrail in step 6 across every generated file and fails on any hit: a CA-J price in a customer-facing string; a fabricated testimonial/rating/review count/result; a spend line without an approval reference; a lowercased or wrong GHL location ID; the disallowed location ID used as a target; `CAJ_HVAC27_US_PURCHASE_TEST02` used as a target or duplicate source; a logo-first creative record; a duplicate canonical; a non-empty secret value. Per-file report, non-zero exit on any hit.
1. **Tests.** Write `tests\test_guardrails.py`, `tests\test_inquiry_validator.py`, `tests\test_idempotency_store.py`, `tests\test_inquiry_handler.py`, `tests\test_metadata_uniqueness.py` (stdlib `unittest`, runnable via `python -m unittest discover -s tests`). Then `src\acceptance_matrix.py` + `tools\run_tests.py` → `out\tests\test_log.md` and `T01.json … T14.json`, each `{test_id, input, expected_result, actual_result, evidence_path, verdict}` with `verdict ∈ PASS | FAIL | BLOCKED`. The fourteen cases are the source's own matrix:
    - `T01 Public routes` — direct load and refresh each URL → 200 and correct route content, no blank shell. Local equivalent: every mock's raw HTML contains title, H1, copy, canonical, nav. Live check `BLOCKED` (no site exists).

    - `T02 Initial HTML` — fetch without executing JS → main copy, H1, title, canonical, links present in raw markup.

    - `T03 Unknown route` — made-up URL → real 404 with useful navigation. Local mock `404.html` verified; host behaviour `BLOCKED`.

    - `T04 Metadata` — compare all indexable routes → distinct intent, correct canonical and preview.

    - `T05 Crawl controls` — inspect sitemap and indexing rules → only intended public URLs eligible.

    - `T06 Form success` — send a synthetic valid inquiry → confirmed saved record and truthful UI. Local: mock adapter returns 201 with opaque reference. Live CRM record `BLOCKED`.

    - `T07 Bad input` — empty, oversized, invalid fields → server rejection, no CRM write.

    - `T08 Retry` — repeat the same `submission_id` → one intended submission and one outcome.

    - `T09 CRM outage` — simulate timeout and rejected token → bounded failure, no false success.

    - `T10 Secret exposure` — inspect HTML, JS, requests, logs → no private credential disclosure.

    - `T11 Private data` — unauthenticated and cross-user access → no unauthorized records returned. `BLOCKED` (depends on the platform's auth model).

    - `T12 Mobile and keyboard` — narrow viewport and keyboard-only flow → usable controls and readable errors. Mock-only heuristics (labelled); real review is a human work order.

    - `T13 Regression` — recheck `/ai`, CTAs, calendar, tracking → existing intended behaviour preserved. `BLOCKED` (requires live access).

    - `T14 Estimator if included` — run approved worked examples → exact results and tampering resistance. `BLOCKED` (no approved rules; feature disabled).

    No `BLOCKED` case may be reported as passing. A failure in rendering, form→CRM persistence, credential handling or routing blocks release of the affected component.

1. **Release package.** `src\release_package.py` → `out\release_package.md` + `out\asset_register.md`. Include: the draft URL (`NEEDS_EVIDENCE`), the saved version and rollback target (`NEEDS_EVIDENCE`), the route and redirect map, redacted configuration names, the page content inventory, the CRM field mapping, the full test matrix, unresolved blockers, and exact restore instructions. Fill the source's required final-status format:
    `Project and location verified: [IDs]` · `Draft/live URL: [URL]` · `Saved version and rollback target: [IDs]` · `Completed steps: [numbers]` · `Test results: [pass/fail/blocked counts and evidence]` · `CRM persistence: [redacted record references]` · `Outstanding inputs: [specific list]` · `Production status: [draft / published / rolled back]` · `Next executable action: [one concrete action]`.

    Every unknown slot prints `NEEDS_EVIDENCE`. Also list, explicitly, every action outside execution authorization: domain change, paid dependency, outbound workflow, publish, migration.

1. **UI work orders.** Write the eight files plus `HUMAN-DECISIONS.md` listed in section 4, each in the repo's work-order format (`**Why:** / **Where:** / **Steps:** / **Verify:** / **Blocked by:**`), with exact object names, fields and values — never "configure the settings". Required content: `001` records the account, location name and ID, project ID, domain, current live URL, and the exact backup/restore process (**if no reversible version exists, stop and do not replace the live project**); `002` requires confirming the actual AI Studio product (not Agent Studio, not the standard funnel editor) and whether *this* project supports SSR + server functions + secrets; `003` carries the per-page title/description/canonical/H1 values and the JSON-LD blocks to paste; `004` names the secrets to create (`GHL_ACCESS_TOKEN`, `GHL_LOCATION_ID`) and the server-function file to deploy; `005` maps fields to verified GHL custom fields and pipeline/stage IDs with the location ID `UWc5vKBgFVPdxNTRAy2s` in exact case and **no assumption about `nuhFUYu0ZF9Eswiz9P79`**; `006` uses synthetic contacts owned by Chuck with the test tag `hermes_ai_studio_test`, requires that tag to be excluded from existing customer messaging workflows **before** testing, and keeps outbound email/SMS inactive; `007` carries a top-of-file gate: **DOMAIN PURCHASE OR ANY PAID DEPENDENCY REQUIRES EXPLICIT WRITTEN HUMAN APPROVAL — show the dollar amount, spend $0 until approved**; `008` uses free Search Console only and states indexing is tracked separately from ranking. `HUMAN-DECISIONS.md` lists every `NEEDS_EVIDENCE` value with owner and next action, every approval gate with its dollar amount, and the warning that `CAJ_HVAC27_US_PURCHASE_TEST02` is FROZEN and STRIPE is connected to that ad account.
1. **README, orchestrator, run and verify.** Write `README.md` (what the build produces; that nothing was published, deployed, sent or purchased; that no GHL, DNS, Search Console or Meta object was touched; run commands). Write `tools\build_all.py` (idempotent, dependency-ordered, logs to `logs\build.log`). Then execute `python tools\validate_config.py`, `python tools\build_all.py`, `python -m unittest discover -s tests`, `python tools\run_tests.py`, `python tools\secret_scan.py`, `python tools\compliance_scan.py`. Confirm every file in section 4 exists, the validator exits 0, the unit suite passes, and both scanners are clean. **Do not report success for anything not actually executed.**

## 6. Configuration & Constants

`config\constants.py`:

`OWNER_NAME              = "Chuck Ashley"
OWNER_PHONE             = "512-229-9199"
OWNER_EMAIL             = "chuck@ca-jconsulting.com"
LEGAL_ENTITY            = "CA&J Enterprises LLC"
GHL_AGENCY_URL          = "https://app.gohighlevel.com"
GHL_LOCATION_ID         = "UWc5vKBgFVPdxNTRAy2s"   # CASE-SENSITIVE. The ONLY build location.
GHL_LOCATION_NAME       = "CA&J Enterprises"
DISALLOWED_LOCATION_ID  = "nuhFUYu0ZF9Eswiz9P79"   # named in the source as a different, unverified location
BOOKING_URL             = "https://ca-jenterprises.com/ai"   # literal, verified destination. Never rewritten.
SITE_ORIGIN             = "NEEDS_EVIDENCE"          # no domain is owned or confirmed for this build
PROPOSED_ROUTES         = ["/", "/services/lead-generation", "/services/reputation-management",
                           "/services/paid-advertising", "/locations/austin", "/locations/round-rock",
                           "/about", "/contact"]     # PROPOSED_NOT_APPROVED
# --- locked pricing (INTERNAL REFERENCE ONLY; must never appear in customer-facing copy) ---
TECH_FEE_MONTHLY_USD    = 650
SETUP_FEE_USD           = 0            # waived
PER_BOOKED_APPOINTMENT_MIN_USD = 250
PER_BOOKED_APPOINTMENT_MAX_USD = 300
QUOTE_PRICE_IN_MESSAGE  = False        # MEETING-FIRST: no price in email, chat, page copy or AI reply
# --- guard flags ---
NO_SPEND_DEFAULT        = True
AD_SPEND_CAP_USD        = 0            # stays 0 until a human authorises an exact amount in writing
TOTAL_BUILD_SPEND_USD   = 0            # this spec authorises zero spend
LOGO_NEVER_FIRST        = True         # creatives lead with outcome/offer; logo = small footer disclaimer only
FROZEN_CAMPAIGN_NAME    = "CAJ_HVAC27_US_PURCHASE_TEST02"
FROZEN_CAMPAIGN_PROTECTED = True       # never edited / paused / duplicated. Separate new drafts only. Out of scope here.
PUBLISH_AUTHORITY       = "none"
SITE_PUBLISH_APPROVED   = False
DOMAIN_PURCHASE_APPROVED = False
APPROVAL_DOMAIN_PURCHASE = False
ESTIMATOR_ENABLED       = False        # phase 2; blocked until approved real pricing rules exist
THIN_CONTENT_SIMILARITY_MAX = 0.80     # above this, refuse to emit a near-duplicate page
# --- inquiry contract ---
INQUIRY_ALLOWED_FIELDS  = ["submission_id","name","email","phone","service_interest","service_area",
                           "message","source_page","consent"]
INQUIRY_REQUIRED_FIELDS = ["name","submission_id"]
INQUIRY_PRIVILEGED_FIELDS_REJECTED = ["location_id","pipeline_id","stage_id","tags","assigned_user",
                                      "opportunity_id","contact_id"]
MAX_NAME_LEN            = 120
MAX_MESSAGE_LEN         = 2000
MAX_PAYLOAD_BYTES       = 16384
UPSTREAM_TIMEOUT_S      = 10
MAX_RETRIES             = 2
IDEMPOTENCY_RETENTION_HOURS = 24
SERVICE_ALLOWLIST       = "NEEDS_EVIDENCE"    # derived from verified services; empty allowlist => reject all
ALLOWED_SOURCE_ORIGINS  = "NEEDS_EVIDENCE"
RATE_LIMIT_CONFIG       = "NEEDS_EVIDENCE"    # no rate-limit capability verified on the platform
STATUS_SAVED            = 201
STATUS_QUEUED           = 202                 # only if a real durable queue exists; UI text = "received for processing"
STATUS_INVALID          = 422
STATUS_BAD_REQUEST      = 400
STATUS_THROTTLED        = 429
STATUS_UPSTREAM_FAIL    = 503
TEST_TAG                = "hermes_ai_studio_test"
NEEDS_EVIDENCE          = "NEEDS_EVIDENCE"`

`config\build_config.json` keys (value `NEEDS_EVIDENCE` unless locked above): `build_mode, site_origin, business_name, primary_location, service_areas, services_verified, primary_service, additional_services, main_offer, offer_url, primary_cta, cta_destination, phone, contact_email, logo_path, hero_image_path, og_image_path, review_rating, review_count, years_in_business, customers_served, guarantee, license_info, privacy_policy_url, ghl_project_id, ghl_project_name, ghl_form_id, ghl_draft_url, ghl_live_url, ghl_version_id, ai_studio_ssr_supported, ghl_api_version, ghl_api_scopes, ghl_pipeline_id, ghl_stage_id, ghl_custom_field_ids, search_console_property, analytics_id, a2p_status, dns_records`.

`.env.example` — names only, empty values:

`# Never commit real values. Copy to .env and fill locally. Never paste a secret into code, copy,
# a generated asset, a screenshot, or a log.
GHL_ACCESS_TOKEN=
GHL_LOCATION_ID=
GHL_API_BASE_URL=
GHL_API_VERSION=
GHL_PIPELINE_ID=
GHL_STAGE_ID=
GHL_CUSTOM_FIELD_SERVICE_INTEREST=
GHL_CUSTOM_FIELD_SERVICE_AREA=
GHL_CUSTOM_FIELD_SOURCE_PAGE=
GHL_CUSTOM_FIELD_SUBMISSION_ID=
SITE_ORIGIN=
GHL_DRAFT_URL=
ALLOWED_SOURCE_ORIGINS=
SERVICE_ALLOWLIST=
SEARCH_CONSOLE_PROPERTY=
ANALYTICS_ID=
OWNER_PHONE=
OWNER_EMAIL=
SITE_PUBLISH_APPROVED=
DOMAIN_PURCHASE_APPROVED=
AD_SPEND_CAP_USD=`

**Rules.** No real secret, token, key, password or ID value may be written into any spec, config, output, log, mock, or screenshot — env var names and `.env.example` only. GHL location IDs are case-sensitive and must carry exact case; `GHL_LOCATION_ID` is configuration, not confidential, but still never hard-coded inside the generated server function (read it from env). Any dollar figure the source supplies and this section does not lock is unverified and belongs in section 8, never in a target. Anything that spends money must be surfaced with its dollar amount and explicitly approved in writing before execution.

## 7. Acceptance Criteria

- [ ] Y/N — `build\05-ghl-ai-studio-seo\` exists with every path in section 4 present.
- [ ] Y/N — `python tools\validate_config.py` exits 0.
- [ ] Y/N — `python -m unittest discover -s tests` passes with zero failures.
- [ ] Y/N — `python tools\secret_scan.py` and `python tools\compliance_scan.py` both exit 0 with zero hits.
- [ ] Y/N — `config\constants.py` contains `GHL_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"` in exact case.
- [ ] Y/N — the string `nuhFUYu0ZF9Eswiz9P79` appears nowhere except the `DISALLOWED_LOCATION_ID` constant and the guardrail rejection list.
- [ ] Y/N — the string `CAJ_HVAC27_US_PURCHASE_TEST02` appears only in the guard constant, this spec, and the `HUMAN-DECISIONS.md` warning line — never as a target, edit subject or duplicate source.
- [ ] Y/N — the literal `https://ca-jenterprises.com/ai` appears as the CTA destination on every page record, the `thank-you.html` mock, and the inquiry-flow escalation path.
- [ ] Y/N — `AD_SPEND_CAP_USD == 0`, `TOTAL_BUILD_SPEND_USD == 0`, and `DOMAIN_PURCHASE_APPROVED`/`SITE_PUBLISH_APPROVED` are `False`.
- [ ] Y/N — no file contains a real token, key, password or credential value; everything is referenced by env var name.
- [ ] Y/N — `out\site\` contains one mock per proposed route plus `404.html` and `thank-you.html`; each opens standalone from `file://`, loads no external script or CDN, and displays the "STATIC CONTENT MOCK" banner.
- [ ] Y/N — every mock's raw HTML contains its title, H1, core copy, canonical and navigation links without JavaScript.
- [ ] Y/N — no testimonial, review, review count, rating, client count, years-in-business figure, license, guarantee or result appears anywhere unless `config\business_facts.json` carries it with an evidence source; unsourced properties appear in `_blocked_fields` instead.
- [ ] Y/N — `assert_no_price_in_message()` passes on all page copy, form copy, message templates and generated strings; no `$650`, `$250`, `$300` or "per booked appointment" figure appears in any customer-facing output.
- [ ] Y/N — `assert_logo_not_first()` passes on every hero/OG/creative record and each `opening_element` is an outcome or offer.
- [ ] Y/N — `assert_canonical_unique()` passes; every indexable route has exactly one canonical and a unique title and description.
- [ ] Y/N — `out\seo\sitemap.xml` contains only canonical public routes and excludes drafts, private tools and thank-you pages.
- [ ] Y/N — the thin-content guard raises on two route bodies above the similarity threshold and no near-identical city page was emitted.
- [ ] Y/N — `src\ghl_adapter.py` contains a `NotImplementedError` stub for every unverified operation plus a `MOCK — NOT PRODUCTION` adapter; no guessed endpoint, field, pipeline or stage ID exists anywhere.
- [ ] Y/N — `out\server_functions\inquiry.ts` contains no secret value and no hard-coded location, pipeline or stage ID.
- [ ] Y/N — the idempotency store returns the prior outcome for a repeated `submission_id` and never creates a second record (proven by test, not by inspection).
- [ ] Y/N — the handler returns `202` only when a durable queue is actually present, and its "received for processing" text never claims the record was saved to CRM.
- [ ] Y/N — `out\tests\test_log.md` contains exactly T01–T14 with verdicts in {PASS, FAIL, BLOCKED}; no BLOCKED case is reported as passing.
- [ ] Y/N — `out\release_package.md` fills the source's final-status format with `NEEDS_EVIDENCE` in every unknown slot and lists every action outside authorization.
- [ ] Y/N — `ui-work-orders\` contains the eight numbered orders plus `HUMAN-DECISIONS.md`, each with Why/Where/Steps/Verify/Blocked by, exact object names and values, and no "configure the settings"-style instruction.
- [ ] Y/N — `ui-work-orders\007-domain-dns-and-publish.md` carries the explicit spend gate with a dollar-amount line item.
- [ ] Y/N — `README.md` states that nothing was published, deployed, sent or purchased and that no GHL, DNS, Search Console or Meta object was touched.

## 8. Blockers & Unverified Items

The spec must NOT assume any of the following.

1. **Nothing has been built or changed.** The source is a plan. No project, route, page, form, server function, secret, CRM record or published site exists. No step in the source has been executed.
1. **No visual UI detail is verified.** The source's own video page could not be retrieved. Every menu label, button name and screen reference is `NEEDS_EVIDENCE`. Do not write UI instructions that assert a specific label.
1. **AI Studio SSR + server functions + a secrets vault are unverified for this account.** The HighLevel announcement was found only as a root-domain search result. Confirm on the actual account before relying on any of it, and do not assume new-project capabilities migrate to an existing project.
1. **The revised 20-prompt playbook, the exact migration prompt, production code, API schemas and pricing formulas were never supplied.** Do not attempt to fetch, reconstruct or approximate them.
1. **The source names location `nuhFUYu0ZF9Eswiz9P79`.** That is not the CA-J build location and must not be used, compared, or treated as equivalent. The only permitted build location is `UWc5vKBgFVPdxNTRAy2s`.
1. **No verified business facts exist yet.** Services, service areas, Austin/Round Rock coverage, logo, photos, the current contents of `/ai`, guarantees, licences and any testimonial or result are all `NEEDS_EVIDENCE`. Never invent an office, a testimonial, a result, a licence, a price or a response-time promise.
1. **The proposed routes are proposals.** `/services/*` and `/locations/*` come from the source, not from approved CA-J offerings. Add only verified services; merge weak location pages into a service-area page rather than generating thin ones.
1. **SSR is not an SEO result.** It does not guarantee indexing, rankings or speed. There is no traffic, ranking, speed or conversion target anywhere in this build, and no observation may be attributed to SSR.
1. **Search Console and analytics access is unverified.** Indexing verification, sitemap submission and analytics changes are `BLOCKED` pending a human with access. Track indexing separately from ranking. Never send email addresses, phone numbers or message contents to analytics.
1. **The GHL API contract is unverified.** Auth method, API version, scopes, base URL, endpoint path, contact matching rule, custom field IDs, pipeline ID and stage ID are all unknown. The adapter is a stub for that reason; a green mock test is not evidence of a working integration.
1. **`POST /api/inquiries` is authored guidance.** The path, fields, bounds, timeout, retry policy and status map are not a platform contract. AI Studio may expose server functions only through a supported equivalent — do not assert the REST path exists.
1. **Rate limiting and anti-spam controls are unverified.** `RATE_LIMIT_CONFIG = NEEDS_EVIDENCE`. Do not claim the public endpoint is protected.
1. **Durable queue semantics may not exist.** `202` may only be returned if a real durable queue accepted the request. If none exists, the only truthful outcomes are `201` (after a confirmed save) and the `4xx/5xx` failures.
1. **Secrets protect credentials only when used correctly.** A vault does not protect customer data and does not establish compliance. The platform's actual data access controls must be verified by a human; no compliance claim may be made.
1. **Messaging is not authorised.** A2P 10DLC and email-provider status are unknown. Testing uses synthetic contacts owned by Chuck with the tag `hermes_ai_studio_test`, and that tag must be excluded from existing customer messaging workflows **before** any test. Keep outbound email/SMS inactive.
1. **The backup/restore mechanism is unverified.** If no reversible version exists for the target project, finish the inventory and do not replace the live project. Never simulate a backend in browser storage and call it complete.
1. **The estimator is blocked.** No approved pricing rules exist, and the source's illustrative formula is not commercial rule data. CA-J's locked pricing is internal and must never appear in customer-facing copy or an AI response (MEETING-FIRST). A contractor estimator belongs to a separate client project.
1. **Out-of-scope video examples are not prerequisites.** HVAC dispatch, invoices, roofing materials, restaurant orders, travel fees, portals and provisioning each need their own data model, permissions, rules and tests. Do not build them.
1. **No paid tool may be introduced.** The source prescribes no paid SEO tool; the zero-cost path (local HTML checks, generated sitemap, free Search Console) is the design. Any paid tool, subscription, domain or upgrade is a spend action: stop, show the dollar amount, require explicit written human approval. This build spends $0.
1. **The frozen Meta campaign is untouchable and out of scope.** `CAJ_HVAC27_US_PURCHASE_TEST02` must never be edited, paused or duplicated-then-deleted — editing resets Meta's learning phase — and **STRIPE is connected to that ad account**, so any budget change draws real money. This spec creates no Meta object. If tracking/UTM work is ever proposed, it is a separate new draft and still may not touch the frozen campaign.
1. **Scope conflict.** Do not let this build replace, merge or shadow any existing CA-J offer, funnel or pipeline, and do not alter the offer currently at `https://ca-jenterprises.com/ai`.
1. **Brand separation.** B2B CA-J Enterprises / Consulting content never blends with consumer brands (Chuck's Daily Grind coffee, the Etsy printables shop). Keep them out of this pilot.
1. **No performance target may be inferred from the source.** Any CPL, CTR, traffic, ranking, speed or conversion figure is `NEEDS_EVIDENCE` or `UNSUBSTANTIATED`; source-author numbers are not CA-J results.

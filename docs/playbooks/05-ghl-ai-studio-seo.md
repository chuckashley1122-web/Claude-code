# GHL AI Studio SEO and Full Stack Implementation
Step by step action plan for the Hermes agent
Prepared for Chuck Ashley and CA-J Enterprises • September 13, 2026
Build and verify an SEO-ready website in GoHighLevel AI Studio, then add a server-processed inquiry flow connected to GHL. This playbook translates the supplied video transcript into an executable sequence with prompts, expected outputs, error handling, and launch checks.
## Source coverage and limits
Primary source: https://www.youtube.com/watch?v=LlqaA96b6qE. The attached transcript runs from the opening through the final segment at 23:13. All supplied transcript sections were reviewed. Direct video retrieval failed, so visuals, exact on-screen controls, and the video description were not independently inspected. This is a complete transcript-based implementation plan, not a claim of frame-by-frame video review.
The presenter, Dominic Baptist, explains SSR, server functions, REST APIs, secrets, and an upcoming revision of a 20-prompt playbook. The actual revised playbook, an exact migration prompt, production code, API schemas, and pricing formulas are not supplied. The prompts and technical contracts below are original implementation additions derived from those concepts.
## Recommended first implementation
Use a draft CA-J Enterprises project as the first pilot, with local-service marketing pages and a working inquiry form. Austin and Round Rock are proposed location priorities. Keep the existing /ai offer path and live funnel behavior intact when applicable. An estimator is an optional second phase; it requires real pricing rules. Do not build every app mentioned in the video.
## How Hermes should execute
Complete the numbered steps in order. Record PASS, FAIL, or BLOCKED with evidence for each step. Continue independent draft work when a credential or business fact is missing. Never label mocked integrations, untested migrations, or unsupplied pricing as production ready. This document does not mean that any account or website has already been changed.
## Definition of done
A saved draft or release candidate with crawlable public routes, distinct page content and metadata, a tested server-side submission flow, confirmed CRM records, private credentials, and a reproducible rollback. Production release is a separate execution action to perform only within Chuck’s actual authorization.

# 1 Video coverage and implementation map
Transcript
| Topic
| Hermes action
|
0:00–2:57
| Update introduction and example apps
| Inventory platform features; use examples as optional scope.
|
3:00–5:47
| Frontend and backend distinction
| Separate public pages, server logic, and CRM integration.
|
5:54–7:34
| SSR explanation
| Inspect initial HTML for content and metadata.
|
7:42–9:16
| SEO still requires strategy
| Map intent, services, locations, headings, links, and images.
|
9:25–10:55
| Server functions and estimates
| Validate inputs and calculate only from supplied business rules.
|
11:04–11:55
| REST APIs and beta caveat
| Define requests, responses, authentication, and failure behavior.
|
12:04–12:33
| Event promotion
| No implementation dependency; no purchase needed.
|
12:42–13:33
| Secrets and privacy discussion
| Store credentials server-side; verify actual data access controls.
|
13:41–15:19
| Agency opportunities and use cases
| Choose one business problem; avoid unnecessary applications.
|
15:26–17:30
| Future prompt playbook changes
| Use the original prompts in this document; exact future prompts are absent.
|
17:39–18:24
| Runtime testing and minimal repairs
| Test routes, forms, functions, and APIs after changes.
|
18:32–19:40
| Four capability recap
| Recheck rendering, logic, integrations, and secret handling.
|
19:48–23:13
| Outlook and community promotion
| No build steps; future announcements are not verified requirements.
|
## Corrections that affect the build
SSR can make primary content available without waiting for client rendering; it does not guarantee indexing, rankings, or speed. A secrets vault protects credentials only when correctly used. It does not automatically protect all customer data or establish compliance. External integrations require supported APIs, permissions, and access; their names in the video are not proof that a connection exists.

# 2 Establish the project and preserve the baseline
## Step 1 Identify the exact target
Open the authorized GHL session. Record account, location name and ID, domain, project ID, and current live URL. If the previously used location nuhFUYu0ZF9Eswiz9P79 is present, verify it belongs to the intended CA-J Enterprises project before making changes. Do not assume all three businesses share one project.
## Step 2 Inspect existing assets
List current routes, forms, calendars, thank-you pages, tracking IDs, integrations, published versions, and DNS mappings. Capture screenshots of the homepage, /ai if present, and conversion flows. Record redirects and current SEO titles. Output: baseline inventory with URLs and date.
## Step 3 Save a recovery point
Duplicate the project or use the platform’s supported version/export mechanism. Record the original version ID and the exact restore process. Keep a draft URL separate from the public domain. If no backup or reversible version exists, finish the inventory and avoid replacing the live project.
## Step 4 Verify AI Studio capabilities
Locate the actual AI Studio product in the current interface; do not confuse it with Agent Studio or the standard funnel editor. Inspect project framework/configuration and available server functions, secrets, logs, and testing tools. Verify whether this existing project supports the new runtime. Do not assume new-project capabilities automatically migrate old projects.
## Step 5 Choose the implementation branch
If SSR and server functions are supported, build a small draft proof first. If the old project cannot support them, create a separate compatible draft and preserve a route-by-route migration map. If unavailable, report the precise missing feature and keep the existing site intact. Never simulate a backend in browser storage and call it complete.
## Prompt 1 Project inspection
Inspect this selected project before editing. Report its framework, routes, rendering behavior, server capabilities, secrets interface, integrations, and current errors. Identify the smallest reversible path to SEO-ready public pages plus a server-side inquiry flow. Preserve working code and existing conversion routes. List missing capabilities with evidence. Do not claim a migration has happened until verified.

# 3 Define business inputs and the page plan
## Step 6 Assemble verified business facts
Collect approved business name, phone, contact email, real service areas, services, logo, photos, offer details, and booking destination. Mark unknown values as TODO in the draft. Do not invent offices, testimonials, results, licensing, pricing, or response-time promises. Keep consulting/lending and coffee content out of this agency pilot.
## Step 7 Create an intent and route inventory
For each route, record audience, search intent, primary topic, title, H1, canonical URL, CTA destination, supporting proof, and internal links. Inspect existing routes first and reuse suitable URLs. Suggested drafts: /, /services/lead-generation, /services/reputation-management, /services/paid-advertising, /locations/austin, /locations/round-rock, /about, /contact. Add only verified services.
## Step 8 Write substantive page content
Give each service page a distinct problem, process, deliverables, FAQs, and relevant CTA. Location pages must explain actual local coverage and contain useful city-specific information. Do not generate near-identical pages by swapping city names. Merge weak pages into one service-area page until enough useful content exists.
## Step 9 Preserve the conversion path
Confirm whether /ai is the active destination and what offer it currently contains. Link to the actual approved offer without rewriting its price or funnel sequence. Ensure every main page has one clear primary action. Use the existing calendar when appropriate; test its loading and correct destination.
## Step 10 Approve the content evidence
Create an asset/source list linking each business claim to approved material. Leave unsupported claims out of public copy. Output: page map, source list, and draft copy ready for implementation.
## Prompt 2 Build the page foundation
Use the approved business inputs and page map to implement responsive public pages in the supported project framework. Put substantive page content, titles, canonical URLs, H1s, and internal anchor links in initial HTML. Preserve existing functional routes and the approved conversion destination. Use unique intent-driven copy, accessible controls, and descriptive image text. Do not invent business facts or create thin location pages. Report every route added or changed.

# 4 Implement and verify search visibility
## Step 11 Prove rendering on a small route
Build one service page first. Fetch its direct URL as raw HTML without executing JavaScript. Confirm the real title, H1, explanatory copy, canonical, and navigation links are present. A blank root container or content only inside script data is not a pass. Save the response and test the same route in a browser.
## Step 12 Apply rendering to all public routes
Use the supported framework routing and metadata APIs, based on the actual installed version. Do not blindly convert code to a different framework. Test direct visits and refreshes on every route, not just client-side navigation. Check that hydration leaves the page interactive and produces no persistent console errors.
## Step 13 Add metadata and structured data
Give each indexable route a unique descriptive title, meta description, and one intended canonical. Add accurate social preview metadata and absolute image URLs. Add Organization or appropriate LocalBusiness data only with verified facts, plus relevant service or breadcrumb data where justified. Do not add fabricated review ratings or addresses.
## Step 14 Handle crawling and URL changes
Generate a sitemap containing only canonical public URLs that return 200. Exclude private tools, drafts, and thank-you pages as appropriate. Use noindex for pages that should not appear in search; robots blocking alone is not privacy. Require authentication for private data. If routes change, map each old URL to its equivalent using a tested permanent redirect.
## Step 15 Verify usability and SEO output
Inspect mobile layout, keyboard navigation, form labels, image dimensions, loading behavior, and readable contrast. Check broken links, missing images, duplicate metadata, canonical targets, and a real 404 on unknown paths. Validate supported structured data. Measure performance before and after; record regressions rather than promising improved rankings.
## Prompt 3 Search verification
Audit every public route using initial response HTML and browser rendering. Report HTTP status, title, H1, canonical, visible core copy, internal links, indexability, and hydration errors. Fix only confirmed failures, preserving working behavior. Verify sitemap and redirects against the route inventory. Distinguish missing content from rendering delays. Re-test changed routes and the main conversion path.

# 5 Build the server side inquiry flow
The following contract is an original implementation specification, not an endpoint or code sample supplied by the video. Use an equivalent supported server function if AI Studio does not expose custom REST paths.
## Step 16 Define the inquiry contract
Proposed operation: POST /api/inquiries. Accept submission_id, name, email or phone, service_interest, service_area, message, source_page, and consent fields only when applicable. Require a name, one valid contact method, and a selected supported service. Suggested bounds: name 120 characters, message 2,000 characters, and total payload 16 KB. Validate on the server even if browser validation passes.
## Step 17 Implement trusted server processing
Normalize fields, reject unknown service values, apply length limits, and validate URLs against allowed source origins. Escape user content on display. Do not accept client-supplied CRM location IDs, tags, pipeline IDs, or privileged fields. Load those from server configuration. Keep raw personal information out of logs and public responses.
## Step 18 Make submission states truthful
Return 201 with an opaque inquiry reference only after the CRM save is confirmed. Return 202 only when a real durable queue accepted the request; display “received for processing,” not “saved to CRM.” Return 400/422 for invalid data, 429 for throttling, and 502/503 for upstream failures. On failure retain entered form values and show a useful retry message.
## Step 19 Prevent duplicate processing
Generate one submission_id per intended submission and reuse it on network retries. Persist an idempotency record on the server with a recommended 24-hour retention. Record processing/success state and the CRM reference. Repeat requests must return the prior outcome, not create another lead. Contact matching and submission idempotency solve different problems.
## Step 20 Handle abuse and runtime failure
Add supported rate limiting and anti-spam controls to the public endpoint. Set a bounded upstream timeout, suggested at 10 seconds. Retry transient failures at most twice with backoff and the same submission_id; respect upstream retry instructions. Do not retry validation or permission errors. If durable storage/queue is unavailable, report failures honestly and avoid claiming guaranteed delivery.
## Prompt 4 Implement the inquiry function
Implement the specified inquiry contract using supported server-only functions. Add validation, field allowlisting, bounded execution, idempotency, and truthful success/failure states. Keep external credentials out of browser code. Connect only to verified server configuration. Use a mock adapter for draft testing when access is missing, label it clearly, and leave production integration BLOCKED until a real CRM record is verified.

# 6 Connect GHL and protect credentials
## Step 21 Map the destination before writing
Inspect the intended GHL location and current supported integration documentation. Record the actual authentication method, API version, required scopes, endpoint, custom field IDs, pipeline ID, and stage ID if used. Prefer an existing verified native integration when it meets the contract. Do not invent endpoint paths or IDs.
## Step 22 Store secrets correctly
Use the actual server-only secrets manager. Suggested logical names: GHL_ACCESS_TOKEN and GHL_LOCATION_ID; the latter is configuration, not necessarily confidential. Supply the minimum required permissions. Never paste tokens into public code, client environment variables, generated copy, screenshots, or logs. Confirm the deployed server can read them without returning their values.
## Step 23 Map incoming data to CRM records
Map name, email, phone, service interest, area, message, and source to verified fields. Use an established contact matching/upsert rule; do not merge ambiguous identities. Record submission_id as a searchable reference when supported. Create one opportunity only if the approved flow requires it, using the verified pipeline and stage. Do not create a separate opportunity on every retry.
## Step 24 Isolate testing from messaging
Use synthetic contacts owned by Chuck and a test tag such as hermes_ai_studio_test. Exclude that tag from existing customer messaging workflows before testing. Verify existing automations triggered by new contacts, tags, forms, and opportunities. Keep outbound email/SMS inactive unless their actual recipient and send scope are authorized.
## Step 25 Verify end to end
Submit one synthetic inquiry through the draft browser form. Find its actual contact and, if configured, opportunity in the correct location. Verify all mapped values and source data. Retry the identical submission; confirm no duplicate. Record the opaque reference, CRM IDs, timestamp, and a screenshot without unnecessary personal data.
## Step 26 Inspect the browser boundary
Search built frontend assets, raw page HTML, source maps when present, network responses, and logs for secret names and credential values using a redacted result. Test missing/expired credentials. The page must remain usable and must not disclose tokens, stack traces, or private customer records. Rotate any credential that was exposed.
## Prompt 5 Integration audit
Trace a synthetic inquiry from browser to server to GHL. Show redacted request/response evidence and the persisted CRM record IDs. Verify destination, field mapping, retries, duplicates, and failure UI. Prove that no browser request carries a private API token. Mark any mocked or unverified step BLOCKED. Make minimal repairs and re-run this same trace.

# 7 Optional estimate calculator
Video basis: 9:25–10:55. This is a second-phase feature, not a requirement for the CA-J Enterprises website pilot. A contractor estimator should be built in a separately identified client project with the client’s actual service and pricing inputs.
## Step 27 Select one calculation problem
Choose one service such as sod installation. Obtain the service unit, allowed quantity range, material rate, labor assumptions, travel rule, minimum charge, tax treatment, exclusions, rounding rule, and whether the output is a binding quote or an indicative estimate. Without approved rules, build only a clearly labeled demonstration with synthetic values.
## Step 28 Define a versioned rule set
Store pricing and business rules on the server, not as authoritative browser values. Assign a pricing_version. A sample model is subtotal = materials + labor + equipment + travel; apply the approved minimum and then the approved tax/rounding order. This model is illustrative only and must not substitute for supplied commercial rules.
## Step 29 Validate quantities and recompute
Reject negative, nonnumeric, nonfinite, and excessive values. Reject unsupported services and ambiguous units. Calculate currency with decimal arithmetic or integer minor units and a documented rounding point. Ignore a browser-supplied total. Record inputs, rule version, timestamp, and computed output for reproducibility.
## Step 30 Present a clear result
Display currency, scope, exclusions, estimate status, and a request-for-confirmation CTA. Keep customer contact submission separate from price calculation until the customer chooses to send an inquiry. Do not promise an appointment, a final quote, or an invoice solely because an estimate was generated.
## Step 31 Test against approved examples
Have the business provide at least three known worked examples. Test the minimum, maximum, zero, fractional quantity, rounding boundary, unsupported service, altered browser total, and unavailable pricing configuration. The output must match the approved expected result exactly; block release if it does not.
## Prompt 6 Add the optional calculator
Implement only the approved service calculation using the supplied versioned pricing rules. Validate and calculate on the server. Return an estimate with its currency, scope, exclusions, and rule version. Do not trust client totals or invent commercial rates. Keep the existing website and inquiry flow working. If rules are missing, report the missing inputs and keep this feature out of production.
## Other examples from the video
HVAC dispatch, invoices, roofing materials, restaurant orders, travel fees, portals, and provisioning are separate product scopes. Each needs its own data model, permissions, business rules, and acceptance tests. Their appearance in the video does not make them prerequisites for this build.

# 8 Acceptance testing and minimal repairs
Run this matrix on the release candidate. Save date, URL or operation, expected result, observed result, PASS/FAIL/BLOCKED, and evidence path. Any failed critical conversion, data isolation, credential, or rendering check blocks release.
Test
| Action
| Pass condition
|
Public routes
| Direct load and refresh each URL
| 200 and correct route content; no blank shell
|
Initial HTML
| Fetch without executing JS
| Main copy, H1, title, canonical, links present
|
Unknown route
| Visit a made-up URL
| Real 404; useful navigation
|
Metadata
| Compare all indexable routes
| Distinct intent; correct canonical and preview
|
Crawl controls
| Inspect sitemap and indexing rules
| Only intended public URLs eligible
|
Form success
| Send synthetic valid inquiry
| Confirmed saved record and truthful UI
|
Bad input
| Empty, oversized, invalid fields
| Server rejection; no CRM write
|
Retry
| Repeat same submission_id
| One intended submission and outcome
|
CRM outage
| Simulate timeout and rejected token
| Bounded failure; no false success
|
Secret exposure
| Inspect HTML, JS, requests, logs
| No private credential disclosure
|
Private data
| Unauthenticated and cross-user access
| No unauthorized records returned
|
Mobile and keyboard
| Narrow viewport and keyboard-only flow
| Usable controls and readable errors
|
Regression
| Recheck /ai, CTAs, calendar, tracking
| Existing intended behavior preserved
|
Estimator if included
| Run approved worked examples
| Exact results and tampering resistance
|
## Step 32 Repair only the demonstrated fault
Reproduce each failure; inspect runtime logs and the smallest relevant code path. Make one targeted repair. Re-test the failing case plus the homepage and inquiry flow after each change. Avoid broad refactors of functioning code. Stop speculative edits if the same fault persists and report the evidence and missing dependency.
## Prompt 7 Runtime quality check
Inspect the application with available logs and testing tools. Exercise every route, form, server function, and API used in this scope. Find hangs, loops, timeouts, and incorrect responses. Repair only the demonstrated fault. After each edit confirm the app loads and the inquiry path still works. Return evidence and unresolved blockers; do not infer a pass from a successful build alone.

# 9 Release and Hermes handoff
## Step 33 Prepare a concrete release package
Provide the draft URL, saved version, route and redirect map, redacted configuration names, page content inventory, CRM mapping, test matrix, unresolved blockers, and exact restore instructions. Clearly identify any domain change, paid dependency, outbound workflow, or migration that remains outside the execution authorization.
## Step 34 Release the verified version
When launch is authorized and all critical checks pass, publish the tested version to the verified target. Use the platform’s supported domain mapping and HTTPS process. Preserve the current audience and existing unrelated projects. Immediately test the homepage, a service page, /ai if present, and one synthetic inquiry. Restore the recorded prior version if core behavior fails.
## Step 35 Verify discovery and measurement
After launch, verify the correct Search Console property when access is available. Submit the canonical sitemap, inspect representative URLs, and track indexing separately from ranking. Connect existing analytics without duplicate tags; count a lead conversion only on confirmed submission success. Do not send email addresses, phone numbers, or message contents to analytics.
## Step 36 Review operational results
Recommended cadence: check server errors and failed submissions the next day; review indexing and broken routes after one week; compare organic visits and successful inquiries after four weeks. These are operating instructions, not scheduled automations created by this document. Report observations without attributing all changes to SSR.
## Copy and paste master instruction for Hermes
Execute this GHL AI Studio SEO and Full Stack Implementation playbook for Chuck Ashley. Start by verifying the selected account, location, project, domain, and available capabilities. Use a reversible draft and preserve live conversion paths. Follow Steps 1–26, then Steps 32–36 as applicable. Treat Steps 27–31 as optional and blocked until real business pricing is supplied. Use the original prompts in this document, with the approved page map and business facts as inputs. Keep secrets server-side. Use synthetic test contacts and prevent accidental outbound messages. Verify actual CRM persistence and initial HTML rather than relying on a preview or build success. Continue independent work when blocked, and list the exact missing dependency. Do not claim the video supplied unpublished prompts or that mocks are live. Return the completed release package and execute production actions only within the authorization already provided.
## Required final status format
Project and location verified: [IDs]. Draft/live URL: [URL]. Saved version and rollback target: [IDs]. Completed steps: [numbers]. Test results: [pass/fail/blocked counts and evidence]. CRM persistence: [redacted record references]. Outstanding inputs: [specific list]. Production status: [draft / published / rolled back]. Next executable action: [one concrete action].

# 10 Sources and implementation boundaries
## Primary source
Dominic Baptist video supplied by Chuck: https://www.youtube.com/watch?v=LlqaA96b6qE
Attached source: Pasted markdown(20260913-190741).md. Transcript coverage: opening through final segment at 23:13. Timestamps in this playbook refer to that supplied transcript. Video page access failed during preparation; no visual UI details are asserted as independently verified.
## Technical cross check
Google Search Central — Understand JavaScript SEO basics
https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
Supports the distinction between crawling and rendering and the value of server-side or pre-rendered content. It does not promise that SSR guarantees rankings.
Google Search Central — Generate structured data with JavaScript
https://developers.google.com/search/docs/appearance/structured-data/generate-structured-data-with-javascript
Supports including structured data in server-rendered output and verifying its presence. Appropriate data and eligibility still depend on the actual page.
## Platform verification limit
A current search surfaced an official HighLevel announcement titled AI Studio Introducing SSR plus Server Functions plus Secrets, describing server-rendered pages, server functions, REST APIs, and a secrets vault for new projects. Search exposed only a root-domain result, so this playbook does not treat it as a detailed implementation reference. Hermes must confirm account availability, the existing project runtime, current API documentation, and deployment controls before executing platform-specific changes.
## What this document adds
The numbered sequence, CA-J Enterprises pilot route plan, prompts, inquiry endpoint contract, validation bounds, timeout/retry recommendations, idempotency policy, test matrix, release criteria, and handoff template are authored implementation guidance. They make the video concepts executable but are not claimed as verbatim instructions from the presenter.
## What remains dependent on the target account
Exact UI labels; supported project migration mechanism; deployed framework version; authentication scopes and API versions; field, pipeline, and stage IDs; credential availability; approved business claims; optional pricing; backup and restore support; Search Console access; and production launch authority. Record each unresolved item in the handoff instead of guessing.
## What the video does not require
No affiliate signup, paid community, event ticket, purchase, future workshop, or unreleased prompt pack is necessary to follow this plan. The source’s promotional sections were reviewed and excluded from the executable build scope.

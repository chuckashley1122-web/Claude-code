# UI-only checklist

Every one of the source's 51 steps, partitioned into what this repository does
(CODE), what only a human in a logged-in browser or a live conversation can do (UI),
and steps with both parts (BOTH).

## Coding-agent-inaccessible systems

The coding agent cannot log in to, operate, or change any of the following. Every
action in them is a human step with an approval gate:

- **GoHighLevel** (entirely UI-only for this build): subaccount creation, snapshots
  (request, import, audit), calendars, AI agents, knowledge base crawling and
  training, chat widgets, phone number settings, A2P messaging registration, payment
  products and checkout, workflows (WF01-WF04), pipelines and opportunities, the
  dialer and LeadConnector app, and sites/funnels.
- **Meta Ads Manager** of any kind (the live campaign CAJ_HVAC27_US_PURCHASE_TEST02
  stays frozen; no budget changes).
- Carrier / phone provider consoles (forwarding, timers, voicemail).
- Payment processor dashboards.
- Email sending platforms, domain registrars and DNS, Instagram, and any other
  logged-in UI or third-party tool named in the source (including Higgsfield).
- Live sales meetings, calls, and walk-ins.

## Steps 01-51

| Step | Title | Layer | Repo artifact (code layer) | UI platform (human) |
|---|---|---|---|---|
| 01 | Confirm the target account | UI | runbooks/ghl-account-and-snapshot.md | GoHighLevel (UI) |
| 02 | Create the build record | CODE | records/*.csv, schemas/*.json, scripts/validate_records.py | repo |
| 03 | Inventory access and training assets | UI | runbooks/ghl-account-and-snapshot.md | GoHighLevel (UI) + training portal |
| 04 | Collect missing business decisions | BOTH | docs/COST-AND-APPROVALS.md, records/Blockers.csv | Chuck (decision) |
| 05 | Keep preparation separate from activation | BOTH | README.md, tests/test-run-protocol.md | all |
| 06 | Qualify the first niche | BOTH | pipeline/stages.md, pipeline/prospects.template.csv | web research (human) |
| 07 | Draft one simple offer | BOTH | docs/COST-AND-APPROVALS.md | Chuck (decision) |
| 08 | Check cost before publishing | CODE | scripts/cost_estimate.py, rates.yaml | repo + invoices |
| 09 | Create the offer page draft | UI | runbooks/demo-page-and-calendar.md | GoHighLevel (UI) Sites/Funnels |
| 10 | Add only the essential content | UI | runbooks/demo-page-and-calendar.md | GoHighLevel (UI) Sites/Funnels |
| 11 | Build the demo calendar | UI | runbooks/demo-page-and-calendar.md | GoHighLevel (UI) Calendars |
| 12 | Connect and test the form | UI | runbooks/demo-page-and-calendar.md | GoHighLevel (UI) Forms/Calendars |
| 13 | Finish the page checks | UI | runbooks/demo-page-and-calendar.md | GoHighLevel (UI) + domain registrar |
| 14 | Start when a demo is booked | UI | workflows/WF01_demo_preparation.md | GoHighLevel (UI) |
| 15 | Build the homepage preview | UI | runbooks/demo-page-and-calendar.md | GoHighLevel (UI) site builder |
| 16 | Isolate and label the demonstration | UI | runbooks/demo-page-and-calendar.md | GoHighLevel (UI) |
| 17 | Load the niche foundation | BOTH | agent/system-prompt.md, scripts/render_templates.py | GoHighLevel (UI) AI Agents |
| 18 | Crawl and validate business facts | BOTH | records/Business_Facts.csv, agent/business-facts-template.csv | GoHighLevel (UI) Knowledge Base |
| 19 | Connect the demo widget | UI | runbooks/demo-page-and-calendar.md | GoHighLevel (UI) chat widget |
| 20 | Discover the actual problem | BOTH | intake/discovery-questions.md | live meeting (Chuck) |
| 21 | Let the owner experience the demo | UI | agent/demo-questions.md | live meeting + GoHighLevel (UI) |
| 22 | Explain the scope and price | UI | docs/COST-AND-APPROVALS.md | live meeting (Chuck) |
| 23 | Handle common questions | UI | intake/discovery-questions.md | live meeting (Chuck) |
| 24 | Build the recurring payment object | UI | runbooks/payment-product.md | GoHighLevel (UI) Payments + processor |
| 25 | Collect payment only after agreement | UI | runbooks/payment-product.md | GoHighLevel (UI) Payments |
| 26 | Create the customer account | UI | runbooks/ghl-account-and-snapshot.md | GoHighLevel (UI) Agency |
| 27 | Audit the imported snapshot | UI | runbooks/ghl-account-and-snapshot.md | GoHighLevel (UI) |
| 28 | Collect the production intake | BOTH | intake/client-intake-form.md, intake/intake.schema.json | owner (human) |
| 29 | Configure usage and user access | UI | runbooks/payment-product.md | GoHighLevel (UI) billing and users |
| 30 | Prepare the production knowledge base | UI | agent/demo-questions.md | GoHighLevel (UI) Knowledge Base |
| 31 | Choose the booking system | UI | intake/client-intake-form.md | GoHighLevel (UI) Calendars or external scheduler |
| 32 | Configure the actual booking action | UI | agent/system-prompt.md | GoHighLevel (UI) AI Agents actions |
| 33 | Verify appointment persistence | UI | tests/T01-T12.csv (T03, T04, T10) | GoHighLevel (UI) |
| 34 | Install the production website widget | UI | runbooks/widget-install.md | GoHighLevel (UI) + client website |
| 35 | Add other channels only within agreed scope | UI | runbooks/widget-install.md | GoHighLevel (UI) + social accounts |
| 36 | Prepare the phone destination | UI | runbooks/phone-routing.md | GoHighLevel (UI) Phone settings |
| 37 | Confirm messaging requirements separately | UI | runbooks/phone-routing.md | GoHighLevel (UI) A2P registration / provider |
| 38 | Choose and document one routing mode | BOTH | runbooks/phone-routing.md | Chuck + owner |
| 39 | Configure forwarding without a loop | UI | runbooks/phone-routing.md | carrier console + GoHighLevel (UI) |
| 40 | Verify each route before switching traffic | UI | runbooks/phone-routing.md | phone (human) |
| 41 | Record the exact rollback | BOTH | runbooks/rollback.md | carrier console (human) |
| 42 | Create the prospect list and pipeline | BOTH | pipeline/stages.md, pipeline/prospects.template.csv | GoHighLevel (UI) Opportunities |
| 43 | Prepare email outreach | BOTH | outreach/email-draft.txt, outreach/followup-cadence.md | sending platform (human) |
| 44 | Prepare Instagram messages and calls | BOTH | outreach/dm-draft.txt, outreach/call-script.txt, outreach/gatekeeper-questions.md | Instagram / phone (human) |
| 45 | Use a dialer only after configuration checks | UI | outreach/call-script.txt | GoHighLevel (UI) dialer / LeadConnector app |
| 46 | Prepare a demonstration video ad | UI | docs/COST-AND-APPROVALS.md | Meta Ads Manager / video tool |
| 47 | Keep advertising measurable | UI | docs/COST-AND-APPROVALS.md | Meta Ads Manager |
| 48 | Plan optional walk-ins | UI | outreach/gatekeeper-questions.md | in person (human) |
| 49 | Run a limited initial launch | UI | tests/test-run-protocol.md | GoHighLevel (UI) + carrier |
| 50 | Maintain verified knowledge | BOTH | workflows/WF04_knowledge_maintenance.md | GoHighLevel (UI) Knowledge Base |
| 51 | Report results and consider expansion | BOTH | pipeline/stages.md | GoHighLevel (UI) reporting |

Counts: CODE = 2, BOTH = 15, UI = 34.

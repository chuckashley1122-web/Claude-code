# Deploy runbook (human steps 01-51)

Maps every source step to the human action, the object it creates, spend, approval,
and the evidence to capture. Nothing here is executed by the coding agent. Spend
amounts are never estimated: every paid item is `NEEDS_EVIDENCE` and requires
approval (see `COST-AND-APPROVALS.md`). Record each completed step in
`records/Build_Log.csv` and run `python3 scripts/validate_records.py`.

Order of gates: verify account (01) -> records (02) -> drafts with synthetic data ->
approval -> live action -> evidence -> Build_Log. A step is complete only when the
actual object exists and its expected behaviour has been checked (source line 95).

| Step | Platform | Exact action | Object to create | Spend | Approval required | Evidence to capture |
|---|---|---|---|---|---|---|
| 01 Confirm the target account | GoHighLevel (UI) | Log in; confirm location ID UWc5vKBgFVPdxNTRAy2s and name CA&J Enterprises on screen | none | none | GHL | screenshot path in Build_Log |
| 02 Create the build record | repo | Keep the five records current; run validate_records.py after every edit | none | none | none | validator exit 0 |
| 03 Inventory access and training assets | GoHighLevel (UI) + training portal | Check permissions; locate licensed HVAC pack and record version and rights | none | licence pack: NEEDS_EVIDENCE | spend if pack must be bought | Asset_Register rows |
| 04 Collect missing business decisions | Chuck (decision) | Confirm usage billing model, support recipient, demo calendar owner, sending identity, spend cap | none | none | Chuck | Blockers rows closed with written decision |
| 05 Keep preparation separate from activation | all | Build drafts with synthetic contacts only; collect approval before any live action | none | none | every live action | approval record per action |
| 06 Qualify the first niche | web research (human) | Answer the three niche questions per business with a source; unknown stays unknown | prospect rows | none | none | prospect rows with sources |
| 07 Draft one simple offer | Chuck (decision) | Offer = after-hours HVAC AI answering; locked CA&J terms; no price in outbound | none | none | Chuck | written offer scope |
| 08 Check cost before publishing | repo + invoices | Human fills verified rates; run cost_estimate.py until exit 0 | none | none | Chuck verifies rates | rates.yaml evidence column |
| 09 Create the offer page draft | GoHighLevel (UI) Sites/Funnels | Duplicate a CA-J page into draft CAJ AI Employee HVAC Offer | page (draft) | none | GHL | page ID in Asset_Register |
| 10 Add only the essential content | GoHighLevel (UI) Sites/Funnels | Add logo, contact, explanation, demo, CTA to https://ca-jenterprises.com/ai; no price | page content | none | GHL | screenshot |
| 11 Build the demo calendar | GoHighLevel (UI) Calendars | Create CAJ HVAC AI Demo, America/Chicago, real availability | calendar | meeting provider: NEEDS_EVIDENCE | GHL | calendar ID and booking URL |
| 12 Connect and test the form | GoHighLevel (UI) Forms/Calendars | Link CTA; book and cancel one synthetic appointment | form | none | GHL | test booking screenshot |
| 13 Finish the page checks | GoHighLevel (UI) + domain registrar | Terms review, mobile, links, SSL after authorized domain connection | none | domain: NEEDS_EVIDENCE | publishing and domain | checklist screenshots |
| 14 Start when a demo is booked | GoHighLevel (UI) | Record prospect details and contact ID | task | none | none | opportunity in Demo booked |
| 15 Build the homepage preview | GoHighLevel (UI) site builder | Build labelled private preview; no live forms or tracking | demo page | none | GHL | preview URL |
| 16 Isolate and label the demonstration | GoHighLevel (UI) | Restrict access; label test forms and slots; separate data per prospect | none | none | GHL | access setting screenshot |
| 17 Load the niche foundation | GoHighLevel (UI) AI Agents | Duplicate licensed agent and KB, or enter the rendered prototype prompt | AI agent, knowledge base | AI usage: NEEDS_EVIDENCE | GHL | agent and KB IDs |
| 18 Crawl and validate business facts | GoHighLevel (UI) Knowledge Base | Crawl site, review facts, record each fact with evidence and date | KB sources | none | GHL | Business_Facts rows VERIFIED with evidence |
| 19 Connect the demo widget | GoHighLevel (UI) chat widget | Create widget; check text and voice mappings; test mic, audio, mobile | widget | AI/voice usage: NEEDS_EVIDENCE | GHL | widget ID, test log |
| 20 Discover the actual problem | live meeting (Chuck) | Ask the three first-two-minute questions and the outcome question | none | none | none | opportunity notes |
| 21 Let the owner experience the demo | live meeting + GoHighLevel (UI) | Show routine question, after-hours request, human handoff, test record | none | none | none | meeting notes |
| 22 Explain the scope and price | live meeting (Chuck) | Chuck states the locked CA&J terms verbally; never the source training figures | none | none | Chuck | proposal reference |
| 23 Handle common questions | live meeting (Chuck) | Answer objections with demonstrations, not promises | none | none | none | objections in notes |
| 24 Build the recurring payment object | GoHighLevel (UI) Payments + processor | Create draft monthly product and checkout; test mode only | product, checkout | processor fees: NEEDS_EVIDENCE | payments | product ID, test results |
| 25 Collect payment only after agreement | GoHighLevel (UI) Payments | Send checkout link; client pays privately; verify subscription | subscription | processor fees: NEEDS_EVIDENCE | payments | subscription ID verified |
| 26 Create the customer account | GoHighLevel (UI) Agency | Create subaccount and request HVAC snapshot after verified sale | subaccount | subaccount/snapshot: NEEDS_EVIDENCE | GHL and spend | location ID, snapshot version |
| 27 Audit the imported snapshot | GoHighLevel (UI) | Disable inherited outbound; replace template values; remove example facts | none | none | GHL | audit screenshots |
| 28 Collect the production intake | owner (human) | Owner answers intake; validate JSON with validate_records.py --intake | none | none | none | filled intake + validator exit 0 |
| 29 Configure usage and user access | GoHighLevel (UI) billing and users | Verify AI/phone billing; client enters payment directly; least-privilege users | users | usage: NEEDS_EVIDENCE | spend | billing screenshot |
| 30 Prepare the production knowledge base | GoHighLevel (UI) Knowledge Base | Crawl and review client facts; attach KB to each agent; rerun six questions | knowledge base | none | GHL | transcripts |
| 31 Choose the booking system | GoHighLevel (UI) Calendars or external scheduler | Confirm calendar owner, timezone, types, buffers, capacity, notice | calendar (if none) | none | GHL | calendar settings |
| 32 Configure the actual booking action | GoHighLevel (UI) AI Agents actions | Configure supported booking action or relabel as request capture | agent action | none | GHL | action mapping screenshot |
| 33 Verify appointment persistence | GoHighLevel (UI) | Book, double-book, unavailable date, failed integration with a synthetic customer | test appointments | none | GHL | appointment IDs |
| 34 Install the production website widget | GoHighLevel (UI) + client website | Install widget after backing up footer; test desktop and mobile | widget | none | GHL and website | widget ID, T11 evidence |
| 35 Add other channels only within agreed scope | GoHighLevel (UI) + social accounts | Connect each added channel separately; test takeover | channel connections | NEEDS_EVIDENCE | written scope | per-channel test log |
| 36 Prepare the phone destination | GoHighLevel (UI) Phone settings | Use existing number or obtain one under approved spend; attach Voice AI agent | phone number | number + usage: NEEDS_EVIDENCE | spend and phone routing | number and ownership record |
| 37 Confirm messaging requirements separately | GoHighLevel (UI) A2P registration / provider | Check current A2P messaging registration and consent requirements | A2P registration | registration: NEEDS_EVIDENCE | spend | registration status |
| 38 Choose and document one routing mode | Chuck + owner | Choose after hours and weekends; write the schedule; save current config | none | none | phone routing | schedule recorded |
| 39 Configure forwarding without a loop | carrier console + GoHighLevel (UI) | Forward per provider documentation only; no invented dial codes | forwarding rule | carrier: NEEDS_EVIDENCE | phone routing | config timestamp |
| 40 Verify each route before switching traffic | phone (human) | Authorized external test calls for each mode and transfer | none | test calls: NEEDS_EVIDENCE | phone routing | call log IDs (T05, T07) |
| 41 Record the exact rollback | carrier console (human) | Fill rollback record before change; verify one inbound call after restore | none | none | phone routing | rollback record + call log (T12) |
| 42 Create the prospect list and pipeline | GoHighLevel (UI) Opportunities | Research 25 businesses into the template; create pipeline stages in GHL | pipeline | none | GHL | prospect rows, pipeline ID |
| 43 Prepare email outreach | sending platform (human) | Render drafts; human authenticates domain, sets suppression, sends reviewed batch of 10 | none | sending platform/domains: NEEDS_EVIDENCE | outbound and spend | batch review record |
| 44 Prepare Instagram messages and calls | Instagram / phone (human) | Use rendered scripts; honest identification; record opt-outs | none | none | outbound | per-contact status |
| 45 Use a dialer only after configuration checks | GoHighLevel (UI) dialer / LeadConnector app | Verify mode, charges, number, dispositions; test an authorized number | dialer config | dialer: NEEDS_EVIDENCE | spend and outbound | test call log |
| 46 Prepare a demonstration video ad | Meta Ads Manager / video tool | Out of scope: no ad build without written authorization | none | ads and Higgsfield: NEEDS_EVIDENCE | spend | n/a until authorized |
| 47 Keep advertising measurable | Meta Ads Manager | Out of scope; never reallocate an existing campaign budget | none | ads: NEEDS_EVIDENCE | spend | n/a until authorized |
| 48 Plan optional walk-ins | in person (human) | Optional, authorized visits only; no invented anchors | none | travel: NEEDS_EVIDENCE | Chuck | visit notes |
| 49 Run a limited initial launch | GoHighLevel (UI) + carrier | Activate only after all critical tests pass and approval; daily review for first week | activation | usage: NEEDS_EVIDENCE | Chuck and owner | activation time, config version, rollback owner |
| 50 Maintain verified knowledge | GoHighLevel (UI) Knowledge Base | Weekly review task; monthly fact reconfirmation; change history | tasks | none | GHL | change history |
| 51 Report results and consider expansion | GoHighLevel (UI) reporting | Report observed metrics only; separate scope and terms for each expansion | none | none | Chuck | report |

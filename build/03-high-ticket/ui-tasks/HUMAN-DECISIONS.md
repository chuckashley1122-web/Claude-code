# Human decisions and approval gates

Every NEEDS_EVIDENCE value and every approval gate, with the next action and owner. Nothing here is approved by the build.

## Config values that are NEEDS_EVIDENCE

| Config key | Next action | Owner |
|---|---|---|
| service_area | Supply a verified value with evidence; record it in config/decision_log.jsonl | Chuck Ashley |
| sales_calendar_id | Supply a verified value with evidence; record it in config/decision_log.jsonl | Chuck Ashley |
| timezone | Supply a verified value with evidence; record it in config/decision_log.jsonl | Chuck Ashley |
| facebook_page_id | Supply a verified value with evidence; record it in config/decision_log.jsonl | Chuck Ashley |
| ad_account_id | Supply a verified value with evidence; record it in config/decision_log.jsonl | Chuck Ashley |
| privacy_policy_url | Supply a verified value with evidence; record it in config/decision_log.jsonl | Chuck Ashley |
| verified_sending_email | Supply a verified value with evidence; record it in config/decision_log.jsonl | Chuck Ashley |
| messaging_eligibility | Supply a verified value with evidence; record it in config/decision_log.jsonl | Chuck Ashley |
| payment_processor | Supply a verified value with evidence; record it in config/decision_log.jsonl | Chuck Ashley |
| service_term | Supply a verified value with evidence; record it in config/decision_log.jsonl | Chuck Ashley |
| ad_budget | Supply a verified value with evidence; record it in config/decision_log.jsonl | Chuck Ashley |
| total_test_cap | Supply a verified value with evidence; record it in config/decision_log.jsonl | Chuck Ashley |
| proof_assets | Supply a verified value with evidence; record it in config/decision_log.jsonl | Chuck Ashley |

## Approval gates

| Gate | Current | Next action | Owner |
|---|---|---|---|
| Ad spend | AD_SPEND_CAP_USD = 0, APPROVAL_AD_SPEND = false | REQUIRES EXPLICIT HUMAN APPROVAL: written daily amount, test cap and end date | Chuck Ashley |
| Launch | LAUNCH_AUTHORITY = none, APPROVAL_LAUNCH = false | REQUIRES EXPLICIT HUMAN APPROVAL after tests pass live | Chuck Ashley |
| Payment product | not created | REQUIRES EXPLICIT HUMAN APPROVAL; choose processor; test mode first | Chuck Ashley |
| Image tool / any purchase | none | REQUIRES EXPLICIT HUMAN APPROVAL | Chuck Ashley |
| SMS sending | messaging eligibility NEEDS_EVIDENCE | Confirm A2P/consent basis; REQUIRES EXPLICIT HUMAN APPROVAL for any messaging fees | Chuck Ashley |
| Stale location ID in source playbook | rejected (DISALLOWED_LOCATION_ID) | Confirm the only build location is `UWc5vKBgFVPdxNTRAy2s` | Chuck Ashley |

## Recorded blockers

| Item | Missing input | Work affected | Next action | Owner | Source |
|---|---|---|---|---|---|
| AI provider and behavior spec | AI provider and behavior spec is unknown (NEEDS_EVIDENCE) | out/delivery_scope.md | Only if AI is sold: choose provider and define behavior; requires approval for usage cost | Chuck Ashley | out/delivery_scope.md |
| ad images (5 concepts x 2 crops) | No image model in this executor; image tool choice and approval | out/creatives/ | Generate with an approved image tool from each image_prompt; proof spelling, margins and crops | Chuck Ashley | out/creatives/ |
| attribution field availability | attribution field availability is unknown (NEEDS_EVIDENCE) | out/field_map.json | Inspect integration mapping UI; record which metadata/attribution fields exist | Chuck Ashley | out/field_map.json |
| attribution field availability | attribution field availability is unknown (NEEDS_EVIDENCE) | out/ghl_facebook_integration.md | Inspect integration mapping UI; record available fields | Chuck Ashley | out/ghl_facebook_integration.md |
| calendar working hours | calendar working hours is unknown (NEEDS_EVIDENCE) | out/calendar_spec.md | Enter owner's actual working hours in the calendar availability | Chuck Ashley | out/calendar_spec.md |
| cancellation terms | cancellation terms is unknown (NEEDS_EVIDENCE) | out/close_pack.md | Decide in writing | Chuck Ashley | out/close_pack.md |
| client acquisition channel and job focus | client acquisition channel and job focus is unknown (NEEDS_EVIDENCE) | out/delivery_scope.md | Set from the signed client scope | Chuck Ashley | out/delivery_scope.md |
| client close_rate | client close_rate is unknown (NEEDS_EVIDENCE) | out/economics/client_break_even.md | Collect on the strategy call (sales_call_guide step 2) | Chuck Ashley | out/economics/client_break_even.md |
| client contribution_per_sale | client contribution_per_sale is unknown (NEEDS_EVIDENCE) | out/economics/client_break_even.md | Collect on the strategy call (sales_call_guide step 2) | Chuck Ashley | out/economics/client_break_even.md |
| client lead_to_held_rate | client lead_to_held_rate is unknown (NEEDS_EVIDENCE) | out/economics/client_break_even.md | Collect on the strategy call (sales_call_guide step 2) | Chuck Ashley | out/economics/client_break_even.md |
| client media_spend | client media_spend is unknown (NEEDS_EVIDENCE) | out/economics/client_break_even.md | Collect on the strategy call (sales_call_guide step 2) | Chuck Ashley | out/economics/client_break_even.md |
| conditional endings availability | conditional endings availability is unknown (NEEDS_EVIDENCE) | out/form_spec.md | Check in Meta form builder; if absent use the GHL flag fallback | Chuck Ashley | out/form_spec.md |
| conditional endings availability | conditional endings availability is unknown (NEEDS_EVIDENCE) | out/qualification_logic.json | Check in Meta form builder; if absent use the GHL flag fallback | Chuck Ashley | out/qualification_logic.json |
| conflict calendar and meeting link | conflict calendar and meeting link is unknown (NEEDS_EVIDENCE) | out/calendar_spec.md | Connect owner calendar and Google Meet if available | Chuck Ashley | out/calendar_spec.md |
| delivery timeline | delivery timeline is unknown (NEEDS_EVIDENCE) | out/sales_call_guide.md | Quote only after the delivery team's capacity review | Chuck Ashley | out/sales_call_guide.md |
| duplicate-match settings | duplicate-match settings is unknown (NEEDS_EVIDENCE) | out/ghl_facebook_integration.md | Inspect GHL contact matching settings; record them | Chuck Ashley | out/ghl_facebook_integration.md |
| facebook_page_id | facebook_page_id is unknown (NEEDS_EVIDENCE) | out/ghl_facebook_integration.md | Confirm the intended Page in GHL Integrations; record its ID with evidence | Chuck Ashley | out/ghl_facebook_integration.md |
| follow-up method (human/workflow/AI) | follow-up method (human/workflow/AI) is unknown (NEEDS_EVIDENCE) | out/delivery_scope.md | Decide per client scope | Chuck Ashley | out/delivery_scope.md |
| form and page IDs for intake filter | form and page IDs for intake filter is unknown (NEEDS_EVIDENCE) | out/workflows/01-intake.md | Record after the human creates the Meta form | Chuck Ashley | out/workflows/01-intake.md |
| guarantee decision | guarantee decision is unknown (NEEDS_EVIDENCE) | out/risk_reversal.md | Keep default (no numerical guarantee) or define every template term in writing | Chuck Ashley | out/risk_reversal.md |
| intake form link | intake form link is unknown (NEEDS_EVIDENCE) | out/close_pack.md | Build the intake form in GHL from intake_form.json | Chuck Ashley | out/close_pack.md |
| intake form link | intake form link is unknown (NEEDS_EVIDENCE) | out/welcome_page/index.html | Build the intake form in GHL from intake_form.json | Chuck Ashley | out/welcome_page/index.html |
| live verification T01 | Live GHL calendar (sales_calendar_id NEEDS_EVIDENCE), workflows 01-03 assembled in a test clone, and a Meta test lead submission | test T01 | Run in a GHL/Meta test clone and record evidence | Chuck Ashley | out/tests/T01.json |
| live verification T02 | Staffed hours (NEEDS_EVIDENCE), owner user in GHL, verified sending email and SMS eligibility (NEEDS_EVIDENCE) | test T02 | Run in a GHL/Meta test clone and record evidence | Chuck Ashley | out/tests/T02.json |
| live verification T03 | Meta Instant Form with conditional ending (availability NEEDS_EVIDENCE) and live GHL intake workflow | test T03 | Run in a GHL/Meta test clone and record evidence | Chuck Ashley | out/tests/T03.json |
| live verification T04 | GHL duplicate-match settings (NEEDS_EVIDENCE) and the live Facebook integration's lead ID mapping | test T04 | Run in a GHL/Meta test clone and record evidence | Chuck Ashley | out/tests/T04.json |
| live verification T05 | Live SMS sender with A2P eligibility (NEEDS_EVIDENCE) and GHL reply/opt-out triggers in a test clone | test T05 | Run in a GHL/Meta test clone and record evidence | Chuck Ashley | out/tests/T05.json |
| live verification T06 | Live GHL calendar reschedule/cancel events and workflow 03 in a test clone | test T06 | Run in a GHL/Meta test clone and record evidence | Chuck Ashley | out/tests/T06.json |
| live verification T07 | Confirmed account timezone (NEEDS_EVIDENCE) and live reminder timing in GHL | test T07 | Run in a GHL/Meta test clone and record evidence | Chuck Ashley | out/tests/T07.json |
| live verification T08 | Real working hours (NEEDS_EVIDENCE) in the live calendar | test T08 | Run in a GHL/Meta test clone and record evidence | Chuck Ashley | out/tests/T08.json |
| live verification T09 | Live Facebook-to-GHL integration and Meta lead form to submit real test leads | test T09 | Run in a GHL/Meta test clone and record evidence | Chuck Ashley | out/tests/T09.json |
| live verification T10 | Payment processor (NEEDS_EVIDENCE) test-mode product, created only after explicit approval | test T10 | Run in a GHL/Meta test clone and record evidence | Chuck Ashley | out/tests/T10.json |
| live verification T11 | Processor webhook behavior in test mode (NEEDS_EVIDENCE) | test T11 | Run in a GHL/Meta test clone and record evidence | Chuck Ashley | out/tests/T11.json |
| live verification T13 | A sold client, a chosen telephony system and live answered/busy/unanswered/after-hours call tests | test T13 | Run in a GHL/Meta test clone and record evidence | Chuck Ashley | out/tests/T13.json |
| live verification T14 | Live Meta draft campaign and GHL workflows to exercise pause/stop in the real accounts (human, approval required) | test T14 | Run in a GHL/Meta test clone and record evidence | Chuck Ashley | out/tests/T14.json |
| live verification of BLOCKED T-cases | Live GHL/Meta/processor test runs (see each BLOCKED row) | launch readiness | Run each BLOCKED case in a test clone and record evidence | Chuck Ashley | out/tests/test_log.md |
| margin input: agency_acquisition_cost | margin input: agency_acquisition_cost is unknown (NEEDS_EVIDENCE) | out/economics/agency_margin.md | Estimate from actual fulfillment plan and vendor quotes; record evidence in decision log | Chuck Ashley | out/economics/agency_margin.md |
| margin input: appointment_setting | margin input: appointment_setting is unknown (NEEDS_EVIDENCE) | out/economics/agency_margin.md | Estimate from actual fulfillment plan and vendor quotes; record evidence in decision log | Chuck Ashley | out/economics/agency_margin.md |
| margin input: booked appointments per term | margin input: booked appointments per term is unknown (NEEDS_EVIDENCE) | out/economics/agency_margin.md | Estimate from actual fulfillment plan and vendor quotes; record evidence in decision log | Chuck Ashley | out/economics/agency_margin.md |
| margin input: editing | margin input: editing is unknown (NEEDS_EVIDENCE) | out/economics/agency_margin.md | Estimate from actual fulfillment plan and vendor quotes; record evidence in decision log | Chuck Ashley | out/economics/agency_margin.md |
| margin input: fulfillment_labor | margin input: fulfillment_labor is unknown (NEEDS_EVIDENCE) | out/economics/agency_margin.md | Estimate from actual fulfillment plan and vendor quotes; record evidence in decision log | Chuck Ashley | out/economics/agency_margin.md |
| margin input: payment_fees | margin input: payment_fees is unknown (NEEDS_EVIDENCE) | out/economics/agency_margin.md | Estimate from actual fulfillment plan and vendor quotes; record evidence in decision log | Chuck Ashley | out/economics/agency_margin.md |
| margin input: refund_exposure | margin input: refund_exposure is unknown (NEEDS_EVIDENCE) | out/economics/agency_margin.md | Estimate from actual fulfillment plan and vendor quotes; record evidence in decision log | Chuck Ashley | out/economics/agency_margin.md |
| margin input: software | margin input: software is unknown (NEEDS_EVIDENCE) | out/economics/agency_margin.md | Estimate from actual fulfillment plan and vendor quotes; record evidence in decision log | Chuck Ashley | out/economics/agency_margin.md |
| messaging_eligibility | messaging_eligibility is unknown (NEEDS_EVIDENCE) | out/messages/ | Confirm SMS/A2P registration status before any SMS | Chuck Ashley | out/messages/ |
| niche: addressable_buyer_count | niche: addressable_buyer_count is unknown (NEEDS_EVIDENCE) | out/niche_brief.md | Research with dated, linked evidence (15-20 min initial choice) | Chuck Ashley | out/niche_brief.md |
| niche: interest_or_experience | niche: interest_or_experience is unknown (NEEDS_EVIDENCE) | out/niche_brief.md | Research with dated, linked evidence (15-20 min initial choice) | Chuck Ashley | out/niche_brief.md |
| niche: seasonality | niche: seasonality is unknown (NEEDS_EVIDENCE) | out/niche_brief.md | Research with dated, linked evidence (15-20 min initial choice) | Chuck Ashley | out/niche_brief.md |
| niche: three competing agencies | niche: three competing agencies is unknown (NEEDS_EVIDENCE) | out/niche_brief.md | Record three competitor agencies with ad links and dates | Chuck Ashley | out/niche_brief.md |
| niche: value_per_customer | niche: value_per_customer is unknown (NEEDS_EVIDENCE) | out/niche_brief.md | Research with dated, linked evidence (15-20 min initial choice) | Chuck Ashley | out/niche_brief.md |
| offer: cancellation | offer: cancellation is unknown (NEEDS_EVIDENCE) | out/offer_spec.md | Decide in writing before converting the offer into public copy | Chuck Ashley | out/offer_spec.md |
| offer: client media budget | offer: client media budget is unknown (NEEDS_EVIDENCE) | out/offer_spec.md | Agree per client on the strategy call | Chuck Ashley | out/offer_spec.md |
| offer: deliverable_quantity | offer: deliverable_quantity is unknown (NEEDS_EVIDENCE) | out/offer_spec.md | Decide in writing before converting the offer into public copy | Chuck Ashley | out/offer_spec.md |
| offer: included_channels | offer: included_channels is unknown (NEEDS_EVIDENCE) | out/offer_spec.md | Decide in writing before converting the offer into public copy | Chuck Ashley | out/offer_spec.md |
| offer: launch timeline | offer: launch timeline is unknown (NEEDS_EVIDENCE) | out/offer_spec.md | Quote only what the delivery team can support after capacity review | Chuck Ashley | out/offer_spec.md |
| offer: renewal terms | offer: renewal terms is unknown (NEEDS_EVIDENCE) | out/offer_spec.md | Decide renewal terms in writing | Chuck Ashley | out/offer_spec.md |
| onboarding booking link | onboarding booking link is unknown (NEEDS_EVIDENCE) | out/close_pack.md | Create a 45-minute onboarding calendar | Chuck Ashley | out/close_pack.md |
| onboarding booking link | onboarding booking link is unknown (NEEDS_EVIDENCE) | out/welcome_page/index.html | Create a 45-minute onboarding calendar | Chuck Ashley | out/welcome_page/index.html |
| payment timing | payment timing is unknown (NEEDS_EVIDENCE) | out/close_pack.md | Decide in writing | Chuck Ashley | out/close_pack.md |
| payment_processor | payment_processor is unknown (NEEDS_EVIDENCE) | out/close_pack.md | Choose processor; create test-mode product only after explicit approval | Chuck Ashley | out/close_pack.md |
| pre-call page hosting URL | pre-call page hosting URL is unknown (NEEDS_EVIDENCE) | out/precall_page/index.html | Publish as a private/unlisted GHL page; record the URL | Chuck Ashley | out/precall_page/index.html |
| pre-call video | pre-call video is unknown (NEEDS_EVIDENCE) | out/precall_page/index.html | Record the outlined video; host it; replace the embed slot | Chuck Ashley | out/precall_page/index.html |
| privacy_policy_url | privacy_policy_url is unknown (NEEDS_EVIDENCE) | out/form_spec.md | Supply the real published privacy policy URL | Chuck Ashley | out/form_spec.md |
| privacy_policy_url | privacy_policy_url is unknown (NEEDS_EVIDENCE) | out/qualification_logic.json | Supply the real published privacy policy URL | Chuck Ashley | out/qualification_logic.json |
| proof_assets | proof_assets is unknown (NEEDS_EVIDENCE) | out/creatives/ | Supply verified proof points or keep NONE | Chuck Ashley | out/creatives/ |
| public calendar URL | public calendar URL is unknown (NEEDS_EVIDENCE) | out/calendar_spec.md | Create calendar, record URL, test-book on desktop and phone | Chuck Ashley | out/calendar_spec.md |
| real campaign and ad IDs | real campaign and ad IDs is unknown (NEEDS_EVIDENCE) | out/attribution_fixtures.json | Record after the human creates the draft campaign in Meta | Chuck Ashley | out/attribution_fixtures.json |
| sales_calendar_id | sales_calendar_id is unknown (NEEDS_EVIDENCE) | out/calendar_spec.md | Record calendar ID after a human creates the calendar | Chuck Ashley | out/calendar_spec.md |
| sales_calendar_id | sales_calendar_id is unknown (NEEDS_EVIDENCE) | out/workflows/03-booked.md | Record the calendar ID for the booking trigger filter | Chuck Ashley | out/workflows/03-booked.md |
| service_area | service_area is unknown (NEEDS_EVIDENCE) | out/copy/ | Confirm the market before naming it in ad copy | Chuck Ashley | out/copy/ |
| service_area | service_area is unknown (NEEDS_EVIDENCE) | out/niche_brief.md | Confirm the service area (playbook proposes Austin and Round Rock) | Chuck Ashley | out/niche_brief.md |
| service_term | service_term is unknown (NEEDS_EVIDENCE) | out/economics/agency_margin.md | Decide the CA-J service term in writing | Chuck Ashley | out/economics/agency_margin.md |
| staffed hours | staffed hours is unknown (NEEDS_EVIDENCE) | out/workflows/02-unbooked.md | Define staffed hours for the 5-minute call task window | Chuck Ashley | out/workflows/02-unbooked.md |
| territory policy | territory policy is unknown (NEEDS_EVIDENCE) | out/form_spec.md | Only document if a real one-company-per-area policy exists; otherwise keep omitted | Chuck Ashley | out/form_spec.md |
| timezone confirmation | timezone confirmation is unknown (NEEDS_EVIDENCE) | out/calendar_spec.md | Confirm America/Chicago in GHL account and owner settings | Chuck Ashley | out/calendar_spec.md |
| verified_sending_email | verified_sending_email is unknown (NEEDS_EVIDENCE) | out/messages/ | Verify the sending domain/email in GHL | Chuck Ashley | out/messages/ |
| welcome video | welcome video is unknown (NEEDS_EVIDENCE) | out/close_pack.md | Record and host; replace the slot | Chuck Ashley | out/close_pack.md |
| welcome video | welcome video is unknown (NEEDS_EVIDENCE) | out/welcome_page/index.html | Record and host; replace the slot | Chuck Ashley | out/welcome_page/index.html |

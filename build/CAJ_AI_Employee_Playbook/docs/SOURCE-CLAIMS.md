# Source claims register

Every quantitative claim, figure, and anchor in the source playbook
(`docs/playbooks/02-ai-employee-action-plan.md` in the repo; original at
`...\caj-growth-system\playbooks\02-ai-employee-action-plan.md`), with its line number.

**Every entry is `unverified`.** None of these is a CA-J price, result, forecast, or
target. The source is a plan derived from a training video whose playback could not
be accessed (source line 8); figures are the presenter's, an attendee's, or the plan's
own proposals. This file and the guardrail denylist (`guardrails/claim_guard.py`,
`scripts/check_guardrails.py`) are the only places these source figures may appear,
and only labelled as source values.

Locked CA&J terms are in `docs/COST-AND-APPROVALS.md`; they replace every pricing
figure below for CA&J.

## Claims (blocked by `guardrails/claim_guard.py`)

| ID | Source line(s) | Verbatim source text | Whose figure | Status | Guard |
|---|---|---|---|---|---|
| SC-01 | 108, 192 (spec cites 104-107) | "$197 per month" (recurring-fee draft default; also in the meeting script) | plan's proposed default from trainer guidance | unverified | claim_guard SC-01 |
| SC-02 | 112 (spec cites 104-107) | "$0 for standard installation" (setup-fee draft default) | plan's proposed default | unverified | claim_guard SC-02 |
| SC-03 | 131 | "The trainer suggests $97–$297 per month, favoring the lower range." | presenter (trainer) | unverified | claim_guard SC-03, SC-04 |
| SC-04 | 131 | "The attendee's $297 setup and $297 monthly sale is one reported example." | an attendee, as reported | unverified | claim_guard SC-04 |
| SC-05 | 131 | "The later "$9.99" upsell transcription is ambiguous and should not be used as a price instruction." | transcript, ambiguous | unverified | claim_guard SC-05 |
| SC-06 | 133 | "Do not advertise unlimited usage or treat the trainer's "virtually nothing" cost statement as a verified rate." | presenter | unverified | claim_guard SC-06 (and RULE-UNLIMITED) |
| SC-07 | 154 | "The trainer budgets about 15 minutes for preparation; treat that as a target, not a guarantee." | presenter | unverified | claim_guard SC-07 |
| SC-08 | 299 | "The video proposes 30–90 emails daily across three domains; this is a training target, not a safe starting volume for every account." | presenter | unverified | claim_guard SC-08 |
| SC-09 | 310 | "The trainer suggests 50 calls daily and discusses GHL's dialer and LeadConnector app." (dialer cost not verified) | presenter | unverified | claim_guard SC-09 |
| SC-10 | 359 | "Do not adopt the trainer's low-churn ... claims as forecasts for CA-J." | presenter | unverified | claim_guard SC-10 |
| SC-11 | 359 | "Do not adopt the trainer's ... valuation claims as forecasts for CA-J." | presenter | unverified | claim_guard SC-11 |
| SC-12 | 321 | "Do not use an invented "normally $1,000 plus $2,000 setup" anchor." | presenter (explicitly prohibited) | unverified | claim_guard SC-12 |
| SC-13 | 134 | "the $27 Review System and $397 audit" (other offers named in the source; prices not verified for this build) | plan's statement | unverified | claim_guard SC-13 |
| SC-14 | 356 | "even though the trainer positions it as low maintenance" | presenter | unverified | claim_guard SC-14 |

## Planning values (not claims about results; listed for completeness)

| ID | Source line(s) | Verbatim source text | Status | How this build uses it |
|---|---|---|---|---|
| PV-01 | 143 | "CAJ HVAC AI Demo with a 15-minute duration" | unverified | proposed demo calendar length; the outreach "15-minute walkthrough" wording comes from the source email draft (line 302) |
| PV-02 | 297 | "a proposed research batch of 25 HVAC businesses" | unverified | `PROSPECT_BATCH_FIRST = 25` is a research batch, not a sending volume |
| PV-03 | 315 | "a draft 30–45 second video" | unverified | optional ad only; ads are out of scope |
| PV-04 | 354 | "For the first seven days, review each available interaction daily" | unverified | launch monitoring guidance |
| PV-05 | 66, 81 | "the presenter's seven-page SOP" | unverified; not supplied | recorded as a missing dependency; contents never invented |
| PV-06 | 85 | a CA-J location ID printed in the source | stale / incorrect | never used; the only build location is `UWc5vKBgFVPdxNTRAy2s` |

## Rules

- No figure above may appear in any outbound message, page, ad, or AI reply.
- None may be stated as a CA-J price, result, benchmark, or forecast.
- CA-J has no results or proof points from this source (spec section 8, item 8).

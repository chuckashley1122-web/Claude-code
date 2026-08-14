# Funnel test matrix

Every case must pass before a build is handed off. Existence of assets is not
correctness — a page can render perfectly while its logic is inverted, so each
case asserts an *outcome*, not that a step ran.

Use synthetic contacts only: addresses and phone numbers the operator controls,
tagged `TEST`, cleaned up afterwards. Never test against real leads.

Record the result per build in `reports/build-<timestamp>.md`.

| # | Test case | Expected result | Pass |
|---|-----------|-----------------|------|
| 1 | Qualified lead, books appointment | Qualified tag; opportunity created and assigned; stage = Appointment Booked; confirmation and reminders queued | ☐ |
| 2 | Qualified lead, does not book | Opportunity in Qualified — Needs Booking; booking nurture starts | ☐ |
| 3 | Disqualified lead | Disqualified tag and stage; decline page shown; **no** sales nurture | ☐ |
| 4 | Missing required answer | Submission blocked, or routed to an exception queue | ☐ |
| 5 | Invalid phone or email | No send attempted; validation or manual review | ☐ |
| 6 | Existing contact reapplies | Contact updated; no duplicate opportunity unless intended | ☐ |
| 7 | Contact is DND or unsubscribed | No outbound messages of any kind | ☐ |
| 8 | Lead replies mid-sequence | Chase sequence stops or routes to a human | ☐ |
| 9 | Appointment rescheduled | Old reminders cancelled; new reminders use the new time | ☐ |
| 10 | Appointment cancelled or no-show | Correct stage; recovery sequence starts | ☐ |
| 11 | Two simultaneous bookings | Round-robin assigns correctly; no double-booking | ☐ |
| 12 | Submission outside business hours | Quiet-hour rules hold; sends are delayed not dropped | ☐ |
| 13 | Mobile form submission | All steps and buttons work at 390×844 | ☐ |
| 14 | UTM / source capture | Attribution present on contact and opportunity | ☐ |
| 15 | Failure partway through build | Partial assets listed in manifest; rerun does not duplicate completed work | ☐ |

## Visual QA

Capture to `screenshots/` at each width and check:

| Width | Device class |
|-------|--------------|
| 1440×900 | Desktop |
| 768×1024 | Tablet |
| 390×844 | Mobile |

- Fold: audience, offer, benefit, and CTA visible without scrolling
- Forms: required markers, progress indicator, conditional fields, validation
  messages, button states, keyboard navigation
- Booking: correct calendar, team, duration, time zone, real slots, confirmation
- Design: no clipped text, overlapping sections, stretched images, weak
  contrast, or sub-14px mobile body text
- Links: privacy policy and terms resolve

A correction is not complete until the affected page **and** its workflow
branch pass again.

## Claims review

Not automatable, and the highest-consequence check here. Before launch, a human
confirms every claim on every page traces to something substantiated in the
offer spec. Invented testimonials, statistics, guarantees, or outcomes are the
most likely way an AI-assisted build creates real legal exposure.

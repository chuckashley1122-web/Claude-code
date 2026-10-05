# Runbook: production phone routing

Covers source steps 36-40. **Human-only**, with provider console access.
Approval gate: `REQUIRE_HUMAN_APPROVAL_FOR_PHONE_ROUTING = True`. Write and verify
`runbooks/rollback.md` for this client **before** any live route change.

## Hard rules

- **Do not invent carrier dial codes.** Follow only the existing provider's own
  documented forwarding process. If the provider's documentation is not available,
  stop and record a blocker.
- **Verify that voicemail does not answer before the AI.** For overflow modes, check
  how the provider's ring timer and the GoHighLevel answer timer interact.
- **Verify that the human-transfer destination does not forward back to the AI number.**
  Use a distinct dispatcher destination when needed.
- Keep the customer's advertised number.
- No number purchase without approved spend (cost NEEDS_EVIDENCE).

## Steps

1. Phone destination (step 36): inspect available numbers and the connected provider
   in the client location's phone settings. Use an existing suitable number, or obtain
   one only under approved spend. Record ownership, capabilities, recurring and usage
   charges (from the provider, never estimated), any verification, and the inbound
   Voice AI agent it is attached to. Number: `<<FILL: GHL_PHONE_NUMBER>>`.
2. Messaging requirements (step 37): check the provider's current requirements for the
   channels actually in use. Voice approval does not imply SMS; SMS confirmations need
   current messaging (A2P) registration and consent setup first.
3. Routing mode (step 38): recommended initial mode is after hours and weekends.
   Business hours (America/Chicago, including holidays): `<<FILL: schedule>>`.
   Confirm the carrier supports the chosen mode; save the current configuration first.
4. Forwarding (step 39): configure per the provider's documentation only.
   Forwarding destination: `<<FILL: destination>>`. Configured at
   `<<FILL: timestamp UTC>>` by `<<FILL: person>>`.
5. Verify every route before switching traffic (step 40), with authorized external
   test calls: business-hours handling, after-hours handling, unanswered calls, human
   transfer (successful and unanswered). Confirm the greeting uses the correct
   business name and call logs and follow-up tasks land in the correct client location.
   Record call log IDs for acceptance tests T05, T07, T11.

## If anything goes wrong

Calls drop, loop, reach the wrong business, or the assistant makes unsafe promises:
restore the prior route using `runbooks/rollback.md`, pause the affected agent, and
verify one inbound call.

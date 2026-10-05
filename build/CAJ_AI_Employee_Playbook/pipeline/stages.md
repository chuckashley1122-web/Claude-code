# Prospect pipeline stages

Source: playbook line 297. Creating these stages in a GoHighLevel pipeline is a
human, logged-in task (see `docs/UI-ONLY-CHECKLIST.md`, step 42).

## Forward stages (in order)

| # | Stage | Enter when | Evidence |
|---|---|---|---|
| 1 | Qualified | Research answers the three niche questions (after-hours calls, callers try another provider, repeated questions) as yes or unknown-to-ask | prospect row with sources |
| 2 | Contacted | First authorized outreach on one channel | channel and date in the prospect row |
| 3 | Replied | The prospect answered (any reply other than opt-out) | reply reference |
| 4 | Demo booked | Appointment exists in the demo calendar (WF01) | appointment ID |
| 5 | Demo held | Meeting took place | meeting notes |
| 6 | Proposal sent | Agreed scope sent after the meeting | proposal reference |
| 7 | Paid and onboarding | Verified active subscription (WF02); never on a success-page visit alone | subscription ID |
| 8 | Active | Activation after all enabled-channel critical tests pass and human approval | activation time, config version, rollback owner |

## Terminal stages

| Stage | Enter when |
|---|---|
| Not now | Prospect declines for now; no further follow-up in the current cadence |
| Lost | Prospect declines, opts out, is disqualified, or stops responding after the final follow-up |

## Rules

- Dedupe keys: business `domain` and `phone` (normalized). One prospect row per business.
- An opt-out moves the prospect to Lost immediately and sets `opt_out` to `yes`; it is
  never contacted again on any channel.
- Reporting (step 51): demo show rate = demos held / demos booked; close rate = paid
  customers / demos held. Use observed data only; never assumed revenue recovered.

# Runbook: rollback (phone routing and website)

Covers source step 41 and acceptance test T12. **Human-only.** Rollback requires a
human at the provider console. Fill sections A and B **before** any live change;
an empty rollback record blocks activation.

## A. Record before changing anything (required)

| Item | Value |
|---|---|
| Previous forwarding destination | `<<FILL: previous destination>>` |
| Previous schedule (days, hours, holidays, timezone) | `<<FILL: previous schedule>>` |
| Previous voicemail behaviour (who answers, after how many rings/seconds) | `<<FILL: previous voicemail behaviour>>` |
| Provider and account reference (no passwords) | `<<FILL: provider>>` |
| Provider-specific restoration steps (from the provider's own documentation) | `<<FILL: restoration steps>>` |
| Responsible person for rollback | `<<FILL: name and contact>>` |
| Recorded by / timestamp (UTC) | `<<FILL: name, timestamp>>` |
| Website footer / widget backup location | `<<FILL: backup location>>` |

## B. Rollback triggers

Restore the prior route and pause the affected agent if calls drop, loop, route to the
wrong business, or the assistant produces unsafe promises.

## C. Restore

1. The responsible person restores the previous forwarding destination, schedule, and
   voicemail behaviour using the recorded provider-specific steps. No invented carrier
   codes.
2. Pause the affected AI agent in the client location.
3. Website: restore the backed-up footer or remove the widget selection.

## D. Verify (required)

1. **Place one inbound call after restoration** and confirm it reaches the original
   destination with the original voicemail behaviour.
2. Record the call log ID and timestamp in `records/Build_Log.csv`, and the result of
   acceptance test T12 with `scripts/run_test_checklist.py`.
3. Tell the customer the route has been restored and how it was verified.

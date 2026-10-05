# UI work order 002-06: Configure production phone routing with a verified rollback

Build: SPEC-02 AI Employee (`build/CAJ_AI_Employee_Playbook/`). Human, logged-in work only; the coding agent cannot do any of this.

- **Platform:** GoHighLevel phone settings, carrier console
- **Source steps:** 36-41
- **Procedure:** build/CAJ_AI_Employee_Playbook/runbooks/phone-routing.md and build/CAJ_AI_Employee_Playbook/runbooks/rollback.md
- **Approval gate:** Approval: phone routing (Chuck and owner); number and telephony costs NEEDS_EVIDENCE; A2P registration if SMS is in scope.

## Actions

1. Fill the rollback record before any change.
2. Follow only the provider's documented forwarding process; no invented dial codes.
3. Verify voicemail does not answer before the AI and the transfer destination does not forward back to the AI number.
4. Test every mode with authorized external calls; restore and verify one inbound call (T12).

## Evidence to capture

- Rollback record, call log IDs for T05, T07, T11, T12.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- No price in any outbound message, page, or AI reply (meeting-first); pricing questions go to https://ca-jenterprises.com/ai.
- Synthetic test contacts only (example.com addresses, 555-01xx numbers) until activation is approved.
- GoHighLevel build location is `UWc5vKBgFVPdxNTRAy2s` (case-sensitive); confirm on screen before any change.
- Record every object ID, timestamp, and evidence path in `build/CAJ_AI_Employee_Playbook/records/` and run `python3 scripts/validate_records.py` from the build root.

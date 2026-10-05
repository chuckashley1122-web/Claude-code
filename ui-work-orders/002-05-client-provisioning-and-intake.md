# UI work order 002-05: Provision a paying client and collect the production intake

Build: SPEC-02 AI Employee (`build/CAJ_AI_Employee_Playbook/`). Human, logged-in work only; the coding agent cannot do any of this.

- **Platform:** GoHighLevel agency (subaccount, snapshot), owner meeting
- **Source steps:** 26-28, 30-33
- **Procedure:** build/CAJ_AI_Employee_Playbook/runbooks/ghl-account-and-snapshot.md (C, D); build/CAJ_AI_Employee_Playbook/intake/
- **Approval gate:** Approval: GHL changes; subaccount/snapshot costs NEEDS_EVIDENCE.

## Actions

1. Only after a verified subscription: create the subaccount and request the HVAC snapshot.
2. Audit the snapshot: disable inherited outbound; replace template values; remove example facts.
3. Owner fills `intake/client-intake-form.md`; validate with `python3 scripts/validate_records.py --intake <file>`.
4. Build the production KB and booking action; run T01, T03, T04, T08, T10.

## Evidence to capture

- Location ID, snapshot version, intake JSON, test evidence.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- No price in any outbound message, page, or AI reply (meeting-first); pricing questions go to https://ca-jenterprises.com/ai.
- Synthetic test contacts only (example.com addresses, 555-01xx numbers) until activation is approved.
- GoHighLevel build location is `UWc5vKBgFVPdxNTRAy2s` (case-sensitive); confirm on screen before any change.
- Record every object ID, timestamp, and evidence path in `build/CAJ_AI_Employee_Playbook/records/` and run `python3 scripts/validate_records.py` from the build root.

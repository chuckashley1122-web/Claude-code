# UI work order 002-08: Run acceptance tests T01-T12 and record results

Build: SPEC-02 AI Employee (`build/CAJ_AI_Employee_Playbook/`). Human, logged-in work only; the coding agent cannot do any of this.

- **Platform:** GoHighLevel agent test interface, widget, phone
- **Source steps:** 33, 40, 49
- **Procedure:** build/CAJ_AI_Employee_Playbook/tests/test-run-protocol.md and build/CAJ_AI_Employee_Playbook/tests/T01-T12.csv
- **Approval gate:** Approval: activation (Chuck and owner).

## Actions

1. Run each test with synthetic contacts and authorized destinations.
2. Record each with `python3 scripts/run_test_checklist.py --test-id Txx --result PASS|FAIL|N/A --evidence <ref>`.
3. No activation until the tool exits 0 and Chuck approves.

## Evidence to capture

- Evidence references for all twelve tests.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- No price in any outbound message, page, or AI reply (meeting-first); pricing questions go to https://ca-jenterprises.com/ai.
- Synthetic test contacts only (example.com addresses, 555-01xx numbers) until activation is approved.
- GoHighLevel build location is `UWc5vKBgFVPdxNTRAy2s` (case-sensitive); confirm on screen before any change.
- Record every object ID, timestamp, and evidence path in `build/CAJ_AI_Employee_Playbook/records/` and run `python3 scripts/validate_records.py` from the build root.

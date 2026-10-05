# UI work order 002-07: Build workflows WF01-WF04 in GoHighLevel

Build: SPEC-02 AI Employee (`build/CAJ_AI_Employee_Playbook/`). Human, logged-in work only; the coding agent cannot do any of this.

- **Platform:** GoHighLevel workflow builder
- **Source steps:** 14, 25, 35, 50
- **Procedure:** build/CAJ_AI_Employee_Playbook/workflows/WF01_demo_preparation.md ... WF04_knowledge_maintenance.md
- **Approval gate:** Approval: GHL changes.

## Actions

1. Build each workflow exactly as specified: trigger, filter, dedupe key, action, notification permission, review route.
2. Keep inherited snapshot workflows disabled unless in scope.
3. Re-send duplicate synthetic events to prove one record per unique event (T10).

## Evidence to capture

- Workflow IDs and T10 evidence.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- No price in any outbound message, page, or AI reply (meeting-first); pricing questions go to https://ca-jenterprises.com/ai.
- Synthetic test contacts only (example.com addresses, 555-01xx numbers) until activation is approved.
- GoHighLevel build location is `UWc5vKBgFVPdxNTRAy2s` (case-sensitive); confirm on screen before any change.
- Record every object ID, timestamp, and evidence path in `build/CAJ_AI_Employee_Playbook/records/` and run `python3 scripts/validate_records.py` from the build root.

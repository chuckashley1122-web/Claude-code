# UI work order 002-10: Optional demonstration ads (out of scope until authorized)

Build: SPEC-02 AI Employee (`build/CAJ_AI_Employee_Playbook/`). Human, logged-in work only; the coding agent cannot do any of this.

- **Platform:** Meta Ads Manager, optional video tool
- **Source steps:** 46-48
- **Procedure:** build/CAJ_AI_Employee_Playbook/docs/COST-AND-APPROVALS.md
- **Approval gate:** Approval: spend (ads and tools NEEDS_EVIDENCE).

## Actions

1. Do nothing unless Chuck authorizes ads in writing with a budget.
2. Never touch or reallocate the live campaign CAJ_HVAC27_US_PURCHASE_TEST02 (frozen).
3. Higgsfield only if already owned and authorized.

## Evidence to capture

- Written authorization, if any.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- No price in any outbound message, page, or AI reply (meeting-first); pricing questions go to https://ca-jenterprises.com/ai.
- Synthetic test contacts only (example.com addresses, 555-01xx numbers) until activation is approved.
- GoHighLevel build location is `UWc5vKBgFVPdxNTRAy2s` (case-sensitive); confirm on screen before any change.
- Record every object ID, timestamp, and evidence path in `build/CAJ_AI_Employee_Playbook/records/` and run `python3 scripts/validate_records.py` from the build root.

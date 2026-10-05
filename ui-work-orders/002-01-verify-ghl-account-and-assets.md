# UI work order 002-01: Verify the GoHighLevel account and locate licensed assets

Build: SPEC-02 AI Employee (`build/CAJ_AI_Employee_Playbook/`). Human, logged-in work only; the coding agent cannot do any of this.

- **Platform:** GoHighLevel (agency login), training portal
- **Source steps:** 01, 02, 03
- **Procedure:** build/CAJ_AI_Employee_Playbook/runbooks/ghl-account-and-snapshot.md (sections A and B)
- **Approval gate:** GHL changes: none in this order (read-only).

## Actions

1. Log in and confirm location ID and name on screen; screenshot.
2. Check permissions for subaccounts, snapshots, websites, AI agents, knowledge bases, calendars, payments, workflows, phone settings.
3. Locate the licensed HVAC pack and the missing source materials (seven-page SOP, demo workshop, niche scripts, outbound email SOP, phone registration SOP, lab account request form); record links and versions, never reconstruct contents.

## Evidence to capture

- Build_Log rows for steps 01-03; Asset_Register rows; Blockers rows for anything missing.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- No price in any outbound message, page, or AI reply (meeting-first); pricing questions go to https://ca-jenterprises.com/ai.
- Synthetic test contacts only (example.com addresses, 555-01xx numbers) until activation is approved.
- GoHighLevel build location is `UWc5vKBgFVPdxNTRAy2s` (case-sensitive); confirm on screen before any change.
- Record every object ID, timestamp, and evidence path in `build/CAJ_AI_Employee_Playbook/records/` and run `python3 scripts/validate_records.py` from the build root.

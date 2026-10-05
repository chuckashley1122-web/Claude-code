# UI work order 002-02: Draft the offer page and build the demo calendar

Build: SPEC-02 AI Employee (`build/CAJ_AI_Employee_Playbook/`). Human, logged-in work only; the coding agent cannot do any of this.

- **Platform:** GoHighLevel Sites/Funnels, Calendars, Forms
- **Source steps:** 09-13
- **Procedure:** build/CAJ_AI_Employee_Playbook/runbooks/demo-page-and-calendar.md (offer page, demo calendar)
- **Approval gate:** Approval: GHL changes; publishing; domain connection (cost NEEDS_EVIDENCE).

## Actions

1. Duplicate a CA-J page into draft `CAJ AI Employee HVAC Offer`; CTA to https://ca-jenterprises.com/ai; no price on the page.
2. Create `CAJ HVAC AI Demo` calendar (15 minutes, America/Chicago, real availability).
3. Book and cancel one synthetic appointment; confirm availability returns.
4. Keep the page as a draft until publication and any domain connection are approved.

## Evidence to capture

- Page ID, calendar ID, booking URL, test-booking screenshot.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- No price in any outbound message, page, or AI reply (meeting-first); pricing questions go to https://ca-jenterprises.com/ai.
- Synthetic test contacts only (example.com addresses, 555-01xx numbers) until activation is approved.
- GoHighLevel build location is `UWc5vKBgFVPdxNTRAy2s` (case-sensitive); confirm on screen before any change.
- Record every object ID, timestamp, and evidence path in `build/CAJ_AI_Employee_Playbook/records/` and run `python3 scripts/validate_records.py` from the build root.

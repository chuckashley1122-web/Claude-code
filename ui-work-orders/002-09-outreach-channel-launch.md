# UI work order 002-09: Launch authorized prospect outreach (email, DM, calls)

Build: SPEC-02 AI Employee (`build/CAJ_AI_Employee_Playbook/`). Human, logged-in work only; the coding agent cannot do any of this.

- **Platform:** Email sending platform, Instagram, phone / GHL dialer
- **Source steps:** 42-45
- **Procedure:** build/CAJ_AI_Employee_Playbook/outreach/ and build/CAJ_AI_Employee_Playbook/pipeline/
- **Approval gate:** Approval: each channel separately; sending platform, domains, and dialer costs NEEDS_EVIDENCE.

## Actions

1. Research the first batch of 25 businesses into the prospect template; dedupe by domain and phone.
2. Human sets up sending domain authentication, suppression, and reply routing.
3. Render drafts with `python3 scripts/render_templates.py --for-send`; send a reviewed first batch of 10 only after channel approval.
4. Follow `outreach/followup-cadence.md`; honor opt-outs permanently.

## Evidence to capture

- Batch review record, per-contact status.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- No price in any outbound message, page, or AI reply (meeting-first); pricing questions go to https://ca-jenterprises.com/ai.
- Synthetic test contacts only (example.com addresses, 555-01xx numbers) until activation is approved.
- GoHighLevel build location is `UWc5vKBgFVPdxNTRAy2s` (case-sensitive); confirm on screen before any change.
- Record every object ID, timestamp, and evidence path in `build/CAJ_AI_Employee_Playbook/records/` and run `python3 scripts/validate_records.py` from the build root.

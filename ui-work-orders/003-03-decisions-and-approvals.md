# UI work order 003-C: Resolve open decisions for the high-ticket HVAC offer

**Spec:** SPEC-03 (High-Ticket Agency). **Build root:** `build/03-high-ticket/`. **Owner:** Chuck Ashley.

Open `build/03-high-ticket/ui-tasks/HUMAN-DECISIONS.md`. It lists every value still marked `NEEDS_EVIDENCE` and every
approval gate, each with a next action.

## Highest priority

1. Service area, staffed hours and calendar working hours (unblocks the calendar and the 5-minute call task).
2. Facebook Page ID, ad account ID, privacy policy URL, verified sending email, SMS eligibility.
3. Service term, cancellation terms and payment processor (unblocks the close pack and payment testing).
4. Whether any guarantee is offered (default: no numerical guarantee).

## How to record a decision

Update `config/build_config.json` (add `<key>_evidence` for any ID), then run `python tools/validate_config.py` and
`python tools/build_all.py`. Never paste a token, key or password into any file; secrets go only in a local `.env`.

## Approval gates

Ad spend, launch, payment product, image tool, messaging fees: REQUIRES EXPLICIT HUMAN APPROVAL in writing.

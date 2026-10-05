# UI work order 002-04: Create the recurring payment product and test checkout

Build: SPEC-02 AI Employee (`build/CAJ_AI_Employee_Playbook/`). Human, logged-in work only; the coding agent cannot do any of this.

- **Platform:** GoHighLevel Payments, payment processor
- **Source steps:** 24, 25, 29
- **Procedure:** build/CAJ_AI_Employee_Playbook/runbooks/payment-product.md
- **Approval gate:** Approval: payments; processor fees NEEDS_EVIDENCE.

## Actions

1. Create draft product `CAJ HVAC AI Employee Monthly` with the locked CA&J terms set by Chuck; setup waived.
2. Test success and failure in processor test mode only; never real card data.
3. Only after an authorized sale: send the checkout link; verify the subscription in the system (a success page is not proof).

## Evidence to capture

- Product ID, test results, subscription ID.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- No price in any outbound message, page, or AI reply (meeting-first); pricing questions go to https://ca-jenterprises.com/ai.
- Synthetic test contacts only (example.com addresses, 555-01xx numbers) until activation is approved.
- GoHighLevel build location is `UWc5vKBgFVPdxNTRAy2s` (case-sensitive); confirm on screen before any change.
- Record every object ID, timestamp, and evidence path in `build/CAJ_AI_Employee_Playbook/records/` and run `python3 scripts/validate_records.py` from the build root.

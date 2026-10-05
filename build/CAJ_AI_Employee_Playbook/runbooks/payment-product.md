# Runbook: recurring payment product and checkout

Covers source steps 24-25 and 29. **Human-only** (GoHighLevel Payments and the
payment processor). Approval gate: `REQUIRE_HUMAN_APPROVAL_FOR_PAYMENTS = True`.

## Rules

- The client enters payment information privately in the checkout. Nobody asks for
  card numbers aloud, records them, or types them into any file, form, or recording.
- Never enter real card data for a test; use the processor's supported test procedure
  in test mode.
- A success-page visit is never proof of payment. Verify payment and subscription
  status in the system before marking anything paid.
- The product amount is the locked CA&J term set by Chuck (internal reference:
  `guardrails/locked_pricing.json`). The source's training figures are never used
  (see `docs/SOURCE-CLAIMS.md`). No amount appears in any outbound message.

## Steps

1. In Payments > Products create a draft product `CAJ HVAC AI Employee Monthly` with the
   confirmed amount, currency, and monthly recurrence. Setup charge: none (waived).
   Product ID: `<<FILL: GHL_PRODUCT_ID>>`.
2. Create a payment link or checkout that displays the recurring terms and how usage is
   treated.
3. Confirm the processor and that test mode is on. Run a successful and a failed test
   payment with the processor's test procedure. Record evidence.
4. For an authorized sale only: Chuck explains the total due now and future charges in
   the meeting, then sends the checkout link. The customer pays privately.
5. Verify the subscription is active in the system (this triggers WF02). Record the
   subscription ID and verification evidence.
6. Usage billing (step 29): verify the agency's actual billing arrangement for AI and
   phone usage, including any rebilling support. Do not assume every plan supports
   the method described in the source.

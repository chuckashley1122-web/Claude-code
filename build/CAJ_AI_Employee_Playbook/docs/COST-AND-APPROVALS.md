# Cost and approvals

**No charges or purchases of any kind are authorized by this spec.** Nothing in this
repository buys, subscribes, charges a card, provisions a number, registers a
domain, or spends on ads. `SPEND_CAP_USD = 0.00` and `DRY_RUN = true` by default.

## Locked CA&J commercial terms (internal only)

| Term | Value |
|---|---|
| Tech fee | $650/mo (`TECH_FEE_MONTHLY_USD = 650`) |
| Setup fee | WAIVED (`SETUP_FEE_USD = 0`) |
| Per booked appointment | $250 to $300 (`PER_BOOKED_APPOINTMENT_MIN_USD = 250`, `PER_BOOKED_APPOINTMENT_MAX_USD = 300`) |
| Machine-readable copy | `guardrails/locked_pricing.json` (used only by `scripts/cost_estimate.py`) |

**MEETING-FIRST.** These terms are internal. No price ever appears in an email, DM,
call script, chat, page, ad, or AI-agent reply. Pricing intent routes to a meeting at
https://ca-jenterprises.com/ai (`guardrails/meeting_first.py`), and
`guardrails/pricing_guard.py` blocks any price in outbound text. Chuck discusses
terms in the live meeting only.

## Source figures are not CA&J prices

The source playbook's pricing figures (the recurring-fee draft default, the setup-fee
draft default, the trainer's monthly range, the attendee's setup-plus-monthly sale,
and the ambiguous upsell; entries SC-01 to SC-05 in `docs/SOURCE-CLAIMS.md`) are
training values from the recording, not CA&J prices. They must never be quoted in any
outbound message or AI reply, and are blocked by `guardrails/claim_guard.py`.

## Approval gates

| Gate | Constant | Who approves |
|---|---|---|
| Any spend | `REQUIRE_HUMAN_APPROVAL_FOR_SPEND = True` | Chuck, in writing, per item and amount |
| Any GoHighLevel change | `REQUIRE_HUMAN_APPROVAL_FOR_GHL = True` | Chuck |
| Any outbound message or call | `REQUIRE_HUMAN_APPROVAL_FOR_OUTBOUND = True` | Chuck, per channel and batch |
| Any phone routing change | `REQUIRE_HUMAN_APPROVAL_FOR_PHONE_ROUTING = True` | Chuck and the client owner |
| Any payment object or charge | `REQUIRE_HUMAN_APPROVAL_FOR_PAYMENTS = True` | Chuck; the client pays privately |
| Any live path in code | `DRY_RUN=false` **and** `ALLOW_LIVE=true` | human only (no live path exists in this build) |

## Spend items (all require approval; no amount is known)

| Service | What it is for | Approval | Cost |
|---|---|---|---|
| GoHighLevel agency plan / subaccount allocation | hosting the client location, agent, calendar, workflows | approval required | NEEDS_EVIDENCE |
| Licensed HVAC snapshot / niche pack | demo agent and knowledge base foundation | approval required | NEEDS_EVIDENCE |
| AI usage (text and voice agent) | conversations and calls handled by the assistant | approval required | NEEDS_EVIDENCE |
| Phone number | inbound destination for the Voice AI agent | approval required | NEEDS_EVIDENCE |
| Telephony minutes (inbound, transfer, dialer) | call handling and transfers | approval required | NEEDS_EVIDENCE |
| A2P messaging registration | only if SMS confirmations are in scope | approval required | NEEDS_EVIDENCE |
| Payment processor fees | collecting the client subscription | approval required | NEEDS_EVIDENCE |
| Email sending platform and sending domains | authorized outreach | approval required | NEEDS_EVIDENCE |
| Domain connection for the offer page | publishing on ca-jenterprises.com | approval required | NEEDS_EVIDENCE |
| Meeting provider integration | demo calendar video link | approval required | NEEDS_EVIDENCE |
| GHL dialer / LeadConnector app | optional calling | approval required | NEEDS_EVIDENCE |
| Meta ads (Meta Ads Manager) | optional ads; out of scope here | approval required | NEEDS_EVIDENCE |
| Higgsfield (named in the source, line 315) | optional ad scene generation; only if already owned | approval required | NEEDS_EVIDENCE |
| Support labour | weekly maintenance and handoff review | approval required | NEEDS_EVIDENCE |

Monthly contribution per client is modelled internally by `scripts/cost_estimate.py`
from these items once a human enters verified rates in `rates.yaml`.

## Standing rules

- Never advertise unlimited usage; any included usage needs a stated allowance and
  overage terms (source line 133).
- The live Meta campaign CAJ_HVAC27_US_PURCHASE_TEST02 stays frozen; no budget is
  reallocated automatically.
- No purchase, domain, number, subscription, or ad spend without explicit written
  human approval.

# Chuck's Daily Grind — credentials and integrations

Names and scopes only. **No secrets in this file, ever.**

Every credential is issued to Chuck's Daily Grind alone. Nothing is shared with
CA-J Enterprises or CA-J Consulting.

| Integration | Needed for | Minimum scope | Phase | Status |
|---|---|---|---|---|
| LLM provider API key | All agent work | Inference only. Dedicated key per business. | 1 | ☐ |
| SearXNG | Coffee topic research | Bundled, local, no credential | 1 | ☐ |
| Website (own) | Content context, internal links | Public read of `chucksdailygrind.com` | 1 | ☐ |
| Google Search Console | Content performance | **Read-only**, single property | 2 | ☐ |
| Google Analytics | Traffic and conversion reporting | **Read-only**, single property | 2 | ☐ |
| Ecommerce platform | Product catalogue sync | **Read-only** on products. Never orders, never customers. | 2 | ☐ |
| Email platform | Campaign drafts | Draft/compose only. **Never** send, never list export. | 3 | ☐ |
| Social scheduler | Calendar drafts | Draft only if the platform supports it. Otherwise no connection. | 3 | ☐ |

Never connected:

- Payment processor
- Customer records or order history
- Supplier contracts or cost pricing
- Anything with a send or publish scope

## Rules

1. **Read-only until proven.** Nothing gets a write scope during the pilot.
2. **Products yes, customers no.** The catalogue sync is for product facts. Order
   and customer data has no role in content generation and is not connected.
3. **No send scope.** Drafting produces text. A human sends it.
4. **No list export.** The email integration must not be able to read subscriber
   lists.
5. **One key per business.** Shared keys break cost attribution and widen the
   blast radius of any leak.
6. **Rotate on exposure**, without deliberating.
7. **Phase 3 needs an explicit decision from Chuck**, per integration.

## Issuance log

| Date | Credential | Scope granted | Issued by | Rotated |
|---|---|---|---|---|
| | | | | |

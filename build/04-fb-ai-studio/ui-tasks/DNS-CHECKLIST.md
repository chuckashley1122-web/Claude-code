# DNS checklist (human, at the domain registrar)

> **DOMAIN PURCHASE REQUIRES EXPLICIT HUMAN APPROVAL.** Buying a domain is a spend item. Do not buy one without a written approval reference (APPROVAL_DOMAIN_PURCHASE).

## CNAME record
| Field | Value |
|---|---|
| Type | CNAME |
| Host | <subdomain>: `offer`, `call` or `contact` |
| Value | NEEDS_EVIDENCE - copy it from AI Studio > Publish > Add Custom Domain (the source's video showed a value that is unverified) |
| Domain | NEEDS_EVIDENCE |

- [ ] Registrar > DNS / Advanced DNS > Add New Record with the values above > Save.
- [ ] Wait for propagation (source suggests 10-30 minutes; retry Verify every 5 minutes).
- [ ] AI Studio > Publish > Verify DNS > Publish.
- [ ] Open the live URL and confirm it loads; record it as landing_page_url in config/build_config.json and rebuild.

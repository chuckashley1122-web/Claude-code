# Approved knowledge sources — ca-j-consulting

The files referenced by `../knowledge-manifest.yml` live here. **Everything in
this directory except this README is gitignored**, because these are real
business documents: brand guidelines, product data, pricing, internal reference
material.

Adding a source is a deliberate act:

1. Put the file here.
2. Add or update its entry in `../knowledge-manifest.yml`.
3. Set `approved: true` and fill in `approver`.
4. Confirm `contains_pii: false` is actually true — read the file, do not assume.
5. Re-index the workspace in Odysseus.

Nothing is indexed unless it is listed in the manifest and marked approved.

Never put in this directory: customer records, contact lists, credentials, or —
for CA-J Consulting especially — anything containing borrower data. See
`../../_shared/safety-rules.md` rules 15–17.

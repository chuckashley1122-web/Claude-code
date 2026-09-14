# Build Specs

Six implementation specifications, one per playbook. These are what you point an
AI coding agent at.

| Spec | Source playbook |
|------|-----------------|
| [SPEC-01 — 8 Best AI Automations](SPEC-01-8-best-ai-automations.md) | [01](../docs/playbooks/01-8-best-ai-automations.md) |
| [SPEC-02 — AI Employee](SPEC-02-ai-employee.md) | [02](../docs/playbooks/02-ai-employee-action-plan.md) |
| [SPEC-03 — High-Ticket Agency](SPEC-03-high-ticket-agency.md) | [03](../docs/playbooks/03-high-ticket-agency-action-plan.md) |
| [SPEC-04 — Facebook Ads + AI Studio](SPEC-04-facebook-ads-ai-studio.md) | [04](../docs/playbooks/04-facebook-ads-ghl-ai-studio-sop.md) |
| [SPEC-05 — GHL AI Studio SEO](SPEC-05-ghl-ai-studio-seo.md) | [05](../docs/playbooks/05-ghl-ai-studio-seo.md) |
| [SPEC-06 — Single Workflow](SPEC-06-single-workflow.md) | [06](../docs/playbooks/06-single-workflow.md) |

Each spec separates the **code layer** an agent can build (files, config,
fixtures, validators, dry-run pipelines) from the **UI layer** a human must do in
a browser. A coding agent has no browser, so it cannot touch GoHighLevel, Meta
Ads Manager, n8n Cloud, or any logged-in interface — those become written work
orders.

## Provenance

These markdown files were extracted from
[`../docs/recovery/CA-J-Growth-System-Build-Specs.docx`](../docs/recovery/CA-J-Growth-System-Build-Specs.docx)
by [`../tools/docx_to_specs.py`](../tools/docx_to_specs.py), because the original
`specs/` folder was wiped on 2026-09-13 and that Word document was the only
survivor. See [`../docs/recovery/`](../docs/recovery/) for the account.

Known losses from the Word round trip: inline `**bold**` and `` `code` `` markers
are gone except where a run used the Consolas font, and ordered lists all render
as `1.` (markdown renumbers them correctly on display). Headings, tables,
numbered steps, bullets, and body text are intact.

To regenerate:

```bash
python tools/docx_to_specs.py          # docx -> specs/*.md
python tools/build_specs_docx.py       # specs/*.md -> docx  (edit ROOT first)
```

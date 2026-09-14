# CA-J Growth System — Playbooks

Six source playbooks for the CA-J Enterprises growth build. Each one was written
from a training video transcript and turned into an ordered, testable
implementation plan. They are the **authoritative source** the build specs were
derived from.

| # | Playbook | What it covers |
|---|----------|----------------|
| 01 | [8 Best AI Automations](01-8-best-ai-automations.md) | Eight n8n/Vapi/OpenAI automations — voice agent, lead gen, UGC spy, faceless video, content agent, FAQ chatbot, YouTube idea generator, HeyGen avatar. Includes build order and cost estimate. |
| 02 | [AI Employee Action Plan](02-ai-employee-action-plan.md) | Selling and fulfilling an after-hours AI employee in GoHighLevel. HVAC in Austin / Round Rock. Steps 01–51: offer, demo, sales meeting, provisioning, phone routing, acceptance tests. |
| 03 | [High Ticket Agency Action Plan](03-high-ticket-agency-action-plan.md) | Agency client acquisition: niche → offer → Meta image ads → qualification form → GHL sync → sales call → close → onboard. Steps 01–59. |
| 04 | [Facebook Ads + GHL AI Studio SOP](04-facebook-ads-ghl-ai-studio-sop.md) | Six-phase local lead gen: Meta Business Portfolio, AI Studio landing page, pipeline + speed-to-lead workflows, creatives, Conversions API, campaign launch. |
| 05 | [GHL AI Studio SEO + Full Stack](05-ghl-ai-studio-seo.md) | SSR pages, server functions, secrets, and a server-processed inquiry flow wired to GHL. Steps 1–36 plus an optional estimator. |
| 06 | [Single Workflow (HVAC Research Pilot)](06-single-workflow.md) | Build **one** workflow end to end: HVAC company URLs → source-backed research brief. Contracts, fixtures, tests, seven-day improvement cycle. |

## How these are meant to be used

- Point an AI coding agent at the **markdown**, never at a `.docx` — Word files
  do not read reliably.
- Every playbook separates what the source video actually said from implementation
  additions. Do not treat the additions as verbatim instructions from a presenter,
  and do not treat a presenter's numbers as verified results.
- Unresolved values are marked (`REQUIRED`, `UNRESOLVED`, `TODO`, `NEEDS_EVIDENCE`).
  Leave them marked rather than guessing.

## Standing guardrails carried by these documents

- **No charges of any kind** — no upgrades, domains, ad spend, or subscriptions.
- **Dry-run only** — nothing sends, writes live, or posts without explicit
  authorization for that specific action.
- The live Meta campaign `CAJ_HVAC27_US_PURCHASE_TEST02` stays frozen; its ad
  account is connected to a real payment method.
- Email sending is blocked upstream (Postmark in test mode; no authenticated
  sending domain). SMS needs A2P 10DLC approval.
- A coding agent has no browser, so all GoHighLevel and Meta Ads Manager work
  becomes a written work order for a human.

The build specs derived from these playbooks live in [`../../specs/`](../../specs/).
Tooling that renders them to and from Word lives in [`../../tools/`](../../tools/).
The Word copies and the account of the 2026-09-13 wipe are in
[`../recovery/`](../recovery/).

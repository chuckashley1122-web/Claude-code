# UI work order 001-01: n8n account, workflow import, and credentials

Build: SPEC-01 8 Best AI Automations (`build/automation-suite/`). Human, logged-in work only; the coding agent cannot do any of this.

- **Platform:** n8n Cloud (or self-hosted n8n), each approved vendor's dashboard
- **Source steps:** automations 01-08 (all "Workflow from screenshot" lines)
- **Procedure:** build/automation-suite/docs/DEPLOY-RUNBOOK.md (steps 2-5)
- **Approval gate:** n8n account is a spend item (cost NEEDS_EVIDENCE); each credential is created only for a service already approved in docs/COST-AND-APPROVALS.md.

## Actions

1. From `build/automation-suite/`, run the six offline checks in the README and keep the output as evidence.
2. Create the n8n account after approval; create the n8n API key and store it only in n8n or a local, uncommitted `.env`.
3. Import `workflows/_common_error_handler.json` first, then `01`-`08`; set each workflow's error workflow to it.
4. Every node type and parameter is unverified (built from screenshot descriptions). Fix any node n8n rejects and record each change; the `caj_guardrails` sub-workflow calls must be replaced with an equivalent guard step before anything goes live.
5. Replace each `*_SET_BY_HUMAN` placeholder (Twilio account SID, voice ids, avatar id) inside n8n, never in the repo.
6. Leave every workflow inactive.

## Evidence to capture

- Import screenshots per workflow, list of node fixes, credential names (never values), offline check output.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- No price in any outbound message, page, or AI reply (meeting-first); pricing questions go to https://ca-jenterprises.com/ai.
- Synthetic test contacts only (example.com addresses, 555-01xx numbers) until activation is approved.
- Source-author numbers (docs/SOURCE-CLAIMS.md) are unverified and never CA-J results.

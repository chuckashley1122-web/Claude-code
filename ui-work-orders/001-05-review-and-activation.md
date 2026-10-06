# UI work order 001-05: Copy review, first live test, and activation

Build: SPEC-01 8 Best AI Automations (`build/automation-suite/`). Human, logged-in work only; the coding agent cannot do any of this.

- **Platform:** n8n, Ayrshare/Blotato, Gmail, Vapi
- **Source steps:** 01 step 6, 02 steps 4-5, 04 step 4, 05 step 5, 08 step 4
- **Procedure:** build/automation-suite/docs/DEPLOY-RUNBOOK.md (steps 18-20)
- **Approval gate:** REQUIRE_HUMAN_APPROVAL_FOR_OUTBOUND and REQUIRE_HUMAN_APPROVAL_FOR_PUBLISH; marketing/legal sign-off.

## Actions

1. Marketing/legal review of all fifteen prompts and every outbound template; review the dry-run drafts in `data/out/mail/` and `data/out/publish/intended.jsonl` after `python3 scripts/run_dry.py`.
2. First live test per automation with synthetic contacts only, one at a time, with `DRY_RUN=false` and `ALLOW_LIVE=1` set by a human.
3. Activate outreach or publishing for real prospects/accounts only with explicit written authorization per batch.

## Evidence to capture

- Reviewer sign-off, n8n execution logs for each test, authorization record per activation.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- No price in any outbound message, page, or AI reply (meeting-first); pricing questions go to https://ca-jenterprises.com/ai.
- No source-author result may be presented as a CA-J result; no unverified proof in prospect-facing copy.

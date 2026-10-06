# UI work order 001-04: n8n vs GoHighLevel architecture decision

Build: SPEC-01 8 Best AI Automations (`build/automation-suite/`). Human decision; the coding agent cannot make it or touch GoHighLevel.

- **Platform:** GoHighLevel (agency login), n8n
- **Source steps:** none (the source is n8n-only); spec section 8 item 1
- **Procedure:** build/automation-suite/docs/DEPLOY-RUNBOOK.md (steps 1 and 17)
- **Approval gate:** architecture decision by Chuck; any GHL change needs REQUIRE_HUMAN_APPROVAL_FOR_GHL sign-off.

## Actions

1. Decide per automation whether it runs on n8n, inside GoHighLevel, or both. The CA-J house stack names GHL as the only build location; this suite builds only the n8n/code layer.
2. If GHL is used for voice (01) or chat (06): configure calendars, conversation AI / voice agent prompts, knowledge base, widget, and phone numbers in the GHL UI, reusing the prompt text and meeting-first rules from `prompts/`.
3. Confirm the build location id shown on screen matches `config/constants.py` exactly (case-sensitive) before any change.

## Evidence to capture

- Written decision per automation; GHL object ids and screenshots for anything created.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- No price in any outbound message, page, or AI reply (meeting-first); pricing questions go to https://ca-jenterprises.com/ai.
- CA-J B2B brands never blend with consumer brands in any GHL asset.

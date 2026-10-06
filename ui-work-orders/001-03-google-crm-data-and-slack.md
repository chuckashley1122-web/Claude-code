# UI work order 001-03: Google OAuth, CRM, data stores, and Slack

Build: SPEC-01 8 Best AI Automations (`build/automation-suite/`). Human, logged-in work only; the coding agent cannot do any of this.

- **Platform:** Google Cloud console (Calendar, Gmail, YouTube Data API v3, Drive), HubSpot, Airtable or Supabase, Slack, domain registrar/DNS
- **Source steps:** 01 steps 3 and 5, 02 steps 1, 4, 5, 06 steps 3 and 5, 07 steps 1, 4, 5, 08 step 4
- **Procedure:** build/automation-suite/docs/DEPLOY-RUNBOOK.md (steps 11-14, 16)
- **Approval gate:** each account and the sending domain/DNS change need approval; SPF/DKIM/DMARC are DNS changes needing domain access.

## Actions

1. Create the Google Cloud project, OAuth consent screen, and enable Calendar, Gmail, YouTube Data API v3, Drive; grant OAuth inside n8n.
2. Create the HubSpot account (contacts) and the Airtable/Supabase base with tables `leads`, `ugc_prompts`, `faceless_posts`, `youtube_ideas`.
3. Create Slack channels `#front-desk-escalations`, `#chat-handoff`, `#ugc`, `#content` and an incoming webhook.
4. If outreach is approved: set up the sending domain and inboxes with SPF/DKIM/DMARC; the "30 emails/day per inbox" figure is a source training target, not a validated limit.
5. Load the client's real FAQ into the chosen vector store (replaces the synthetic fixture).

## Evidence to capture

- OAuth scopes screenshot, base/table screenshots, channel names, DNS records, vector index name.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- Contacting a real prospect by email, DM, SMS, or call is human-authorized only.
- Synthetic test contacts only (example.com addresses, 555-01xx numbers) until activation is approved.

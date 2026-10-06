# Deploy runbook (human steps only)

None of these steps can be executed by the coding agent: each needs a browser,
a logged-in account, a purchase, or a human decision. Do them in order, and only
after the approval named in each step is recorded. Costs are `NEEDS_EVIDENCE`
throughout (see `docs/COST-AND-APPROVALS.md`); capture the vendor's current
pricing page as evidence before approving.

Before starting: run the offline checks from the repo root and keep the output
as evidence:

```
python scripts/validate_workflows.py
python scripts/check_guardrails.py
python scripts/check_env.py
python scripts/render_prompts.py
python scripts/run_dry.py
python scripts/cost_estimate.py
```

(`python3` on Linux/macOS.) `cost_estimate.py` exits non-zero by design.

| # | Action | Account | Cost | Approval required | Evidence to capture |
|---|---|---|---|---|---|
| 1 | Decide whether these automations run on n8n, inside GoHighLevel, or both (spec section 8 item 1). Record the decision. | none | none | Yes (architecture) | written decision |
| 2 | Create the n8n account (Cloud, or self-hosted on a VPS). | n8n | NEEDS_EVIDENCE | Yes (spend) | account screenshot, plan |
| 3 | Create the n8n API key; store it only in n8n / a local `.env` (never committed). | n8n | none | Yes | key name (not value) |
| 4 | Import `workflows/_common_error_handler.json`, then `01`-`08`. Set each workflow's error workflow. Every node type is unverified: fix any node n8n rejects and record what changed. | n8n | none | No | import screenshots, list of node fixes |
| 5 | Create credentials in n8n for each service actually approved (OpenAI, Google, HubSpot, Airtable/Supabase, Slack). | each vendor | NEEDS_EVIDENCE | Yes | credential names |
| 6 | Vapi (or Retell/Bland) account; plan selection; concurrency setting. | Vapi | NEEDS_EVIDENCE | Yes (spend gate) | plan, concurrency screenshot |
| 7 | Buy a Twilio (or Vapi) phone number; point it at the Vapi assistant; paste the n8n webhook URL into Vapi Server URL. | Twilio / Vapi | NEEDS_EVIDENCE | Yes (spend gate: number purchase) | number, config screenshot |
| 8 | Apify account; select actors (`google-maps-scraper`, TikTok scraper); legal review of each actor's terms of service. Apollo scraping stays unapproved. | Apify | NEEDS_EVIDENCE | Yes (spend gate + legal) | actor ids, legal sign-off |
| 9 | HeyGen, ElevenLabs, Creatomate, Ayrshare subscriptions; choose avatar id, voice id, templates; link social accounts in Ayrshare (platform TOS). | HeyGen / ElevenLabs / Creatomate / Ayrshare | NEEDS_EVIDENCE | Yes (spend gate) | plan screenshots, ids |
| 10 | Sora 2 / Runway / Pika access, if UGC video generation is approved. | OpenAI / Runway / Pika | NEEDS_EVIDENCE | Yes (spend gate) | access confirmation |
| 11 | Google Cloud project: OAuth consent, Calendar, Gmail, YouTube Data API v3, Drive; grant OAuth in n8n. | Google | NEEDS_EVIDENCE | Yes | consent screen, scopes |
| 12 | Sending domain and inboxes; SPF/DKIM/DMARC DNS records; Instantly/Hunter accounts if approved. | registrar / Google / Instantly / Hunter | NEEDS_EVIDENCE | Yes (spend + DNS change) | DNS records, inbox list |
| 13 | HubSpot account (contacts). | HubSpot | NEEDS_EVIDENCE | Yes | portal id |
| 14 | Supabase or Airtable base with `leads`, `ugc_prompts`, `faceless_posts`, `youtube_ideas` tables. | Supabase / Airtable | NEEDS_EVIDENCE | Yes | base id, table screenshot |
| 15 | Pinecone or Supabase Vector index; upload the client's real FAQ. | Pinecone / Supabase | NEEDS_EVIDENCE | Yes (spend gate) | index name |
| 16 | Slack workspace channels and incoming webhook for escalations. | Slack | NEEDS_EVIDENCE | Yes | channel names |
| 17 | GoHighLevel-side configuration (calendars, AI agents, knowledge base, widgets, phone numbers, workflows), only if step 1 decides GHL is involved. Confirm the build location id on screen (case-sensitive) before any change. | GoHighLevel | NEEDS_EVIDENCE | Yes (`REQUIRE_HUMAN_APPROVAL_FOR_GHL`) | object ids, screenshots |
| 18 | Marketing/legal review of every prompt in `prompts/` and every outbound template. | none | none | Yes | reviewer sign-off |
| 19 | First live test with synthetic contacts only (example.com, 555-01xx), one automation at a time, `DRY_RUN=false` and `ALLOW_LIVE=1` set by a human. Note: this repo's live adapters refuse every call by design; live execution happens inside n8n. | n8n | NEEDS_EVIDENCE | Yes | execution logs |
| 20 | Activation for real prospects: outbound and publishing each need explicit human authorization. | all | NEEDS_EVIDENCE | Yes (`REQUIRE_HUMAN_APPROVAL_FOR_OUTBOUND`, `_PUBLISH`) | approval record |

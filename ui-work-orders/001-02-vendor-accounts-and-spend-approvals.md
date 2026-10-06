# UI work order 001-02: Vendor accounts and spend approvals

Build: SPEC-01 8 Best AI Automations (`build/automation-suite/`). Human, logged-in work only; the coding agent cannot do any of this.

- **Platform:** Vapi (or Retell/Bland), Twilio, Apify, HeyGen, ElevenLabs, Creatomate, Ayrshare/Blotato, OpenAI (incl. Sora), Hunter.io, Instantly, Perplexity, Pinecone
- **Source steps:** 01 step 1, 02 steps 1-4, 03 steps 1 and 5, 04 steps 1-4, 05 steps 3-5, 06 step 3, 08 steps 2-4; cost estimate line 117
- **Procedure:** build/automation-suite/docs/DEPLOY-RUNBOOK.md (steps 6-10, 12, 15) and docs/COST-AND-APPROVALS.md
- **Approval gate:** every row in the COST-AND-APPROVALS spend table. Nothing is pre-approved.

## Actions

1. For each vendor Chuck wants, capture the vendor's current pricing page (dated screenshot) and record unit cost and worst-case monthly volume in `config/pricing.yaml`; run `python3 scripts/cost_estimate.py` and present the printed figure for sign-off.
2. Only after written approval of the specific plan and amount: create the account, choose the plan, and create the API key inside n8n credentials.
3. Phone number purchase (Twilio/Vapi) and concurrency settings are separate approvals; the source's "10 calls at a time" is unverified.
4. Apify: legal review of each actor's terms of service before any run; Apollo scraping stays unapproved; no yt-dlp downloads.
5. Ayrshare/Blotato: review TikTok, Instagram, YouTube, LinkedIn, X automation terms before linking any account.

## Evidence to capture

- Pricing screenshots, signed approval per vendor, account/plan screenshots, legal and platform-terms sign-offs.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- The source's prices are the source author's, not CA-J's rates; never copy them as current rates.
- The live Meta campaign CAJ_HVAC27_US_PURCHASE_TEST02 stays frozen; paid ads are out of scope.

# UI-only checklist

Every item here needs a browser, a logged-in account, a purchase, or a human
decision. All of it is **coding-agent-inaccessible**: Claude Code has no browser
and cannot log in or buy anything. These platforms are coding-agent-inaccessible
by design:

- **GoHighLevel** (all subaccount, snapshot, calendar, AI agent, knowledge base,
  widget, phone number, payment/product, and workflow work; GHL is UI-only and
  the build location id in `config/constants.py` is reference-only)
- **Meta Ads Manager** (out of scope; live campaign `CAJ_HVAC27_US_PURCHASE_TEST02` stays frozen)
- n8n Cloud, OpenAI platform dashboard, Vapi, Retell, Bland, Twilio console,
  Apify console, Apollo, Hunter.io, Instantly, HeyGen, Sora / Runway / Pika,
  Creatomate, JSON2Video, ElevenLabs, Ayrshare, Blotato, Perplexity, Leonardo,
  Pexels, Google Cloud console (Calendar, Gmail, YouTube Data API, Drive),
  HubSpot, Supabase, Airtable, Pinecone, Slack, Voiceflow, Botpress, Notion,
  TikTok / Instagram / YouTube / LinkedIn / X account settings, and any domain
  registrar or DNS console.

Before any item: confirm the matching approval in `docs/COST-AND-APPROVALS.md`.

## All automations

- [ ] Create the n8n account (approval gate); create the n8n API key.
- [ ] Import `workflows/_common_error_handler.json` first, then each automation; set each workflow's error workflow to it.
- [ ] Create every credential in the n8n UI (never paste keys into workflow JSON or this repo).
- [ ] Decide whether these automations run on n8n, inside GoHighLevel, or both (human architecture decision, spec section 8 item 1).
- [ ] Replace each `*_SET_BY_HUMAN` placeholder (account SID, voice id, avatar id) inside n8n, not in this repo.
- [ ] Marketing/legal review of all outbound copy before activation.

## 01 AI Voice Call Agent

- [ ] Create the Vapi (or Retell / Bland) account; choose a plan; set concurrency (paid; the "10 calls at a time" claim is unverified).
- [ ] Buy a Twilio (or Vapi) phone number (purchase; approval gate).
- [ ] Paste the n8n webhook URL into the Vapi Server URL field.
- [ ] Configure the Vapi assistant (model, voice, system prompt from `prompts/01_voice_receptionist_system.txt`, the four tools).
- [ ] Google Calendar OAuth grant; HubSpot account; Slack workspace webhook.
- [ ] Any GoHighLevel conversation AI or voice agent prompt entry (UI-only).
- [ ] Live test call (only after approval), using synthetic test details.

## 02 Lead Generation AI

- [ ] Apify account and actor selection (`google-maps-scraper`), plus terms-of-service/legal review. Apollo scraping is not approved.
- [ ] Hunter.io and/or Instantly accounts (paid).
- [ ] Sending domain and inboxes; SPF/DKIM/DMARC DNS records (domain access, human).
- [ ] Gmail OAuth grant for sending and reply watching.
- [ ] Airtable or Supabase base with a `leads` table.
- [ ] Approve each outbound batch (`REQUIRE_HUMAN_APPROVAL_FOR_OUTBOUND = True`); contacting a real prospect is human-authorized only.

## 03 AI UGC Ads Spy Generator

- [ ] Apify TikTok scraper actor (paid) and a ToS review of downloading third-party ads; no yt-dlp downloads.
- [ ] Sora 2 / Runway / Pika / HeyGen access (paid, logged-in; Sora API access unverified).
- [ ] Creatomate account if assembling stock + TTS; Google Drive folder for output.
- [ ] Slack channel for notifications.

## 04 Animated Faceless AI Videos

- [ ] Perplexity API or Apify trending actor (paid).
- [ ] ElevenLabs voice selection; Creatomate template creation (UI).
- [ ] Ayrshare/Blotato account and linking TikTok, Instagram, YouTube accounts (platform TOS).
- [ ] Approve each publish (`REQUIRE_HUMAN_APPROVAL_FOR_PUBLISH = True`).

## 05 Content Creation Agent

- [ ] Image generation account (Leonardo / OpenAI images), ElevenLabs, Creatomate timeline template (UI).
- [ ] Ayrshare/Blotato account with TikTok, Instagram, YouTube, LinkedIn, X linked.
- [ ] Decide loop cadence; the source's "loop forever" needs a human-set stop condition.

## 06 Multilingual FAQ Chatbot

- [ ] Choose the widget (n8n Chat Trigger, Voiceflow, or Botpress) and host it; chat subdomain DNS.
- [ ] Pinecone or Supabase Vector account; upload the client's real FAQ (replaces `data/fixtures/faqs.sample.md`).
- [ ] Google Calendar OAuth for availability; Slack handoff channel.
- [ ] If the chat runs inside GoHighLevel instead, configure it in the GHL UI.

## 07 Viral YouTube Video Idea Generator

- [ ] Google Cloud project with YouTube Data API v3 enabled; API key or OAuth.
- [ ] Airtable/Notion destination; Gmail OAuth for the weekly report.

## 08 AI Avatar Generator

- [ ] HeyGen account (paid): choose avatar id and voice id in the HeyGen UI.
- [ ] ElevenLabs custom voice (optional, paid); Creatomate intro/outro template; brand logo asset.
- [ ] Google Drive or S3 destination; Ayrshare with LinkedIn, YouTube, Instagram linked; Slack channel.

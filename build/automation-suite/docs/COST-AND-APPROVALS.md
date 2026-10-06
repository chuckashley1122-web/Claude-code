# Cost and approvals

**No purchase of any kind is authorized by this spec (SPEC-01) or by anything in
this repository.** `SPEND_CAP_USD = 0.00`. Every paid service below is an
approval gate: a human (Chuck) must approve the specific service, plan, and
amount in writing before any account, subscription, phone number, domain, or
usage-based spend is created. The coding agent never purchases anything.

## Locked CA-J commercial terms (internal only)

These are the only CA-J terms; they live in `config/constants.py` and are never
restated differently:

- Tech fee: $650/mo (`TECH_FEE_MONTHLY_USD = 650`)
- Setup fee: waived (`SETUP_FEE_USD = 0`)
- $250 to $300 per booked appointment (`PER_BOOKED_APPOINTMENT_MIN_USD = 250`,
  `PER_BOOKED_APPOINTMENT_MAX_USD = 300`)

They are internal. Meeting-first applies to every prospect-facing artifact this
suite produces: no price ever appears in outbound or prospect-facing copy, and
pricing intent is routed to https://ca-jenterprises.com/ai. `guardrails/pricing_guard.py`
blocks any price (including these) in outbound text; `guardrails/meeting_first.py`
answers pricing questions with the booking link only. These are therefore the
only pricing this suite may reference anywhere, and only internally.

## Spend items requiring approval

"Usable at $0" is **No** for every row: even where a vendor advertises a free
tier, that is unverified here and still needs an account, an approval, and a
human login. Cost is `NEEDS_EVIDENCE` for every row: no figure in this table is
verified, and the source playbook's figures (`docs/SOURCE-CLAIMS.md`, C21-C31)
are the source author's, not CA-J's rates.

| # | Service | Used by | What it is for | Usable at $0 | Approval required | Cost |
|---|---|---|---|---|---|---|
| 1 | n8n Cloud (or self-hosted n8n + VPS) | all | workflow orchestrator; importing `workflows/*.json` | No | Yes | NEEDS_EVIDENCE |
| 2 | OpenAI API (GPT-4o, Realtime, Whisper, Vision, image generation) | 01-08 | text, voice model, transcription, vision, images | No | Yes | NEEDS_EVIDENCE |
| 3 | OpenAI Sora 2 API, or Runway / Pika | 03 | generative UGC video | No | Yes | NEEDS_EVIDENCE |
| 4 | Vapi.ai (or Retell.ai / Bland.ai) | 01 | voice agent platform, call concurrency | No | Yes | NEEDS_EVIDENCE |
| 5 | Twilio phone number + usage | 01 | inbound number, call transfer | No | Yes (number purchase) | NEEDS_EVIDENCE |
| 6 | Apify (actor compute) | 02, 03, 04 | scraping actors (plus terms-of-service / legal review) | No | Yes | NEEDS_EVIDENCE |
| 7 | Apollo | 02 | lead data; scraping it is **not approved** (ToS / legality) | No | Yes (and legal review) | NEEDS_EVIDENCE |
| 8 | Hunter.io | 02 | email finder | No | Yes | NEEDS_EVIDENCE |
| 9 | Instantly | 02 | cold email sending | No | Yes | NEEDS_EVIDENCE |
| 10 | Sending inboxes / Google Workspace seats, domain for SPF/DKIM | 02 | outreach identity and deliverability | No | Yes | NEEDS_EVIDENCE |
| 11 | HeyGen | 03, 08 | avatar video | No | Yes | NEEDS_EVIDENCE |
| 12 | ElevenLabs | 04, 05, 08 | voiceover | No | Yes | NEEDS_EVIDENCE |
| 13 | Creatomate (or JSON2Video) | 03, 04, 05, 08 | video assembly, captions | No | Yes | NEEDS_EVIDENCE |
| 14 | Ayrshare (or Blotato) | 04, 05, 08 | multi-platform publishing (plus platform TOS review) | No | Yes | NEEDS_EVIDENCE |
| 15 | Perplexity API | 04 | trending-topic research | No | Yes | NEEDS_EVIDENCE |
| 16 | Leonardo.ai / Pexels | 04, 05 | images and stock footage | No | Yes | NEEDS_EVIDENCE |
| 17 | Google Cloud project (Calendar, Gmail, YouTube Data API v3, Drive) | 01, 02, 07, 08 | OAuth grant, calendar, mail, YouTube search, storage | No | Yes | NEEDS_EVIDENCE |
| 18 | HubSpot | 01, 02 | CRM contacts | No | Yes | NEEDS_EVIDENCE |
| 19 | Supabase / Airtable | 02, 03, 05, 07 | record tables | No | Yes | NEEDS_EVIDENCE |
| 20 | Pinecone (or Supabase Vector) | 06 | FAQ vector store | No | Yes | NEEDS_EVIDENCE |
| 21 | Slack workspace | 01, 03, 06, 08 | human escalation and notifications | No | Yes | NEEDS_EVIDENCE |
| 22 | Voiceflow / Botpress (if chosen over n8n Chat Trigger), chat subdomain DNS | 06 | hosted chat widget | No | Yes | NEEDS_EVIDENCE |
| 23 | Redis, VPS, proxy, Retool (source "Scaling", line 115) | all | out of scope: scaling | No | Yes | NEEDS_EVIDENCE |
| 24 | Notion | 07 | idea output (alternative to Airtable) | No | Yes | NEEDS_EVIDENCE |

`config/pricing.yaml` carries one row per vendor named on source line 117 with
`unit_cost: null` and `verified: false`. `python3 scripts/cost_estimate.py`
reports the monthly worst case as **UNBOUNDED (NEEDS_EVIDENCE)** and exits
non-zero, because nothing is verified and anything above `SPEND_CAP_USD = 0.00`
needs sign-off. To prepare a sign-off figure, a human records each vendor's
current rate and worst-case monthly volume from the vendor's own pricing page
(with a dated screenshot as evidence), then reruns the script; it still exits
non-zero and the printed figure is what gets approved.

## Out of scope

Paid ads, upsells, upgrades, and "scaling" steps from the source are out of
scope. The live Meta campaign `CAJ_HVAC27_US_PURCHASE_TEST02` stays frozen; this
suite does not touch Meta Ads Manager.

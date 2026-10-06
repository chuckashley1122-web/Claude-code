# Source claims (all unverified)

Source: `docs/playbooks/01-8-best-ai-automations.md` (spec section 1 path:
`caj-growth-system\playbooks\01-8-best-ai-automations.md`). Stated origin
(line 2): "Source: TikTok @martiendejong_dev - 8 automations from your 4 screenshots."

Every quantitative or capability claim below is copied verbatim with its source
line number and is labelled `unverified`. These are the source author's numbers
at the author's date. They are **not** CA-J's results, rates, targets, costs, or
forecasts and must never be restated as such.

This file is the single source of truth for spec section 8 and is parsed by
`guardrails/claim_guard.py`: every non-empty value in the **Denylist phrase**
column is blocked from outbound copy (alongside the static base list
"unlimited", "virtually nothing", "10 calls at a time").

## Claims table

| ID | Line | Verbatim claim | Category | Denylist phrase | Status |
|---|---|---|---|---|---|
| C01 | 6 | "Vapi.ai or Retell.ai or Bland.ai (for Voice Agent concurrency)" | vendor capability | - | unverified |
| C02 | 15 | "1. AI Voice Call Agent - Answers 10 calls at a time, unlimited/day" | concurrency / unlimited | unlimited/day | unverified |
| C03 | 19 | "set concurrency to 10 in dashboard. Vapi handles 10+ simultaneous calls natively." | concurrency | 10+ simultaneous calls | unverified |
| C04 | 35 | "Limit 30 emails/day per inbox. Setup SPF/DKIM." | deliverability | 30 emails/day | unverified |
| C05 | 41 | "generate 5 Sora 2-ready prompts, produce UGC 10x faster." | performance | 10x faster | unverified |
| C06 | 45 | "Extract Hook (first 3 sec), Script, Visual Style, CTA, Music vibe, Camera." | vendor capability (GPT-4o Vision) | - | unverified |
| C07 | 54 | "Creates, publishes, scales faceless short-form video channels on TikTok and Instagram automatically." | outcome | scales faceless | unverified |
| C08 | 58 | "Write 30-sec viral script: Hook (0-3s shocking), 3 value points, CTA. 120 words." | format | - | unverified |
| C09 | 61 | "After 24h Apify pulls views/likes into Airtable. OpenAI analyzes best hooks to improve next scripts." | performance | improve next scripts | unverified |
| C10 | 72 | "n8n Wait 12h + Loop forever" | operations | - | unverified |
| C11 | 77 | "Supports English, Hindi, Spanish, French, German, 20+ languages" | capability | 20+ languages | unverified |
| C12 | 83 | "Confidence <0.7 => handoff to human via Slack." | threshold | - | unverified |
| C13 | 88 | "gives fresh content ideas backed by real data" | outcome | backed by real data | unverified |
| C14 | 91 | "Pull 50 videos: title, views, likes, tags." | volume | - | unverified |
| C15 | 104 | "HeyGen API POST /v2/video/generate avatar_id (realistic), voice_id, background office. Poll status until done." | vendor API | - | unverified |
| C16 | 107 | "n8n Cron > OpenAI Script > HeyGen Generate > Wait 2 min > Check Status > Download > Drive > Publish > Slack notify." | performance (render time) | - | unverified |
| C17 | 111 | "Build #6 FAQ Chatbot (fastest win)." | outcome | fastest win | unverified |
| C18 | 112 | "Build #1 Voice Agent via Vapi.ai (2 days) + #7 YouTube Idea Generator (1 day)." | effort estimate | - | unverified |
| C19 | 114 | "then clone for #4 Faceless and #8 Avatar (80% same nodes)." | effort estimate | 80% same nodes | unverified |
| C20 | 115 | "Scaling: Move n8n to VPS, add Redis queue, 10 Gmail inboxes, proxy, Retool dashboard." | deliverability / scale | 10 Gmail inboxes | unverified |
| C21 | 117 | "Vapi $0.05/min" | cost | $0.05/min | unverified |
| C22 | 117 | "OpenAI Realtime $0.06/min" | cost | $0.06/min | unverified |
| C23 | 117 | "100 calls/day ~ $30/day" | cost / volume | $30/day | unverified |
| C24 | 117 | "Apify $50/mo" | cost | $50/mo | unverified |
| C25 | 117 | "Apollo $100/mo" | cost | $100/mo | unverified |
| C26 | 117 | "HeyGen $29/mo" | cost | $29/mo | unverified |
| C27 | 117 | "ElevenLabs $22/mo" | cost | $22/mo | unverified |
| C28 | 117 | "Creatomate $30/mo" | cost | $30/mo | unverified |
| C29 | 117 | "Ayrshare $30/mo" | cost | - | unverified |
| C30 | 117 | "OpenAI $50-100/mo" | cost | $50-100/mo | unverified |
| C31 | 117 | "Total startup ~ $300-400/mo to run all 8 at small scale." | cost | $300-400/mo | unverified |

Notes:

- C29 has the same figure as C28, so its denylist phrase is already covered.
- Every cost row (C21-C31) is also blocked independently by
  `guardrails/pricing_guard.py`, which blocks any dollar amount in outbound text.
- None of these figures is copied into `config/pricing.yaml`; every row there is
  `unit_cost: null`, `verified: false` (cost = NEEDS_EVIDENCE).

## Implied outcomes (never to be restated as CA-J results)

The source implies virality, "UGC 10x faster", channel scale, and revenue. These
are the source author's implied outcomes. No results, metrics, benchmarks, or
proof points exist for CA-J in this source; prospect-facing copy generated from
these workflows must contain no unverified proof.

# 8 BEST AI AUTOMATIONS - Exact Implementation Playbook
Source: TikTok @martiendejong_dev - 8 automations from your 4 screenshots. This doc gives exact step-by-step build plan for each using n8n + Vapi + OpenAI + Apify + HeyGen + Sora 2 / Runway. Build order and exact prompts included.
# Prerequisites - Accounts Needed
n8n Cloud (main orchestrator)
OpenAI API (GPT-4o, Whisper)
Vapi.ai or Retell.ai or Bland.ai (for Voice Agent concurrency)
Apify (scraping leads + TikTok/YouTube)
HeyGen API (Avatar)
Sora 2 / Runway / Pika / Creatomate (UGC video)
Google Calendar + Gmail APIs
HubSpot free CRM
Ayrshare or Blotato (publish to TikTok, IG, YouTube, LinkedIn, X)
YouTube Data API v3
Supabase / Airtable (database)
# 1. AI Voice Call Agent - Answers 10 calls at a time, unlimited/day
Purpose: Inbound AI receptionist for hotel/business. Handles concurrent calls, checks availability, books calendar, answers questions, sends confirmation, creates HubSpot contact, escalates to human.
Workflow from screenshot: Webhook (Custom Webhook) -> Call Agent (OpenAI Realtime) -> Check Availability (Tools) + Book Appointment (Google Calendar) + Handle Questions (AI Assistant) + Escalate to Human (Router) + Send Confirmation Email (Gmail) + Create CRM Contact (HubSpot)
## Step-by-Step Implementation
Step 1 - Use Vapi.ai not raw Realtime: Create Vapi.ai account, buy phone number via Twilio, set concurrency to 10 in dashboard. Vapi handles 10+ simultaneous calls natively.
Step 2 - Webhook Trigger in n8n: New Workflow > Webhook Trigger (POST). Copy URL. Paste into Vapi > Server URL. This is your Custom webhook node.
Step 3 - Build 4 Tools: Tool 1 Check Availability: Google Calendar Get Availability (free/busy). Tool 2 Book Appointment: Google Calendar Create Event. Tool 3 Handle Questions: OpenAI Assistant with business knowledge base (upload PDF FAQs). Tool 4 Escalate: Slack message + Twilio Transfer Call to human.
Step 4 - Configure Call Agent: Vapi Assistant settings: Model GPT-4o, Voice ElevenLabs Rachel, System Prompt: Hotel receptionist concise. Attach all 4 tools.
Step 5 - Post-call flow: After call ends, n8n runs Gmail Send (confirmation template) + HubSpot Create Contact (with transcript summary via OpenAI Summarize).
Step 6 - Test: Call your Vapi number, ask availability tomorrow, book it, check Calendar, Gmail, HubSpot.
## Prompts / Templates
System Prompt: You are [Hotel] receptionist. Greet, ask how to help. If booking, ALWAYS call check_availability first. Never invent times. Confirm email before sending. If user repeats confusion 2x, escalate_to_human. Keep answers <25 words.
Email Template: Hi {{name}}, confirmed {{date}} at {{time}}. Address: ... Cancel link.
# 2. Lead Generation AI - Automate Cold Outreach
Purpose: Automate Research, Scraping, Qualifying, Emailing, Follow-ups for B2B leads.
Workflow from screenshot: Scrape Leads (Apify) -> Research & Enrich (OpenAI) -> Qualify Leads (Filter) -> Send Outreach Email (Gmail) -> Follow-ups (Scheduler)
## Step-by-Step Implementation
Step 1 - Scrape Leads: n8n Apify node > Actor apollo-io-scraper or google-maps-scraper. Input: Niche like Plumbers in Texas. Output: Name, Website, Email. Save to Airtable.
Step 2 - Research & Enrich: For each lead, OpenAI analyzes website: Summarize business, employee count, pain points. Use Hunter.io API to find email if missing.
Step 3 - Qualify Leads: n8n IF node: Only if has email AND not contacted before AND fit_score >7. Fit score via OpenAI rating 1-10.
Step 4 - Send Outreach: Gmail node or Instantly API. Personalize with AI icebreaker. Limit 30 emails/day per inbox. Setup SPF/DKIM.
Step 5 - Follow-ups Scheduler: n8n Cron daily 9am > Fetch Airtable where next_followup = today AND no reply > Send follow-up 2/3. Gmail Trigger watches for replies to stop sequence.
## Prompts / Templates
Enrich Prompt: Analyze {{website}}. Return JSON: what_they_do, pain_points, decision_maker, fit_score 1-10, icebreaker (2 sentences).
Cold Email: Subject: Quick idea for {{company}}. Body: {{icebreaker}}. We help {{niche}} get [result] without [pain]. Worth 10 min? - Chuck
# 3. AI UGC Ads Spy Generator - Reverse-engineer viral ads
Purpose: Reverse-engineer viral ads, rebuild with brand-specific messaging, generate 5 Sora 2-ready prompts, produce UGC 10x faster.
Workflow from screenshot: Input: Paste viral ad link or upload video (TikTok/IG/YouTube) -> Analyze Ad Extract key elements -> Get Insights Hook/script/format -> Generate Prompts 5 Sora 2 prompts -> Create UGC Brand-specific -> Output UGC content ready + Sora 2 Video prompts
## Step-by-Step Implementation
Step 1 - Input: n8n Webhook with file upload + URL field. Use Apify TikTok Scraper or yt-dlp to download video.
Step 2 - Analyze Ad: GPT-4o Vision: Send 5 frames + transcript via Whisper. Extract Hook (first 3 sec), Script, Visual Style, CTA, Music vibe, Camera.
Step 3 - Get Insights: OpenAI JSON: hook_type, script_structure, emotional_trigger, format (green-screen/testimonial), why_viral.
Step 4 - Generate 5 Sora 2 Prompts: OpenAI: Given insights + your brand {{brand_desc}} {{product}}, generate 5 detailed Sora 2 prompts keeping viral structure. Include scene, camera, actor, dialogue, style, 9:16, 8 sec.
Step 5 - Create UGC: Loop prompts to Sora 2 API or Runway/Pika/HeyGen. Or Creatomate to assemble stock + TTS. Save to Google Drive.
Step 6 - Output: Slack notification with 5 video links + caption suggestions.
## Prompts / Templates
Deconstruction Prompt: You are viral ad analyst. Analyze video. Return Hook text/type, Full script, Shot list, Psychological triggers, Why it worked.
Sora Prompt Format: UGC style, 24yo woman in kitchen, iPhone selfie, natural light, says: [line], product in hand, TikTok style, 9:16, 8 seconds
# 4. Animated Faceless AI Videos - Scale faceless channels
Purpose: Creates, publishes, scales faceless short-form video channels on TikTok and Instagram automatically.
Workflow from screenshot: Write Video Script (AI Script Generator + Trending Topics + Custom Prompt) -> Create Faceless Video (AI Avatars + Stock Footage + Voiceover) -> Publish to Social Media (Auto Posting + Multi-Channel + Track Performance)
## Step-by-Step Implementation
Step 1 - Trending Topics: Apify TikTok trending scraper or Perplexity API: Top 10 viral topics in [niche] today. Cron daily 6am.
Step 2 - Write Script: OpenAI: Write 30-sec viral script: Hook (0-3s shocking), 3 value points, CTA. 120 words. Input: Trending topic.
Step 3 - Create Faceless Video: Creatomate or JSON2Video: Pexels API for stock footage keywords + ElevenLabs voiceover + Auto-subtitles (Hormozi style big words). Optional HeyGen Avatars.
Step 4 - Publish: Ayrshare API: Upload to TikTok, IG Reels, YouTube Shorts same time. Hashtags via OpenAI.
Step 5 - Track Performance: After 24h Apify pulls views/likes into Airtable. OpenAI analyzes best hooks to improve next scripts.
## Prompts / Templates
Script Prompt: You write viral 30s scripts for faceless [finance/health] channel. Structure: Hook shocking question, 3 tips numbered, CTA follow. Keep punchy. Topic: {{trending_topic}}
# 5. Content Creation Agent - Fully Automated Ideation to Publishing
Purpose: Fully automated agent handles every part of content process and repeats automatically.
Workflow from screenshot: Topic Research (Trends & Ideas) -> Generate Script (AI Writing) -> Create Video (Images/Voice/Edit) -> Add Captions (Auto Subtitles) -> Publish (All Platforms TikTok, IG, YouTube, LinkedIn, X) -> Repeat Automatically
## Step-by-Step Implementation
Step 1 - Topic Research: Combine Google Trends + Reddit scraper + YouTube search for niche keywords. OpenAI ranks by virality 1-10.
Step 2 - Generate Script: OpenAI: Write 45-sec script for platform. Include hook, story, lesson, CTA. Tone: your brand tone.
Step 3 - Create Video: Leonardo.ai/DALL-E for images, ElevenLabs voice, Creatomate auto-edit timeline. 9:16 TikTok/IG/YT, 1:1 LinkedIn/X.
Step 4 - Add Captions: Whisper transcription + styled captions (Alex Hormozi style).
Step 5 - Publish & Loop: Ayrshare for all platforms. n8n Wait 12h + Loop forever as dashed Repeat Automatically line in screenshot.
## Prompts / Templates
System: Automate ideation -> creation -> publishing. Use n8n: Research > Generate Script > Create Video > Add Captions > Publish > Repeat Automatically (Loop node + Wait 12h).
# 6. Multilingual FAQ Chatbot - Real-time GPT answers in 20+ languages
Purpose: When customer sends chat message via website or shared link, AI answers scheduling queries in real-time using GPT in user's language.
Workflow from screenshot: User Message (Website/Link) -> Language Detection -> GPT (FAQ Answer) Real-time Response -> Send Reply in User's Language -> Handle Follow-up Questions Automatically. Supports English, Hindi, Spanish, French, German, 20+ languages
## Step-by-Step Implementation
Step 1 - Deploy Widget: Voiceflow or Botpress or n8n Chat Trigger. Create embed <script src=chat.js>. Hosted link chat.yourdomain.com.
Step 2 - Language Detection: OpenAI gpt-4o-mini prompt: Detect language of {{user_message}} Return ISO code. Or Google Translate Detect.
Step 3 - GPT FAQ Answer: Vector DB: Upload FAQs to Pinecone/Supabase Vector. RAG: Retrieve relevant chunks + GPT-4o generates answer. Check Calendar availability if scheduling intent.
Step 4 - Translate Reply: OpenAI: Translate answer to {{detected_language}} friendly tone. Send via chat widget.
Step 5 - Follow-ups: n8n memory or Redis store last 5 messages. Confidence <0.7 => handoff to human via Slack.
## Prompts / Templates
RAG Prompt: Answer only from context. Context: {{retrieved_faq}}. Question: {{user_msg}}. If scheduling, mention availability. Keep <50 words.
Translate Prompt: Translate to {{lang}} keeping friendly tone.
# 7. Viral YouTube Video Idea Generator - Data-backed ideas
Purpose: Automation pulls best-performing YouTube videos in your niche, analyses them, gives fresh content ideas backed by real data: titles, keywords, angles audience already searching for.
Workflow from screenshot: Fetch Top Performing Videos YouTube API -> Analyze Content Titles, Keywords, Engagement -> Generate Fresh Ideas AI-Powered -> Get Actionable Ideas Titles, Angles, Keywords + Trending Topics, High-Intent Keywords, Proven Angles & Formats, Ready-to-Use Video Ideas
## Step-by-Step Implementation
Step 1 - Fetch Top Videos: YouTube Data API v3 search with niche keywords, order viewCount, publishedAfter last 30 days. Pull 50 videos: title, views, likes, tags.
Step 2 - Analyze Content: OpenAI analyzes title formula, keywords, thumbnail text, engagement ratio likes/views. Prompt extracts pattern, keywords, angle, why performed.
Step 3 - Generate Fresh Ideas: OpenAI: Given analysis, generate 10 fresh video ideas combining proven angles but unique. For each: Title 3 variants, Angle, Target keyword, Hook script, Outline.
Step 4 - Actionable Output: Format into Airtable/Notion: Title Ideas, Keywords, Proven Angles, Ready-to-Use Ideas, Trending Topics. Add button Create Video linking to Automation 5.
Step 5 - Automate: Cron weekly Monday 7am + Run Automation button > Email report.
## Prompts / Templates
Analysis Prompt: For video {{title}} {{views}} {{description}}, extract title pattern, high-intent keywords, angle, why it performed.
Idea Prompt: Given top performers {{analysis}}, generate 10 fresh video ideas that keep proven psychology but unique.
# 8. AI Avatar Generator - HeyGen + n8n Talking-Head
Purpose: Fully automated AI content creator using HeyGen + n8n. Generates realistic talking-head avatar video. Script -> Generate Avatar -> Add Voice & Edit -> Export Video Ready to Publish
Workflow from screenshot: Create Script (AI Generated) -> Generate Avatar (HeyGen) -> Add Voice & Edit (AI Voice) -> Export Video (Ready to Publish) -> Realistic, Multiple Languages, Fully Ready for Social Media
## Step-by-Step Implementation
Step 1 - Create Script: OpenAI generates 60-sec talking-head script: Hook, Problem, Solution, CTA. Add directions [smile] [pause].
Step 2 - Generate Avatar: HeyGen API POST /v2/video/generate avatar_id (realistic), voice_id, background office. Poll status until done.
Step 3 - Add Voice & Edit: ElevenLabs audio if custom voice, upload to HeyGen. Creatomate add intro/outro, captions, logo.
Step 4 - Export Video: HeyGen returns URL. Download to Google Drive/S3. Auto-post via Ayrshare to LinkedIn, YouTube, IG. Ready for Social Media.
Step 5 - Full Template: n8n Cron > OpenAI Script > HeyGen Generate > Wait 2 min > Check Status > Download > Drive > Publish > Slack notify. This is Run Automation button.
## Prompts / Templates
HeyGen Payload: {avatar_id: '...', voice_id: '...', script: '{{script}}', background: '#ffffff', dimensions: {1080x1920}}. Script Prompt: Write 60s talking-head script for {{niche}} founder. Hook, Problem, Solution, CTA.
# Master Build Order
Week 1: Setup n8n, OpenAI, Google, HubSpot, Ayrshare, Apify. Build #6 FAQ Chatbot (fastest win).
Week 2: Build #1 Voice Agent via Vapi.ai (2 days) + #7 YouTube Idea Generator (1 day).
Week 3: Build #2 Lead Gen + #3 UGC Spy (share Apify + OpenAI nodes).
Week 4: Build #5 Content Creation Agent as factory, then clone for #4 Faceless and #8 Avatar (80% same nodes).
Scaling: Move n8n to VPS, add Redis queue, 10 Gmail inboxes, proxy, Retool dashboard.
# Cost Estimate
Voice Agent: Vapi $0.05/min + OpenAI Realtime $0.06/min. 100 calls/day ~ $30/day. Lead Gen: Apify $50/mo + Apollo $100/mo. UGC/Faceless/Content/Avatar: HeyGen $29/mo, ElevenLabs $22/mo, Creatomate $30/mo, Ayrshare $30/mo, OpenAI $50-100/mo. Total startup ~ $300-400/mo to run all 8 at small scale.

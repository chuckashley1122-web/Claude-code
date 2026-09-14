# Hermes Agent - Complete Facebook Ads + GoHighLevel AI Studio Build SOP
Source Video: https://www.youtube.com/watch?v=3ikJQWLRhNM | Title: Facebook Ads + GoHighLevel AI Studio - Complete Local Lead Generation Tutorial
Generated: 2026-09-12 for Chuck Ashley
Purpose: Exact step-by-step action plan for Hermes agent to autonomously build full campaign funnel.
## Overview - 6 Phase System
Phase 1: Foundation and Accounts (0:00-4:28)
Phase 2: Building Landing Pages with AI Studio + Offer (4:28-28:20)
Phase 3: Pipelines, Automations, and Nurturing (28:20-47:06)
Phase 4: Ad Creatives and Ad Copy (47:06-56:16)
Phase 5: Conversion Tracking - Meta Conversions API (56:16-1:11:37)
Phase 6: Final Campaign Launch (1:11:37-End)

Core Principle from video: Do NOT boost posts. Use Business Portfolio + proper campaign structure + high-speed AI Studio landing pages + CAPI for 100% lead tracking + speed-to-lead nurturing.
## PHASE 1: FOUNDATION AND ACCOUNTS
Objective: Create Meta infrastructure and GoHighLevel sub-account

STEP 1.1 - Meta Business Portfolio Setup:
1. Go to business.facebook.com
2. Create Business Portfolio (formerly Business Manager)
3. Verify business email and domain
4. Create Ad Account inside portfolio
5. Add payment method
6. Connect Facebook Page and Instagram Profile to portfolio (Settings > Accounts > Pages / Instagram Accounts)
7. Verify you have Admin access to all assets
Reference video in description for detailed Business Portfolio setup - agent should check if already exists before creating.

STEP 1.2 - GoHighLevel Agency Setup:
1. Log into GoHighLevel Agency account
2. Go to Sub-Accounts > Create Sub-Account
3. Choose 'Create Blank Snapshot' (no automations yet)
4. Name format: [Client Business Name] - e.g., 'Cary Junk Removers'
5. Once created, go into Sub-Account > Settings > Labs
6. Search 'AI Studio' > Click 'Activate Feature' > Select this sub-account
7. Confirm AI Studio appears in left nav
8. Optional: Buy domain for client (Namecheap/GoDaddy/Hostinger) - needed for subdomain later
CHECKPOINT: Business Portfolio verified + Ad Account created + FB/IG connected + GHL sub-account with AI Studio enabled = Phase 1 complete
## PHASE 2: OFFER + AI STUDIO LANDING PAGE
Objective: Create irresistible low-friction offer and build high-converting landing page

STEP 2.1 - Offer Creation (Critical - Interruptive Marketing):
Facebook is interruptive, not intent-based like Google. Offer must be SPECIFIC, LOW-FRICTION, EASY YES.
DO NOT USE: 'Contact us', 'Learn more', 'Submit card details' as first touch.
GOOD OFFERS for local businesses:
- Free class / Free trial (martial arts, gym)
- Free consultation (no obligation)
- Free assessment / Free quote
- First visit discounted - tied to booking this week (e.g., 50% off first visit)
- $49 drain cleaning or money-back guarantee (example from video)
ACTION: Use ChatGPT/Claude prompt: 'I have a [business type] in [location]. What are 5 proven low-friction Facebook offers that historically generate leads? Criteria: specific, no upfront payment, urgency.' Pick 1 and stick with it.

STEP 2.2 - AI Studio Landing Page Prompt:
1. In GHL Sub-Account > AI Studio > New Project
2. Copy MEGA PROMPT from video description Google Doc (contains Alex Hormozi landing page framework)
3. Replace ALL placeholders at top of prompt:
 - Business Name: e.g., Cary Junk Removers
 - Primary Location: Cary, North Carolina
 - Service Areas: Cary NC and all surrounding areas
 - Primary Service: Junk Removal
 - Additional Services: Furniture removal, yard waste, appliance removal
 - Main Offer: $50 discount on first service / $100 discount on first service (must match Step 2.1)
 - Offer Expiration: Only 6 remaining this month (creates urgency)
 - Primary CTA: Get a no obligation free quote (no obligation keyword important)
 - Phone: [client phone]
 - Avg Response Time: 1 hour or 30 min (lower = higher conversion)
 - Est Service Time: 1 day (optional, can remove if confusing)
 - Years in business: 20 years
 - Customers served: 500+
 - Google Review Rating: 4.9
 - Number of Reviews: 150+
 - Guarantee: [if applicable]
 - Insurance/License: [if relevant]
 - USP: Family-owned and operated / Veteran owned (high trust for home services)
 - Main Pain Points: Use ChatGPT: 'What are pain points a junk removal company can highlight?' e.g., 'Your space is too cluttered'
 - Desired Outcomes: e.g., Ready to reclaim your garage or basement
 - Testimonials: Keep placeholder - will add later
 - Team/Owner: Keep placeholder
 - Hero image: Keep placeholder
 - Logo: Keep placeholder
 - Brand colors/fonts: Use from logo or 'use whatever suits a [business] company' - but prefer real brand colors
4. Paste full prompt into AI Studio and generate (takes few minutes). It will create Landing Page + Thank You Page.

STEP 2.3 - Iterate Landing Page (Do 5-7 changes at a time max):
Change 1: Drag & drop logo > Prompt: 'Update the logo and follow the colors from the logo to use in the page'
Change 2: Upload real before/after images > Prompt: 'Update these images in the section after the hero section on the landing page'
Change 3: Upload hero background image > Prompt: 'Use the attached image in the background of the hero section. Maintain an overlay that has the left and right elements of the hero section stand out. At same time we should be able to see a glimpse of background image.'
Change 4 (multi-change prompt example):
'Remove the image from over the form on the right side of hero. Make logo on header 1.8 times bigger. Add 2-3 navigation menu items on header right side of logo to take us to different sections of page. On left side of phone call option in header add a Google review badge with number of reviews and average rating.'
Change 5: 'Make header wider and change background to light background'
Change 6: Mobile fix: 'Remove phone number from header, centralize logo on mobile, fix hero button layout'
Validation: Every button should scroll to form. Check desktop + mobile preview.

STEP 2.4 - Connect Form to CRM (Native Integration):
1. In AI Studio chat, prompt: 'Connect or integrate the form on the landing page to my CRM'
2. Click 'Connect' button that appears
3. Wait few minutes for integration

STEP 2.5 - Connect Subdomain (Critical for Trust + CAPI):
1. In AI Studio > Publish > Publish Changes
2. Click 'Add Custom Domain' > Enter subdomain: offer.[domain].com or call.[domain].com or contact.[domain].com
3. Copy CNAME record: Type=CNAME, Host=[subdomain], Value=vibe.cloud (shown in AI Studio)
4. Go to Domain Provider (Namecheap example: Dashboard > Manage > Advanced DNS > Add New Record)
5. Paste record > Save
6. Wait 10-30 min for propagation
7. Go back to AI Studio > Publish > Verify DNS > Publish
8. Test live URL loads

STEP 2.6 - Test Form Submission:
1. Go to live subdomain URL
2. Submit test: Name, Email, Phone, Service Needed
3. Check GHL > Contacts - should appear instantly
4. Click contact > Activity - verify attribution data: page URL, source, submission ID, mapped fields
5. If not working, troubleshoot integration
CHECKPOINT: Live subdomain landing page + working form to GHL + attribution data captured = Phase 2 complete
## PHASE 3: PIPELINES, AUTOMATIONS, AND NURTURING
Objective: Build sales pipeline + speed-to-lead automations

STEP 3.1 - Create Pipeline:
1. GHL > Opportunities > Pipelines > Create New Pipeline
2. Name: Meta Ads Leads
3. Create Stages (keep 4-7 max):
 Stage 1: New Lead (form submit enters here)
 Stage 2: Hot Lead / Responded (replied to follow-up)
 Stage 3: Closed (won)
 Stage 4: Lost (no response after sequence)
 [Optional additional stages based on sales process]

STEP 3.2 - Workflow 1: New Lead Automation (Worst-case = no reply):
1. Automation > Workflows > Create Workflow > Start from Scratch > Name: New Lead Automation
2. Trigger: AI Studio Form Submitted
 - Add Filter: AI Studio Project = [Your Project Name e.g., Cary Junk]
 - Add Filter: AI Studio Form = [Your Form]
3. Action 1: Create/Update Opportunity
 - Pipeline: Meta Ads Leads
 - Stage: New Lead
 - Opportunity Name: {{contact.full_name}} (custom value)
 - Status: Open
4. Action 2: Add Tag = 'Facebook Landing Page' or 'Facebook Ads'
5. Action 3: Send Internal Notification (SMS or Email)
 - Method: SMS to custom number (business owner number) - Requires A2P verified number in GHL
 - Message: 'Hello, we have a new lead: {{contact.full_name}} - {{contact.phone}} - Service: {{service_needed}}'
6. Action 4: Wait 1 minute (reason: let system settle)
7. Action 5: Send SMS to Contact (Send Message > SMS)
 Template 1 (Immediate):
 'Hi {{contact.first_name}}, it's [Owner Name] from [Business Name]. Thanks for asking about {{service_needed}}. Quick question so I can help you best - when do you want us to come by? Just reply here and I'll sort you out.'
 - Must look like human, not ChatGPT robotic. Short, conversational.
8. Action 6: Wait 2 hours
9. Action 7: Send SMS 2:
 'Hi, just checking if you got my last text. Wanted to know when do you want us to come by?'
10. Action 8: Wait 1 day
11. Action 9: Send SMS 3:
 'Hi, tried contacting you yesterday about a junk removal inquiry that you had on our website. Do you still need it?'
 - IMPORTANT: Say 'website' not 'landing page'
12. Continue sequence per best practice (from video):
 - 2 messages Day 1 (already done)
 - 1 message Day 3
 - 1 message Day 7
 - 1 message Day 10
 - 1 message Day 14
 - Agent should create 6-7 total follow-ups
13. Final Actions: Wait 1 day after last message > Create/Update Opportunity > Move to Stage: Lost
14. Publish Workflow

STEP 3.3 - Workflow 2: Hot Lead - Customer Replied Handler:
1. Create Workflow > Name: Hot Lead - Replied
2. Trigger: Customer Replied
 - Filter: Replied to Workflow = New Lead Automation (any message from Workflow 1)
3. Action 1: Remove from Workflow = New Lead Automation (STOPS further auto-nags after reply)
4. Action 2: Send Internal Notification (SMS to owner)
 - To: Custom number (owner)
 - Message: 'Hot lead responded: {{contact.full_name}} - {{contact.phone}} - Reply: {{message.body}}'
 - Use custom value Message Body to pull actual reply
5. Action 3: Create/Update Opportunity > Pipeline: Meta Ads Leads > Stage: Hot Lead / Responded
6. Publish
Note: Add A2P verification for SMS - US numbers require A2P 10DLC approval. Video references training on his channel for this.

CHECKPOINT: Pipeline visible in Opportunities + 2 workflows published + test lead moves New Lead > reply moves to Hot Lead = Phase 3 complete
## PHASE 4: AD CREATIVES AND AD COPY
Objective: Build creative assets that ARE the targeting (Meta Andromeda update)

STEP 4.1 - Research Creatives via Meta Ad Library:
1. Go to facebook.com/ads/library
2. Select Country = US (or client country), Category = All
3. Search niche keyword: e.g., 'junk removal'
4. Filter > Media Type > Videos (for video ideas) and Images (for image ideas)
5. Sort by Longest Running - ads running since 2024/2025 or months are winners
6. Analyze: What hooks? Before/After? Time-lapse of cleanup? AI videos? Team photos?
Video Best Practices from video:
- Max 30 sec (attention span), absolute max 60 sec, NOT 3 minutes
- Can shoot on iPhone, no need Canva/fancy editor
- Simple: before/after, cleanup timelapse, team at work
- AI video tools: Higgsfield, 11Labs, Meta AI (with watermark)
- Plain images work too - team clearing junk, no fancy headlines needed

STEP 4.2 - Define Ad Angles (Each creative = one angle):
Angle 1: Pain Point - 'Are you suffering from clutter? No space in home?'
Angle 2: Desired Outcome / Dream Result - 'Do you want to reclaim your space? Clear lawn/garage?'
Angle 3: Objection - 'No time to clear? Tried before and failed? Is junk removal expensive? We solve that'
Angle 4: Offer - Lead with discount: 'We are providing $100 discount on first service'
ACTION FOR HERMES: Create 3-4 videos (each different angle) + 3-4 images = 6-8 total to start
Budget strategy: If high budget, run all at once. If low, start with 2 videos + 3 images, keep others as backup to replace low performers.

STEP 4.3 - Ad Copy Generation (ChatGPT Prompt System):
Use prompt from video Google Doc - format:
'Write ad copy for [Company Name] - [Location] - Main Service: [Service] - Residential - Creative Angle: [pain point/desire/objection/offer] - Main message: [homeowners to feel understood, e.g., outdated home can be upgraded so they can reclaim space, let us do heavy lifting] - Specific features: [list] - Services to mention: [list] - Offer: $100 discount on first service - CTA: Get free estimate'
ACTION:
1. Copy full prompt from doc
2. Fill placeholders for each creative
3. Paste into ChatGPT
4. Output: 5 ad copy variations per creative
5. If you have 5 creatives x 5 copies = 25 ad copies total
Copy best practices:
- Add location callout in first line: 'Cary NC Homeowners' or 'Cary North Carolina Homeowners'
- Keep conversational, not robotic
- Each ad should have up to 5 Primary Text variations to let Meta test

STEP 4.4 - Image Specs:
- 1080x1080 square - REQUIRED to avoid cropping in placements (Stories, Feed, Search)
- Avoid brand names like Google/Facebook in headline to prevent rejection
CHECKPOINT: 3-4 videos (30 sec max) + 3-4 images (1080x1080) + 5 copy variations each angle = Phase 4 complete
## PHASE 5: CONVERSION TRACKING - META CONVERSIONS API (CAPI)
Objective: Track page views via Pixel + track form submissions 100% via CAPI

STEP 5.1 - Prerequisites Check:
1. AI Studio funnel has valid subdomain connected (Phase 2.5)
2. Form is natively connected to GHL CRM (Phase 2.4)
3. If not, CAPI will FAIL

STEP 5.2 - Create Meta Pixel / Dataset:
1. Go to business.facebook.com > Click gear icon (Business Settings)
2. Data Sources > Datasets and Pixels > Add > Create Dataset/Pixel
3. Name: [Business Name] Pixel or Dataset - e.g., 'Cary Junk Removers Pixel'
4. No category needed > Create
5. Connect to Ad Account when prompted (must say Yes)
6. Go to Connected Assets tab > Verify ad account is connected

STEP 5.3 - Install Pixel Code (Browser Tracking - PageViews only):
1. Go to Events Manager > Click Setup Meta Pixel > Install code manually
2. Copy full pixel base code
3. Go to GHL AI Studio > Open Project > In AI chat prompt: 'Install this pixel code on this project: [paste code]'
4. Wait for AI to install
5. Back in Events Manager > Continue > Turn on Automatic Advanced Matching > Done
6. In AI Studio > Publish > Publish Changes > Click Publish button to deploy pixel
Purpose: This tracks PageView for future retargeting audiences only. NOT for lead events.

STEP 5.4 - Setup Conversions API:
1. In Events Manager > If new pixel: Click Setup Conversions API
 If old pixel: Click Manage Integrations > Setup Conversions API
2. Choose Setup Manually > Next
3. Select: Conversions API and Meta Pixel > Start CAPI Setup
4. Business Category: Select relevant or 'Other business category' if not found
5. Events to track: Select Contact and Lead (if calendar booking also, select Schedule)
6. For EACH event (Contact and Lead):
 - Identify lead by Event ID
 - Check ALL boxes for signals: email, phone, first name, last name, city, state, zip, country, fbp, fbc, etc.
7. Continue through steps until Access Token screen
8. Generate Access Token: Select Dataset > Generate
9. COPY Access Token (keep safe - sensitive)
10. Finish setup wizard > Go to Settings > Copy Pixel ID / Dataset ID
11. You now have: Pixel ID + Access Token

STEP 5.5 - Create GHL Workflow to Send CAPI Event:
1. GHL > Automation > Workflows > Create New > Name: Landing Page CAPI - Lead
2. Trigger: AI Studio Form Submitted
 - Filter: AI Studio Project = [Your Project]
 - Filter: AI Studio Form = [Your Form]
3. Action: Meta Conversion API (or Facebook Conversion API)
 - Event Type: Funnel Event (because event happened on funnel/page)
 - Access Token: Paste from Step 5.4
 - Dataset ID / Pixel ID: Paste from Step 5.4
 - Event to Send: Lead (if plain lead form) / Schedule (if calendar) / Purchase (if order form)
 - Lifetime Value: e.g., $1000 (LTV of customer in this business) - optional but recommended
 - Currency: USD
 - Test Code: Leave empty
 - Custom Mapping: OFF (because AI Studio contacts are native GHL contacts - custom mapping only for non-native)
4. Save Action > Save Workflow > Publish (move camera if hidden)

STEP 5.6 - Test CAPI with Dummy Tracking Parameters:
1. Use ChatGPT prompt from video: 'Take the landing page URL below and append realistic dummy tracking values for these parameters: fbclid, utm_source, utm_medium, utm_campaign, utm_content, etc.'
2. Paste live subdomain URL > Get back URL with fake Facebook tracking params
3. Example: offer.caryjunkremovers.com?utm_source=facebook&utm_medium=paid_social&utm_campaign=test&fbclid=xxx&fbc=xxx&fbp=xxx
4. Open that URL in incognito
5. Submit test form: Name John Smith, Phone, Email john@gmail.com, Service Furniture Removal
6. Should go to Thank You page
7. Go to GHL > Contacts > Find John Smith > Check:
 - Page URL field = URL with UTMs?
 - Source = Paid Social? (Must be Paid Social for CAPI to fire as Facebook lead)
 - Attribution details present?
8. Go to Workflow Landing Page CAPI > Execution Logs > Click latest run > Meta Conversions API step should say SUCCESS
 - If success: CAPI is working 100% - every real Facebook lead will fire
 - If fails: Check if contact marked as Facebook lead. Non-Facebook leads won't fire (expected) - but test with Facebook params must succeed
9. If someone submits without Facebook params (direct visit), GHL won't mark as Facebook lead, workflow will not send conversion - this is correct behavior (prevents false conversions)
CHECKPOINT: Pixel tracking PageViews + CAPI workflow publishing Lead events with SUCCESS logs = Phase 5 complete
## PHASE 6: FINAL CAMPAIGN LAUNCH
Objective: Launch Facebook Leads campaign driving to AI Studio landing page

STEP 6.1 - Go to Ads Manager:
1. Go to ads.facebook.com or business.facebook.com > Ads Manager
2. Top left dropdown > Switch from Personal Ad Account to Business Ad Account (Cary Junk Removers Ad Account)
3. Click Create

STEP 6.2 - Campaign Level:
1. Objective: Leads > Continue
2. Close any Meta AI recommendations (do NOT follow auto recommendations - will waste money)
3. Name: Leads Campaign - Landing Page or [Business] - Leads - LP
4. Buying Type: Auction
5. Campaign Objective: Leads
6. Campaign Spending Limit: None
7. Budget: DO NOT set at campaign level if testing multiple audiences (CBO will unevenly distribute). Leave OFF for ABO (Ad Set Budget). If single ad set, can set here but video recommends Ad Set level.
8. Click Next

STEP 6.3 - Ad Set Level (Broad Targeting - Andromeda Update):
1. Name: Broad Audience (or Location - Broad)
2. Conversion Location: Website (means landing page, NOT instant forms)
3. Conversion Type: Maximize number of leads (or Maximize number of conversion leads)
4. Dataset / Pixel: Select Pixel from Phase 5 (same one CAPI setup in)
5. Conversion Event: Lead (must match CAPI event)
6. Dynamic Creative: OFF
7. Budget: Daily Budget $70 (video says $50+ minimum, recommends 50/60/70/100). DO NOT do $5/$10/$20 - not enough data for AI. Start $70 daily.
8. Schedule: Start now, no end, no ad scheduling
9. Show More Settings: Leave default
10. Audience - Locations:
 - Click pencil icon > Search city: e.g., Cary, North Carolina
 - Set radius: 17 km (or 10-25 miles depending on service area)
 - CRITICAL: Uncheck 'Reach more people likely to respond to your ads' (prevents showing outside radius in Chapel Hill/Wake Forest etc)
 - Optional: Drop pins to narrow further: Click Drop Pin > Reduce radius to 10km for precise zones
 - Usually home services travel 20-25 miles - keep reasonable
11. Age: Minimum age leave default or set 24+ or 30+ for homeowners (but video says keep broad to give Meta breathing room - don't narrow too much)
12. Exclude: Nothing needed
13. Detailed Targeting / Demographics / Interests / Behaviors: LEAVE EMPTY - Let Meta decide (Broad targeting is new best practice due to Andromeda)
14. Placements: Advantage+ Placements (Let Meta decide)
15. Click Next

STEP 6.4 - Ad Level (Create 5-7 ads under this ad set):
For EACH ad:
1. Name: Image 1 or Video 1 - Pain Point or descriptive (e.g., Before After, Team Photo)
2. Facebook Page: Select client FB Page
3. Instagram Profile: Select (if no IG, ads still show via FB Page on IG placements)
4. Threads: Leave default
5. Setup Creative: Select 'Setup Creative' > Use image or video
6. Website URL: Paste live subdomain URL (e.g., offer.caryjunkremovers.com) - ensure clean, no extra params
7. Display Link: Same subdomain (e.g., offer.caryjunkremovers.com)
8. Upload Creative:
 - Image: Upload 1080x1080 square image (avoids cropping)
 - Video: Upload 30 sec max video
 - Check all placement previews (Feed, Stories, Reels, Search) - must look good
9. Primary Text: Paste from ChatGPT outputs (up to 5 variations per ad)
 - Add location callout in first line: e.g., 'Cary NC Homeowners...' 
10. Headline (multiple):
 - Headline 1: Get a no obligation free quote
 - Headline 2: Junk Removers Cary North Carolina
 - Headline 3: 250+ Positive Reviews (avoid saying Google/Facebook to prevent rejection)
 - Add 2-3 more variations
11. CTA Button: Learn More (video recommends Learn More, not See Details)
12. Advantage+ Creative Enhancements: Review AI-generated variations - if they look weird, uncheck. If fine, keep checked to give Meta more breathing room
13. Click Done / Next
14. Duplicate Ad: Click Duplicate > Change only creative (image/video) + optionally ad copies tailored to that angle
 - If you keep same copies across all ads: You test only creative
 - If you shuffle copies per creative: You test copy angles too (recommended)
15. Repeat until you have 5-7 ads (e.g., 3 videos + 4 images)

STEP 6.5 - Publish Correctly:
1. Go back to Campaign level
2. Select Campaign checkbox (not just ad)
3. Review: Campaign > Ad Set > Each Ad - check everything
4. Click Publish at CAMPAIGN level (Important: If you publish from ad level, only that ad publishes)
5. Wait for approval (usually minutes)

STEP 6.6 - Post-Launch Optimization (Beyond video but required for Hermes):
1. After 2-3 days, check metrics: CTR, CPC, Landing Page Views, Leads, Cost Per Lead
2. Replace low performers with backup creatives from Phase 4
3. Keep winning ads, create variations of winners (same angle, different hook)
4. After enough leads, create retargeting audience: People who visited landing page (needs Pixel PageView from Phase 5.3)
5. Weekly review via Loom recording if part of School Community
6. Never follow all Meta recommendations blindly

CHECKPOINT: Campaign Published with 5-7 ads under 1 broad ad set driving to live subdomain, budget $70/day, CAPI firing = LAUNCH COMPLETE
## HERMES AGENT EXECUTION CHECKLIST (For Automation)
Use this as code logic / task list for Hermes:

[ ] INPUT: Business name, location, service areas, primary service, additional services, offer, phone, years in business, customers served, review count/rating, USP, brand colors/logo files, hero images, before/after images
[ ] Phase1: Check Business Portfolio exists else create + verify email + create ad account + connect FB page + IG + payment method
[ ] Phase1: Create GHL sub-account blank snapshot + enable AI Studio via Labs
[ ] Phase2: Generate offer via LLM if not provided (prompt given)
[ ] Phase2: Load Hormozi mega prompt from Google Doc, replace placeholders with inputs
[ ] Phase2: Generate landing page in AI Studio
[ ] Phase2: Iterative image/logo fixes (5-7 changes per prompt, prompt templates provided)
[ ] Phase2: Prompt 'Connect form to CRM' + verify integration
[ ] Phase2: Create subdomain offer.{domain} + add CNAME vibe.cloud + verify DNS + publish
[ ] Phase2: Test form submission -> verify contact in GHL with attribution
[ ] Phase3: Create pipeline Meta Ads Leads with stages New Lead, Hot Lead/Responded, Closed, Lost
[ ] Phase3: Build Workflow New Lead Automation with filters, opportunity creation, tag, internal SMS notification, wait 1 min, SMS1, wait 2h SMS2, wait 1d SMS3, plus Day3,7,10,14, then move to Lost
[ ] Phase3: Build Workflow Hot Lead - trigger Customer Replied to Workflow New Lead Automation, action Remove from Workflow, internal notification with {{message.body}}, move to Hot Lead
[ ] Phase4: Scrape Meta Ad Library for niche, collect longest-running ads (video + image)
[ ] Phase4: Generate 3-4 videos (30s max) using provided angles: pain, desire, objection, offer
[ ] Phase4: Ensure images 1080x1080
[ ] Phase4: Generate ad copies via ChatGPT prompt template - 5 variations per creative (25 total)
[ ] Phase5: Create Pixel/Dataset, connect ad account, install pixel code via AI Studio prompt, enable advanced matching, publish
[ ] Phase5: Setup CAPI manual, select Contact+Lead events, check all signals, generate access token + pixel ID
[ ] Phase5: Build Workflow Landing Page CAPI - Lead with trigger AI Studio Form Submitted, action Meta Conversion API Funnel Event Lead + LTV
[ ] Phase5: Test with dummy UTM/fbclid URL + form submission + check Execution Logs SUCCESS
[ ] Phase6: Create campaign Leads objective, auction, ABO budget at ad set level
[ ] Phase6: Ad Set: Website conversion, dataset Lead event, daily budget $70+, location radius 17km uncheck expand, broad targeting (no interests), Advantage+ placements
[ ] Phase6: Create 5-7 ads, each with unique creative + 5 primary texts + 3-4 headlines + CTA Learn More + website URL subdomain
[ ] Phase6: Publish at campaign level
[ ] Phase6: Monitor and rotate creatives

Required Secrets: Meta Business Portfolio ID, GHL API key, Domain provider credentials, GHL phone number A2P status, Access Token, Pixel ID

Failure Modes to Handle: DNS propagation delay (retry verify every 5 min), A2P not verified (fallback to email notification), Pixel not installed (re-prompt AI Studio), CAPI fail due to non-Facebook source (expected), Ad rejection due to brand name in headline (remove Google/Facebook words)
## Prompts Library for Hermes
1. Offer Brainstorm Prompt:
'I have a [business type] in [location]. I want to run Facebook ads. What are 5 proven low-friction offers that have historically gotten good results? Must be specific, low friction, easy yes, no big commitment on first touch.'

2. AI Studio Mega Prompt Placeholder - Get from video description Google Doc link: docs.google.com/document/d/1G... (Facebook Ads Document From Video). Contains Alex Hormozi structure.

3. Landing Page Iteration Prompts:
- 'Update the logo and follow the colors from the logo to use in the page'
- 'Update these images in the section after the hero section on the landing page'
- 'Use the attached image in the background of the hero section. Maintain an overlay that has left and right elements stand out while glimpse of background visible'
- 'Remove image from over form on right side of hero. Make logo on header 1.8 times bigger. Add 2-3 navigation menu items on header right side of logo to take us to different sections. On left side of phone call option in header add Google review badge with number of reviews and average rating.'
- 'Make header wider and change background to light background'
- 'Remove phone number from header, centralize logo on mobile'
- 'Connect or integrate the form on the landing page to my CRM'
- 'Install this pixel code on this project: [PASTE CODE]'

4. Ad Copy Prompt:
'Company: [Name], Location: [City, State], Main Service: [Service] + Residential, Creative Angle: [pain point - talking about pain point and emphasizing how we help solve], Main Message: Homeowners to feel understood seeing ad - example their outdated home can be upgraded so they can reclaim space, Let us do heavy lifting, Specific features: [list], Services: [list], Offer: $100 discount on first service, CTA: Get free estimate. Write 5 ad copy variations following proven local home service format.'

5. CAPI Test URL Prompt:
'Take the landing page URL below and append realistic dummy tracking values for these parameters: fbclid, fbc, fbp, utm_source=facebook, utm_medium=paid_social, utm_campaign, utm_content, utm_term. URL: [YOUR SUBDOMAIN]'
## Deliverables
- Live AI Studio Landing Page on subdomain (e.g., offer.business.com)
- Thank You Page
- GHL Pipeline with 4 stages
- 2 Workflows: New Lead Automation + Hot Lead Handler
- Meta Pixel installed + CAPI firing Lead events
- Facebook Campaign with 1 broad ad set ($70/day) + 5-7 ads (1080x1080 images + 30s videos) + 25 ad copies
- Internal SMS notifications to owner
- Speed-to-lead SMS sequence (Day1 x2, Day3, Day7, Day10, Day14)

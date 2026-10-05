# Runbook: offer page, demo calendar, and private demo

Covers source steps 09-19. **Human-only** (GoHighLevel Sites/Funnels, Calendars,
AI Agents, Knowledge Base, chat widget). Approval gates: GHL changes, publishing,
domain connection.

## Offer page (steps 09, 10, 13)

1. Duplicate an appropriate existing CA-J page into a draft named
   `CAJ AI Employee HVAC Offer`. Proposed path `/hvac-ai-employee` on
   ca-jenterprises.com; confirm availability first.
2. Content: CA-J logo, public contact (Chuck Ashley, 512-229-9199,
   chuck@ca-jconsulting.com), a clear explanation, a short demonstration, and one
   primary CTA "Book your HVAC AI demo" linking to https://ca-jenterprises.com/ai.
3. **No price on the page.** The source step 10 asks for "draft price and usage terms";
   CA&J is meeting-first, so the page shows none. Terms are discussed in the meeting.
4. Use only verified capabilities. No results, testimonials, or review counts unless a
   verified CA-J source exists.
5. Privacy and service terms must match actual data collection; a generated draft is
   not a substitute for review. Check mobile layout, links, SSL after an authorized
   domain connection, and the form success state. Keep the page as a draft until
   publication is authorized.

## Demo calendar (steps 11, 12)

1. Create `CAJ HVAC AI Demo`: 15-minute duration, owner Chuck or the confirmed
   salesperson, timezone America/Chicago, real availability, buffers and minimum
   notice that allow demo preparation.
2. Form fields: first name, business name, website, email, phone, main after-hours
   problem. Optional marketing permission kept separate.
3. Book one synthetic appointment (example.com email), confirm owner, timezone,
   meeting link, contact, and appointment record; cancel it and confirm availability
   returns.
4. Record calendar ID and booking URL in `records/Asset_Register.csv` and set
   `DEMO_CALENDAR_ID` / `DEMO_CALENDAR_URL` locally (never commit `.env`).

## Private personalized demo (steps 14-19)

1. Record prospect business name, homepage, niche, meeting time, contact ID.
2. Build the preview in an isolated demo workspace, labelled "Demo preview"; remove
   live purchases, external lead forms, and tracking. Never replace the prospect's
   live website. noindex alone does not make a page private.
3. Duplicate the licensed HVAC demo agent and knowledge base as
   `DEMO HVAC [Business] [Date]`. If the licensed pack is missing, use
   `agent/system-prompt.md` rendered with `scripts/render_templates.py` and record that
   it is a basic prototype, not the trainer's pack.
4. Crawl the prospect's site (service, contact, FAQ, area, hours pages); review the
   extracted facts; exclude stale promotions. Add verified text manually if the crawl
   fails, with its source URL and date.
5. Create the chat widget, check the text agent and the web-call (voice) mappings
   separately, attach it to the preview page, and test microphone, audio, text, and
   mobile.
6. Run the six questions in `agent/demo-questions.md`; save one text transcript and
   one voice test log; fix and rerun failures before the meeting.

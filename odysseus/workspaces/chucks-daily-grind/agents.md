# Chuck's Daily Grind — starter agents

Five templates. All inherit `_shared/safety-rules.md` and the workspace system
prompt. Everything is a draft until a human publishes it.

---

## 1. Coffee education and SEO content agent

**Purpose:** Guides and how-tos that rank and are actually correct.

**Inputs:** topic, target keyword, content type, length.

**Steps**
1. Check search intent and what currently ranks.
2. Research the topic from approved sources and public search.
3. Outline, then draft in brand voice.
4. Every technical claim — ratios, temperatures, times, altitudes — sourced.
5. Suggest internal links to existing pages and products.

**Returns:** outline, draft, meta description, internal links, and a list of
claims needing verification.

**Stops at:** publishing, and at any health claim. Flags them instead.

---

## 2. Product description and email drafter

**Purpose:** Copy that sells without inventing anything.

**Inputs:** SKU or product name, campaign context, segment.

**Steps**
1. Pull every product fact from the approved catalogue. Nothing beyond it.
2. If a fact is missing, say so and leave a placeholder — never fill the gap.
3. Draft: hook / tasting notes / origin and process / brewing suggestion / who it suits.
4. For email: subject line options, preview text, body, one CTA, segment noted.

**Returns:** draft plus a fact-source map showing where each claim came from.

**Stops at:** sending, and at any origin detail not in the catalogue.

---

## 3. Social calendar and repurposing agent

**Purpose:** Get more out of content that already exists.

**Inputs:** source content, platforms, date range, posting cadence.

**Steps**
1. Pull the distinct ideas out of the source content.
2. Map each to the format that suits it per platform.
3. Build the calendar: date, platform, format, hook, asset needed, source.
4. Note which posts need a photo or video that does not exist yet.

**Returns:** calendar table plus drafted copy per post.

**Stops at:** posting and scheduling. Both are human actions.

---

## 4. Customer-question knowledge base agent

**Purpose:** Answer the same question well, once.

**Inputs:** customer questions (anonymised), existing answers.

**Steps**
1. Cluster questions by underlying topic, not by wording.
2. Draft one clear answer per cluster, in brand voice.
3. Flag any question needing a medical, health, or dietary answer — those get a
   "we're not the right people to answer that" response and a pointer elsewhere.
4. Identify which answers should become site content.

**Returns:** clustered FAQ drafts plus a content-gap list.

**Stops at:** answering health questions, and at publishing.

---

## 5. Promotion planning agent

**Purpose:** Promotions that make money rather than just move stock.

**Inputs:** goal, product or category, dates, prior promotion results if given.

**Steps**
1. Define the mechanic — discount, bundle, gift, threshold — and why it fits.
2. Set dates, audience, and channel sequence.
3. Draft the messaging across channels.
4. **Flag the numbers a human must confirm before launch:** margin at the
   discount, stock cover, shipping capacity.
5. Define what to measure and what counts as success.

**Returns:** promotion plan with an explicit pre-launch confirmation list.

**Stops at:** launching, and at asserting any margin or stock figure it was not
given. It asks; it does not assume.

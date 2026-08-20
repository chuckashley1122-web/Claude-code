# Local market sourcing — CA-J Enterprises

**Status:** DRAFT. Not yet approved. `approved: false` in the knowledge manifest.

> Drafted by Claude Code. **This file deliberately contains almost no local
> facts.** Permit rules, fee schedules, code cycles, and licensing requirements
> change, and a stale fact in a reference file propagates into every article
> written from it. What it contains instead is *where to look* — so the
> `local-content-research` skill can source a claim at the moment it writes it,
> which is the only time the answer is reliable.
>
> Verify list at the end.

---

## 1. The rule

Local content wins on specifics. Specifics are also where invented detail does
the most damage: a wrong permit requirement or a wrong licensing claim is the
kind of error a competitor screenshots, and it makes the client look like they
do not know their own market.

So:

**Every local claim gets sourced at the time of writing, from a primary source,
with the URL and the date checked recorded in the draft.**

Not from this file. Not from memory. Not from a competitor's blog post, which is
where most local misinformation originates and propagates.

A claim that cannot be sourced does not get written. It goes on the
owner-verification list instead — which is why every research brief and content
draft in this workspace ends with one.

---

## 2. Source hierarchy

Use the highest tier available. Never cite a lower tier when a higher one exists.

| Tier | Source | Use for |
|---|---|---|
| 1 | The governing authority's own site — city, county, state agency, licensing board | Permits, code, licensing, fees, timelines |
| 2 | Published industry standards bodies and manufacturers | Technical specification, product life, warranty terms |
| 3 | Established trade publications and utility providers | Context, seasonality, cost drivers |
| 4 | The client's own documented experience | Anything only they can attest to — mark it as their claim |
| — | Competitor blogs, content farms, AI summaries, forum posts | **Never a source.** Useful for finding what to verify, never for the claim itself |

Tier 4 is not weak — a client saying "in this market we usually see X" is
genuinely valuable. It just gets attributed as their experience rather than
presented as a fact.

---

## 3. Where to verify, by claim type

Named so the researcher can navigate to the current page rather than trusting a
URL that may have moved.

### Trade licensing (Texas)

- **Texas Department of Licensing and Regulation (TDLR)** — air conditioning and
  refrigeration contractors, electricians, and a range of other trades. TDLR
  publishes a public license search; use it to verify a specific license number
  and status.
- **Texas State Board of Plumbing Examiners** — plumbers.
- **Roofing** — verify current status before writing anything. As of drafting,
  Texas does not license roofing contractors at state level, which means
  "licensed roofer" claims are a problem. See
  `ad-platform-policies.md` §5. **Re-confirm this; it is exactly the kind of
  thing a legislature changes.**
- **General contracting** — no statewide licence historically, but local
  registration may apply. Check the specific city.

Always verify a client's actual licence number and status through the issuing
body before any content or ad claims it.

### Permits, inspections, and code

- **City of Austin** — development services / building permits, for properties
  inside Austin city limits.
- **City of Round Rock** — building inspections and permits.
- **Travis County and Williamson County** — for properties outside city limits,
  where county rather than city rules apply. This distinction catches people
  out: an Austin mailing address does not mean Austin jurisdiction.
- **Adopted code editions and amendments** are published per jurisdiction and
  are on a revision cycle. Never state which code edition applies without
  checking the current adoption for that specific jurisdiction.

Because service areas straddle city and county lines, always determine which
authority actually governs the address before writing about permits.

### Insurance and storm claims

- **Texas Department of Insurance** — consumer guidance, licensing of public
  adjusters, and complaint processes.
- The deductible and public-adjusting restrictions in
  `ad-platform-policies.md` §4 are the highest-risk area in this market. Confirm
  the current statutory position before any storm-related content or campaign.

### Weather, climate, and seasonality

- **National Weather Service** and **NOAA** for historical weather, storm dates,
  hail events, and freeze events.
- **ERCOT** for grid conditions and demand context — relevant to HVAC content.
- Local utility providers for rate structures and efficiency programmes.

Storm-damage content frequently cites a specific past event. Get the date and
the affected area from a weather source, not from a roofing company's blog.

### Market and demographic context

- **US Census Bureau** and the American Community Survey for household counts,
  housing age, and owner-occupancy.
- **City and county open data portals** for permit volumes and construction
  activity — often the best available proxy for local demand.

**Fair housing caution.** Demographic data may inform where a client operates.
It must never be used to target, exclude, or tailor messaging by a protected
characteristic, and content must never describe a neighborhood in terms that
function as a demographic proxy. The reasoning in the CA-J Consulting compliance
guardrails applies here too — the Fair Housing Act reaches advertising, and
home-services work sits close enough to housing to warrant the same discipline.

---

## 4. Claims that need a source every time

Never write these from memory or from a competitor's page:

- Any permit requirement, cost, or timeline
- Any licensing requirement, or a claim a client is licensed
- Any building code provision or adopted edition
- Any statement about what insurance covers
- Any statistic about the local market
- Any date or severity of a past weather event
- Any claim about local climate, soil, or common failure modes
- Any utility rate, rebate, or incentive programme
- Any legal or regulatory requirement on a homeowner

---

## 5. What to record in the draft

For every sourced local claim:

- the claim as written
- the source name and URL
- the date checked
- the tier from §2

For every claim that could not be sourced:

- the claim, on the owner-verification list, with what would be needed to
  confirm it

A draft that reaches a human without these is incomplete, regardless of how good
the copy reads.

---

## 6. Freshness

Local facts decay at very different rates. Re-verify before reusing:

| Claim type | Re-verify |
|---|---|
| Permit fees and timelines | Every use |
| Licensing requirements | Every use |
| Adopted code edition | Every use |
| Insurance rules | Every use, and with counsel for anything material |
| Weather event details | Once; they are historical |
| Census and demographic data | Annually, or at each data release |
| Client-attested claims | At each engagement |

"I checked that last quarter" is not a source. Re-check, or move the claim to
the verification list.

---

## Verify before approval

1. **The licensing landscape in §3** — which body currently licenses each trade,
   and specifically whether roofing remains unlicensed at state level in Texas.
   This is asserted in two files and should be confirmed once, properly.
2. Confirm the named authorities are current and correctly named — agencies get
   reorganised and renamed.
3. Confirm the city/county jurisdiction split guidance matches how the client's
   actual service area works.
4. Decide whether Tier 4 client-attested claims may appear in published content
   at all, or only in internal briefs.
5. Confirm the fair-housing caution in §3 is strong enough for the client mix,
   and whether any client's work is housing-related enough to trigger the Meta
   Special Ad Category in `ad-platform-policies.md` §2.
6. Add any authority specific to a client's trade that this file omits.

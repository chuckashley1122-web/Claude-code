<!-- FROZEN-CAMPAIGN-WARNING:START -->
> **WARNING - FROZEN LIVE CAMPAIGN: `CAJ_HVAC27_US_PURCHASE_TEST02`**
> It must NOT be edited, paused, resumed or duplicated, and must never be selected as the target of any step below. Editing it resets Meta's learning phase. All work in this checklist happens in a SEPARATE NEW draft campaign.
<!-- FROZEN-CAMPAIGN-WARNING:END -->

# META checklist (human, logged in to business.facebook.com)

Nothing below has been done by the build. Work top to bottom; tick only what you actually did.

## 1. Business Portfolio and assets
- [ ] Business Settings: confirm a Business Portfolio exists for CA-J Enterprises (create only if none exists).
- [ ] Verify the business email and domain in the portfolio.
- [ ] Ad account: confirm or create the CA-J ad account (ID goes in local .env as META_AD_ACCOUNT_ID; NEEDS_EVIDENCE).
- [ ] Payment method: REQUIRES EXPLICIT HUMAN APPROVAL (spend item). Do not add without a written approval reference.
- [ ] Settings > Accounts > Pages: connect the CA-J Facebook Page (META_PAGE_ID in .env).
- [ ] Settings > Accounts > Instagram accounts: connect the CA-J Instagram profile (if one exists).
- [ ] Confirm Admin access on the portfolio, ad account, Page and Instagram profile.

## 2. Pixel / Dataset (see out/pixel_capi_spec.md)
- [ ] Business Settings > Data Sources > Datasets and Pixels > Add > Create: name `<BUSINESS> Pixel` (NEEDS_EVIDENCE).
- [ ] Connect to ad account when prompted: answer Yes. Verify under Connected Assets.
- [ ] Events Manager > Setup Meta Pixel > Install code manually > copy base code; install via AI Studio chat (never paste it into the repo).
- [ ] Turn on Automatic Advanced Matching > Done.

## 3. Conversions API
- [ ] Setup Conversions API > Setup Manually > Conversions API and Meta Pixel.
- [ ] Events: Contact and Lead (add Schedule only if calendar booking is added).
- [ ] Each event: identify by Event ID; check signals: email, phone, first name, last name, city, state, zip, country, fbp, fbc.
- [ ] Generate access token; store ONLY in the GHL CAPI action and local .env as META_CAPI_ACCESS_TOKEN.
- [ ] Copy Pixel/Dataset ID into local .env as META_PIXEL_ID / META_DATASET_ID.

## 4. NEW draft campaign `CAJ-FB-HVAC-Leads-20261005-DRAFT` (values from out/campaign_config.json)
- [ ] Ads Manager > switch to the CA-J business ad account > Create > Objective Leads. Name `CAJ-FB-HVAC-Leads-20261005-DRAFT`.
- [ ] Close Meta AI recommendations. Buying type Auction. Campaign spending limit None.
- [ ] Campaign budget: OFF (ABO - budget at ad-set level).
- [ ] Special Ad Category: NEEDS_EVIDENCE - decide from the actual campaign and current platform prompts.
- [ ] Ad set `Broad Audience - DRAFT`: conversion location Website; Maximize number of leads; dataset = the pixel above; conversion event Lead; dynamic creative OFF.
- [ ] Ad-set daily budget: NEEDS_EVIDENCE - REQUIRES EXPLICIT HUMAN APPROVAL. Leave unset without a written approval reference.
- [ ] Schedule NEEDS_EVIDENCE; location NEEDS_EVIDENCE radius NEEDS_EVIDENCE; UNCHECK 'Reach more people likely to respond to your ads'.
- [ ] Age NEEDS_EVIDENCE; exclusions none; detailed targeting EMPTY; placements Advantage+ Placements.
- [ ] Create 6 ads per out/campaign_spec.md: Page, Instagram profile, website URL = verified landing-page URL (clean, no parameters), display link, creative, up to 5 primary texts, 3-4 headlines, CTA Learn More.
- [ ] Every creative opens with a pain or an outcome - never the logo. Check every placement preview.
- [ ] Review Advantage+ creative enhancements manually; uncheck odd variations.
- [ ] Headlines: no 'Google'/'Facebook' wording (rejection risk).

## 5. Publish (only after approval)
- [ ] Publish: REQUIRES EXPLICIT HUMAN APPROVAL (APPROVAL_LAUNCH and APPROVAL_AD_SPEND, with written references).
- [ ] Publish at CAMPAIGN level by ticking the `CAJ-FB-HVAC-Leads-20261005-DRAFT` campaign checkbox - never from the ad level.
- [ ] Rollback if needed: toggle off THIS draft campaign at campaign level; set GHL workflows 01 and 03 to Draft.

# Human decisions queue

Every `NEEDS_EVIDENCE` value and every approval gate. Owner for all items: Chuck Ashley.

## NEEDS_EVIDENCE values
| Item | Current value / missing input | Next action | Owner |
|---|---|---|---|
| build_config.primary_location | NEEDS_EVIDENCE | Supply a verified value for `primary_location` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.service_areas | NEEDS_EVIDENCE | Supply a verified value for `service_areas` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.primary_service | NEEDS_EVIDENCE | Supply a verified value for `primary_service` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.additional_services | NEEDS_EVIDENCE | Supply a verified value for `additional_services` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.offer_expiration | NEEDS_EVIDENCE | Keep omitted unless verified evidence exists; to use `offer_expiration`, attach the evidence and remove it from EVIDENCE_GATED_KEYS in tools/validate_config.py (human decision). | Chuck Ashley |
| build_config.avg_response_time | NEEDS_EVIDENCE | Supply a verified value for `avg_response_time` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.est_service_time | NEEDS_EVIDENCE | Supply a verified value for `est_service_time` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.years_in_business | NEEDS_EVIDENCE | Keep omitted unless verified evidence exists; to use `years_in_business`, attach the evidence and remove it from EVIDENCE_GATED_KEYS in tools/validate_config.py (human decision). | Chuck Ashley |
| build_config.customers_served | NEEDS_EVIDENCE | Keep omitted unless verified evidence exists; to use `customers_served`, attach the evidence and remove it from EVIDENCE_GATED_KEYS in tools/validate_config.py (human decision). | Chuck Ashley |
| build_config.review_rating | NEEDS_EVIDENCE | Keep omitted unless verified evidence exists; to use `review_rating`, attach the evidence and remove it from EVIDENCE_GATED_KEYS in tools/validate_config.py (human decision). | Chuck Ashley |
| build_config.review_count | NEEDS_EVIDENCE | Keep omitted unless verified evidence exists; to use `review_count`, attach the evidence and remove it from EVIDENCE_GATED_KEYS in tools/validate_config.py (human decision). | Chuck Ashley |
| build_config.guarantee | NEEDS_EVIDENCE | Keep omitted unless verified evidence exists; to use `guarantee`, attach the evidence and remove it from EVIDENCE_GATED_KEYS in tools/validate_config.py (human decision). | Chuck Ashley |
| build_config.usp | NEEDS_EVIDENCE | Supply a verified value for `usp` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.main_pain_points | NEEDS_EVIDENCE | Supply a verified value for `main_pain_points` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.desired_outcomes | NEEDS_EVIDENCE | Supply a verified value for `desired_outcomes` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.brand_colors | NEEDS_EVIDENCE | Supply a verified value for `brand_colors` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.logo_path | NEEDS_EVIDENCE | Supply a verified value for `logo_path` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.hero_image_path | NEEDS_EVIDENCE | Supply a verified value for `hero_image_path` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.before_after_images | NEEDS_EVIDENCE | Supply a verified value for `before_after_images` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.landing_page_url | NEEDS_EVIDENCE | Supply a verified value for `landing_page_url` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.facebook_page_id | NEEDS_EVIDENCE | Record only in a local .env as `META_PAGE_ID`; never commit. Config stays NEEDS_EVIDENCE. | Chuck Ashley |
| build_config.ad_account_id | NEEDS_EVIDENCE | Record only in a local .env as `META_AD_ACCOUNT_ID`; never commit. Config stays NEEDS_EVIDENCE. | Chuck Ashley |
| build_config.instagram_profile_id | NEEDS_EVIDENCE | Select it in Ads Manager when building the ad; no ID is stored in the repo. | Chuck Ashley |
| build_config.pixel_id | NEEDS_EVIDENCE | Record only in a local .env as `META_PIXEL_ID`; never commit. Config stays NEEDS_EVIDENCE. | Chuck Ashley |
| build_config.dataset_id | NEEDS_EVIDENCE | Record only in a local .env as `META_DATASET_ID`; never commit. Config stays NEEDS_EVIDENCE. | Chuck Ashley |
| build_config.ghl_project_name | NEEDS_EVIDENCE | Supply a verified value for `ghl_project_name` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.ghl_form_name | NEEDS_EVIDENCE | Supply a verified value for `ghl_form_name` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.a2p_status | NEEDS_EVIDENCE | Supply a verified value for `a2p_status` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| build_config.privacy_policy_url | NEEDS_EVIDENCE | Supply a verified value for `privacy_policy_url` in config/build_config.json and rebuild (or keep omitted). | Chuck Ashley |
| constants.CNAME_VALUE | NEEDS_EVIDENCE | Read the CNAME target from AI Studio when adding the custom domain | Chuck Ashley |
| constants.DAILY_BUDGET_USD | NEEDS_EVIDENCE | Approve an exact daily budget in writing, or leave unset | Chuck Ashley |
| campaign.special_ad_category | NEEDS_EVIDENCE | Decide from the actual campaign and current Meta prompts | Chuck Ashley |
| ad_set.schedule | NEEDS_EVIDENCE | Choose start date / no end date | Chuck Ashley |
| ad_set.radius | NEEDS_EVIDENCE | Choose a radius for the target market | Chuck Ashley |
| ad_set.age | NEEDS_EVIDENCE | Choose age setting (source says keep broad) | Chuck Ashley |
| capi.ltv | NEEDS_EVIDENCE | Choose a lifetime value figure for the CAPI action, or leave blank | Chuck Ashley |
| capi.pixel_name | NEEDS_EVIDENCE | Name the pixel `<BUSINESS> Pixel` | Chuck Ashley |
| capi.business_category | NEEDS_EVIDENCE | Pick the Events Manager business category | Chuck Ashley |
| landing.mega_prompt_body | NEEDS_EVIDENCE | Obtain the source's mega prompt (Google Doc never supplied) | Chuck Ashley |
| landing.consent_wording | NEEDS_EVIDENCE | Legal review of the consent disclosure | Chuck Ashley |
| landing.insurance_license | NEEDS_EVIDENCE | Confirm whether any licence/insurance statement applies | Chuck Ashley |
| landing.testimonials | NEEDS_EVIDENCE | Supply real testimonials with written permission, or keep omitted | Chuck Ashley |
| ads.[LOCATION] callout | NEEDS_EVIDENCE | Supply the target location for the first-line callout | Chuck Ashley |
| ads.creative_source_files | NEEDS_EVIDENCE | Produce the images/videos from out/ads/creative_specs.md | Chuck Ashley |
| workflows.merge_token_fields | NEEDS_EVIDENCE | Insert every {{...}} field with the GHL field picker and preview | Chuck Ashley |
| ai_studio.availability | NEEDS_EVIDENCE | Confirm Settings > Labs > AI Studio exists on this account | Chuck Ashley |
| blocker.a2p_status | A2P 10DLC registration status for the GHL sending number | Confirm A2P status in GHL; until then use the email fallback path | Chuck Ashley |
| blocker.ghl_project_name | Exact AI Studio project name | Read the name from AI Studio after the page is generated; set it in build_config.json | Chuck Ashley |
| blocker.ghl_form_name | Exact AI Studio form name | Read the name from AI Studio after the page is generated; set it in build_config.json | Chuck Ashley |
| blocker.pixel_id | Pixel/Dataset created in Business Settings (value kept in .env as META_PIXEL_ID) | Human completes META-CHECKLIST Pixel section | Chuck Ashley |
| blocker.mega_prompt_body | The source's AI Studio mega prompt (Google Doc, never supplied) | Chuck obtains the doc text and pastes it with the fill script | Chuck Ashley |
| blocker.primary_location | Target location / service area for the ad callout and ad set | Chuck supplies the target market; replace [LOCATION] | Chuck Ashley |
| blocker.creative_assets | Real images/videos produced from the briefs | Human shoots on a phone or uses an approved tool (spend item) | Chuck Ashley |
| blocker.daily_budget | Exact daily budget + written approval reference | Chuck approves an amount in writing or leaves it unset | Chuck Ashley |
| blocker.landing_page_url | Verified live subdomain URL | Publish AI Studio page on the approved subdomain, set landing_page_url, rebuild | Chuck Ashley |

## Approval gates (spend and launch)
| Service / action | Purpose | Approval | Cost |
|---|---|---|---|
| Meta ad spend (campaign daily budget) | Delivering the NEW draft Leads campaign once approved | approval required | NEEDS_EVIDENCE |
| Meta ad account payment method | Required by Meta before any ad can deliver | approval required | NEEDS_EVIDENCE |
| Domain purchase (registrar) | Domain for the offer./call./contact. landing-page subdomain | approval required | NEEDS_EVIDENCE |
| GoHighLevel sub-account / AI Studio access | Hosting the landing page, form, pipeline and workflows | approval required | NEEDS_EVIDENCE |
| A2P 10DLC registration for the GHL number | Sending the speed-to-lead SMS sequence and owner SMS alerts | approval required | NEEDS_EVIDENCE |
| GHL SMS / email usage | Per-message sending for the follow-up sequence | approval required | NEEDS_EVIDENCE |
| AI image / video generation tool | Producing the 1080x1080 images and 30-second videos from the creative briefs | approval required | NEEDS_EVIDENCE |
| Launch / publish the draft campaign | Start delivery | approval required | see ad spend |
| Publish GHL workflows | Start sending messages | approval required | see SMS/email usage |

# 005 HUMAN-DECISIONS (SPEC-05)

WARNING: CAJ_HVAC27_US_PURCHASE_TEST02 is FROZEN — never edit, pause or duplicate it; STRIPE is connected to that ad account, so any budget change is a real financial action. This build does not touch it.

**Why:** Every unknown value and approval gate in SPEC-05 needs a named human decision.

**Where:** config/build_config.json, config/business_facts.json and the GHL account (https://app.gohighlevel.com).

**Steps:**

1. Work through each table below; replace NEEDS_EVIDENCE only with a value that has an evidence link.
2. Re-run `python tools/build_all.py` from the build root after each change.

**Verify:** `python tools/secret_scan.py` and `python tools/compliance_scan.py` exit 0 after edits.

**Blocked by:** human access to GHL, the registrar, Search Console and approved business material.

## NEEDS_EVIDENCE values

| Key | Where | Owner | Next action |
|---|---|---|---|
| site_origin | config/build_config.json | Chuck Ashley | Supply verified value |
| business_name | config/build_config.json | Chuck Ashley | Supply verified value |
| primary_location | config/build_config.json | Chuck Ashley | Supply verified value |
| service_areas | config/build_config.json | Chuck Ashley | Supply verified value |
| services_verified | config/build_config.json | Chuck Ashley | Supply verified value |
| primary_service | config/build_config.json | Chuck Ashley | Supply verified value |
| additional_services | config/build_config.json | Chuck Ashley | Supply verified value |
| main_offer | config/build_config.json | Chuck Ashley | Supply verified value |
| primary_cta | config/build_config.json | Chuck Ashley | Supply verified value |
| logo_path | config/build_config.json | Chuck Ashley | Supply verified value |
| hero_image_path | config/build_config.json | Chuck Ashley | Supply verified value |
| og_image_path | config/build_config.json | Chuck Ashley | Supply verified value |
| review_rating | config/build_config.json | Chuck Ashley | Supply verified value |
| review_count | config/build_config.json | Chuck Ashley | Supply verified value |
| years_in_business | config/build_config.json | Chuck Ashley | Supply verified value |
| customers_served | config/build_config.json | Chuck Ashley | Supply verified value |
| guarantee | config/build_config.json | Chuck Ashley | Supply verified value |
| license_info | config/build_config.json | Chuck Ashley | Supply verified value |
| privacy_policy_url | config/build_config.json | Chuck Ashley | Supply verified value |
| ghl_project_id | config/build_config.json | Chuck Ashley | Supply verified value |
| ghl_project_name | config/build_config.json | Chuck Ashley | Supply verified value |
| ghl_form_id | config/build_config.json | Chuck Ashley | Supply verified value |
| ghl_draft_url | config/build_config.json | Chuck Ashley | Supply verified value |
| ghl_live_url | config/build_config.json | Chuck Ashley | Supply verified value |
| ghl_version_id | config/build_config.json | Chuck Ashley | Supply verified value |
| ai_studio_ssr_supported | config/build_config.json | Chuck Ashley | Supply verified value |
| ghl_api_version | config/build_config.json | Chuck Ashley | Supply verified value |
| ghl_api_scopes | config/build_config.json | Chuck Ashley | Supply verified value |
| ghl_pipeline_id | config/build_config.json | Chuck Ashley | Supply verified value |
| ghl_stage_id | config/build_config.json | Chuck Ashley | Supply verified value |
| ghl_custom_field_ids | config/build_config.json | Chuck Ashley | Supply verified value |
| search_console_property | config/build_config.json | Chuck Ashley | Supply verified value |
| analytics_id | config/build_config.json | Chuck Ashley | Supply verified value |
| a2p_status | config/build_config.json | Chuck Ashley | Supply verified value |
| dns_records | config/build_config.json | Chuck Ashley | Supply verified value |
| business_name | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| site_origin | config/business_facts.json | Chuck Ashley | Confirm domain in work order 005-001; no purchase without approval (005-007) |
| services_verified | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| service_areas | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| primary_location | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| local_coverage_austin | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| local_coverage_round_rock | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| offer_details_at_ai | config/business_facts.json | Chuck Ashley | Human records the current /ai offer as-is in work order 005-001 |
| logo_file | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| photos | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| license_info | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| insurance | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| guarantee | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| response_time | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| testimonials | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| review_rating | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| review_count | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| years_in_business | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| customers_served | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| results | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| office_address | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| opening_hours | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| privacy_policy_url | config/business_facts.json | Chuck Ashley | Supply approved material and an evidence link, then set verified=true |
| SERVICE_ALLOWLIST | config/constants.py | Chuck Ashley | Supply verified value |
| ALLOWED_SOURCE_ORIGINS | config/constants.py | Chuck Ashley | Supply verified value |
| RATE_LIMIT_CONFIG | config/constants.py | Chuck Ashley | Supply verified value |

## Open blockers

| Item | Missing input | Next action |
|---|---|---|
| estimator | service unit; allowed quantity range; material rate; labour assumptions; travel rule; minimum charge; tax treatment; exclusions; rounding rule; binding-vs-indicative status; pricing_version; at least three approved worked examples | Business supplies versioned pricing rules and three worked examples |
| existing_routes | Existing live route list | Human supplies URL list and runs tools/baseline_inventory.py |
| fact:business_name | Approved public business name for page copy and JSON-LD | Supply approved material and an evidence link, then set verified=true |
| fact:customers_served | Count of clients served | Supply approved material and an evidence link, then set verified=true |
| fact:guarantee | Any guarantee offered | Supply approved material and an evidence link, then set verified=true |
| fact:insurance | Insurance held | Supply approved material and an evidence link, then set verified=true |
| fact:license_info | Licences held | Supply approved material and an evidence link, then set verified=true |
| fact:local_coverage_austin | Actual local coverage and city-specific information for Austin | Supply approved material and an evidence link, then set verified=true |
| fact:local_coverage_round_rock | Actual local coverage and city-specific information for Round Rock | Supply approved material and an evidence link, then set verified=true |
| fact:logo_file | Approved logo file (footer use only) | Supply approved material and an evidence link, then set verified=true |
| fact:offer_details_at_ai | What the offer at the booking URL currently contains (do not rewrite it) | Human records the current /ai offer as-is in work order 005-001 |
| fact:office_address | Public office/postal address | Supply approved material and an evidence link, then set verified=true |
| fact:opening_hours | Published opening hours | Supply approved material and an evidence link, then set verified=true |
| fact:photos | Approved photos with descriptive alt text | Supply approved material and an evidence link, then set verified=true |
| fact:primary_location | Primary business location | Supply approved material and an evidence link, then set verified=true |
| fact:privacy_policy_url | Privacy policy URL | Supply approved material and an evidence link, then set verified=true |
| fact:response_time | Any response-time promise | Supply approved material and an evidence link, then set verified=true |
| fact:results | Client results or statistics | Supply approved material and an evidence link, then set verified=true |
| fact:review_count | Review count with source | Supply approved material and an evidence link, then set verified=true |
| fact:review_rating | Review rating with source | Supply approved material and an evidence link, then set verified=true |
| fact:service_areas | Real service areas actually covered | Supply approved material and an evidence link, then set verified=true |
| fact:services_verified | Approved list of services actually offered | Supply approved material and an evidence link, then set verified=true |
| fact:site_origin | Owned/confirmed domain (scheme + host) for canonicals and sitemap | Confirm domain in work order 005-001; no purchase without approval (005-007) |
| fact:testimonials | Client testimonials with written permission | Supply approved material and an evidence link, then set verified=true |
| fact:years_in_business | Years in business | Supply approved material and an evidence link, then set verified=true |
| jsonld:BreadcrumbList | verified source for BreadcrumbList (needs absolute URLs from a verified site_origin) | Supply verified fact in config/business_facts.json, then rebuild |
| jsonld:LocalBusiness | verified source for LocalBusiness (needs verified address and service area) | Supply verified fact in config/business_facts.json, then rebuild |
| jsonld:Service | verified source for Service (service not in services_verified) | Supply verified fact in config/business_facts.json, then rebuild |
| jsonld:address | verified source for address | Supply verified fact in config/business_facts.json, then rebuild |
| jsonld:aggregateRating | verified source for aggregateRating | Supply verified fact in config/business_facts.json, then rebuild |
| jsonld:areaServed | verified source for areaServed | Supply verified fact in config/business_facts.json, then rebuild |
| jsonld:logo | verified source for logo | Supply verified fact in config/business_facts.json, then rebuild |
| jsonld:openingHours | verified source for openingHours | Supply verified fact in config/business_facts.json, then rebuild |
| jsonld:priceRange | verified source for priceRange | Supply verified fact in config/business_facts.json, then rebuild |
| jsonld:review | verified source for review | Supply verified fact in config/business_facts.json, then rebuild |
| jsonld:url | verified source for url | Supply verified fact in config/business_facts.json, then rebuild |
| location_pages | Verified local coverage per city | Supply verified coverage and city-specific information, or approve one service-area page that lists only confirmed areas. |
| og_image | Approved absolute social preview image URL | Supply an approved image hosted at the confirmed origin |
| redirect_sources | Real old URLs from the existing site | Human supplies config/redirect_input.json after baseline inventory |
| site_origin | Confirmed site origin (domain) | Human confirms domain via work order 005-001 / 005-007 |

## Approval gates

| Gate | Dollar amount | Current state |
|---|---|---|
| Site publish | $0 | SITE_PUBLISH_APPROVED = False |
| Domain purchase | USD NEEDS_EVIDENCE (quote required) | DOMAIN_PURCHASE_APPROVED = False |
| Ad spend | $0 cap | AD_SPEND_CAP_USD = 0 |
| Estimator enablement | $0 | ESTIMATOR_ENABLED = False |
| Domain registration or transfer (only if no owned domain is confirmed) | USD NEEDS_EVIDENCE | approval required, none given |
| GoHighLevel plan change or AI Studio add-on (only if SSR/server functions/secrets require it) | USD NEEDS_EVIDENCE | approval required, none given |
| GoHighLevel API access beyond the current plan (if required for the inquiry integration) | USD NEEDS_EVIDENCE | approval required, none given |
| Paid SEO tool (none prescribed; the zero-cost path is the design) | USD NEEDS_EVIDENCE | approval required, none given |
| Ad spend (out of scope; AD_SPEND_CAP_USD = 0) | USD NEEDS_EVIDENCE | approval required, none given |

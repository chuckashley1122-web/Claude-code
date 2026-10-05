"""Human UI checklists -> ui-tasks/*.md and ui-work-orders/004-*.md (SPEC-04 step 24).

Every item names the exact object, field and value. Nothing here is reported
as done; each box is for a human with a logged-in session.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.ai_studio_prompts import ITERATION_PROMPTS  # noqa: E402
from src.common import NE, md_table  # noqa: E402
from src.pixel_capi_spec import SIGNALS  # noqa: E402
from tools.guardrails import BANNER_END, BANNER_START  # noqa: E402

APPROVAL = "REQUIRES EXPLICIT HUMAN APPROVAL"


def _box(items: list[str]) -> list[str]:
    return [f"- [ ] {i}" for i in items]


def frozen_banner() -> str:
    return "\n".join([
        BANNER_START,
        f"> **WARNING - FROZEN LIVE CAMPAIGN: `{C.FROZEN_CAMPAIGN_NAME}`**",
        "> It must NOT be edited, paused, resumed or duplicated, and must never be selected as the target of any step "
        "below. Editing it resets Meta's learning phase. All work in this checklist happens in a SEPARATE NEW draft "
        "campaign.",
        BANNER_END,
    ])


def meta_checklist(ctx) -> str:
    camp = json.loads((ctx.out / "campaign_config.json").read_text(encoding="utf-8"))
    name, aset = camp["campaign"]["name"], camp["ad_set"]
    return "\n".join([
        frozen_banner(), "", "# META checklist (human, logged in to business.facebook.com)", "",
        "Nothing below has been done by the build. Work top to bottom; tick only what you actually did.", "",
        "## 1. Business Portfolio and assets",
        *_box(["Business Settings: confirm a Business Portfolio exists for CA-J Enterprises (create only if none exists).",
               "Verify the business email and domain in the portfolio.",
               f"Ad account: confirm or create the CA-J ad account (ID goes in local .env as META_AD_ACCOUNT_ID; {NE}).",
               f"Payment method: {APPROVAL} (spend item). Do not add without a written approval reference.",
               "Settings > Accounts > Pages: connect the CA-J Facebook Page (META_PAGE_ID in .env).",
               "Settings > Accounts > Instagram accounts: connect the CA-J Instagram profile (if one exists).",
               "Confirm Admin access on the portfolio, ad account, Page and Instagram profile."]), "",
        "## 2. Pixel / Dataset (see out/pixel_capi_spec.md)",
        *_box(["Business Settings > Data Sources > Datasets and Pixels > Add > Create: name `<BUSINESS> Pixel` "
               f"({NE}).", "Connect to ad account when prompted: answer Yes. Verify under Connected Assets.",
               "Events Manager > Setup Meta Pixel > Install code manually > copy base code; install via AI Studio "
               "chat (never paste it into the repo).", "Turn on Automatic Advanced Matching > Done."]), "",
        "## 3. Conversions API",
        *_box(["Setup Conversions API > Setup Manually > Conversions API and Meta Pixel.",
               "Events: Contact and Lead (add Schedule only if calendar booking is added).",
               "Each event: identify by Event ID; check signals: " + ", ".join(SIGNALS) + ".",
               f"Generate access token; store ONLY in the GHL CAPI action and local .env as {C.CAPI_ACCESS_TOKEN_ENV}.",
               f"Copy Pixel/Dataset ID into local .env as {C.PIXEL_ID_ENV} / {C.DATASET_ID_ENV}."]), "",
        f"## 4. NEW draft campaign `{name}` (values from out/campaign_config.json)",
        *_box([f"Ads Manager > switch to the CA-J business ad account > Create > Objective Leads. Name `{name}`.",
               "Close Meta AI recommendations. Buying type Auction. Campaign spending limit None.",
               "Campaign budget: OFF (ABO - budget at ad-set level).",
               f"Special Ad Category: {NE} - decide from the actual campaign and current platform prompts.",
               f"Ad set `{aset['name']}`: conversion location Website; Maximize number of leads; dataset = the pixel "
               f"above; conversion event {aset['conversion_event']}; dynamic creative OFF.",
               f"Ad-set daily budget: {aset['daily_budget']} - {APPROVAL}. Leave unset without a written approval reference.",
               f"Schedule {aset['schedule']}; location {aset['locations']['location']} radius {aset['locations']['radius']}; "
               "UNCHECK 'Reach more people likely to respond to your ads'.",
               f"Age {aset['age']}; exclusions none; detailed targeting EMPTY; placements Advantage+ Placements.",
               f"Create {len(camp['ads'])} ads per out/campaign_spec.md: Page, Instagram profile, website URL = verified "
               "landing-page URL (clean, no parameters), display link, creative, up to 5 primary texts, 3-4 headlines, CTA Learn More.",
               "Every creative opens with a pain or an outcome - never the logo. Check every placement preview.",
               "Review Advantage+ creative enhancements manually; uncheck odd variations.",
               "Headlines: no 'Google'/'Facebook' wording (rejection risk)."]), "",
        "## 5. Publish (only after approval)",
        *_box([f"Publish: {APPROVAL} (APPROVAL_LAUNCH and APPROVAL_AD_SPEND, with written references).",
               f"Publish at CAMPAIGN level by ticking the `{name}` campaign checkbox - never from the ad level.",
               "Rollback if needed: toggle off THIS draft campaign at campaign level; set GHL workflows 01 and 03 to Draft."]), "",
    ])


def ghl_checklist(ctx) -> str:
    return "\n".join([
        "# GHL checklist (human, logged in to " + C.GHL_AGENCY_URL + ")", "",
        f"Target location ID: `{C.GHL_LOCATION_ID}` (case-sensitive). Do not use any other location.", "",
        "## 1. Sub-account and AI Studio",
        *_box([f"Confirm the sub-account for location `{C.GHL_LOCATION_ID}` (create only with approval - spend item).",
               "Sub-account > Settings > Labs > search 'AI Studio' > Activate Feature (availability on this account is "
               f"{NE}).", "Confirm AI Studio appears in the left nav."]), "",
        "## 2. Pipeline (out/pipeline_spec.md)",
        *_box([f"Opportunities > Pipelines > Create New Pipeline: `{C.NEW_PIPELINE_NAME}`.",
               "Stages in order: " + ", ".join(C.NEW_PIPELINE_STAGES) + ".",
               f"Do NOT edit `{C.GHL_PIPELINE_NAME}` (`{C.GHL_PIPELINE_ID}`).",
               "Custom field 'Service Needed' (insert via field picker; key " + NE + ")."]), "",
        "## 3. Workflows (build from the specs, keep in Draft until approved)",
        *_box(["Workflow 01 'New Lead Automation' per out/workflows/01-new-lead-automation.md.",
               "Workflow 02 'Hot Lead - Replied' per out/workflows/02-hot-lead-replied.md (Remove from Workflow 01 FIRST).",
               "Workflow 03 'Landing Page CAPI - Lead' per out/workflows/03-landing-page-capi-lead.md.",
               "Insert every {{...}} field with the field picker; send a preview of each message.",
               "Field mapping: confirm the AI Studio form fields map to native contact fields (name, email, phone, service needed).",
               f"A2P 10DLC: confirm status ({NE}); until approved, use the email fallback to {C.OWNER_EMAIL}.",
               f"Publishing workflows: {APPROVAL}."]), "",
    ])


def ai_studio_checklist(ctx) -> str:
    return "\n".join([
        "# AI Studio checklist (human, in GHL > AI Studio)", "",
        "## 1. Generate", *_box(["AI Studio > New Project.",
                                 "Paste the fill script from out/landing/ai_studio_prompt_pack.md above the mega-prompt body "
                                 f"(body is {NE}: never supplied).",
                                 "Generate; review against out/landing/content_spec.md and the static mock out/landing/index.html."]), "",
        "## 2. The seven iteration prompts (5-7 changes per round max)",
        *_box([f"{n}: `{t}`" for n, t in ITERATION_PROMPTS]), "",
        "Skip the review-badge sentence and the before/after images until verified data exists. The logo/colour prompt "
        "applies to the page only; paid ad creatives never lead with the logo.", "",
        "## 3. Connect form to CRM", *_box(["Prompt: 'Connect or integrate the form on the landing page to my CRM' > click Connect > wait.",
                                            "Submit a test (example.com email, 555-01xx phone) and confirm the contact appears with attribution."]), "",
        "## 4. Publish", *_box(["Install pixel via the chat prompt (code from Events Manager).",
                                "Publish > Publish Changes > Add Custom Domain (see DNS-CHECKLIST.md).",
                                f"Publishing the page: {APPROVAL}."]), "",
    ])


def dns_checklist(ctx) -> str:
    return "\n".join([
        "# DNS checklist (human, at the domain registrar)", "",
        f"> **DOMAIN PURCHASE {APPROVAL}.** Buying a domain is a spend item. Do not buy one without a written approval "
        "reference (APPROVAL_DOMAIN_PURCHASE).", "",
        "## CNAME record",
        md_table(["Field", "Value"], [["Type", "CNAME"],
                                       ["Host", f"<subdomain>: `{C.DOMAIN_OFFER_SLUG}`, `{C.DOMAIN_CALL_SLUG}` or `{C.DOMAIN_CONTACT_SLUG}`"],
                                       ["Value", f"{C.CNAME_VALUE} - copy it from AI Studio > Publish > Add Custom Domain "
                                                 "(the source's video showed a value that is unverified)"],
                                       ["Domain", NE]]), "",
        *_box(["Registrar > DNS / Advanced DNS > Add New Record with the values above > Save.",
               "Wait for propagation (source suggests 10-30 minutes; retry Verify every 5 minutes).",
               "AI Studio > Publish > Verify DNS > Publish.",
               "Open the live URL and confirm it loads; record it as landing_page_url in config/build_config.json and rebuild."]), "",
    ])


def human_decisions(ctx) -> str:
    from tools.validate_config import EVIDENCE_GATED_KEYS, ID_KEYS_ENV_ONLY
    env_names = {"facebook_page_id": "META_PAGE_ID", "ad_account_id": "META_AD_ACCOUNT_ID",
                 "pixel_id": C.PIXEL_ID_ENV, "dataset_id": C.DATASET_ID_ENV}
    rows = []
    for key, value in ctx.config.items():
        if value != NE:
            continue
        if key in ID_KEYS_ENV_ONLY:
            action = (f"Record only in a local .env as `{env_names[key]}`; never commit. Config stays NEEDS_EVIDENCE."
                      if key in env_names else "Select it in Ads Manager when building the ad; no ID is stored in the repo.")
        elif key in EVIDENCE_GATED_KEYS:
            action = (f"Keep omitted unless verified evidence exists; to use `{key}`, attach the evidence and remove it "
                      "from EVIDENCE_GATED_KEYS in tools/validate_config.py (human decision).")
        else:
            action = f"Supply a verified value for `{key}` in config/build_config.json and rebuild (or keep omitted)."
        rows.append([f"build_config.{key}", NE, action, C.OWNER_NAME])
    extras = [
        ("constants.CNAME_VALUE", "Read the CNAME target from AI Studio when adding the custom domain"),
        ("constants.DAILY_BUDGET_USD", "Approve an exact daily budget in writing, or leave unset"),
        ("campaign.special_ad_category", "Decide from the actual campaign and current Meta prompts"),
        ("ad_set.schedule", "Choose start date / no end date"),
        ("ad_set.radius", "Choose a radius for the target market"),
        ("ad_set.age", "Choose age setting (source says keep broad)"),
        ("capi.ltv", "Choose a lifetime value figure for the CAPI action, or leave blank"),
        ("capi.pixel_name", "Name the pixel `<BUSINESS> Pixel`"),
        ("capi.business_category", "Pick the Events Manager business category"),
        ("landing.mega_prompt_body", "Obtain the source's mega prompt (Google Doc never supplied)"),
        ("landing.consent_wording", "Legal review of the consent disclosure"),
        ("landing.insurance_license", "Confirm whether any licence/insurance statement applies"),
        ("landing.testimonials", "Supply real testimonials with written permission, or keep omitted"),
        ("ads.[LOCATION] callout", "Supply the target location for the first-line callout"),
        ("ads.creative_source_files", "Produce the images/videos from out/ads/creative_specs.md"),
        ("workflows.merge_token_fields", "Insert every {{...}} field with the GHL field picker and preview"),
        ("ai_studio.availability", "Confirm Settings > Labs > AI Studio exists on this account"),
    ]
    rows += [[k, NE, a, C.OWNER_NAME] for k, a in extras]
    for b in ctx.state.load_blockers():
        rows.append([f"blocker.{b['item']}", b["missing_input"], b["next_action"], C.OWNER_NAME])
    gates = [[s["service"], s["purpose"], s["approval"], s["cost"]] for s in C.SPEND_ITEMS]
    gates += [["Launch / publish the draft campaign", "Start delivery", "approval required", "see ad spend"],
              ["Publish GHL workflows", "Start sending messages", "approval required", "see SMS/email usage"]]
    return "\n".join([
        "# Human decisions queue", "",
        "Every `NEEDS_EVIDENCE` value and every approval gate. Owner for all items: " + C.OWNER_NAME + ".", "",
        "## NEEDS_EVIDENCE values", md_table(["Item", "Current value / missing input", "Next action", "Owner"], rows), "",
        "## Approval gates (spend and launch)", md_table(["Service / action", "Purpose", "Approval", "Cost"], gates), "",
    ])


WORK_ORDERS = [
    ("004-meta-pixel-capi-and-draft-campaign.md", "Meta: pixel, CAPI and NEW draft Leads campaign", "ui-tasks/META-CHECKLIST.md",
     "Create the pixel/dataset and CAPI token, then build the NEW draft campaign from out/campaign_config.json. "
     "Do not publish. Never touch the protected frozen live campaign."),
    ("004-ghl-pipeline-and-workflows.md", "GHL: Meta Ads Leads pipeline and three workflows", "ui-tasks/GHL-CHECKLIST.md",
     "Create the pipeline and build workflows 01-03 in Draft from the specs."),
    ("004-ghl-ai-studio-landing-page.md", "GHL AI Studio: generate and iterate the landing page", "ui-tasks/AI-STUDIO-CHECKLIST.md",
     "Generate the page from the prompt pack, run the iteration prompts, connect the form to the CRM."),
    ("004-dns-subdomain.md", "DNS: connect the landing-page subdomain", "ui-tasks/DNS-CHECKLIST.md",
     "Add the CNAME record and verify. Domain purchase requires explicit human approval."),
]


def work_order(title: str, checklist: str, summary: str) -> str:
    return "\n".join([
        f"# UI work order: {title}", "",
        "- Source build: `build/04-fb-ai-studio/` (SPEC-04)",
        f"- Owner: {C.OWNER_NAME} ({C.OWNER_EMAIL})",
        "- Status: Not started (human, browser and login required)",
        f"- Exact steps: `build/04-fb-ai-studio/{checklist}`", "",
        "## What to do", summary, "",
        "## Gates",
        f"- Any spend (ad budget, domain, payment method, tools): {APPROVAL}.",
        f"- Location ID `{C.GHL_LOCATION_ID}` only (case-sensitive).",
        "- Ads lead with a pain or an outcome, never the logo. No price in any message; pricing questions go to "
        f"{C.BOOKING_URL}.", "",
    ])


def build(ctx) -> list[Path]:
    paths = [
        ctx.write_asset("ui-tasks/META-CHECKLIST.md", meta_checklist(ctx), "ui_meta_checklist", "src/ui_checklists.py",
                        status="Not started"),
        ctx.write_asset("ui-tasks/GHL-CHECKLIST.md", ghl_checklist(ctx), "ui_ghl_checklist", "src/ui_checklists.py",
                        status="Not started"),
        ctx.write_asset("ui-tasks/AI-STUDIO-CHECKLIST.md", ai_studio_checklist(ctx), "ui_ai_studio_checklist",
                        "src/ui_checklists.py", status="Not started"),
        ctx.write_asset("ui-tasks/DNS-CHECKLIST.md", dns_checklist(ctx), "ui_dns_checklist", "src/ui_checklists.py",
                        status="Not started"),
        ctx.write_asset("ui-tasks/HUMAN-DECISIONS.md", human_decisions(ctx), "ui_human_decisions", "src/ui_checklists.py",
                        status="Not started"),
    ]
    for fname, title, checklist, summary in WORK_ORDERS:
        paths.append(ctx.write_asset(fname, work_order(title, checklist, summary), f"work_order_{fname[4:-3]}",
                                     "src/ui_checklists.py", status="Not started", base=ctx.work_orders_dir))
    return paths

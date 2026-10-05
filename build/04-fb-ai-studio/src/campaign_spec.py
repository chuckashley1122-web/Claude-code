"""Campaign spec -> out/campaign_spec.md + out/campaign_config.json (SPEC-04 step 20).

A NEW, separate DRAFT Leads campaign with every field pre-filled. Budget sits at
the ad-set level (ABO) and stays NEEDS_EVIDENCE; campaign-level budget is OFF.
The draft is also stored through LocalDraftGateway (offline) so the rollback
rehearsal in T14 has a real prior config to restore. Nothing is published.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.ad_angles import ANGLES  # noqa: E402
from src.ad_copy import COPY, CTA  # noqa: E402
from src.common import DRAFT_NOTICE, NE, cfg_value, md_table  # noqa: E402
from src.creative_specs import STARTING_SET, creative_records  # noqa: E402
from tools.guardrails import assert_campaign_name_is_draft, assert_not_frozen_campaign  # noqa: E402
from tools.meta_gateway import LocalDraftGateway  # noqa: E402

FROZEN_GUARD_TEXT = ("This is a NEW, separate draft. It never edits, pauses, resumes or duplicates the protected live "
                     "campaign (held only in config/constants.py as FROZEN_CAMPAIGN_NAME); editing that campaign "
                     "resets Meta's learning phase.")


def campaign_config(ctx) -> dict:
    name = ctx.draft_campaign_name()
    assert_campaign_name_is_draft(name)
    angle_names = {a["id"]: a["name"] for a in ANGLES}
    recs = {r["asset_id"]: r for r in creative_records()}
    ads = []
    for i, asset_id in enumerate(STARTING_SET, 1):
        r = recs[asset_id]
        ads.append({
            "name": f"{'Video' if r['format'] == 'video' else 'Image'} {i} - {angle_names[r['angle']]}",
            "facebook_page": cfg_value(ctx, "facebook_page_id"),
            "instagram_profile": cfg_value(ctx, "instagram_profile_id"),
            "website_url": cfg_value(ctx, "landing_page_url"),
            "display_link": cfg_value(ctx, "landing_page_url"),
            "creative_asset": asset_id,
            "creative_source_file": r["source_asset"],
            "primary_texts_ref": f"out/ads/copy/{r['angle']}.md",
            "primary_text_count": len(COPY[r["angle"]]["primary_texts"]),
            "headlines": COPY[r["angle"]]["headlines"],
            "cta": CTA,
            "advantage_plus_creative_enhancements": "review manually; uncheck any odd variation",
        })
    return {
        "status": "DRAFT_UNPUBLISHED",
        "draft": True,
        "published_by_build": False,
        "separate_new_draft": True,
        "frozen_campaign_guard": FROZEN_GUARD_TEXT,
        "campaign": {
            "name": name, "objective": "Leads", "buying_type": "Auction", "spending_limit": "None",
            "campaign_budget": "OFF", "budget_level": "ad_set (ABO)", "special_ad_category": NE,
            "meta_ai_recommendations": "close / do not apply",
        },
        "ad_set": {
            "name": "Broad Audience - DRAFT",
            "conversion_location": "Website", "conversion_type": "Maximize number of leads",
            "dataset_pixel": f"env:{C.PIXEL_ID_ENV}", "conversion_event": C.CAPI_EVENT_TO_SEND,
            "dynamic_creative": "OFF",
            "daily_budget": C.DAILY_BUDGET_USD,
            "daily_budget_requires": "explicit written human approval (APPROVAL_AD_SPEND) with an approval reference",
            "daily_budget_source_guidance_unverified": "Source instructor guidance only (suggested a daily figure in "
                                                       "the 50-100 range); not authority, not a CA-J budget.",
            "schedule": NE,
            "locations": {"location": cfg_value(ctx, "primary_location"), "radius": NE,
                          "uncheck_reach_more_people_likely_to_respond": True},
            "age": NE, "exclusions": [], "detailed_targeting": [],
            "placements": "Advantage+ Placements",
        },
        "ads": ads,
        "budget_exposure_usd": 0,
        "approval_ref": "",
        "publish_rule": "Publish only at CAMPAIGN level, by a human, after APPROVAL_LAUNCH and APPROVAL_AD_SPEND. "
                        "This build does not publish.",
        "rollback": {
            "pause": "Ads Manager > select THIS draft campaign's checkbox > toggle off (campaign level).",
            "stop_workflows": "GHL > Workflows > set 'New Lead Automation' and 'Landing Page CAPI - Lead' to Draft.",
            "recover_config": "Restore out/campaign_config.json from git / LocalDraftGateway history and rebuild.",
            "never": "Never pause or edit the protected live campaign as part of a rollback.",
        },
    }


def render_md(cfg: dict) -> str:
    camp, aset = cfg["campaign"], cfg["ad_set"]
    ad_rows = [[a["name"], a["creative_asset"], a["website_url"], a["primary_texts_ref"], " / ".join(a["headlines"]), a["cta"]]
               for a in cfg["ads"]]
    return "\n".join([
        f"# Campaign spec: {camp['name']}", "", DRAFT_NOTICE, "",
        f"> **NEW DRAFT - never published by this build.** {FROZEN_GUARD_TEXT}", "",
        "## Campaign level",
        md_table(["Field", "Value"], [["Name", camp["name"]], ["Objective", camp["objective"]],
                                       ["Buying type", camp["buying_type"]], ["Campaign spending limit", camp["spending_limit"]],
                                       ["Campaign budget (CBO)", "**OFF** - budget is set at the ad-set level (ABO)"],
                                       ["Special Ad Category", camp["special_ad_category"]],
                                       ["Meta AI recommendations", camp["meta_ai_recommendations"]]]), "",
        "## Ad-set level (budget lives here)",
        md_table(["Field", "Value"], [
            ["Name", aset["name"]], ["Conversion location", aset["conversion_location"]],
            ["Conversion type", aset["conversion_type"]], ["Dataset / Pixel", aset["dataset_pixel"]],
            ["Conversion event", aset["conversion_event"] + " (must match CAPI)"],
            ["Dynamic creative", aset["dynamic_creative"]],
            ["Daily budget", f"{aset['daily_budget']} - REQUIRES EXPLICIT HUMAN APPROVAL"],
            ["Source budget guidance", aset["daily_budget_source_guidance_unverified"]],
            ["Schedule", aset["schedule"]],
            ["Location", f"{aset['locations']['location']} (radius {aset['locations']['radius']}); UNCHECK 'Reach more people likely to respond'"],
            ["Age", aset["age"]], ["Detailed targeting", "EMPTY (broad)"], ["Placements", aset["placements"]]]), "",
        f"## Ads ({len(cfg['ads'])}, from the starting creative set)",
        md_table(["Ad", "Creative", "Website URL", "Primary texts", "Headlines", "CTA"], ad_rows), "",
        "Page, Instagram profile, website URL and display link are `NEEDS_EVIDENCE` until supplied. Advantage+ creative "
        "enhancements are reviewed manually; never follow every Meta recommendation blindly.", "",
        "## Budget exposure", "`0` until a human approves an exact amount in writing.", "",
        "## Publish rule", cfg["publish_rule"], "",
        "## Rollback", *[f"- **{k}**: {v}" for k, v in cfg["rollback"].items()], "",
    ])


def build(ctx) -> list[Path]:
    cfg = campaign_config(ctx)
    text = render_md(cfg)
    assert_not_frozen_campaign(text)
    assert_not_frozen_campaign(json.dumps(cfg))
    LocalDraftGateway(ctx.out / "drafts").create_draft_campaign(cfg)
    ctx.state.record_blocker("daily_budget", "Exact daily budget + written approval reference",
                             "Ad-set budget; campaign cannot deliver", "Chuck approves an amount in writing or leaves it unset")
    return [ctx.write_asset("out/campaign_spec.md", text, "campaign_spec", "src/campaign_spec.py"),
            ctx.write_json("out/campaign_config.json", cfg, "campaign_config", "src/campaign_spec.py")]

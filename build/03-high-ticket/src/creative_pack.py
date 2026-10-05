"""Five image ad concepts (playbook steps 19-20) -> out/creatives/A01..A05.{md,json}

No image files are produced: this executor has no image model. Each record
carries the exact prompt and specs for a human or an approved image tool.
"""
from __future__ import annotations

from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src.common import OFFER_VERSION, niche_label  # noqa: E402
from tools import guardrails as G  # noqa: E402

AD_HEADLINE = "Review your HVAC growth plan"
CTA = "Learn More"
VERSION = "v1-draft"

CONCEPT_PROMPT = (
    "Act as a direct response creative planner for [BUSINESS]. Target [BUYER] in [MARKET]. Our exact offer is "
    "[APPROVED OFFER]. Create five simple image ad concepts covering lead quality, shared leads, a clear service offer, "
    "referral dependence and past agency disappointment. Return exact on-image words, visual direction, primary text, "
    "headline and CTA for each. Use only these verified proof points: [PROOF OR NONE]. Do not invent results, scarcity, "
    "guarantees or exclusivity. Keep every claim consistent with the offer."
)

CLOSE = ("CA-J Enterprises builds and manages the agreed advertising and follow-up system, so your team can focus on "
         "calls and estimates. Book a strategy session to review your market, capacity and budget.")

ANGLES = [
    ("A01", "lead quality", "More useful HVAC inquiries start with a better system",
     "Simple business-focused layout; no fake lead dashboard",
     "Are your inquiries turning into estimates your team can actually run?"),
    ("A02", "shared leads / ownership", "Build a lead system for your HVAC business",
     "One HVAC business and one clear inquiry path",
     "Tired of chasing leads that were sent to several companies? Build an inquiry and follow-up path around your own business."),
    ("A03", "clear service offer", "HVAC lead generation and follow-up handled for you",
     "Large black type on white; small brand and CTA",
     "Want a clear, managed process for bringing in inquiries and following up?"),
    ("A04", "referral dependence", "Ready to grow beyond referrals",
     "Simple calendar motif without invented booking totals",
     "Referrals are valuable, but they are hard to plan around."),
    ("A05", "past agency disappointment", "Know what your marketing is doing",
     "Real reporting concept; any chart is an empty layout labeled 'Sample layout - not real data'",
     "Been burned by an agency that could not explain what you were paying for? Get reporting on spend, inquiries and booked estimates you can review."),
]


def fill_prompt(config: dict) -> str:
    area = config.get("service_area", C.NEEDS_EVIDENCE)
    proof = config.get("proof_assets", C.NEEDS_EVIDENCE)
    return (CONCEPT_PROMPT.replace("[BUSINESS]", C.BRAND_NAME)
            .replace("[BUYER]", f"{niche_label(config)} owners and marketing decision makers")
            .replace("[MARKET]", area if area != C.NEEDS_EVIDENCE else f"[MARKET: {C.NEEDS_EVIDENCE}]")
            .replace("[APPROVED OFFER]", f"offer version {OFFER_VERSION} (managed HVAC lead generation and follow-up)")
            .replace("[PROOF OR NONE]", "NONE" if proof in (C.NEEDS_EVIDENCE, [], "", None) else str(proof)))


def primary_text(hook: str, config: dict) -> str:
    area = config.get("service_area", C.NEEDS_EVIDENCE)
    lead = f"HVAC owners in {area}: " if area != C.NEEDS_EVIDENCE else "HVAC owners: "
    return lead + hook[0].lower() + hook[1:] + " " + CLOSE


def record(ad_id, angle, on_image, visual_note, hook, config) -> dict:
    vd = [
        {"order": 1, "element": "outcome_headline", "text": on_image, "style": "large black type on white"},
        {"order": 2, "element": "offer_line", "text": "Managed lead generation and follow-up for HVAC businesses"},
        {"order": 3, "element": "supporting_visual", "text": visual_note},
        {"order": 4, "element": "cta", "text": CTA},
        {"order": 5, "element": "logo", "placement": "footer", "size": "small", "text": "CA-J Enterprises (small footer disclaimer only)"},
    ]
    rec = {
        "ad_id": ad_id, "angle": angle, "on_image_words": on_image, "visual_direction": vd,
        "primary_text": primary_text(hook, config), "headline": AD_HEADLINE, "cta": CTA,
        "offer_reference": OFFER_VERSION, "version": VERSION, "proof_points": "NONE",
        "formats": [{"name": "feed", "size": "1080x1350"}, {"name": "alternate_crop", "size": "1080x1080", "note": "confirm in placement preview"}],
        "style": "black text on white",
        "constraints": ["original or licensed imagery only", "competitor ads for research only, never copied",
                        "outcome or offer leads; logo only as a small footer disclaimer", "no fake dashboards",
                        "no invented booking totals", "no unverified guarantees", "no scarcity or exclusivity claims"],
        "image_prompt": (f"Create a 1080x1350 static ad, white background, black text. Top and largest: \"{on_image}\". "
                         f"Below it: \"Managed lead generation and follow-up for HVAC businesses\". Visual: {visual_note}. "
                         f"Button-style text \"{CTA}\". Bottom footer, small: \"CA-J Enterprises\". No numbers, no dashboards, "
                         "no people's faces unless licensed. Then produce a 1080x1080 alternate crop with the same order."),
        "image_status": "NOT GENERATED - human/image tool task (see ui-tasks/META-BUILD-CHECKLIST.md)",
        "status": "Draft",
    }
    return rec


def check(rec: dict) -> dict:
    G.assert_logo_not_first(rec)
    for key in ("on_image_words", "primary_text", "headline", "cta"):
        G.assert_prospect_copy(rec[key])
    return rec


def concepts(config: dict) -> list[dict]:
    return [check(record(*a, config=config)) for a in ANGLES]


def render_md(rec: dict, prompt: str) -> str:
    vd = "\n".join(f"{e['order']}. {e['element']}: {e['text']}" + (f" ({e['placement']}, {e['size']})" if e["element"] == "logo" else "")
                   for e in rec["visual_direction"])
    return "\n".join([
        f"# {rec['ad_id']} - {rec['angle']}", "",
        f"Status: Draft. Version `{rec['version']}`. Offer reference `{rec['offer_reference']}`. Proof points: {rec['proof_points']}.", "",
        f"**On-image words:** {rec['on_image_words']}", "", "**Visual direction (top to bottom):**", "", vd, "",
        f"**Primary text:** {rec['primary_text']}", "", f"**Headline:** {rec['headline']}", "", f"**CTA:** {rec['cta']}", "",
        "**Formats:** 1080x1350 feed + 1080x1080 alternate crop. Black text on white.", "",
        "**Image prompt (for a human / approved image tool):**", "", "> " + rec["image_prompt"], "",
        f"Image status: {rec['image_status']}", "", "**Concept prompt used:**", "", "> " + prompt, "",
    ])


def build(state) -> list[Path]:
    prompt = fill_prompt(state.config)
    paths = []
    for rec in concepts(state.config):
        paths.append(state.write_json(f"out/creatives/{rec['ad_id']}.json", rec, f"CREATIVE-{rec['ad_id']}-JSON", source="src/creative_pack.py"))
        paths.append(state.write(f"out/creatives/{rec['ad_id']}.md", render_md(rec, prompt), f"CREATIVE-{rec['ad_id']}-MD", source="src/creative_pack.py"))
    state.needs("ad images (5 concepts x 2 crops)", "out/creatives/", "Generate with an approved image tool from each image_prompt; proof spelling, margins and crops",
                missing_input="No image model in this executor; image tool choice and approval")
    state.needs("proof_assets", "out/creatives/", "Supply verified proof points or keep NONE")
    return paths


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

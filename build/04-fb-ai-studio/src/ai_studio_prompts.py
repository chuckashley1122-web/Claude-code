"""AI Studio prompt pack -> out/landing/ai_studio_prompt_pack.md (SPEC-04 step 15).

(a) placeholder-fill script for the source's mega prompt. The mega-prompt body
itself was never supplied (a Google Doc) and is NOT fetched or reproduced.
(b) the seven iteration prompts, transcribed verbatim from the source.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.common import DRAFT_NOTICE, NE, cfg_value, md_table  # noqa: E402
from tools.guardrails import assert_no_price_in_message, assert_no_unverified_claims  # noqa: E402

OMIT = "OMIT - do not mention on the page"
# (placeholder label, build_config key or None, fixed value, omit_if_unknown)
PLACEHOLDERS = [
    ("Business Name", "business_name", None, False),
    ("Primary Location", "primary_location", None, False),
    ("Service Areas", "service_areas", None, False),
    ("Primary Service", "primary_service", None, False),
    ("Additional Services", "additional_services", None, False),
    ("Main Offer", "main_offer", None, False),
    ("Offer Expiration", "offer_expiration", None, True),
    ("Primary CTA", "primary_cta", None, False),
    ("Phone", "phone", None, False),
    ("Avg Response Time", "avg_response_time", None, True),
    ("Est Service Time", "est_service_time", None, True),
    ("Years in Business", "years_in_business", None, True),
    ("Customers Served", "customers_served", None, True),
    ("Google Review Rating", "review_rating", None, True),
    ("Number of Reviews", "review_count", None, True),
    ("Guarantee", "guarantee", None, True),
    ("Insurance/License", None, NE, True),
    ("USP", "usp", None, False),
    ("Main Pain Points", "main_pain_points", None, False),
    ("Desired Outcomes", "desired_outcomes", None, False),
    ("Testimonials", None, NE, True),
    ("Team/Owner", None, f"{C.OWNER_NAME} (owner photo {NE})", False),
    ("Hero Image", "hero_image_path", None, False),
    ("Logo", "logo_path", None, False),
    ("Brand Colors/Fonts", "brand_colors", None, False),
]

# Source STEP 2.3 changes 1-6 (verbatim) + STEP 2.4 connect-form prompt = seven iteration prompts.
ITERATION_PROMPTS = [
    ("Change 1 - logo/colors", "Update the logo and follow the colors from the logo to use in the page"),
    ("Change 2 - images after hero", "Update these images in the section after the hero section on the landing page"),
    ("Change 3 - hero background",
     "Use the attached image in the background of the hero section. Maintain an overlay that has the left and right "
     "elements of the hero section stand out. At same time we should be able to see a glimpse of background image."),
    ("Change 4 - multi-change",
     "Remove the image from over the form on the right side of hero. Make logo on header 1.8 times bigger. Add 2-3 "
     "navigation menu items on header right side of logo to take us to different sections of page. On left side of "
     "phone call option in header add a Google review badge with number of reviews and average rating."),
    ("Change 5 - header", "Make header wider and change background to light background"),
    ("Change 6 - mobile fix", "Remove phone number from header, centralize logo on mobile, fix hero button layout"),
    ("Change 7 - connect form to CRM", "Connect or integrate the form on the landing page to my CRM"),
]

GUARD_INSTRUCTIONS = [
    "Do not invent reviews, ratings, testimonials, client counts, years in business or results.",
    "Do not show any price, fee or money-off offer anywhere on the page.",
    f"Every button scrolls to the form. The thank-you page links to {C.BOOKING_URL}.",
    "Say 'website', not 'landing page', in any visible copy.",
]


def resolve(ctx) -> list[dict]:
    rows = []
    for label, key, fixed, omit_if_unknown in PLACEHOLDERS:
        value = fixed if key is None else cfg_value(ctx, key)
        unknown = NE in str(value)
        paste = OMIT if (unknown and omit_if_unknown) else value
        rows.append({"placeholder": label, "value": value, "paste_as": paste,
                     "status": NE if unknown else "known", "config_key": key or "-"})
    return rows


def fill_script(rows: list[dict]) -> str:
    lines = [f"{r['placeholder']}: {r['paste_as']}" for r in rows]
    lines += ["", "Rules for this page:"] + [f"- {g}" for g in GUARD_INSTRUCTIONS]
    text = "\n".join(lines)
    assert_no_price_in_message(text)
    assert_no_unverified_claims(text)
    return text


def render(ctx) -> str:
    rows = resolve(ctx)
    return "\n".join([
        "# AI Studio prompt pack", "", DRAFT_NOTICE, "",
        "## Part A - placeholder-fill script",
        "The source's AI Studio **mega prompt** lives in a Google Doc that was **never supplied**. Its body is "
        f"`{NE}`. It is not fetched and not reproduced here. When a human obtains it, paste the block below over the "
        "placeholder section at its top, then paste the whole prompt into GHL > AI Studio > New Project.", "",
        md_table(["Placeholder", "CA-J value", "Paste as", "Status", "build_config key"],
                 [[r["placeholder"], r["value"], r["paste_as"], r["status"], r["config_key"]] for r in rows]), "",
        "Offer expiration, review rating, review count, customers served and years in business default to **omitted**, "
        "never invented.", "",
        "```text", fill_script(rows), "",
        f"[MEGA PROMPT BODY: {NE} - never supplied; do not reconstruct]", "```", "",
        "## Part B - the seven iteration prompts (verbatim from the source)",
        "Run 5-7 changes at a time at most. Check desktop and mobile preview after each round; every button must "
        "scroll to the form.", "",
        *[f"{i}. **{name}**\n\n   ```text\n   {text}\n   ```\n" for i, (name, text) in enumerate(ITERATION_PROMPTS, 1)],
        "### Notes on these prompts",
        "- Change 1 (logo/colors): applies to the landing page only. It must **never** result in the CA-J logo being "
        "the first thing in any paid ad creative; ads lead with a pain or an outcome and carry the logo as a small "
        "footer mark only.",
        "- Change 2 needs real before/after images (`before_after_images` = "
        f"`{NE}`). Skip it until real images exist.",
        "- Change 4 adds a review badge. Leave that sentence out unless the review count and rating are verified "
        f"(both are `{NE}`).",
        "- Pixel install prompt (`Install this pixel code on this project: [PASTE CODE]`) is in `out/pixel_capi_spec.md`; "
        "the code is pasted by the human from Events Manager, never stored in this repo.", "",
    ])


def build(ctx) -> Path:
    ctx.state.record_blocker("mega_prompt_body", "The source's AI Studio mega prompt (Google Doc, never supplied)",
                             "AI Studio page generation", "Chuck obtains the doc text and pastes it with the fill script")
    return ctx.write_asset("out/landing/ai_studio_prompt_pack.md", render(ctx), "ai_studio_prompt_pack",
                           "src/ai_studio_prompts.py")

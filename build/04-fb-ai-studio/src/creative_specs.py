"""Creative specs -> out/ads/creative_specs.md (SPEC-04 step 19).

Briefs only: image/video generation is not possible here and no asset file is
fabricated (source_asset = NEEDS_EVIDENCE). Every record opens with a pain or
an outcome and passes assert_logo_not_first().
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.common import DRAFT_NOTICE, NE, md_table  # noqa: E402
from tools.guardrails import assert_ad_copy_clean, assert_logo_not_first, assert_no_consumer_brand  # noqa: E402

SPEC_BLOCK = "creative-records"
LOGO_PLACEMENT = "small footer disclaimer only (bottom edge, never the opening frame)"
SQUARE = f"{C.REQUIRED_IMAGE_DIMENSIONS[0]}x{C.REQUIRED_IMAGE_DIMENSIONS[1]}"
ALT = f"{C.ALTERNATE_IMAGE_DIMENSIONS[0]}x{C.ALTERNATE_IMAGE_DIMENSIONS[1]}"
CROP_NOTES = ("Square master avoids cropping across Feed, Stories, Reels and Search. Keep text and faces in the "
              "centre; keep the top and bottom edges clear of text where Stories/Reels UI overlays. Check every "
              "placement preview before publish.")

_BRIEFS = [
    ("A01", "video", "pain", "A phone buzzing on a truck seat with a missed-call notification while a tech works on a condenser",
     ["Missed the call?", "Reply before they call someone else", "Fast follow-up for HVAC companies"],
     "Phone-shot, natural light. Open on the buzzing phone (pain), cut to the tech mid-job, end on a calm owner reading a reply."),
    ("A01", "image", "pain", "A stack of unanswered callback notes next to a ringing office phone",
     ["Calls going to voicemail?", "Reply to every inquiry in minutes"],
     "Simple, real office desk. No stock smiles. Callback notes in focus."),
    ("A02", "video", "outcome", "An owner opening a calendar view filled with booked appointments",
     ["Booked appointments, not callbacks", "Free strategy session"],
     "Screen-and-face shot: owner scrolls a full calendar, small nod, then back to the job site."),
    ("A02", "image", "outcome", "A tidy weekly calendar with appointments filled in, held by an HVAC owner",
     ["Your week, already booked", "Free strategy session"],
     "Clean, bright, real person in work clothes. Calendar readable at thumbnail size."),
    ("A03", "video", "pain", "An owner sighing at an inbox of unreachable leads from a past campaign",
     ["Tried marketing that didn't stick?", "We fix the follow-up first"],
     "Talking-head style, plain background. Lead with the frustration, then the calm explanation."),
    ("A03", "image", "pain", "A cold, unanswered lead list on a clipboard on a service van dashboard",
     ["Leads nobody could reach?", "Fix the follow-up first"],
     "Dashboard close-up, natural light, no heavy graphics."),
    ("A04", "video", "outcome", "An owner on a short video call, writing a simple plan on a notepad",
     ["Leave with a clear plan", "Free, no-obligation strategy session"],
     "Owner-to-camera, under 30 seconds. Outcome first, the free session second, booking prompt last."),
    ("A04", "image", "outcome", "A notepad titled 'Faster follow-up plan' next to a phone showing a reply notification",
     ["A plan for faster follow-up", "Free strategy session, no obligation"],
     "Flat-lay, real objects, readable at thumbnail size."),
]

STARTING_SET = ["A01-V1", "A02-V1", "A03-V1", "A01-I1", "A02-I1", "A04-I1"]
BACKUPS = ["A04-V1", "A03-I1"]
LOW_BUDGET_FALLBACK = ["A01-V1", "A02-V1", "A01-I1", "A02-I1", "A04-I1"]


def creative_records() -> list[dict]:
    recs = []
    for angle, fmt, lead, desc, on_image, shot in _BRIEFS:
        asset_id = f"{angle}-{'V' if fmt == 'video' else 'I'}1"
        rec = {
            "asset_id": asset_id, "angle": angle, "format": fmt,
            "dimensions": SQUARE if fmt == "video" else f"{SQUARE} (required); {ALT} alternate where a 4:5 Feed crop is required",
            "max_duration": (f"{C.MAX_VIDEO_SECONDS}s (absolute max {C.ABSOLUTE_MAX_VIDEO_SECONDS}s)" if fmt == "video" else "n/a"),
            "opening_element": {"type": lead, "description": desc},
            "logo_placement": LOGO_PLACEMENT,
            "shot_direction": shot,
            "on_image_text": on_image,
            "placement_crop_notes": CROP_NOTES,
            "source_asset": NE,
            "role": "starting set" if asset_id in STARTING_SET else "backup",
        }
        recs.append(rec)
    return recs


def check(records: list[dict]) -> None:
    for r in records:
        assert_logo_not_first(r)
        assert_ad_copy_clean(" ".join(r["on_image_text"]))
        assert_no_consumer_brand(json.dumps(r))


def render(records: list[dict]) -> str:
    rows = [[r["asset_id"], r["angle"], r["format"], r["dimensions"], r["max_duration"],
             f"{r['opening_element']['type']}: {r['opening_element']['description']}", r["logo_placement"],
             " / ".join(r["on_image_text"]), r["shot_direction"], r["source_asset"], r["role"]] for r in records]
    vids = sum(1 for r in records if r["format"] == "video")
    return "\n".join([
        "# Creative specs (briefs for a human or an image/video tool)", "", DRAFT_NOTICE, "",
        "**No image or video was generated and no asset file exists.** Each row is a brief. `source_asset` stays "
        f"`{NE}` until a human produces the file.", "",
        f"- Mix: {vids} videos + {len(records) - vids} images = {len(records)} total (source: 3-4 videos + 3-4 images).",
        f"- Starting set (6 ads): {', '.join(STARTING_SET)}. Backups: {', '.join(BACKUPS)}.",
        f"- Low-budget fallback (2 videos + 3 images): {', '.join(LOW_BUDGET_FALLBACK)}.",
        f"- Images {SQUARE} square (required); videos {C.MAX_VIDEO_SECONDS}s max, absolute max {C.ABSOLUTE_MAX_VIDEO_SECONDS}s.",
        "- **Opening element is always a pain or an outcome. The CA-J logo is never first;** it is a small footer mark only.",
        f"- Placement crop notes: {CROP_NOTES}", "",
        md_table(["asset_id", "angle", "format", "dimensions", "max_duration", "opening_element", "logo_placement",
                  "on_image_text", "shot_direction", "source_asset", "role"], rows), "",
        f"```json {SPEC_BLOCK}", json.dumps(records, indent=2), "```", "",
    ])


def build(ctx) -> Path:
    recs = creative_records()
    check(recs)
    ctx.state.record_blocker("creative_assets", "Real images/videos produced from the briefs",
                             "Ads in the draft campaign", "Human shoots on a phone or uses an approved tool (spend item)")
    return ctx.write_asset("out/ads/creative_specs.md", render(recs), "creative_specs", "src/creative_specs.py")

"""Ad angles -> out/ads/angles.md + angles.json (SPEC-04 step 17).

Four angles from the source (pain / desired outcome / objection / offer),
re-expressed for CA-J's HVAC-owner ICP. Every angle LEADS with a pain or an
outcome - never the logo, never a price. The offer angle opens with the outcome
and then presents the free strategy session.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.common import DRAFT_NOTICE, md_table  # noqa: E402
from tools.guardrails import assert_ad_copy_clean, assert_no_consumer_brand  # noqa: E402

LOCATION_TOKEN = "[LOCATION]"   # NEEDS_EVIDENCE: primary_location / service area not yet supplied

ANGLES = [
    {"id": "A01", "name": "Pain Point", "lead": "pain",
     "hook": "Calls hit voicemail while the crew is on a job; inquiries sit until tomorrow.",
     "message": "HVAC owners feel understood: missed and slow-answered inquiries are a fixable follow-up problem.",
     "source_framing": "Source: 'Are you suffering from clutter?' (junk removal) - re-expressed for HVAC owners."},
    {"id": "A02", "name": "Desired Outcome", "lead": "outcome",
     "hook": "A calendar with booked appointments instead of a list of callbacks.",
     "message": "Show the result the owner wants: fast replies and booked appointments without chasing.",
     "source_framing": "Source: 'Do you want to reclaim your space?' - re-expressed as the owner's ideal week."},
    {"id": "A03", "name": "Objection", "lead": "pain",
     "hook": "Tried marketing before, got leads nobody could reach; no time to manage it.",
     "message": "Name the objection, then answer it: follow-up is set up first and built with the owner.",
     "source_framing": "Source: 'No time? Tried before and failed? Is it expensive?' - the cost objection is answered "
                       "only by inviting them to the call (no price before the call)."},
    {"id": "A04", "name": "Offer", "lead": "outcome",
     "hook": "Leave with a clear plan for turning more calls into booked appointments.",
     "message": "Open with the outcome, then the offer: a free, no-obligation strategy session.",
     "source_framing": "Source led with a dollar discount. Overridden: no price or discount for a CA-J service; "
                       "the offer is the free strategy session."},
]

INDUSTRY_CLAIM = ("'Creatives ARE the targeting' (attributed in the source to Meta's 'Andromeda' update) is an "
                  "industry claim repeated from the video, not a CA-J-verified result.")


def angles_doc() -> dict:
    doc = {"status": "Draft", "icp": "HVAC company owners (BUILD_MODE=CAJ_HVAC)",
           "location_callout_token": LOCATION_TOKEN, "location_status": C.NEEDS_EVIDENCE,
           "booking_url": C.BOOKING_URL, "industry_claim_unverified": INDUSTRY_CLAIM, "angles": ANGLES}
    for a in ANGLES:
        assert a["lead"] in C.ALLOWED_OPENING_ELEMENT_TYPES
        assert_ad_copy_clean(a["hook"])
        assert_no_consumer_brand(json.dumps(a))
    return doc


def render_md(doc: dict) -> str:
    return "\n".join([
        "# Ad angles", "", DRAFT_NOTICE, "",
        f"ICP: {doc['icp']}. Every angle leads with a **pain or an outcome**; the CA-J logo is never first and no "
        "price appears before the call.", "",
        md_table(["ID", "Angle", "Leads with", "Hook", "Main message", "Source framing"],
                 [[a["id"], a["name"], a["lead"], a["hook"], a["message"], a["source_framing"]] for a in doc["angles"]]), "",
        "## Unverified framing", f"- {INDUSTRY_CLAIM}",
        "- 'Longest-running ads in the Ad Library are winners' is a heuristic from the source, not verified.",
        f"- Location callout uses `{LOCATION_TOKEN}` until the target location is supplied (`{C.NEEDS_EVIDENCE}`).", "",
    ])


def build(ctx) -> list[Path]:
    doc = angles_doc()
    return [ctx.write_asset("out/ads/angles.md", render_md(doc), "ads_angles_md", "src/ad_angles.py"),
            ctx.write_json("out/ads/angles.json", doc, "ads_angles_json", "src/ad_angles.py")]

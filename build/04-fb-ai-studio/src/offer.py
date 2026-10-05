"""Offer definition -> out/offer.md (SPEC-04 step 7)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.common import DRAFT_NOTICE, NE, md_table  # noqa: E402
from tools.guardrails import assert_meeting_first, assert_no_consumer_brand  # noqa: E402

FORBIDDEN_FIRST_TOUCH = ["Contact us", "Learn more (as the offer itself)", "Submit card details"]

# The tutorial's example offers (junk-removal / home-service business). Not CA-J offers.
TUTORIAL_EXAMPLE_OFFERS = [
    "$100 discount on first service",
    "$50 discount on first service",
    "$49 drain cleaning or money-back guarantee",
    "50% off first visit, tied to booking this week",
    "Free class / free trial",
    "Free consultation (no obligation)",
    "Free assessment / free quote",
]

OFFER_BRAINSTORM_PROMPT = (
    "I have a [business type] in [location]. I want to run Facebook ads. What are 5 proven low-friction offers "
    "that have historically gotten good results? Must be specific, low friction, easy yes, no big commitment on "
    "first touch."
)


def caj_offer() -> dict:
    offer = {
        "name": "Free strategy session",
        "statement": "A free, no-obligation strategy session for HVAC company owners, booked online.",
        "booking_url": C.BOOKING_URL,
        "first_touch_ask": "Pick a time for a strategy session",
        "price_before_call": "none - no price is stated anywhere before the call",
    }
    assert_meeting_first(" ".join(str(v) for v in offer.values()))
    return offer


def render(ctx) -> str:
    offer = caj_offer()
    parts = [
        "# Offer definition (CA-J agency acquisition, BUILD_MODE=CAJ_HVAC)", "", DRAFT_NOTICE, "",
        "## The rule carried forward from the source",
        "Facebook is interruptive, not intent-based. The offer must be **specific, low-friction and an easy yes**.",
        "Do not use any of these as the first touch: " + ", ".join(f"`{x}`" for x in FORBIDDEN_FIRST_TOUCH) + ".", "",
        "## CA-J offer",
        md_table(["Field", "Value"], [[k, v] for k, v in offer.items()]), "",
        "Meeting-first: **no price is stated anywhere before the call.** Any pricing question routes to "
        f"{C.BOOKING_URL}.", "",
        "## Tutorial example offers (NOT CA-J offers)",
        "These come from the source tutorial's worked example (a junk-removal business). They are recorded for "
        "reference only. None is a CA-J offer; each is `NEEDS_EVIDENCE` and needs explicit written approval "
        "before any use. Discount/price offers for a client's own consumers are out of scope for this build.", "",
        md_table(["Example (source)", "Status", "Use allowed?"],
                 [[o, NE, "No - explicit approval required"] for o in TUTORIAL_EXAMPLE_OFFERS]), "",
        "## Reference: offer brainstorm prompt (from the source prompt library)",
        "```text", OFFER_BRAINSTORM_PROMPT, "```",
        "Any output from this prompt must be filtered through `assert_no_price_in_message()` before it is used in "
        "an ad, SMS, email, form or AI reply. A price-led idea is rejected, not edited in.", "",
    ]
    text = "\n".join(parts)
    assert_no_consumer_brand(text)
    return text


def build(ctx) -> Path:
    ctx.state.log("main_offer", caj_offer()["statement"], "SPEC-04 step 7", "Draft")
    return ctx.write_asset("out/offer.md", render(ctx), "offer", "src/offer.py")

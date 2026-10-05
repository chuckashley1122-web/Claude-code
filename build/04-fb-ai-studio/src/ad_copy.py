"""Ad copy pack -> out/ads/copy/A01..A04.md (SPEC-04 step 18).

Per angle: 5 primary-text variations, 3-4 headlines, CTA `Learn More`.
Every variation opens with the location callout followed by a pain or an
outcome (never the logo/brand), and every string passes the price, claim,
guarantee/scarcity, brand and banned-phrase guards.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.ad_angles import ANGLES, LOCATION_TOKEN  # noqa: E402
from src.common import DRAFT_NOTICE, NE  # noqa: E402
from tools.guardrails import (assert_ad_copy_clean, assert_copy_leads_with_pain_or_outcome,  # noqa: E402
                              assert_no_banned_phrases, assert_no_consumer_brand, assert_no_price_in_message,
                              find_platform_names_in_headline)

CTA = "Learn More"
CALLOUT = f"{LOCATION_TOKEN} HVAC owners:"
COPY_BLOCK = "ad-copy"


def _v(lead: str, *lines: str) -> dict:
    return {"lead": lead, "text": "\n".join(lines)}


COPY = {
    "A01": {
        "primary_texts": [
            _v("pain", f"{CALLOUT} how many calls hit voicemail last week while your crew was on a job?",
               "Every missed call is a homeowner who may ring the next company on the list. CA-J Enterprises sets up "
               "fast text follow-up so new inquiries hear back within minutes.",
               "Book a free strategy session to see how it would work for your shop."),
            _v("pain", f"{CALLOUT} a website inquiry that waits until tomorrow can go cold.",
               "We set up a follow-up system that replies to new inquiries right away and alerts you when they answer.",
               "Book a free, no-obligation strategy session."),
            _v("pain", f"{CALLOUT} tired of chasing leads between service calls?",
               "Let a follow-up system send the first text and tell you when someone replies. You step in when "
               "they're ready to talk.", "Book a free strategy session."),
            _v("pain", f"{CALLOUT} busy season, phones ringing, nobody free to call back?",
               "New inquiries get a quick, friendly text while you finish the job in front of you.",
               "See how it works on a free strategy session."),
            _v("pain", f"{CALLOUT} running ads but can't tell which ones bring in booked appointments?",
               "We set up tracking that ties each lead to the ad behind it, plus fast follow-up so leads don't sit.",
               "Book a free strategy session."),
        ],
        "headlines": ["Stop losing calls to voicemail", "Fast follow-up for HVAC leads",
                      "Free strategy session for HVAC", "No-obligation strategy call"],
    },
    "A02": {
        "primary_texts": [
            _v("outcome", f"{CALLOUT} picture opening your calendar and seeing booked appointments, not a list of callbacks.",
               "CA-J Enterprises builds the follow-up system that gets new inquiries a fast reply and a time on your calendar.",
               "Book a free strategy session."),
            _v("outcome", f"{CALLOUT} what would your week look like if every new inquiry got a reply within minutes?",
               "That's the system we set up: instant text follow-up, an alert when they reply, and a clean pipeline.",
               "Book a free, no-obligation strategy session."),
            _v("outcome", f"{CALLOUT} spend your time on the jobs, not on chasing leads.",
               "The follow-up runs in the background and hands you the conversations that are ready.",
               "Pick a time for a free strategy session."),
            _v("outcome", f"{CALLOUT} know which ads actually bring in booked appointments.",
               "We connect your page, your CRM and your ad tracking so every lead is accounted for.",
               "Book a free strategy session."),
            _v("outcome", f"{CALLOUT} get a text the moment a lead replies, and take it from there.",
               "No more refreshing inboxes. The system follows up; you close the conversation.",
               "Book a free, no-obligation strategy session."),
        ],
        "headlines": ["More booked appointments", "Your calendar, not callbacks", "Free strategy session for HVAC"],
    },
    "A03": {
        "primary_texts": [
            _v("pain", f"{CALLOUT} tried an agency before and got leads nobody could reach?",
               "Leads go cold when nobody follows up fast. We set up the follow-up first, then talk about ads.",
               "Book a free strategy session."),
            _v("pain", f"{CALLOUT} no time to manage ads or answer every inquiry?",
               "The system sends the first reply for you and only pulls you in when someone answers.",
               "Book a free strategy session. It's a conversation, not a sales pitch."),
            _v("pain", f"{CALLOUT} worried this is another long sales call?",
               "The strategy session is free and no-obligation. We look at how leads reach you today and what we'd change.",
               "Pick a time that suits you."),
            _v("pain", f"{CALLOUT} not sure your website can handle paid traffic?",
               "We set up a fast page and a form connected to your CRM before a single ad runs.",
               "Book a free strategy session."),
            _v("pain", f"{CALLOUT} tech-heavy setups not your thing?",
               "We build and test it with you, step by step, before anything goes live.",
               "Book a free, no-obligation strategy session."),
        ],
        "headlines": ["No hard sell. Just a plan.", "Free, no-obligation strategy call", "Built and tested with you"],
    },
    "A04": {
        "primary_texts": [
            _v("outcome", f"{CALLOUT} want more of your calls turned into booked appointments?",
               "Book a free, no-obligation strategy session. We'll map how leads reach you today and where they slip away.",
               "Pick a time that works for you."),
            _v("outcome", f"{CALLOUT} get a clear plan for faster lead follow-up.",
               "A free strategy session, no obligation and no hard sell. Bring your questions.", "Book online."),
            _v("outcome", f"{CALLOUT} leave with a plan to stop losing inquiries to voicemail.",
               "Free strategy session, no obligation.", "Pick a time on our calendar."),
            _v("outcome", f"{CALLOUT} see which of your ads lead to booked appointments.",
               "We'll walk through it together on a free strategy session.", "Book a time that suits you."),
            _v("outcome", f"{CALLOUT} faster replies, fewer lost leads, more booked appointments.",
               "Start with a free, no-obligation strategy session.", "Book now."),
        ],
        "headlines": ["Book a free strategy session", "No-obligation strategy call", "A plan for faster follow-up",
                      "Built for HVAC companies"],
    },
}


def check_angle(angle_id: str) -> None:
    pack = COPY[angle_id]
    assert len(pack["primary_texts"]) == 5, f"{angle_id}: need exactly 5 primary texts"
    assert 3 <= len(pack["headlines"]) <= 4, f"{angle_id}: need 3-4 headlines"
    for v in pack["primary_texts"]:
        assert v["text"].startswith(CALLOUT), f"{angle_id}: first line must carry the location callout"
        assert_copy_leads_with_pain_or_outcome(v)
    for s in [v["text"] for v in pack["primary_texts"]] + pack["headlines"] + [CTA]:
        assert_no_price_in_message(s)
        assert_ad_copy_clean(s)
        assert_no_consumer_brand(s)
        assert_no_banned_phrases(s)
    for h in pack["headlines"]:
        hits = find_platform_names_in_headline(h)
        assert not hits, f"{angle_id}: {hits}"


def render(angle: dict) -> str:
    pack = COPY[angle["id"]]
    parts = [f"# {angle['id']} - {angle['name']} ad copy", "", DRAFT_NOTICE, "",
             f"- Leads with: **{angle['lead']}** (never the logo).",
             f"- CTA button: `{CTA}`.",
             f"- Website URL: `{NE}` (the verified landing-page URL; no extra parameters). Display link: `{NE}`.",
             f"- `{LOCATION_TOKEN}` is a placeholder: target location is `{NE}`. Replace before upload.",
             "- No price, guarantee, scarcity, review count or client outcome. Headlines avoid platform brand names "
             "to reduce rejection risk.", "",
             "## Primary text variations (up to 5 per ad)"]
    for i, v in enumerate(pack["primary_texts"], 1):
        parts += [f"### Variation {i} (leads with {v['lead']})", "```text", v["text"], "```", ""]
    parts += ["## Headlines", *[f"{i}. {h}" for i, h in enumerate(pack["headlines"], 1)], "",
              f"```json {COPY_BLOCK}", json.dumps({"angle": angle["id"], "cta": CTA, **pack}, indent=2), "```", ""]
    return "\n".join(parts)


def build(ctx) -> list[Path]:
    paths = []
    for angle in ANGLES:
        check_angle(angle["id"])
        paths.append(ctx.write_asset(f"out/ads/copy/{angle['id']}.md", render(angle), f"ad_copy_{angle['id']}",
                                     "src/ad_copy.py"))
    ctx.state.record_blocker("primary_location", "Target location / service area for the ad callout and ad set",
                             "Ad copy callout, ad-set locations", "Chuck supplies the target market; replace [LOCATION]")
    return paths

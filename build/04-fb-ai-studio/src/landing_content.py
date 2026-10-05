"""Landing-page content spec -> out/landing/content_spec.md + content_spec.json (SPEC-04 step 13).

`content()` is the single source used by landing_mock.py, so the mock and the
spec cannot drift (checked by T02). No proof element is invented: every
testimonial, review, rating, client count or case study is NEEDS_EVIDENCE with
a blank evidence column and is omitted from the page.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.common import DRAFT_NOTICE, NE, cfg_value, md_table  # noqa: E402
from tools.guardrails import (assert_meeting_first, assert_no_banned_phrases,  # noqa: E402
                              assert_no_consumer_brand, assert_no_unverified_claims)

FORM_ID = "lead-form"
CTA_TEXT = "Book a free strategy session"


def content(ctx) -> dict:
    privacy = cfg_value(ctx, "privacy_policy_url")
    return {
        "status": "Draft",
        "booking_url": C.BOOKING_URL,
        "hero": {
            "headline": "Turn more of your HVAC calls into booked appointments",
            "subhead": "CA-J Enterprises sets up the follow-up system that answers new inquiries fast and gets them "
                       "on your calendar, so fewer jobs slip away to the next contractor.",
            "primary_cta": {"text": CTA_TEXT, "action": f"scroll to #{FORM_ID}"},
            "hero_image": NE,
        },
        "problem": {"title": "Sound familiar?", "items": [
            "Calls go to voicemail while your techs are out on a job.",
            "Website inquiries sit for hours before anyone replies.",
            "You can't tell which ads actually turn into booked appointments.",
        ]},
        "what_we_do": {"title": "What CA-J does", "items": [
            "A fast page and form connected straight to your CRM.",
            "A text follow-up that goes out within minutes of every new inquiry.",
            "An alert to you the moment a lead replies, so you take it from there.",
            "Ad tracking set up so each lead is tied to the campaign that produced it.",
        ]},
        "how_it_works": {"title": "How it works", "steps": [
            "Book a free strategy session.",
            "We map your service area and how leads reach you today.",
            "We build and test the system with you before anything goes live.",
        ]},
        "who_its_for": {"title": "Who it's for",
                        "text": "HVAC company owners who want more booked appointments and less time chasing leads.",
                        "service_area": cfg_value(ctx, "service_areas")},
        "trust": [
            {"element": "Review count", "value": NE, "evidence": "", "display": "omitted"},
            {"element": "Average rating", "value": NE, "evidence": "", "display": "omitted"},
            {"element": "Years in business", "value": NE, "evidence": "", "display": "omitted"},
            {"element": "Customers served", "value": NE, "evidence": "", "display": "omitted"},
            {"element": "Testimonials", "value": NE, "evidence": "", "display": "omitted"},
            {"element": "Case studies / client outcomes", "value": NE, "evidence": "", "display": "omitted"},
        ],
        "faq": [
            {"q": "Is the strategy session really free?",
             "a": "Yes. It's a no-obligation conversation about how leads reach you today."},
            {"q": "How much does it cost?",
             "a": f"Pricing is covered on the strategy session once we understand your business. Book at {C.BOOKING_URL}."},
            {"q": "What happens after I fill in the form?",
             "a": f"Chuck will reach out by text or email to set a time, or you can book directly at {C.BOOKING_URL}."},
            {"q": "Do you work in my area?",
             "a": "Tell us your service area on the call and we'll go through it together."},
        ],
        "form": {
            "id": FORM_ID,
            "fields": [
                {"name": "full_name", "label": "Full name", "type": "text", "required": True},
                {"name": "email", "label": "Email", "type": "email", "required": True},
                {"name": "phone", "label": "Mobile phone", "type": "tel", "required": True},
                {"name": "service_needed", "label": "What do you want help with?", "type": "select", "required": True,
                 "options": ["More booked appointments", "Faster lead follow-up", "Ad tracking", "Not sure yet"]},
                {"name": "consent", "label": "Communication consent", "type": "checkbox", "required": True},
            ],
            "consent_disclosure": "By submitting, you agree that CA-J Enterprises may contact you by phone, text and "
                                  "email about your inquiry. Message and data rates may apply. Reply STOP to opt out. "
                                  f"Privacy policy: {privacy}.",
            "consent_review": f"Legal wording {NE}: a human confirms the disclosure before publish.",
            "submit_text": CTA_TEXT,
        },
        "footer": {
            "business": f"{C.BUSINESS_DISPLAY_NAME} ({C.LEGAL_ENTITY})",
            "contact": f"{C.OWNER_NAME} - {C.OWNER_PHONE} - {C.OWNER_EMAIL}",
            "logo": f"small footer mark only ({NE} file)",
            "privacy_policy_url": privacy,
            "disclaimer": "This site is not part of the Facebook website or Meta Platforms, Inc.",
        },
        "variants": {
            "desktop": "Two-column hero (copy left, form right); sticky header with 2-3 section links; every button scrolls to the form.",
            "mobile": "Single column; logo centred and small; no phone number in the header; hero CTA full width; form directly after the hero.",
        },
        "rules": ["Every button scrolls to the form.", "No testimonial, review count, client count or case study is fabricated.",
                  f"Booking link is always {C.BOOKING_URL}.", "No price anywhere on the page (meeting-first)."],
    }


def all_copy(c: dict) -> str:
    bits = [c["hero"]["headline"], c["hero"]["subhead"], c["hero"]["primary_cta"]["text"], c["who_its_for"]["text"],
            c["form"]["consent_disclosure"], c["form"]["submit_text"]]
    for key in ("problem", "what_we_do"):
        bits += c[key]["items"]
    bits += c["how_it_works"]["steps"]
    for f in c["faq"]:
        bits += [f["q"], f["a"]]
    for f in c["form"]["fields"]:
        bits.append(f["label"])
        bits += f.get("options", [])
    return "\n".join(bits)


def check(c: dict) -> None:
    text = all_copy(c)
    assert_meeting_first(text)
    assert_no_unverified_claims(text)
    assert_no_consumer_brand(text)
    assert_no_banned_phrases(text)


def render_md(c: dict) -> str:
    form_rows = [[f["name"], f["label"], f["type"], "yes" if f["required"] else "no", ", ".join(f.get("options", []))]
                 for f in c["form"]["fields"]]
    return "\n".join([
        "# Landing-page content spec", "", DRAFT_NOTICE, "",
        f"Booking link: {C.BOOKING_URL}", "",
        "## Hero",
        md_table(["Element", "Value"], [["Headline", c["hero"]["headline"]], ["Subhead", c["hero"]["subhead"]],
                                         ["Primary CTA", f"{c['hero']['primary_cta']['text']} ({c['hero']['primary_cta']['action']})"],
                                         ["Hero image", c["hero"]["hero_image"]]]), "",
        f"## Problem - {c['problem']['title']}", *[f"- {i}" for i in c["problem"]["items"]], "",
        f"## {c['what_we_do']['title']}", *[f"- {i}" for i in c["what_we_do"]["items"]], "",
        f"## {c['how_it_works']['title']}", *[f"{n}. {s}" for n, s in enumerate(c["how_it_works"]["steps"], 1)], "",
        f"## {c['who_its_for']['title']}", c["who_its_for"]["text"], f"Service area: {c['who_its_for']['service_area']}", "",
        "## Trust block (nothing invented)",
        md_table(["Element", "Value", "Evidence", "Display"],
                 [[t["element"], t["value"], t["evidence"], t["display"]] for t in c["trust"]]), "",
        "## FAQ", *[f"**{f['q']}**  \n{f['a']}\n" for f in c["faq"]], "",
        f"## Form (`#{c['form']['id']}`)", md_table(["Field", "Label", "Type", "Required", "Options"], form_rows), "",
        f"Consent disclosure: {c['form']['consent_disclosure']}", "", c["form"]["consent_review"], "",
        "## Footer", md_table(["Element", "Value"], [[k, v] for k, v in c["footer"].items()]), "",
        "## Desktop and mobile variants", md_table(["Variant", "Spec"], [[k, v] for k, v in c["variants"].items()]), "",
        "## Rules", *[f"- {r}" for r in c["rules"]], "",
    ])


def build(ctx) -> list[Path]:
    c = content(ctx)
    check(c)
    return [ctx.write_asset("out/landing/content_spec.md", render_md(c), "landing_content_md", "src/landing_content.py"),
            ctx.write_json("out/landing/content_spec.json", c, "landing_content_json", "src/landing_content.py")]

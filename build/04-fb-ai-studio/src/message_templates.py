"""Message templates -> out/messages/sms_01..sms_06.md + internal_alerts.md (SPEC-04 step 12).

The tutorial's junk-removal lines are rewritten into CA-J agency-acquisition
language. Every message is checked with assert_meeting_first (no price; the
only link is the booking URL), the brand guard and the banned-phrase guard.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.common import A2P_CAVEAT, DRAFT_NOTICE, MERGE_TOKEN_FLAG, md_table  # noqa: E402
from tools.guardrails import (assert_meeting_first, assert_no_banned_phrases,  # noqa: E402
                              assert_no_consumer_brand, assert_no_unverified_claims)

OPT_OUT_LINE = "Reply STOP to opt out."

# day = calendar day of the sequence (Day 1 = form submission day); wait = wait step before this send.
SMS_STEPS = [
    {"id": "sms_01", "day": 1, "wait_before": "1 minute",
     "body": "Hi {{contact.first_name}}, it's Chuck with CA-J Enterprises. Thanks for reaching out on our website "
             "about {{service_needed}}. Quick question so I can help: when is a good time this week for a short call? "
             "Just reply here."},
    {"id": "sms_02", "day": 1, "wait_before": "2 hours",
     "body": "Hi {{contact.first_name}}, just checking you got my last text. When works for a quick call?"},
    {"id": "sms_03", "day": 3, "wait_before": "2 days (until Day 3)",
     "body": "Hi {{contact.first_name}}, I reached out a couple of days ago about the request you sent on our "
             "website. Still want to talk it through?"},
    {"id": "sms_04", "day": 7, "wait_before": "4 days (until Day 7)",
     "body": "Hi {{contact.first_name}}, Chuck again. If it's easier, pick a time that suits you here: "
             + C.BOOKING_URL},
    {"id": "sms_05", "day": 10, "wait_before": "3 days (until Day 10)",
     "body": "Hi {{contact.first_name}}, no pressure at all. Is turning more of your HVAC calls into booked "
             "appointments still on your list? A quick yes or no is fine."},
    {"id": "sms_06", "day": 14, "wait_before": "4 days (until Day 14)",
     "body": "Hi {{contact.first_name}}, last note from me so I don't clutter your phone. If the timing is better "
             "later, book whenever you like: " + C.BOOKING_URL},
]

INTERNAL_ALERTS = [
    {"id": "alert_new_lead", "workflow": "01 New Lead Automation", "channel": "SMS to owner (A2P required) / email fallback",
     "to": f"{C.OWNER_NAME} - {C.OWNER_PHONE} (SMS) / {C.OWNER_EMAIL} (email fallback)",
     "body": "New website lead: {{contact.full_name}} - {{contact.phone}} - {{contact.email}} - "
             "Wants help with: {{service_needed}}"},
    {"id": "alert_hot_lead", "workflow": "02 Hot Lead - Replied", "channel": "SMS to owner (A2P required) / email fallback",
     "to": f"{C.OWNER_NAME} - {C.OWNER_PHONE} (SMS) / {C.OWNER_EMAIL} (email fallback)",
     "body": "Hot lead replied: {{contact.full_name}} - {{contact.phone}} - Reply: {{message.body}}"},
]

TOKEN_RE = re.compile(r"\{\{[^}]+\}\}")


def full_sms(step: dict) -> str:
    return f"{step['body']} {OPT_OUT_LINE}"


def check_message(text: str) -> None:
    assert_meeting_first(text)
    assert_no_consumer_brand(text)
    assert_no_banned_phrases(text)
    assert_no_unverified_claims(text)
    if "landing page" in text.lower():
        raise ValueError("Copy rule: say 'website', not 'landing page'")


def render_sms(step: dict) -> str:
    text = full_sms(step)
    check_message(text)
    tokens = sorted(set(TOKEN_RE.findall(text)))
    return "\n".join([
        f"# {step['id'].upper()} - speed-to-lead follow-up (Workflow 01)", "", DRAFT_NOTICE, "", MERGE_TOKEN_FLAG, "",
        md_table(["Field", "Value"], [["Sequence day", f"Day {step['day']}"], ["Wait before send", step["wait_before"]],
                                       ["Channel", "SMS to contact"],
                                       ["Pre-send check", "If contact replied or opted out / DND -> stop, do not send"],
                                       ["Placeholders (unconfirmed)", ", ".join(f"`{t}`" for t in tokens) or "none"]]),
        "", "## Message", "```text", text, "```", "",
        "## Rules applied",
        "- Short, human, non-robotic. Says 'website', never 'landing page'.",
        f"- No price, fee or discount (meeting-first). The only link allowed is {C.BOOKING_URL}.",
        f"- Ends with `{OPT_OUT_LINE}`", f"- {A2P_CAVEAT}", "",
    ])


def render_alerts() -> str:
    parts = ["# Internal alerts (owner notifications)", "", DRAFT_NOTICE, "", MERGE_TOKEN_FLAG, "", A2P_CAVEAT, ""]
    for a in INTERNAL_ALERTS:
        check_message(a["body"])
        parts += [f"## {a['id']}", md_table(["Field", "Value"], [["Workflow", a["workflow"]], ["Channel", a["channel"]],
                                                                ["To", a["to"]]]),
                  "", "```text", a["body"], "```", ""]
    return "\n".join(parts)


def build(ctx) -> list[Path]:
    paths = [ctx.write_asset(f"out/messages/{s['id']}.md", render_sms(s), f"message_{s['id']}",
                             "src/message_templates.py") for s in SMS_STEPS]
    paths.append(ctx.write_asset("out/messages/internal_alerts.md", render_alerts(), "message_internal_alerts",
                                 "src/message_templates.py"))
    ctx.state.record_blocker("a2p_status", "A2P 10DLC registration status for the GHL sending number",
                             "All SMS steps in Workflow 01/02 and owner SMS alerts",
                             "Confirm A2P status in GHL; until then use the email fallback path")
    return paths

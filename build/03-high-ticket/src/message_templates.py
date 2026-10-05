"""Message templates (playbook section 10) -> out/messages/*.md

Bracketed tokens are CONTENT PLACEHOLDERS, not guaranteed GHL merge syntax.
"""
from __future__ import annotations

import re
from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from tools import guardrails as G  # noqa: E402

TEMPLATES = {
    "booking_ack": {"channel": "email", "subject": "Your strategy session with CA-J Enterprises",
                    "body": ("Hi [FIRST NAME], thanks for your interest. Choose a time here: [CALENDAR LINK]. We will review your "
                             "business, service area, lead follow-up and marketing goals. If you have already booked, your meeting "
                             "details will arrive separately. — Chuck")},
    "confirmation": {"channel": "email", "subject": "Confirm your strategy session",
                     "body": ("Hi [FIRST NAME], your session is booked for [DATE AND TIME WITH TIMEZONE]. Join here: [MEETING LINK]. "
                              "Please reply to confirm you can attend. You can reschedule here: [RESCHEDULE LINK]. Before we meet, "
                              "review [PRE-CALL LINK] and bring your current marketing spend, average job value and available capacity.")},
    "reminder_sms": {"channel": "sms", "subject": None,
                     "body": ("Hi [FIRST NAME], Chuck with CA-J Enterprises here. Your strategy session is [DATE/TIME/TIMEZONE]. "
                              "Join: [MEETING LINK]. Need another time? [RESCHEDULE LINK]. Reply STOP to opt out.")},
    "no_show": {"channel": "email", "subject": "Would another time work?",
                "body": ("Hi [FIRST NAME], we missed you at our strategy session. If you still want to review your marketing and "
                         "follow-up process, choose another time here: [RESCHEDULE LINK]. If your plans changed, reply and I will "
                         "update our notes.")},
    # Build additions (not source copy): the two unbooked follow-ups named in workflow 02.
    "unbooked_reminder": {"channel": "sms", "subject": None, "build_addition": True,
                          "body": ("Hi [FIRST NAME], Chuck with CA-J Enterprises here. You asked about a strategy session. "
                                   "Choose a time that works: [CALENDAR LINK]. Reply STOP to opt out.")},
    "unbooked_followup": {"channel": "email", "subject": "Still want to review your marketing?", "build_addition": True,
                          "body": ("Hi [FIRST NAME], following up on your request for a strategy session. If it is still useful, "
                                   "choose a time here: [CALENDAR LINK]. If now is not the right time, reply and let me know. — Chuck")},
}
TOKEN_RE = re.compile(r"\[([A-Z][A-Z /\-]*)\]")


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def render_message(template_id: str, values: dict) -> str:
    """Fill placeholders for previews/simulation. Missing values raise; nothing is guessed."""
    body = TEMPLATES[template_id]["body"]
    missing = [t for t in tokens(body) if t not in values]
    if missing:
        raise KeyError(f"{template_id}: no value for placeholders {missing}")
    out = TOKEN_RE.sub(lambda m: str(values[m.group(1)]), body)
    G.assert_prospect_copy(out)
    return out


def check_all() -> None:
    for tid, t in TEMPLATES.items():
        G.assert_meeting_first(t["body"])
        G.assert_prospect_copy(t["body"])
        if t["subject"]:
            G.assert_prospect_copy(t["subject"])
    if "Reply STOP to opt out." not in TEMPLATES["reminder_sms"]["body"]:
        raise G.GuardrailViolation("SMS reminder must include the opt-out line")


def render(tid: str) -> str:
    t = TEMPLATES[tid]
    origin = "Build addition (workflow 02 follow-up; not source copy)" if t.get("build_addition") else "Source copy (playbook section 10)"
    lines = [f"# Message template: {tid}", "", f"Status: Draft. Channel: {t['channel']}. {origin}.", ""]
    if t["subject"]:
        lines += [f"**Subject:** {t['subject']}", ""]
    lines += ["**Body:**", "", "> " + t["body"], "",
              "**Placeholders:** " + ", ".join(f"[{x}]" for x in tokens(t["body"])), "",
              "Every bracketed token is a **content placeholder, not guaranteed GHL merge syntax**. A human must insert fields "
              "with the account's field picker and send test previews before any workflow activates.", "",
              "Passed assert_meeting_first(): no price or currency appears. Sends require valid channel permission; "
              "opted-out channels are suppressed.", ""]
    return "\n".join(lines)


def build(state) -> list[Path]:
    check_all()
    state.needs("verified_sending_email", "out/messages/", "Verify the sending domain/email in GHL")
    state.needs("messaging_eligibility", "out/messages/", "Confirm SMS/A2P registration status before any SMS")
    return [state.write(f"out/messages/{tid}.md", render(tid), f"MSG-{tid.upper()}", source="src/message_templates.py")
            for tid in TEMPLATES]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

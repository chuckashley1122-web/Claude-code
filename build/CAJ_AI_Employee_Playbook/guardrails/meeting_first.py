"""Meeting-first routing.

Detects pricing intent in an inbound message and produces a reply that offers a
meeting at the booking URL instead of quoting anything. The reply itself is
verified against pricing_guard for every outbound channel.
"""
from __future__ import annotations

import re

from guardrails import pricing_guard

BOOKING_URL = pricing_guard.BOOKING_URL

_INTENT_PATTERNS = (
    r"\bhow\s+much\b",
    r"\bpric(?:e|es|ed|ing)\b",
    r"\bcost(?:s|ing)?\b",
    r"\bfees?\b",
    r"\brates?\b",
    r"\bquotes?\b",
    r"\bcharges?\b",
    r"\bwhat\s+do\s+you\s+charge\b",
    r"\bexpensive\b",
    r"\bcheap(?:er|est)?\b",
    r"\bbudget\b",
    r"\bafford(?:able)?\b",
    r"\bper\s+month\b",
    r"\bmonthly\b",
    r"\bsubscription\b",
    r"\bdiscounts?\b",
    r"[$€£]",
)
_INTENT_RE = re.compile("|".join(_INTENT_PATTERNS), re.IGNORECASE)

MEETING_REPLY = (
    "Good question. That depends on how your after-hours calls are handled today, "
    "so we walk through it together in a short meeting. You can pick a time that "
    f"works for you here: {BOOKING_URL}"
)


def detect_price_intent(text: str) -> bool:
    return bool(_INTENT_RE.search(text or ""))


def meeting_reply(first_name: str | None = None) -> str:
    reply = MEETING_REPLY if not first_name else f"Hi {first_name.strip()}. {MEETING_REPLY}"
    # The reply must itself be price-free in every outbound channel.
    for channel in pricing_guard.OUTBOUND_CHANNELS:
        pricing_guard.assert_clean(reply, channel)
    return reply


def respond(inbound: str, first_name: str | None = None) -> str | None:
    """Return the meeting-first reply when ``inbound`` asks about price, else None."""
    if detect_price_intent(inbound):
        return meeting_reply(first_name)
    return None


def enforce_outbound(draft: str, channel: str, first_name: str | None = None) -> tuple[str, bool]:
    """Return (text_to_send, was_rewritten).

    A draft that contains any price content is replaced wholesale by the
    meeting-first reply; a clean draft passes through unchanged.
    """
    if pricing_guard.is_clean(draft, channel):
        return draft, False
    return meeting_reply(first_name), True

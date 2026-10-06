"""Meeting-first routing: detect pricing intent and reply with the booking link.

The reply never contains a number or a price; it invites a meeting and links
``BOOKING_URL``. The reply is itself checked by ``pricing_guard`` before return.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from config.constants import BOOKING_URL
from guardrails import pricing_guard

# Pricing intent in the languages the FAQ bot is expected to see.
_INTENT_PATTERNS = (
    r"\bhow\s+much\b", r"\bpric(?:e|es|ed|ing)\b", r"\bcosts?\b", r"\bfees?\b",
    r"\brates?\b", r"\bquotes?\b", r"\bcharge[sd]?\b", r"\bbudget\b",
    r"\bafford(?:able)?\b", r"\bexpensive\b", r"\bcheap\b", r"\bmonthly\b",
    r"\bper\s+month\b", r"\bsubscription\b", r"\binvoice\b", r"\bdiscount\b",
    r"[$€£]", r"\bdollars?\b", r"\busd\b",
    # Spanish / French / German / Portuguese / Hindi (romanised)
    r"\bprecios?\b", r"\bcu[aá]nto\s+cuesta\b", r"\bcuesta\b", r"\bcobran?\b",
    r"\bprix\b", r"\bcombien\b", r"\btarifs?\b", r"\bco[uû]te?\b",
    r"\bpreis(?:e)?\b", r"\bkosten?\b", r"\bkostet\b", r"\bpre[cç]o\b",
    r"\bkitna\b", r"\bkeemat\b", r"\bkimat\b",
)
_INTENT = re.compile("|".join(_INTENT_PATTERNS), re.I)

MEETING_REPLY = (
    "Good question. The right setup depends on your business, so the best next "
    "step is a short meeting where we can look at it together. You can pick a "
    f"time here: {BOOKING_URL}"
)


@dataclass(frozen=True)
class Routing:
    pricing_intent: bool
    reply: Optional[str]
    matched: Optional[str] = None


def detect_pricing_intent(message: str) -> Optional[str]:
    """Return the matched trigger text if ``message`` shows pricing intent."""
    if not message:
        return None
    m = _INTENT.search(message)
    return m.group(0) if m else None


def meeting_reply() -> str:
    reply = pricing_guard.assert_clean(MEETING_REPLY, "meeting_first reply")
    if re.search(r"\d", reply):
        raise ValueError("meeting-first reply must never contain a number")
    return reply


def route(message: str) -> Routing:
    """Route an inbound message. If pricing intent is found, return the meeting
    reply; otherwise ``reply`` is None and the normal flow continues."""
    matched = detect_pricing_intent(message)
    if matched:
        return Routing(True, meeting_reply(), matched)
    return Routing(False, None, None)

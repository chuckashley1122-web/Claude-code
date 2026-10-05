"""Pricing guard (MEETING-FIRST).

Blocks any price or price language in outbound text. CA&J never quotes a price in
an email, DM, call script, chat, page, ad, or AI-agent reply; pricing intent is
routed to a meeting at https://ca-jenterprises.com/ai instead (see meeting_first.py).

Two strictness levels:
  * outbound channels  -> money amounts AND price words are blocked
  * internal channels  -> money amounts only (agent instructions and project
    records need to *talk about* pricing rules, e.g. "never state a price",
    but must never contain an actual figure)
"""
from __future__ import annotations

import re
from dataclasses import dataclass

BOOKING_URL = "https://ca-jenterprises.com/ai"

OUTBOUND_CHANNELS = frozenset(
    {"email", "dm", "call", "sms", "chat", "agent_reply", "voice", "page", "ad"}
)
INTERNAL_CHANNELS = frozenset({"internal_instructions", "record"})

# Money amounts: any currency symbol, currency code, or spelled-out currency.
_AMOUNT_PATTERNS: tuple[tuple[str, str], ...] = (
    ("currency_symbol", r"[$€£¥]"),
    ("currency_code", r"\bUSD\b"),
    ("dollars", r"\bdollars?\b"),
    ("bucks", r"\bbucks\b"),
    ("cents", r"\bcents?\b"),
)

# Price words: blocked in every outbound channel.
_TERM_PATTERNS: tuple[tuple[str, str], ...] = (
    ("setup_fee", r"\bset[\s-]?up\s+fees?\b"),
    ("fee", r"\bfees?\b"),
    ("price", r"\bpric(?:e|es|ed|ing)\b"),
    ("cost", r"\bcost(?:s|ing)?\b"),
    ("per_month", r"\bper\s+month\b"),
    ("monthly", r"\bmonthly\b"),
    ("per_mo", r"/\s?mo(?:nth)?\b|\bper\s+mo\b"),
    ("per_appointment", r"\bper\s+(?:booked\s+)?appointments?\b"),
)

_AMOUNT_RE = [(k, re.compile(p, re.IGNORECASE)) for k, p in _AMOUNT_PATTERNS]
_TERM_RE = [(k, re.compile(p, re.IGNORECASE)) for k, p in _TERM_PATTERNS]


@dataclass(frozen=True)
class Violation:
    kind: str
    match: str
    start: int


class PricingViolation(ValueError):
    """Raised when outbound text contains a price or price language."""

    def __init__(self, channel: str, violations: list[Violation]):
        self.channel = channel
        self.violations = violations
        found = ", ".join(f"{v.kind}={v.match!r}" for v in violations)
        super().__init__(
            f"MEETING-FIRST: price content blocked in channel '{channel}': {found}. "
            f"Route pricing questions to a meeting at {BOOKING_URL}."
        )


def _scan(text: str, patterns) -> list[Violation]:
    out: list[Violation] = []
    for kind, rx in patterns:
        for m in rx.finditer(text):
            out.append(Violation(kind, m.group(0), m.start()))
    return out


def find_violations(text: str, channel: str) -> list[Violation]:
    """Return every price violation in ``text`` for ``channel``, ordered by position."""
    if channel in OUTBOUND_CHANNELS:
        found = _scan(text, _AMOUNT_RE) + _scan(text, _TERM_RE)
    elif channel in INTERNAL_CHANNELS:
        found = _scan(text, _AMOUNT_RE)
    else:
        raise ValueError(
            f"unknown channel '{channel}'; expected one of "
            f"{sorted(OUTBOUND_CHANNELS | INTERNAL_CHANNELS)}"
        )
    return sorted(found, key=lambda v: (v.start, v.kind))


def find_amounts(text: str) -> list[Violation]:
    """Money amounts only (used by the record validator)."""
    return find_violations(text, "record")


def is_clean(text: str, channel: str) -> bool:
    return not find_violations(text, channel)


def assert_clean(text: str, channel: str) -> str:
    """Return ``text`` unchanged if clean; raise PricingViolation otherwise."""
    violations = find_violations(text, channel)
    if violations:
        raise PricingViolation(channel, violations)
    return text

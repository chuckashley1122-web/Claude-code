"""Outbound pricing guard: blocks any outbound text that quotes or mentions a price.

Meeting-first rule: no price, fee, rate, or dollar amount may appear in any
outbound / prospect-facing text. Pricing intent goes to BOOKING_URL instead
(see ``guardrails.meeting_first``).

Usage::

    result = check(text)        # -> GuardResult(status="BLOCKED"|"CLEAN", findings=[...])
    assert_clean(text)          # raises PricingViolation if blocked
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

BLOCKED = "BLOCKED"
CLEAN = "CLEAN"

_NUM = r"\d[\d,]*(?:\.\d+)?"
_RANGE = rf"{_NUM}(?:\s*(?:-|–|—|to)\s*\$?\s*{_NUM})?"
_UNITS = (r"(?:booked\s+)?(?:appointment|appt|booking|lead|call|month|mo|year|yr|"
          r"week|wk|day|hour|hr|minute|min|seat|user|location)s?")

# (rule name, compiled pattern). Order matters only for reporting.
RULES: tuple[tuple[str, re.Pattern], ...] = (
    ("currency_amount", re.compile(rf"[$€£]\s*{_NUM}(?:\s*[kKmM]\b)?")),
    ("amount_currency_word", re.compile(rf"\b{_NUM}\s*(?:usd|dollars?|bucks|eur|euros?|gbp)\b", re.I)),
    ("currency_word_amount", re.compile(rf"\b(?:usd|eur|gbp)\s*{_NUM}", re.I)),
    ("currency_symbol", re.compile(r"[$€£]")),
    ("currency_word", re.compile(r"\b(?:usd|dollars?|bucks)\b", re.I)),
    ("rate_expression", re.compile(rf"\b{_RANGE}\s*(?:/|per|a|an|each)\s*{_UNITS}\b", re.I)),
    ("setup_fee", re.compile(r"\bset[\s-]?up\s+fees?\b", re.I)),
    ("per_month", re.compile(r"\bper\s+month\b", re.I)),
    ("monthly", re.compile(r"\bmonthly\b", re.I)),
    ("price", re.compile(r"\bpric(?:e|es|ed|ing)\b", re.I)),
    ("fee", re.compile(r"\bfees?\b", re.I)),
    ("cost", re.compile(r"\bcost(?:s|ing|ly)?\b", re.I)),
)


@dataclass(frozen=True)
class Finding:
    rule: str
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class GuardResult:
    status: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return self.status == BLOCKED


class PricingViolation(ValueError):
    def __init__(self, result: GuardResult, label: str = "text"):
        self.result = result
        spans = "; ".join(f"{f.rule}@{f.start}-{f.end}:{f.text!r}" for f in result.findings)
        super().__init__(f"BLOCKED by pricing_guard in {label}: {spans}")


def check(text: str) -> GuardResult:
    """Scan ``text`` and return every offending span. Overlapping spans are kept
    once (the first rule that claimed the start offset wins)."""
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    findings: list[Finding] = []
    claimed: set[tuple[int, int]] = set()
    for name, pattern in RULES:
        for m in pattern.finditer(text):
            span = (m.start(), m.end())
            if any(s <= span[0] < e for s, e in claimed):
                continue
            claimed.add(span)
            findings.append(Finding(name, m.start(), m.end(), m.group(0)))
    findings.sort(key=lambda f: f.start)
    return GuardResult(BLOCKED if findings else CLEAN, findings)


def assert_clean(text: str, label: str = "text") -> str:
    """Return ``text`` unchanged if clean; raise :class:`PricingViolation` otherwise.
    Used by every outbound-sending node handler."""
    result = check(text)
    if result.blocked:
        raise PricingViolation(result, label)
    return text

"""Guardrails for SPEC-05. Every function raises ``GuardrailViolation`` on a hit.

Used by ``tools/compliance_scan.py``, the generators and ``tools/run_tests.py``;
individually tested in ``tests/test_guardrails.py``.

Sensitive literals (frozen campaign name, disallowed location ID) are imported
from ``config/constants.py`` so they never appear here as literals. Banned
phrases are assembled at runtime for the same reason.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402


class GuardrailViolation(Exception):
    def __init__(self, rule: str, detail: str):
        super().__init__(f"[{rule}] {detail}")
        self.rule = rule
        self.detail = detail


# ---------------------------------------------------------------- no spend
SPEND_CATEGORIES = ("domain", "upgrade", "subscription", "seo_tool", "ad_spend", "payment_method",
                    "plan_change")


def assert_no_spend(item: str, approval_ref: str | None) -> None:
    """Raise unless an explicit written approval reference is supplied for a spend item."""
    if not approval_ref or not str(approval_ref).strip() or str(approval_ref).strip() == C.NEEDS_EVIDENCE:
        raise GuardrailViolation(
            "no-spend",
            f"spend item {item!r} has no written approval reference; spend $0 until a human approves",
        )
    if C.AD_SPEND_CAP_USD != 0:
        raise GuardrailViolation("no-spend", "AD_SPEND_CAP_USD must stay 0 in this build")


# ---------------------------------------------------------------- no price in message
_PRICE_PATTERNS = [
    (re.compile(r"\$\s?650\b"), "$650"),
    (re.compile(r"\b650\s*/\s*mo", re.I), "650/mo"),
    (re.compile(r"\$\s?250\b"), "$250"),
    (re.compile(r"\$\s?300\b"), "$300"),
    (re.compile(r"per\s+booked\s+appointment", re.I), "per booked appointment"),
    (re.compile(r"\$\s?250\s*(to|-|–)\s*\$?\s?300", re.I), "$250 to $300"),
    (re.compile(r"set\s*-?\s*up\s+fee", re.I), "setup fee"),
    (re.compile(r"\btech(nology)?\s+fee\b", re.I), "tech fee"),
]


def assert_no_price_in_message(text: str) -> None:
    """Raise if any CA-J price or fee wording appears in customer-facing text."""
    for pattern, label in _PRICE_PATTERNS:
        if pattern.search(text):
            raise GuardrailViolation("no-price-in-message", f"customer-facing text contains {label!r}")


# ---------------------------------------------------------------- logo never first
_LOGO_RE = re.compile(r"logo", re.I)


def assert_logo_not_first(creative: Mapping[str, Any]) -> None:
    """Raise if the logo is the opening/first visual element of a hero/OG/ad creative record."""
    opening = str(creative.get("opening_element", ""))
    elements = list(creative.get("elements") or [])
    if not opening:
        raise GuardrailViolation("logo-not-first", "creative record has no opening_element")
    if _LOGO_RE.search(opening):
        raise GuardrailViolation("logo-not-first", f"opening_element is the logo ({opening!r})")
    if elements and _LOGO_RE.search(str(elements[0])):
        raise GuardrailViolation("logo-not-first", f"first element is the logo ({elements[0]!r})")
    if elements and str(elements[0]) != opening:
        raise GuardrailViolation("logo-not-first", "opening_element does not match the first element")
    pos = str(creative.get("logo_position", "footer"))
    if pos not in ("footer", "none"):
        raise GuardrailViolation("logo-not-first", f"logo_position must be footer or none, got {pos!r}")


# ---------------------------------------------------------------- frozen campaign
_PROTECTIVE_LINE = re.compile(r"FROZEN", re.I)
_PROTECTIVE_NEGATION = re.compile(r"\b(never|do not|must not|untouchable)\b", re.I)


def is_frozen_campaign_warning_line(line: str) -> bool:
    return bool(_PROTECTIVE_LINE.search(line) and _PROTECTIVE_NEGATION.search(line))


def assert_frozen_campaign_untouched(text: str) -> None:
    """Raise if text names the frozen campaign other than in a FROZEN warning line."""
    for line in text.splitlines():
        if C.FROZEN_CAMPAIGN_NAME in line and not is_frozen_campaign_warning_line(line):
            raise GuardrailViolation(
                "frozen-campaign",
                "frozen Meta campaign named as a target/duplicate source/edit subject",
            )


# ---------------------------------------------------------------- disallowed location
def assert_not_disallowed_location(text: str) -> None:
    if C.DISALLOWED_LOCATION_ID in text:
        raise GuardrailViolation("disallowed-location", "the disallowed GHL location ID appears in text")


_LOCATION_CI = re.compile(re.escape(C.GHL_LOCATION_ID), re.I)


def assert_location_id_exact_case(text: str) -> None:
    for m in _LOCATION_CI.finditer(text):
        if m.group(0) != C.GHL_LOCATION_ID:
            raise GuardrailViolation("location-case", "GHL location ID appears with wrong case")


# ---------------------------------------------------------------- no fabricated fact
# category -> (fact key in business_facts.json that would authorise it, pattern)
FABRICATION_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("testimonials", re.compile(r"\btestimonials?\b|[\"“][^\"”]{20,}[\"”]\s*[—–-]\s*[A-Z][a-z]+", re.I)),
    ("review_rating", re.compile(r"\b\d(\.\d)?\s*(/\s*5|out of 5|stars?)\b|★", re.I)),
    ("review_count", re.compile(r"\b\d[\d,]*\+?\s+(\S+\s+)?(reviews|ratings)\b", re.I)),
    ("customers_served", re.compile(r"\b\d[\d,]*\+?\s+(happy\s+)?(clients|customers|businesses|contractors)\b", re.I)),
    ("years_in_business", re.compile(r"\b\d+\+?\s+years?\b", re.I)),
    ("license_info", re.compile(r"\b(licen[cs]ed|bonded|insured|certified|accredited)\b", re.I)),
    ("office_address", re.compile(r"\b\d{2,6}\s+[A-Z][a-z]+(\s+[A-Z][a-z]+)*\s+(St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Suite|Dr|Drive)\b")),
    ("response_time", re.compile(r"\b(within|in under|under)\s+\d+\s+(minutes?|hours?|days?)\b|\bsame[- ]day\b|24/7", re.I)),
    ("results", re.compile(r"\b\d+(\.\d+)?\s*%|\b\d+x\b|\bguarantee[ds]?\b|\bROI of\b", re.I)),
]


def _fact_verified(facts: Any, key: str) -> bool:
    records = facts.get("facts", facts) if isinstance(facts, Mapping) else facts
    if isinstance(records, Mapping):
        records = list(records.values())
    for rec in records or []:
        if rec.get("key") == key:
            return bool(rec.get("verified")) and bool(str(rec.get("evidence_source", "")).strip())
    return False


def assert_no_fabricated_fact(text: str, facts: Any) -> None:
    """Raise if text asserts a review/rating/count/tenure/licence/address/response-time/result
    claim whose fact key is not verified with an evidence source in business_facts.json."""
    for key, pattern in FABRICATION_PATTERNS:
        m = pattern.search(text)
        if m and not _fact_verified(facts, key):
            raise GuardrailViolation("no-fabricated-fact",
                                     f"unsourced {key} claim near {m.group(0)!r}")


# ---------------------------------------------------------------- canonical uniqueness
def assert_canonical_unique(metadata_set: Iterable[Mapping[str, Any]]) -> None:
    seen: dict[str, dict[str, str]] = {"title": {}, "meta_description": {}, "canonical": {}}
    for rec in metadata_set:
        if not rec.get("indexable", True):
            continue
        route = rec.get("route", "?")
        canonical = rec.get("canonical")
        if not canonical or not isinstance(canonical, str):
            raise GuardrailViolation("canonical-unique", f"route {route} has no single canonical")
        for field in ("title", "meta_description", "canonical"):
            value = str(rec.get(field, "")).strip()
            if not value:
                raise GuardrailViolation("canonical-unique", f"route {route} missing {field}")
            norm = value.lower()
            if norm in seen[field]:
                raise GuardrailViolation("canonical-unique",
                                         f"duplicate {field} on {route} and {seen[field][norm]}")
            seen[field][norm] = route


# ---------------------------------------------------------------- banned phrases (build rule 7)
BANNED_PHRASES = [
    "qualified" + " appointment",
    "shows" + " up",
    "10-25" + " leads" + "/month",
    "10\u201325" + " leads" + "/month",
]


def assert_no_banned_phrase(text: str) -> None:
    low = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase.lower() in low:
            raise GuardrailViolation("banned-phrase", f"banned phrase {phrase!r} present")


# ---------------------------------------------------------------- brand separation (build rule 8)
CONSUMER_BRAND_PATTERNS = [
    re.compile(r"daily\s+grind", re.I),
    re.compile(r"\betsy\b", re.I),
    re.compile(r"\bprintables?\b", re.I),
    re.compile(r"\bcoffee\b", re.I),
]


def assert_no_consumer_brand(text: str) -> None:
    for pattern in CONSUMER_BRAND_PATTERNS:
        m = pattern.search(text)
        if m:
            raise GuardrailViolation("brand-separation",
                                     f"consumer brand mention {m.group(0)!r} in B2B content")


# ---------------------------------------------------------------- public contact (build rule 9)
_BANNED_PHONE_DIGITS = str(8665663444 + 1)  # computed so the number never appears literally


def assert_public_contact_only(text: str) -> None:
    for line in text.splitlines():
        if _BANNED_PHONE_DIGITS in re.sub(r"\D", "", line):
            raise GuardrailViolation("public-contact", "non-public phone number present")


def check_all(text: str, customer_facing: bool, facts: Any) -> list[str]:
    """Run every text guardrail; return violation messages instead of raising."""
    checks = [assert_frozen_campaign_untouched, assert_location_id_exact_case,
              assert_no_banned_phrase, assert_public_contact_only]
    if customer_facing:
        checks += [assert_no_price_in_message, assert_no_consumer_brand,
                   assert_not_disallowed_location, lambda t: assert_no_fabricated_fact(t, facts)]
    problems = []
    for check in checks:
        try:
            check(text)
        except GuardrailViolation as exc:
            problems.append(str(exc))
    return problems

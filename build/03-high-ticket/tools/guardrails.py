"""Hard guardrails: frozen campaign, no spend, meeting-first, logo-not-first,
plus brand separation and banned phrasing. Called by compliance_scan.py,
run_tests.py and every generator that emits copy or creatives.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402


class GuardrailViolation(Exception):
    """Base class for every guardrail failure."""


class FrozenCampaignViolation(GuardrailViolation):
    pass


class CampaignNameViolation(GuardrailViolation):
    pass


class SpendNotApproved(GuardrailViolation):
    pass


class MeetingFirstViolation(GuardrailViolation):
    pass


class LogoFirstViolation(GuardrailViolation):
    pass


class BrandBlendViolation(GuardrailViolation):
    pass


class BannedPhraseViolation(GuardrailViolation):
    pass


# ---- currency / price detection ----------------------------------------------
CURRENCY_RE = re.compile(
    r"(?:US\$|\$|€|£)\s?\d[\d,]*(?:\.\d+)?[kKmM]?"
    r"|\bUSD\s?\d[\d,]*(?:\.\d+)?"
    r"|\b\d[\d,]*(?:\.\d+)?\s?(?:USD|dollars?|bucks)\b",
    re.IGNORECASE,
)
PRICE_RATE_RE = re.compile(
    r"\b\d[\d,]*(?:\.\d+)?\s?(?:/|per\s+)(?:mo|month|week|day|appointment|appt|booked appointment)\b",
    re.IGNORECASE,
)


def find_currency(text: str) -> list[str]:
    return [m.group(0) for m in CURRENCY_RE.finditer(text or "")]


def find_price_mentions(text: str) -> list[str]:
    return find_currency(text) + [m.group(0) for m in PRICE_RATE_RE.finditer(text or "")]


# ---- 1. frozen campaign ------------------------------------------------------
NEW_NAME_RE = re.compile(r"^(?P<prefix>" + "|".join(re.escape(p) for p in C.OBJECT_PREFIX_MAP.values())
                         + r")-Leads-(?P<ymd>\d{8})$")


def assert_not_frozen_campaign(name: str) -> str:
    """Raise on the frozen live campaign (or anything derived from it in place).

    Never edit, pause, duplicate-in-place, or otherwise touch the frozen campaign:
    editing resets Meta's learning phase.
    """
    if not isinstance(name, str):
        raise CampaignNameViolation(f"campaign name must be a string, got {type(name).__name__}")
    if C.FROZEN_CAMPAIGN_NAME.upper() in name.strip().upper():
        raise FrozenCampaignViolation(
            f"{name!r} is (or derives from) the frozen live campaign; do not edit, pause or duplicate it. "
            "Build a separate NEW draft instead (editing resets Meta's learning phase).")
    return name


def assert_new_campaign_name(name: str) -> str:
    assert_not_frozen_campaign(name)
    m = NEW_NAME_RE.match(name)
    if not m:
        raise CampaignNameViolation(f"{name!r} does not match {C.NEW_CAMPAIGN_NAME_PATTERN}")
    try:
        datetime.strptime(m.group("ymd"), "%Y%m%d")
    except ValueError as exc:
        raise CampaignNameViolation(f"{name!r} has an invalid date") from exc
    return name


def new_campaign_name(on: date, mode: str = C.BUILD_MODE) -> str:
    prefix = C.OBJECT_PREFIX_MAP[mode]
    return assert_new_campaign_name(f"{prefix}-Leads-{on:%Y%m%d}")


# ---- 2. no spend ---------------------------------------------------------------
def assert_no_spend(amount, approval_flag, item: str = "spend") -> None:
    """Raise unless approval_flag is True. Applies to ad spend, domains,
    subscriptions, upgrades and tools. A zero amount is not spend."""
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise SpendNotApproved(f"{item}: amount must be a number, got {amount!r}")
    if amount < 0:
        raise SpendNotApproved(f"{item}: negative amount {amount!r}")
    if amount == 0:
        return
    if approval_flag is not True:
        raise SpendNotApproved(f"{item}: {amount} requires explicit written human approval (approval flag is {approval_flag!r})")


# ---- 3. meeting first ------------------------------------------------------------
def assert_meeting_first(text: str) -> str:
    """Raise if message/ad/chat copy contains a currency amount or a price."""
    hits = find_price_mentions(text)
    if hits:
        raise MeetingFirstViolation(f"price or currency in prospect-facing copy: {hits}; route pricing to {C.BOOKING_URL}")
    return text


# ---- 4. logo not first -------------------------------------------------------------
LEAD_ELEMENTS = {"outcome_headline", "offer_line", "outcome", "offer"}


def assert_logo_not_first(creative) -> None:
    """Raise if the CA-J logo comes before the outcome/offer element, or is
    anything other than a small footer disclaimer."""
    vd = creative.get("visual_direction") if isinstance(creative, dict) else creative
    if isinstance(vd, list):
        elements = sorted(vd, key=lambda e: e["order"])
        if not elements:
            raise LogoFirstViolation("visual direction is empty")
        names = [e["element"] for e in elements]
        lead_idx = [i for i, n in enumerate(names) if n in LEAD_ELEMENTS]
        if not lead_idx:
            raise LogoFirstViolation("visual direction has no outcome or offer element")
        if names[0] not in LEAD_ELEMENTS:
            raise LogoFirstViolation(f"first element is {names[0]!r}; outcome or offer must lead")
        for i, e in enumerate(elements):
            if e["element"] == "logo":
                if i < lead_idx[0]:
                    raise LogoFirstViolation("logo placed before the outcome/offer element")
                if e.get("placement") != "footer" or e.get("size") != "small":
                    raise LogoFirstViolation("logo allowed only as a small footer disclaimer")
        return
    if isinstance(vd, str):
        low = vd.lower()
        leads = [low.find(w) for w in ("outcome", "offer") if low.find(w) >= 0]
        if not leads:
            raise LogoFirstViolation("visual direction has no outcome or offer element")
        logo = low.find("logo")
        if logo >= 0:
            if logo < min(leads):
                raise LogoFirstViolation("logo mentioned before the outcome/offer element")
            if "footer" not in low[logo:]:
                raise LogoFirstViolation("logo allowed only as a small footer disclaimer")
        return
    raise LogoFirstViolation(f"unsupported visual_direction type {type(vd).__name__}")


# ---- brand separation and phrasing ---------------------------------------------------
def assert_b2b_brand_clean(text: str) -> str:
    low = (text or "").lower()
    hits = [b for b in C.CONSUMER_BRANDS if b.lower() in low]
    if hits:
        raise BrandBlendViolation(f"consumer brand in B2B content: {hits}")
    return text


def find_banned_phrases(text: str) -> list[str]:
    low = (text or "").lower()
    hits = [p for p in C.BANNED_PHRASES if p.lower() in low]
    if C.FORBIDDEN_PHONE in (text or ""):
        hits.append("forbidden phone number")
    return hits


def assert_no_banned_phrases(text: str) -> str:
    hits = find_banned_phrases(text)
    if hits:
        raise BannedPhraseViolation(f"banned phrasing: {hits}")
    return text


def assert_prospect_copy(text: str) -> str:
    """Every guard that applies to prospect-facing copy, in one call."""
    assert_meeting_first(text)
    assert_b2b_brand_clean(text)
    assert_no_banned_phrases(text)
    return text

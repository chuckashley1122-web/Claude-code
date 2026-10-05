"""Guardrails used by every generator, compliance_scan.py and run_tests.py.

Core four (SPEC-04 §5.6):
  assert_not_frozen_campaign(text)   - frozen live campaign tripwire
  assert_no_spend(item, approval_ref) - no spend without an explicit approval reference
  assert_no_price_in_message(text)   - meeting-first: no CA-J price in any message copy
  assert_logo_not_first(creative)    - creatives lead with pain or outcome, never the logo

Plus supporting checks (brand separation, banned phrases, unverified claims,
guarantee/scarcity, secrets). Each `find_*` returns a list of hit strings; each
`assert_*` raises a GuardrailViolation subclass when hits exist.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402


class GuardrailViolation(Exception):
    pass


class FrozenCampaignError(GuardrailViolation):
    pass


class SpendNotApproved(GuardrailViolation):
    pass


class PriceInMessageError(GuardrailViolation):
    pass


class LogoFirstError(GuardrailViolation):
    pass


class BrandBlendError(GuardrailViolation):
    pass


class BannedPhraseError(GuardrailViolation):
    pass


class UnverifiedClaimError(GuardrailViolation):
    pass


class SecretLeakError(GuardrailViolation):
    pass


# ---------------------------------------------------------------------------
# Frozen campaign
# ---------------------------------------------------------------------------
BANNER_START = "<!-- FROZEN-CAMPAIGN-WARNING:START -->"
BANNER_END = "<!-- FROZEN-CAMPAIGN-WARNING:END -->"


def _squash(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def strip_warning_banner(text: str) -> str:
    """Remove the single permitted warning-banner block (META-CHECKLIST only)."""
    pattern = re.escape(BANNER_START) + r".*?" + re.escape(BANNER_END)
    return re.sub(pattern, "", text, flags=re.S)


def find_frozen_campaign(text: str, allow_banner: bool = False) -> list[str]:
    body = strip_warning_banner(text) if allow_banner else text
    hits = []
    if _squash(C.FROZEN_CAMPAIGN_NAME) in _squash(body):
        hits.append("frozen live campaign named in content (only the constant and the META-CHECKLIST warning banner may name it)")
    return hits


def assert_not_frozen_campaign(text: str, allow_banner: bool = False) -> None:
    """Raise if the frozen campaign is named anywhere outside the permitted banner.

    Matching ignores case and separators, so `caj-hvac27-us-purchase-test02` and
    similar spellings also trip the wire.
    """
    hits = find_frozen_campaign(text, allow_banner=allow_banner)
    if hits:
        raise FrozenCampaignError("; ".join(hits))


def assert_campaign_name_is_draft(name: str) -> None:
    assert_not_frozen_campaign(name)
    if not re.match(C.NEW_CAMPAIGN_NAME_REGEX, name):
        raise FrozenCampaignError(
            f"Campaign name {name!r} does not match {C.NEW_CAMPAIGN_NAME_PATTERN}; new work must be a separate NEW draft.")


# ---------------------------------------------------------------------------
# Spend
# ---------------------------------------------------------------------------
SPEND_CATEGORIES = ("ad_budget", "domain", "subscription", "tool", "upgrade", "payment_method")


def assert_no_spend(item: str, approval_ref) -> dict:
    """Raise SpendNotApproved unless a real approval reference is supplied."""
    ref = (approval_ref or "").strip() if isinstance(approval_ref, str) else ""
    if not ref or ref.upper() in {C.NEEDS_EVIDENCE, "NONE", "N/A", "TBD", "PENDING"}:
        raise SpendNotApproved(
            f"Spend item {item!r} requires an explicit written human approval reference; none supplied.")
    return {"item": item, "approval_ref": ref}


# ---------------------------------------------------------------------------
# Price in message (meeting-first)
# ---------------------------------------------------------------------------
_PRICE_PATTERNS = [
    (r"\$\s?\d", "dollar figure"),
    (r"\b\d[\d,]*(?:\.\d+)?\s?(?:usd|dollars?|bucks)\b", "currency amount"),
    (r"\b(?:%d|%d|%d)\b" % (C.TECH_FEE_MONTHLY_USD, C.PER_BOOKED_APPOINTMENT_MIN_USD,
                           C.PER_BOOKED_APPOINTMENT_MAX_USD), "locked CA-J price figure"),
    (r"\b(?:setup|set-up|tech|monthly|management|retainer)\s+fee", "fee language"),
    (r"\bper\s+booked\s+appointment\b", "per-appointment pricing language"),
    (r"\b\d+\s?%\s?off\b", "percentage discount"),
    (r"\bdiscount", "discount offer (needs approval)"),
    (r"\bper\s+month\b|/\s?mo\b", "recurring price language"),
]


def find_price(text: str) -> list[str]:
    hits = []
    for pattern, label in _PRICE_PATTERNS:
        for m in re.finditer(pattern, text, flags=re.I):
            hits.append(f"{label}: {m.group(0)!r}")
    return hits


def assert_no_price_in_message(text: str) -> None:
    hits = find_price(text)
    if hits:
        raise PriceInMessageError(
            "Price found in message copy (meeting-first; route pricing to " + C.BOOKING_URL + "): " + "; ".join(hits))


_URL_RE = re.compile(r"https?://[^\s)\"'<>\]]+", re.I)


def assert_meeting_first(text: str, allowed_urls: tuple[str, ...] = ()) -> None:
    """No price, and the only call-to-action link is the booking URL (or an allowed placeholder)."""
    assert_no_price_in_message(text)
    for url in _URL_RE.findall(text):
        url = url.rstrip(".,;:")
        if url != C.BOOKING_URL and url not in allowed_urls:
            raise PriceInMessageError(f"Message links to {url!r}; booking destination must be {C.BOOKING_URL}")


# ---------------------------------------------------------------------------
# Logo not first / opening element
# ---------------------------------------------------------------------------
_BRAND_LEAD_RE = re.compile(r"^\W*(ca[-&]?j|caj\b|logo)", re.I)


def assert_logo_not_first(creative: dict) -> None:
    """Raise if a creative's first visual element is the logo / brand mark.

    Creatives must open with a pain or an outcome; the logo is a small footer
    disclaimer only.
    """
    opening = creative.get("opening_element")
    if not isinstance(opening, dict):
        raise LogoFirstError(f"{creative.get('asset_id', '?')}: opening_element missing")
    otype = str(opening.get("type", "")).lower()
    desc = str(opening.get("description", ""))
    if otype == "logo" or "logo" in desc.lower() or _BRAND_LEAD_RE.match(desc):
        raise LogoFirstError(f"{creative.get('asset_id', '?')}: first visual element is the logo/brand mark")
    if otype not in C.ALLOWED_OPENING_ELEMENT_TYPES:
        raise LogoFirstError(
            f"{creative.get('asset_id', '?')}: opening element type {otype!r} must be one of {C.ALLOWED_OPENING_ELEMENT_TYPES}")
    placement = str(creative.get("logo_placement", "")).lower()
    if "footer" not in placement:
        raise LogoFirstError(f"{creative.get('asset_id', '?')}: logo must be a small footer disclaimer only")
    on_image = creative.get("on_image_text") or []
    if on_image and _BRAND_LEAD_RE.match(str(on_image[0])):
        raise LogoFirstError(f"{creative.get('asset_id', '?')}: on-image text leads with the brand")


def assert_copy_leads_with_pain_or_outcome(variant: dict) -> None:
    """Primary-text variants carry a `lead` tag and must not open with the brand."""
    if variant.get("lead") not in C.ALLOWED_OPENING_ELEMENT_TYPES:
        raise LogoFirstError(f"Copy lead {variant.get('lead')!r} must be pain or outcome")
    first_line = variant["text"].strip().splitlines()[0]
    after_callout = first_line.split(":", 1)[1] if ":" in first_line else first_line
    if _BRAND_LEAD_RE.match(first_line) or _BRAND_LEAD_RE.match(after_callout):
        raise LogoFirstError("Copy opens with the brand instead of a pain or outcome")


# ---------------------------------------------------------------------------
# Brand separation, banned phrases, contact
# ---------------------------------------------------------------------------
def find_consumer_brand(text: str) -> list[str]:
    low = text.lower()
    hits = [f"consumer brand {b!r} in B2B content" for b in C.CONSUMER_BRAND_BLOCKLIST
            if re.search(r"\b" + re.escape(b.lower()) + r"\b", low)]
    hits += [f"forbidden phone number {p!r}" for p in C.FORBIDDEN_PHONE_NUMBERS if p in text]
    return hits


def assert_no_consumer_brand(text: str) -> None:
    hits = find_consumer_brand(text)
    if hits:
        raise BrandBlendError("; ".join(hits))


# Built by concatenation so the banned literals never appear in this file.
BANNED_PHRASES = (
    "qualified" + " appointment",
    "shows" + " up",
    "10-25" + " leads/month",
    "10–25" + " leads/month",
)


def find_banned_phrases(text: str) -> list[str]:
    low = text.lower()
    return [f"banned phrase {p!r}" for p in BANNED_PHRASES if p.lower() in low]


def assert_no_banned_phrases(text: str) -> None:
    hits = find_banned_phrases(text)
    if hits:
        raise BannedPhraseError("; ".join(hits))


# ---------------------------------------------------------------------------
# Unverified claims, guarantee/scarcity
# ---------------------------------------------------------------------------
_CLAIM_PATTERNS = [
    (r"\b\d[\d,.]*\s?\+?\s*(?:five-star\s+|5-star\s+|positive\s+)?(?:reviews|ratings|clients|customers|contractors|homeowners)\b",
     "count claim"),
    (r"\b\d[\d,.]*\s?\+?\s*years?\s+(?:in\s+business|of\s+experience)\b", "years-in-business claim"),
    (r"\b\d(?:\.\d)?\s?(?:stars?|/\s?5|out\s+of\s+5)\b", "rating claim"),
    (r"\b\d+\s?%\s*(?:more|increase|growth|roi|boost|higher|lift)\b", "percentage result claim"),
    (r"\broi\s+of\b|\breturn\s+on\s+ad\s+spend\s+of\b", "ROI claim"),
    (r"\b\d+\s?x\s+(?:more|roi|return|leads|growth|revenue)\b", "multiplier result claim"),
    (r"\b(?:our|my)\s+clients?\s+(?:saw|got|booked|made|grew|increased)\b", "client outcome claim"),
    (r"\bwe\s+helped\b|\bcase\s+study\s*:", "client outcome claim"),
]


def find_unverified_claims(text: str) -> list[str]:
    hits = []
    for pattern, label in _CLAIM_PATTERNS:
        for m in re.finditer(pattern, text, flags=re.I):
            hits.append(f"{label}: {m.group(0)!r}")
    return hits


def assert_no_unverified_claims(text: str) -> None:
    hits = find_unverified_claims(text)
    if hits:
        raise UnverifiedClaimError("; ".join(hits))


_AD_RISK_PATTERNS = [
    (r"\bguarantee", "guarantee"),
    (r"\brisk[-\s]free\b", "guarantee"),
    (r"\bonly\s+\d+\b|\bspots?\s+left\b|\blimited\s+(?:time|spots|availability)\b|\bact\s+now\b|\bhurry\b|"
     r"\blast\s+chance\b|\bexpires?\b|\bends\s+(?:soon|tonight|today)\b|\bremaining\s+this\b", "scarcity"),
]


def find_ad_risk(text: str) -> list[str]:
    hits = []
    for pattern, label in _AD_RISK_PATTERNS:
        for m in re.finditer(pattern, text, flags=re.I):
            hits.append(f"{label}: {m.group(0)!r}")
    return hits + find_unverified_claims(text) + find_price(text)


def assert_ad_copy_clean(text: str) -> None:
    """Ad copy: no price, guarantee, scarcity, review count or client outcome."""
    hits = find_ad_risk(text)
    if hits:
        raise UnverifiedClaimError("; ".join(hits))


def find_platform_names_in_headline(headline: str) -> list[str]:
    return [f"platform brand name {n!r} in headline" for n in ("google", "facebook", "meta", "instagram")
            if re.search(r"\b" + n + r"\b", headline, flags=re.I)]


# ---------------------------------------------------------------------------
# Secrets and IDs
# ---------------------------------------------------------------------------
_SECRET_PATTERNS = [
    (r"\bEAA[A-Za-z0-9]{20,}", "Meta access token"),
    (r"\bsk-[A-Za-z0-9_-]{16,}", "API secret key"),
    (r"\bgh[pousr]_[A-Za-z0-9]{20,}", "GitHub token"),
    (r"\bpit-[0-9a-f]{8}-[0-9a-f-]{20,}", "GHL private integration token"),
    (r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "JWT"),
    (r"\bBearer\s+[A-Za-z0-9._-]{16,}", "bearer token"),
    (r"(?<![\d.])\d{15,16}(?![\d.])", "pixel/dataset ID-shaped number"),
    (r"(?i)\b(?:password|passwd|api[_-]?key|access[_-]?token|secret)\s*[:=]\s*[\"']?[A-Za-z0-9/_+-]{12,}", "credential assignment"),
]


def find_secrets(text: str) -> list[str]:
    hits = []
    for pattern, label in _SECRET_PATTERNS:
        for m in re.finditer(pattern, text):
            hits.append(f"{label}: {m.group(0)[:12]}...")
    return hits


def find_location_id_problems(text: str) -> list[str]:
    hits = []
    if C.DISALLOWED_LOCATION_ID.lower() in text.lower():
        hits.append("unverified location ID (constants.DISALLOWED_LOCATION_ID) present")
    for m in re.finditer(re.escape(C.GHL_LOCATION_ID), text, flags=re.I):
        if m.group(0) != C.GHL_LOCATION_ID:
            hits.append(f"GHL location ID in wrong case: {m.group(0)!r}")
    return hits

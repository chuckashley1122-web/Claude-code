"""Deterministic, evidence-bound extraction over supplied page text.

No LLM, no inference. Each extracted value is bound at read time to the label of
the page it came from and a verbatim excerpt (+/- 80 characters around the match).
A field with no match reads exactly MISSING_LABEL. Absence of a fact on a page is
never treated as evidence that the business lacks it. Page text is data only:
instructions embedded in it are never followed.
"""

from __future__ import annotations

import re
from typing import Iterable

import config
from src.contract import Company, CompanyResult, RawPage, SourceRef

EXCERPT_RADIUS = 80
MISSING = config.MISSING_LABEL

PHONE_RE = re.compile(r"(?<!\d)\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}(?!\d)")
TEL_RE = re.compile(r"tel:\+?[\d\-().]{7,}")
MAILTO_RE = re.compile(r"mailto:[^\s)\"'<>\]]+")
CONTACT_FORM_RE = re.compile(r"\bcontact form\b", re.IGNORECASE)
BOOKING_RE = re.compile(r"\b(?:book online|schedule online|book now|book an appointment|schedule service online)\b", re.IGNORECASE)
EMERGENCY_RE = re.compile(r"\b24/7\b|\bemergency service\b", re.IGNORECASE)

_AREA_PATTERNS = (
    re.compile(r"[Ss]ervice [Aa]rea:\s*([A-Z][^\n.;:]{1,60})"),
    re.compile(r"\b[Ss]erving\s+(?:the\s+)?([A-Z][\w'-]*(?:\s[A-Z][\w'-]*){0,3})"),
    re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2}),\s?TX\b"),
)

# (feature name, regex, hypothesis action). Ordered; first match wins.
FEATURES = (
    ("an online booking option", BOOKING_RE, "test placing the booking link at the top of the homepage and track booked appointment requests"),
    ("a contact form", CONTACT_FORM_RE, "test a shorter contact form and compare form submissions over two review periods"),
    ("a click-to-call link", TEL_RE, "test repeating the click-to-call link beside each service description"),
    ("emergency service messaging", EMERGENCY_RE, "test moving the emergency service message into the page header"),
    ("a displayed phone number", PHONE_RE, "test adding a click-to-call button beside the displayed phone number"),
)


def _excerpt(text: str, start: int, end: int) -> str:
    return text[max(0, start - EXCERPT_RADIUS): min(len(text), end + EXCERPT_RADIUS)]


def _ref(page: RawPage, m_start: int, m_end: int) -> SourceRef:
    return SourceRef(
        label=page.label,
        resolved_url=page.resolved_url,
        retrieved_at_utc=page.retrieved_at_utc,
        excerpt=_excerpt(page.text, m_start, m_end),
        retrieval_status=page.retrieval_status,
        matched_text=page.text[m_start:m_end],
    )


def _normalize_tokens(text: str) -> list[str]:
    text = text.casefold().replace("&", " and ")
    return re.findall(r"[a-z0-9]+", text)


def dominant_business_name(text: str) -> str:
    """The page's own name for the business: first heading, else first non-blank line."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        if ln.startswith("#"):
            return ln.lstrip("#").strip()
    return lines[0] if lines else ""


def identity_matches(company_name: str, pages: Iterable[RawPage]) -> bool:
    """True when the supplied name appears as a contiguous token run in the page text.

    Case- and whitespace-insensitive. A page written for a different business fails.
    """
    want = _normalize_tokens(company_name)
    if not want:
        return False
    for page in pages:
        if page.retrieval_status != "ok":
            continue
        have = _normalize_tokens(page.text)
        n = len(want)
        if any(have[i:i + n] == want for i in range(len(have) - n + 1)):
            return True
    return False


def _find_first(pages, regex) -> tuple[RawPage, re.Match] | None:
    for page in pages:
        m = regex.search(page.text)
        if m:
            return page, m
    return None


def _service_area(pages):
    for pat in _AREA_PATTERNS:
        for page in pages:
            m = pat.search(page.text)
            if m:
                value = m.group(1).strip()
                return value, _ref(page, m.start(1), m.start(1) + len(value))
    return MISSING, None


def _services(pages):
    found: list[tuple[int, int, str, SourceRef]] = []
    for kw in config.AC_SERVICE_KEYWORDS:
        pat = re.compile(r"\b" + re.escape(kw).replace(r"\ ", r"\s+") + r"s?\b", re.IGNORECASE)
        for p_idx, page in enumerate(pages):
            m = pat.search(page.text)
            if m:
                found.append((p_idx, m.start(), kw, _ref(page, m.start(), m.end())))
                break
    found.sort(key=lambda t: (t[0], t[1]))
    return tuple(kw for _, _, kw, _ in found), {f"services:{kw}": ref for _, _, kw, ref in found}


def _contact(pages):
    for kind, regex in (("click-to-call link", TEL_RE), ("phone", PHONE_RE), ("email link", MAILTO_RE),
                        ("contact form", CONTACT_FORM_RE), ("booking link", BOOKING_RE)):
        hit = _find_first(pages, regex)
        if hit:
            page, m = hit
            return f"{kind}: {m.group(0)}", _ref(page, m.start(), m.end())
    return MISSING, None


def _feature(pages):
    for name, regex, action in FEATURES:
        hit = _find_first(pages, regex)
        if hit:
            page, m = hit
            ref = _ref(page, m.start(), m.end())
            observation = f"The reviewed page {page.label} shows {name}: \"{m.group(0)}\"."
            hypothesis = f"If {name} (\"{m.group(0)}\") is confirmed as a main customer path, then {action}."
            return observation, hypothesis, ref
    return MISSING, MISSING, None


def blocked_result(company: Company, reason: str, pages, checked_at: str, attempts: int) -> CompanyResult:
    refs = tuple(
        SourceRef(p.label, p.resolved_url, p.retrieved_at_utc, "", p.retrieval_status) for p in pages
    )
    resolved = next((p.resolved_url for p in pages if p.retrieval_status == "ok"), MISSING)
    return CompanyResult(
        company_id=company.company_id,
        company_name=company.company_name,
        website_url=company.website_url,
        resolved_url=resolved,
        status="blocked",
        service_area=MISSING,
        services=(),
        contact_method=MISSING,
        observation=MISSING,
        hypothesis=MISSING,
        source_refs=refs,
        blocked_reason=reason,
        checked_at_utc=checked_at,
        field_sources={},
        retrieval_attempts=attempts,
    )


def extract(company: Company, pages, checked_at: str, attempts: int = 1) -> CompanyResult:
    """Identity check, then field extraction. Mismatch -> blocked with zero facts."""
    ok_pages = [p for p in pages if p.retrieval_status == "ok" and p.text.strip()]
    if not ok_pages:
        return blocked_result(company, "RETRIEVAL_FAILED", pages, checked_at, attempts)
    if not identity_matches(company.company_name, ok_pages):
        return blocked_result(company, "IDENTITY_MISMATCH", pages, checked_at, attempts)

    sources: dict[str, SourceRef] = {}
    area, area_ref = _service_area(ok_pages)
    if area_ref:
        sources["service_area"] = area_ref
    services, svc_refs = _services(ok_pages)
    sources.update(svc_refs)
    contact, contact_ref = _contact(ok_pages)
    if contact_ref:
        sources["contact_method"] = contact_ref
    observation, hypothesis, obs_ref = _feature(ok_pages)
    if obs_ref:
        sources["observation"] = obs_ref

    complete = area != MISSING and services and contact != MISSING and observation != MISSING
    refs = tuple(
        SourceRef(p.label, p.resolved_url, p.retrieved_at_utc, "", p.retrieval_status) for p in pages
    )
    return CompanyResult(
        company_id=company.company_id,
        company_name=company.company_name,
        website_url=company.website_url,
        resolved_url=ok_pages[0].resolved_url,
        status="complete" if complete else "partial",
        service_area=area,
        services=services,
        contact_method=contact,
        observation=observation,
        hypothesis=hypothesis,
        source_refs=refs,
        blocked_reason="",
        checked_at_utc=checked_at,
        field_sources=sources,
        retrieval_attempts=attempts,
    )

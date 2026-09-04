"""Enrich a lead from the prospect's OWN website.

Two layers, cheapest first:

1. `detect_signals` — Scrapling fetches the homepage and a couple of common
   sub-pages, then pattern-matches for buying signals. No LLM, no cost.
2. `llm_extract` — Scrapegraph-ai runs an LLM over the page to pull the things
   patterns cannot reliably get: a named decision-maker, a direct email, what
   the business actually sells. Opt-in, because it costs tokens.

A company's own public website is the one place where fetching is
uncontroversial: it exists to be read, and robots.txt is respected below.
"""

from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import urljoin

from .browser import fetch
from .models import Lead

# --- signal patterns -------------------------------------------------------

_ADS = re.compile(r"googletagmanager|gtag\(|fbq\(|facebook\.net/.*fbevents|adroll|taboola", re.I)
_AUTOMATION = re.compile(r"hubspot|marketo|pardot|klaviyo|activecampaign|mailchimp|braze", re.I)
_AGENCY = re.compile(
    r"\b(marketing agency|digital agency|seo agency|ad agency|we help brands|growth agency)\b", re.I
)
_LENDER = re.compile(
    r"\b(we lend|our loan products|apply for a loan|lending solutions|we are a lender)\b", re.I
)
_HIRING_MKT = re.compile(r"\b(marketing (manager|director|coordinator|specialist)|growth lead)\b", re.I)
_HIRING_GROWTH = re.compile(r"\b(now hiring|we[' ]re hiring|join our team|careers)\b", re.I)
_EQUIPMENT = re.compile(r"\b(fleet|excavat|forklift|cnc|machining|refrigerat|trucking|logistics)\b", re.I)
_MULTI_LOC = re.compile(r"\b(our locations|all locations|find a location|\d+\s+locations)\b", re.I)
_CRE = re.compile(r"\b(new location|now open|expanding to|second location|grand opening)\b", re.I)
_YEAR = re.compile(r"(?:©|copyright)\s*(?:\d{4}\s*[-–]\s*)?(\d{4})", re.I)
_SOCIAL = re.compile(r"(facebook|instagram|linkedin|twitter|x)\.com/", re.I)
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")

_SUBPAGES = ("", "/about", "/contact", "/careers", "/blog", "/locations")

# Addresses that are never a person you can call.
_JUNK_EMAIL = re.compile(r"^(no-?reply|donotreply|postmaster|abuse|privacy|webmaster)@", re.I)


def _text_of(url: str, stealthy: bool = False) -> tuple[str, str]:
    """Return (visible_text, raw_html) or ('','') if the page will not load."""
    try:
        page = fetch(url, stealthy=stealthy, timeout=25000)
    except Exception:  # noqa: BLE001 — a dead prospect site is normal, not fatal
        return "", ""
    if getattr(page, "status", 200) >= 400:
        return "", ""
    html = getattr(page, "html_content", "") or str(page)
    try:
        text = page.get_all_text(ignore_tags=("script", "style"))
    except Exception:  # noqa: BLE001
        text = re.sub(r"<[^>]+>", " ", html)
    return text, html


def crawl_site(domain: str, stealthy: bool = False, max_pages: int = 4) -> tuple[str, str]:
    """Concatenate a few key pages so one regex pass sees the whole picture."""
    if not domain:
        return "", ""
    base = f"https://{domain}"
    texts, htmls = [], []
    for path in _SUBPAGES[:max_pages]:
        text, html = _text_of(urljoin(base, path), stealthy=stealthy)
        if text:
            texts.append(text)
            htmls.append(html)
    return "\n".join(texts), "\n".join(htmls)


def detect_signals(lead: Lead, stealthy: bool = False) -> Lead:
    """Fill lead.signals (and any contact details found in the clear)."""
    domain = lead.company_domain
    if not domain:
        return lead

    text, html = crawl_site(domain, stealthy=stealthy)
    if not text:
        lead.notes = (lead.notes + " | site unreachable").strip(" |")
        return lead

    blob = f"{text}\n{html}"
    has_blog = "/blog" in html or re.search(r"\b(latest posts|recent articles)\b", text, re.I)
    last_year = max((int(y) for y in _YEAR.findall(html)), default=0)

    lead.signals.update({
        # ca-jenterprises signals
        "running_ads": bool(_ADS.search(html)),
        "no_marketing_automation": not bool(_AUTOMATION.search(html)),
        "has_blog_but_stale": bool(has_blog and last_year and last_year < 2025),
        "hiring_marketing_role": bool(_HIRING_MKT.search(blob)),
        "thin_seo": not bool(re.search(r'<meta[^>]+name=["\']description', html, re.I)),
        "no_social_links": not bool(_SOCIAL.search(html)),
        "dated_site": bool(last_year and last_year <= 2022),
        "is_marketing_agency": bool(_AGENCY.search(text)),
        "enterprise_scale": bool(lead.employee_count and lead.employee_count > 1000),
        # ca-jconsulting signals
        "hiring_growth_roles": bool(_HIRING_GROWTH.search(blob)),
        "equipment_heavy": bool(_EQUIPMENT.search(text)),
        "multi_location": bool(_MULTI_LOC.search(text)),
        "recent_cre_activity": bool(_CRE.search(text)),
        "is_lender_competitor": bool(_LENDER.search(text)),
    })

    if not lead.email:
        for candidate in _EMAIL.findall(text):
            if not _JUNK_EMAIL.match(candidate) and domain.split(".")[0] in candidate.lower():
                lead.email = candidate
                break
    if not lead.phone and (m := _PHONE.search(text)):
        lead.phone = m.group(0)
    if not lead.website:
        lead.website = f"https://{domain}"
    return lead


# --- LLM layer -------------------------------------------------------------

_PROMPT = (
    "From this company website extract: the business's primary service in one "
    "sentence; the owner's or the most senior named decision-maker's full name "
    "and job title if stated; the best direct contact email; the best phone "
    "number; the city and state; and any sign the business is growing (hiring, "
    "new locations, expansion, funding). Use null for anything not stated on "
    "the page. Never guess an email address."
)


def llm_extract(lead: Lead, model: str | None = None) -> Lead:
    """Run Scrapegraph-ai over the prospect's site for details regex misses."""
    if not lead.company_domain:
        return lead

    from scrapegraphai.graphs import SmartScraperGraph

    model = model or os.getenv("LEADGEN_LLM_MODEL", "openai/gpt-4o-mini")
    config: dict[str, Any] = {"llm": {"model": model}, "verbose": False, "headless": True}
    if model.startswith("openai/"):
        config["llm"]["api_key"] = os.getenv("OPENAI_API_KEY", "")

    try:
        result = SmartScraperGraph(
            prompt=_PROMPT, source=f"https://{lead.company_domain}", config=config
        ).run()
    except Exception as exc:  # noqa: BLE001 — enrichment is best-effort
        lead.notes = (lead.notes + f" | llm_extract failed: {exc}").strip(" |")
        return lead

    if not isinstance(result, dict):
        return lead

    def take(*keys: str) -> str:
        for key in keys:
            value = result.get(key)
            if value and str(value).lower() not in {"null", "none", "n/a"}:
                return str(value).strip()
        return ""

    lead.email = lead.email or take("email", "contact_email", "best_direct_contact_email")
    lead.phone = lead.phone or take("phone", "phone_number", "best_phone_number")
    lead.title = lead.title or take("job_title", "title")
    lead.location = lead.location or take("city_and_state", "location", "city")
    summary = take("primary_service", "service", "business_summary")
    growth = take("growth_signs", "growth", "signs_of_growth")
    if not lead.full_name and (name := take("decision_maker_name", "owner_name", "full_name")):
        parts = name.split()
        lead.first_name, lead.last_name = parts[0], " ".join(parts[1:])
    extra = " | ".join(x for x in (summary, growth) if x)
    if extra:
        lead.notes = (lead.notes + " | " + extra).strip(" |")
    if growth:
        lead.signals["hiring_growth_roles"] = True
    lead.raw["llm"] = result
    return lead

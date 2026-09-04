"""ICP fit scoring.

Score = title match + headcount fit + signal weights from the brand's YAML.
Everything is explainable: `explain()` says exactly why a lead scored what it
did, so a bad list can be diagnosed instead of re-run blindly.
"""

from __future__ import annotations

from typing import Any

from .models import Lead

TITLE_POINTS = 20
HEADCOUNT_POINTS = 10
INDUSTRY_POINTS = 10
CONTACTABLE_POINTS = 8


def _title_hit(title: str, wanted: list[str], excluded: list[str]) -> bool:
    low = title.lower()
    if any(x.lower() in low for x in excluded):
        return False
    return any(x.lower() in low for x in wanted)


def score_lead(lead: Lead, config: dict[str, Any]) -> Lead:
    icp = config.get("icp", {})
    signals = config.get("signals", {})
    thresholds = config.get("thresholds", {"hot": 45, "warm": 25})

    total = 0
    if _title_hit(lead.title, icp.get("titles", []), icp.get("exclude_titles", [])):
        total += TITLE_POINTS

    lo, hi = icp.get("employee_range", [0, 10**9])
    if lead.employee_count is not None and lo <= lead.employee_count <= hi:
        total += HEADCOUNT_POINTS

    if lead.industry and any(
        i.lower() in lead.industry.lower() for i in icp.get("industries", [])
    ):
        total += INDUSTRY_POINTS

    # A lead you cannot reach is not a lead.
    if lead.email or lead.phone:
        total += CONTACTABLE_POINTS

    for bucket in ("positive", "negative"):
        for key, spec in (signals.get(bucket) or {}).items():
            if lead.signals.get(key):
                total += int(spec.get("weight", 0))

    lead.score = total
    lead.tier = (
        "hot" if total >= thresholds["hot"]
        else "warm" if total >= thresholds["warm"]
        else "cold"
    )
    return lead


def explain(lead: Lead, config: dict[str, Any]) -> list[str]:
    """Human-readable breakdown of a lead's score."""
    icp = config.get("icp", {})
    signals = config.get("signals", {})
    lines: list[str] = []

    if _title_hit(lead.title, icp.get("titles", []), icp.get("exclude_titles", [])):
        lines.append(f"+{TITLE_POINTS} title matches ICP ({lead.title})")
    lo, hi = icp.get("employee_range", [0, 10**9])
    if lead.employee_count is not None and lo <= lead.employee_count <= hi:
        lines.append(f"+{HEADCOUNT_POINTS} headcount {lead.employee_count} in [{lo},{hi}]")
    if lead.industry and any(i.lower() in lead.industry.lower() for i in icp.get("industries", [])):
        lines.append(f"+{INDUSTRY_POINTS} industry {lead.industry}")
    if lead.email or lead.phone:
        lines.append(f"+{CONTACTABLE_POINTS} reachable")

    for bucket in ("positive", "negative"):
        for key, spec in (signals.get(bucket) or {}).items():
            if lead.signals.get(key):
                weight = int(spec.get("weight", 0))
                lines.append(f"{weight:+d} {key} — {spec.get('why', '')}")

    lines.append(f"= {lead.score} ({lead.tier})")
    return lines


def dedupe(leads: list[Lead]) -> list[Lead]:
    """Collapse duplicates, keeping the record with the most filled-in fields."""
    best: dict[str, Lead] = {}
    for lead in leads:
        key = lead.dedupe_key()
        incumbent = best.get(key)
        if incumbent is None or _filled(lead) > _filled(incumbent):
            best[key] = lead
    return list(best.values())


def _filled(lead: Lead) -> int:
    return sum(
        1
        for value in (
            lead.first_name, lead.last_name, lead.title, lead.company,
            lead.company_domain, lead.email, lead.phone, lead.linkedin_url,
            lead.industry, lead.location,
        )
        if value
    ) + (1 if lead.employee_count else 0)

"""Your own LinkedIn / Sales Navigator export.

This is the source with zero legal ambiguity: you ran the search inside
LinkedIn under your own seat and exported the result LinkedIn handed you.
Nothing here touches LinkedIn's servers — it reads a file off your disk.

Sales Navigator: Lead list -> ... -> Export to CSV (Advanced Plus seats), or
"Save to list" and export via your CRM connector. Column names differ between
LinkedIn products and CRM re-exports, so the header mapping is fuzzy.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from ..models import Lead, normalize_domain
from .base import Source, SourceError

# Every spelling we have seen, lowercased, mapped to our field.
_ALIASES: dict[str, str] = {
    "first name": "first_name", "firstname": "first_name", "given name": "first_name",
    "last name": "last_name", "lastname": "last_name", "surname": "last_name",
    "full name": "_full_name", "name": "_full_name",
    "title": "title", "job title": "title", "position": "title", "current title": "title",
    "company": "company", "company name": "company", "account name": "company",
    "current company": "company", "organization": "company",
    "website": "website", "company website": "website", "company domain": "company_domain",
    "domain": "company_domain",
    "industry": "industry",
    "employees": "employee_count", "company size": "employee_count",
    "headcount": "employee_count", "employee count": "employee_count",
    "location": "location", "geography": "location", "company location": "location",
    "email": "email", "email address": "email", "work email": "email",
    "phone": "phone", "phone number": "phone", "mobile": "phone", "direct phone": "phone",
    "linkedin": "linkedin_url", "linkedin url": "linkedin_url",
    "profile url": "linkedin_url", "person linkedin url": "linkedin_url",
}


def _to_int(value: str) -> int | None:
    """'51-200 employees' -> 51. Ranges collapse to their low end."""
    digits = ""
    for ch in value:
        if ch.isdigit():
            digits += ch
        elif digits:
            break
    return int(digits) if digits else None


class SalesNavigatorCSVSource(Source):
    name = "sales-nav-csv"
    linkedin_data = True

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def available(self) -> tuple[bool, str]:
        if not self.path.exists():
            return False, f"CSV not found: {self.path}"
        return True, f"ready ({self.path.name})"

    def search(self, icp: dict[str, Any], limit: int = 100000) -> list[Lead]:
        ok, why = self.available()
        if not ok:
            raise SourceError(why)

        leads: list[Lead] = []
        with self.path.open(newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                lead = self._to_lead(row)
                if lead.full_name or lead.company:
                    leads.append(lead)
                if len(leads) >= limit:
                    break
        return leads

    def _to_lead(self, row: dict[str, str]) -> Lead:
        mapped: dict[str, Any] = {}
        for header, value in row.items():
            field = _ALIASES.get((header or "").strip().lower())
            if field and (value or "").strip():
                mapped[field] = value.strip()

        full = mapped.pop("_full_name", "")
        if full and "first_name" not in mapped:
            parts = full.split()
            mapped["first_name"] = parts[0]
            mapped["last_name"] = " ".join(parts[1:])

        if "employee_count" in mapped:
            mapped["employee_count"] = _to_int(str(mapped["employee_count"]))
        if "company_domain" not in mapped and mapped.get("website"):
            mapped["company_domain"] = normalize_domain(mapped["website"])
        elif "company_domain" in mapped:
            mapped["company_domain"] = normalize_domain(mapped["company_domain"])

        return Lead(
            source="sales-nav-csv",
            source_ref=self.path.name,
            raw=dict(row),
            **mapped,
        )

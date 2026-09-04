"""NMLS Consumer Access — the public mortgage licensing registry.

Purpose-built for ca-jconsulting: every licensed loan originator, mortgage
broker and lending company in the US is listed here by federal mandate under
the SAFE Act. It is an official public registry, published *so that* it can be
looked up, and it carries the one field LinkedIn will never give you — a
verified NMLS ID and licence status.

Best used to build a referral-partner list (loan officers, brokers) and to
verify anyone you are about to co-broker with.

Note: NMLS publishes no free REST API. This drives the public site with
Scrapling's stealth fetcher and parses the rendered result, so it is
best-effort and will need selector updates when the site changes. For volume
or SLA, CSBS sells an official B2B subscription feed — see
https://mortgage.nationwidelicensingsystem.org.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ..browser import fetch
from ..models import Lead
from .base import Source, SourceError

SEARCH_URL = "https://www.nmlsconsumeraccess.org/EntityDetails.aspx"
BASE = "https://www.nmlsconsumeraccess.org"


class NMLSSource(Source):
    name = "nmls"
    linkedin_data = False

    def __init__(self, state: str = "", entity_type: str = "individual"):
        self.state = state.upper()
        self.entity_type = entity_type

    def available(self) -> tuple[bool, str]:
        return True, "ready (public registry; no key required)"

    def search(self, icp: dict[str, Any], limit: int = 100) -> list[Lead]:
        """Search by the ICP's locations. Falls back to a plain name search."""
        states = [self.state] if self.state else _states_from(icp.get("locations", []))
        leads: list[Lead] = []
        for state in states or [""]:
            leads.extend(self._search_state(state, limit - len(leads)))
            if len(leads) >= limit:
                break
        return leads[:limit]

    def _search_state(self, state: str, limit: int) -> list[Lead]:
        url = f"{BASE}/Home/Search?searchText=&state={state}&type={self.entity_type}"
        try:
            page = fetch(url, stealthy=True, timeout=45000)
        except Exception as exc:  # noqa: BLE001 - surface as a source error
            raise SourceError(f"NMLS fetch failed: {exc}") from exc

        if getattr(page, "status", 200) >= 400:
            raise SourceError(f"NMLS returned HTTP {page.status}")

        records = self._extract(page)
        return [self._to_lead(r, state) for r in records[:limit]]

    @staticmethod
    def _extract(page) -> list[dict[str, Any]]:
        """The results grid is JSON embedded in the page; fall back to rows."""
        html = page.html_content if hasattr(page, "html_content") else str(page)
        for match in re.finditer(r'(\{"[Rr]esults?"\s*:\s*\[.*?\]\s*\})', html, re.S):
            try:
                blob = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            rows = blob.get("results") or blob.get("Results") or []
            if rows:
                return rows

        out: list[dict[str, Any]] = []
        for row in page.css("table tr, .search-result-row"):
            cells = [c.clean() for c in row.css("td::text, .result-field::text")]
            if len(cells) >= 2:
                out.append({"name": cells[0], "nmls_id": cells[1],
                            "company": cells[2] if len(cells) > 2 else ""})
        return out

    @staticmethod
    def _to_lead(rec: dict[str, Any], state: str) -> Lead:
        name = str(rec.get("name") or rec.get("Name") or "").strip()
        parts = name.split()
        nmls_id = str(rec.get("nmls_id") or rec.get("NMLSID") or rec.get("id") or "")
        return Lead(
            first_name=parts[0] if parts else "",
            last_name=" ".join(parts[1:]) if len(parts) > 1 else "",
            title="Mortgage Loan Originator",
            company=str(rec.get("company") or rec.get("EmployerName") or ""),
            industry="Real Estate",
            location=state,
            source="nmls",
            source_ref=nmls_id,
            signals={"nmls_licensed": True},
            notes=f"NMLS ID {nmls_id}" if nmls_id else "",
            raw=rec,
        )


_STATE_CODES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV", "wisconsin": "WI",
    "wyoming": "WY",
}


def _states_from(locations: list[str]) -> list[str]:
    out: list[str] = []
    for loc in locations:
        low = loc.lower().strip()
        if low in _STATE_CODES:
            out.append(_STATE_CODES[low])
        elif len(loc) == 2 and loc.isalpha():
            out.append(loc.upper())
    return out

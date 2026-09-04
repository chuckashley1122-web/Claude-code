"""Apollo.io — licensed B2B contact data.

Apollo maintains its own contact database and licenses it to subscribers, so
this is the workhorse source: you get LinkedIn-shaped firmographics (title,
company, headcount, profile URL) without touching LinkedIn yourself.

Docs: https://docs.apollo.io/reference/people-search
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from ..models import Lead, normalize_domain
from .base import Source, SourceError

SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/search"
ENRICH_URL = "https://api.apollo.io/api/v1/people/match"

# Apollo wants headcount as "min,max" bucket strings rather than a raw range.
_BUCKETS = ["1,10", "11,20", "21,50", "51,100", "101,200", "201,500", "501,1000"]


def _buckets_for(lo: int, hi: int) -> list[str]:
    out = []
    for bucket in _BUCKETS:
        b_lo, b_hi = (int(x) for x in bucket.split(","))
        if b_hi >= lo and b_lo <= hi:
            out.append(bucket)
    return out or ["1,10"]


class ApolloSource(Source):
    name = "apollo"
    linkedin_data = True

    def __init__(self, api_key: str | None = None, reveal_contacts: bool = False):
        self.api_key = api_key or os.getenv("APOLLO_API_KEY", "")
        # Revealing emails/phones burns Apollo credits, so it is opt-in.
        self.reveal_contacts = reveal_contacts

    def available(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, "APOLLO_API_KEY not set — get one at https://developer.apollo.io"
        return True, "ready"

    def _headers(self) -> dict[str, str]:
        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def search(self, icp: dict[str, Any], limit: int = 100) -> list[Lead]:
        ok, why = self.available()
        if not ok:
            raise SourceError(why)

        lo, hi = icp.get("employee_range", [1, 1000])
        payload: dict[str, Any] = {
            "person_titles": icp.get("titles", []),
            "person_locations": icp.get("locations", []),
            "organization_num_employees_ranges": _buckets_for(lo, hi),
            "per_page": min(100, limit),
            "page": 1,
        }
        if icp.get("industries"):
            payload["q_organization_keyword_tags"] = icp["industries"]

        leads: list[Lead] = []
        with httpx.Client(timeout=60) as client:
            while len(leads) < limit:
                resp = client.post(SEARCH_URL, headers=self._headers(), json=payload)
                if resp.status_code == 429:
                    time.sleep(60)
                    continue
                if resp.status_code >= 400:
                    raise SourceError(f"Apollo {resp.status_code}: {resp.text[:300]}")
                body = resp.json()
                people = body.get("people") or body.get("contacts") or []
                if not people:
                    break
                leads.extend(self._to_lead(p) for p in people)
                if len(people) < payload["per_page"]:
                    break
                payload["page"] += 1
                time.sleep(1)  # ~1 req/s keeps us clear of Apollo's throttle

            leads = leads[:limit]
            if self.reveal_contacts:
                for lead in leads:
                    self._reveal(client, lead)
        return leads

    def _reveal(self, client: httpx.Client, lead: Lead) -> None:
        """Spend a credit to unlock a verified email/phone for one person."""
        if not lead.raw.get("id"):
            return
        try:
            resp = client.post(
                ENRICH_URL,
                headers=self._headers(),
                json={
                    "id": lead.raw["id"],
                    "reveal_personal_emails": True,
                    "reveal_phone_number": True,
                },
            )
            if resp.status_code >= 400:
                return
            person = resp.json().get("person") or {}
        except httpx.HTTPError:
            return
        lead.email = lead.email or person.get("email") or ""
        phones = person.get("phone_numbers") or []
        if phones and not lead.phone:
            lead.phone = phones[0].get("sanitized_number") or phones[0].get("raw_number") or ""

    @staticmethod
    def _to_lead(person: dict[str, Any]) -> Lead:
        org = person.get("organization") or person.get("account") or {}
        # Apollo masks unrevealed addresses as "email_not_unlocked@domain.com".
        email = person.get("email") or ""
        if "email_not_unlocked" in email:
            email = ""
        location = ", ".join(
            x for x in (person.get("city"), person.get("state"), person.get("country")) if x
        )
        return Lead(
            first_name=person.get("first_name") or "",
            last_name=person.get("last_name") or "",
            title=person.get("title") or "",
            company=org.get("name") or "",
            company_domain=normalize_domain(org.get("primary_domain") or org.get("website_url")),
            industry=org.get("industry") or "",
            employee_count=org.get("estimated_num_employees"),
            location=location,
            email=email,
            phone=person.get("sanitized_phone") or org.get("primary_phone", {}).get("number", "") or "",
            linkedin_url=person.get("linkedin_url") or "",
            website=org.get("website_url") or "",
            source="apollo",
            source_ref=person.get("id") or "",
            raw=person,
        )

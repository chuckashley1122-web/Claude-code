"""Bright Data — LinkedIn public-profile dataset API.

Bright Data collects public LinkedIn profile data as a licensed dataset and
serves it over an async trigger/poll/snapshot API. You hand it profile URLs or
a filter; it hands back structured records. Your account never touches
LinkedIn, and no LinkedIn login is involved.

Docs: https://docs.brightdata.com/scraping-automation/web-scraper-api
Default dataset: LinkedIn People Profiles (gd_l1viktl72bvl7bjuj0)
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from ..models import Lead, normalize_domain
from .base import Source, SourceError

TRIGGER_URL = "https://api.brightdata.com/datasets/v3/trigger"
PROGRESS_URL = "https://api.brightdata.com/datasets/v3/progress"
SNAPSHOT_URL = "https://api.brightdata.com/datasets/v3/snapshot"
DEFAULT_DATASET = "gd_l1viktl72bvl7bjuj0"


class BrightDataSource(Source):
    name = "brightdata"
    linkedin_data = True

    def __init__(self, api_key: str | None = None, dataset_id: str | None = None):
        self.api_key = api_key or os.getenv("BRIGHTDATA_API_KEY", "")
        self.dataset_id = (
            dataset_id or os.getenv("BRIGHTDATA_LINKEDIN_DATASET_ID") or DEFAULT_DATASET
        )

    def available(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, "BRIGHTDATA_API_KEY not set — https://brightdata.com/cp/api_tokens"
        return True, "ready"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def search(self, icp: dict[str, Any], limit: int = 100) -> list[Lead]:
        """ICP-filter search. Bright Data's discovery mode takes keyword filters."""
        inputs = [
            {"first_name": "", "last_name": "", "keyword": title, "location": loc}
            for title in icp.get("titles", [])[:10]
            for loc in (icp.get("locations") or [""])[:3]
        ]
        return self.collect(inputs, limit=limit, discover_by="keyword")

    def collect(
        self,
        inputs: list[dict[str, Any]],
        limit: int = 100,
        discover_by: str | None = None,
        poll_seconds: int = 10,
        timeout_seconds: int = 900,
    ) -> list[Lead]:
        """Trigger a collection, poll until ready, download the snapshot."""
        ok, why = self.available()
        if not ok:
            raise SourceError(why)

        params: dict[str, Any] = {"dataset_id": self.dataset_id, "format": "json"}
        if discover_by:
            params["type"] = "discover_new"
            params["discover_by"] = discover_by
            params["limit_per_input"] = max(1, limit // max(1, len(inputs)))

        with httpx.Client(timeout=120) as client:
            resp = client.post(TRIGGER_URL, headers=self._headers(), params=params, json=inputs)
            if resp.status_code >= 400:
                raise SourceError(f"Bright Data trigger {resp.status_code}: {resp.text[:300]}")
            snapshot_id = resp.json().get("snapshot_id")
            if not snapshot_id:
                raise SourceError(f"no snapshot_id in trigger response: {resp.text[:300]}")

            deadline = time.time() + timeout_seconds
            while time.time() < deadline:
                prog = client.get(f"{PROGRESS_URL}/{snapshot_id}", headers=self._headers())
                status = prog.json().get("status") if prog.status_code < 400 else None
                if status == "ready":
                    break
                if status == "failed":
                    raise SourceError(f"Bright Data job {snapshot_id} failed")
                time.sleep(poll_seconds)
            else:
                raise SourceError(f"Bright Data job {snapshot_id} timed out after {timeout_seconds}s")

            data = client.get(
                f"{SNAPSHOT_URL}/{snapshot_id}", headers=self._headers(), params={"format": "json"}
            )
            if data.status_code >= 400:
                raise SourceError(f"Bright Data snapshot {data.status_code}: {data.text[:300]}")
            records = data.json()

        if isinstance(records, dict):
            records = records.get("data", [])
        return [self._to_lead(r) for r in records[:limit]]

    @staticmethod
    def _to_lead(rec: dict[str, Any]) -> Lead:
        # Field names vary a little across Bright Data's LinkedIn datasets, so
        # read each value from the first key that is actually present.
        def pick(*keys: str) -> str:
            for key in keys:
                if rec.get(key):
                    return str(rec[key])
            return ""

        name = pick("name", "full_name")
        first = pick("first_name") or (name.split(" ")[0] if name else "")
        last = pick("last_name") or (" ".join(name.split(" ")[1:]) if " " in name else "")

        experience = rec.get("current_company") or {}
        if not isinstance(experience, dict):
            experience = {}

        return Lead(
            first_name=first,
            last_name=last,
            title=pick("position", "title", "current_position"),
            company=experience.get("name") or pick("current_company_name", "company"),
            company_domain=normalize_domain(
                experience.get("website") or pick("current_company_website", "company_website")
            ),
            industry=pick("industry"),
            location=pick("location", "city", "country_code"),
            email=pick("email"),
            linkedin_url=pick("url", "input_url", "profile_url", "linkedin_url"),
            source="brightdata",
            source_ref=pick("id", "linkedin_id"),
            raw=rec,
        )

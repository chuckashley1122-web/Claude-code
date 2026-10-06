"""Apify interface: serves fixture datasets instead of running scraping actors.

Actor ids come from the source (line 32, line 44) and are unverified. Apollo
scraping is deliberately NOT approved (spec section 8, item 6): requesting it
raises :class:`ActorNotApproved` even in dry run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from adapters.base import LiveAdapter, MockAdapter, load_json_fixture


class ActorNotApproved(PermissionError):
    pass


NOT_APPROVED = {"apollo-io-scraper": "Apollo scraping carries an unresolved terms-of-service and legality question."}


class ApifyClient(Protocol):
    def run_actor(self, actor_id: str, actor_input: dict) -> list[dict]: ...


@dataclass
class MockApify(MockAdapter):
    service: str = "apify"

    def run_actor(self, actor_id: str, actor_input: dict) -> list[dict]:
        if actor_id in NOT_APPROVED:
            raise ActorNotApproved(f"{actor_id}: {NOT_APPROVED[actor_id]} Human/legal approval required.")
        self._guard("run_actor", actor_id=actor_id)
        if actor_id == "google-maps-scraper":
            leads = load_json_fixture("leads.sample.json", self.fixtures_dir)["leads"]
            niche = (actor_input.get("niche") or "").lower()
            matched = [dict(l) for l in leads if niche and niche in l["niche"].lower()]
            return matched or [dict(l) for l in leads]
        if actor_id == "tiktok-scraper":
            url = actor_input.get("url")
            ads = load_json_fixture("ad_transcript.sample.json", self.fixtures_dir)["ads"]
            found = [dict(a) for a in ads if a["ad_url"] == url]
            if not found:
                raise LookupError(f"no fixture ad for {url!r}")
            return found
        raise LookupError(f"no fixture dataset for actor {actor_id!r}")


class LiveApify(LiveAdapter):
    service = "apify"
    credential_env = ("APIFY_TOKEN",)

    def run_actor(self, actor_id: str, actor_input: dict) -> list[dict]:
        self._refuse("run_actor")

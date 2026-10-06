"""Publisher interface (Ayrshare / Blotato, Slack, chat widget, call transfer
stand-in): records intended posts and messages to data/out/publish and
publishes nothing.

Public-facing text (social posts, chat replies) passes the pricing and claim
guards before it is even recorded.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional, Protocol

from adapters.base import LiveAdapter, MockAdapter, stable_id
from guardrails import claim_guard, pricing_guard

PLATFORMS = {"tiktok", "instagram", "youtube", "linkedin", "x"}
NOT_PUBLISHED = "not_published_dry_run"


class PublisherClient(Protocol):
    def post(self, platforms: list[str], text: str, media_ref: Optional[str]) -> dict: ...
    def analytics(self, post_id: str) -> dict: ...
    def notify(self, channel: str, text: str) -> dict: ...
    def reply(self, session_id: str, text: str) -> dict: ...
    def transfer_call(self, call_id: str, reason: str) -> dict: ...


@dataclass
class MockPublisher(MockAdapter):
    service: str = "publisher"
    records: list = field(default_factory=list)

    def _record(self, kind: str, data: dict) -> dict:
        entry = {"kind": kind, "status": NOT_PUBLISHED, **data}
        self.records.append(entry)
        with (self._out("publish") / "intended.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
        return entry

    def post(self, platforms: list[str], text: str, media_ref: Optional[str]) -> dict:
        self._guard("post", platforms=platforms)
        bad = [p for p in platforms if p not in PLATFORMS]
        if bad or not platforms:
            raise ValueError(f"unknown or missing platforms: {bad or platforms}")
        pricing_guard.assert_clean(text, "social post")
        claim_guard.assert_no_claims(text, "social post")
        post_id = stable_id("post", platforms, text, media_ref)
        return self._record("social_post", {"post_id": post_id, "platforms": platforms,
                                            "text": text, "media_ref": media_ref})

    def analytics(self, post_id: str) -> dict:
        self._guard("analytics", post_id=post_id)
        # Nothing was published, so there are no metrics. Never fabricate any.
        return {"post_id": post_id, "views": None, "likes": None, "status": NOT_PUBLISHED}

    def notify(self, channel: str, text: str) -> dict:
        self._guard("notify", channel=channel)
        return self._record("internal_notification", {"channel": channel, "text": text})

    def reply(self, session_id: str, text: str) -> dict:
        self._guard("reply", session_id=session_id)
        pricing_guard.assert_clean(text, "chat reply")
        claim_guard.assert_no_claims(text, "chat reply")
        return self._record("chat_reply", {"session_id": session_id, "text": text})

    def transfer_call(self, call_id: str, reason: str) -> dict:
        self._guard("transfer_call", call_id=call_id)
        return self._record("call_transfer_intent", {"call_id": call_id, "reason": reason})


class LivePublisher(LiveAdapter):
    service = "publisher"
    credential_env = ("AYRSHARE_API_KEY", "SLACK_WEBHOOK_URL", "TWILIO_AUTH_TOKEN")

    def post(self, platforms, text, media_ref):
        self._refuse("post")

    def analytics(self, post_id):
        self._refuse("analytics")

    def notify(self, channel, text):
        self._refuse("notify")

    def reply(self, session_id, text):
        self._refuse("reply")

    def transfer_call(self, call_id, reason):
        self._refuse("transfer_call")

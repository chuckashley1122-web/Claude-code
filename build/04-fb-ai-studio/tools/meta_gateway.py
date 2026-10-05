"""Campaign gateway: the only code path that models Meta campaign operations.

This build makes NO Meta API calls. Two implementations sit behind one
interface:

* LocalDraftGateway - zero-cost, offline. Stores NEW draft campaigns as JSON
  files on disk, keeps a version history so a prior config is recoverable, and
  supports a local "pause" for rollback rehearsal. It can never publish.
* LiveMetaGateway   - refuses every call with LiveCallBlocked. It exists so a
  future live integration has a typed, approval-gated seam; it never silently
  succeeds.

Both run the frozen-campaign tripwire FIRST on every call, so the protected
live campaign can never become a target, even by mistake.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Protocol

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from tools.guardrails import assert_campaign_name_is_draft, assert_not_frozen_campaign  # noqa: E402


class LiveCallBlocked(Exception):
    """A live Meta call was requested. Needs explicit human approval and a logged-in human."""


class LaunchNotApproved(Exception):
    """Publishing was requested. This build never publishes; a human does it at campaign level."""


class CampaignGateway(Protocol):
    def create_draft_campaign(self, config: dict) -> dict: ...
    def get_campaign(self, name: str) -> dict: ...
    def pause_campaign(self, name: str) -> dict: ...
    def restore_previous(self, name: str) -> dict: ...
    def publish_campaign(self, name: str, approval_ref: str | None = None) -> dict: ...


def _tripwire(name: str, payload: dict | None = None) -> None:
    assert_not_frozen_campaign(name)
    if payload is not None:
        assert_not_frozen_campaign(json.dumps(payload))


class LocalDraftGateway:
    STATUS_DRAFT = "DRAFT_UNPUBLISHED"
    STATUS_PAUSED = "PAUSED_DRAFT"

    def __init__(self, store_dir: Path):
        self.store_dir = Path(store_dir)

    def _path(self, name: str) -> Path:
        return self.store_dir / f"{name}.json"

    def _load(self, name: str) -> dict:
        p = self._path(name)
        if not p.exists():
            raise KeyError(f"No local draft named {name!r}")
        return json.loads(p.read_text(encoding="utf-8"))

    def _save(self, doc: dict) -> None:
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._path(doc["name"]).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    def create_draft_campaign(self, config: dict) -> dict:
        name = config["campaign"]["name"]
        _tripwire(name, config)
        assert_campaign_name_is_draft(name)
        history = []
        if self._path(name).exists():
            prior = self._load(name)
            history = prior.get("history", [])
            if prior["config"] != config or prior["status"] != self.STATUS_DRAFT:
                history = history + [{"status": prior["status"], "config": prior["config"]}]
        doc = {"name": name, "status": self.STATUS_DRAFT, "published_by_build": False,
               "config": copy.deepcopy(config), "history": history}
        self._save(doc)
        return doc

    def get_campaign(self, name: str) -> dict:
        _tripwire(name)
        return self._load(name)

    def pause_campaign(self, name: str) -> dict:
        _tripwire(name)
        doc = self._load(name)
        doc["history"].append({"status": doc["status"], "config": copy.deepcopy(doc["config"])})
        doc["status"] = self.STATUS_PAUSED
        self._save(doc)
        return doc

    def restore_previous(self, name: str) -> dict:
        _tripwire(name)
        doc = self._load(name)
        if not doc["history"]:
            raise KeyError(f"No prior config recorded for {name!r}")
        prior = doc["history"].pop()
        doc["status"] = prior["status"]
        doc["config"] = prior["config"]
        self._save(doc)
        return doc

    def publish_campaign(self, name: str, approval_ref: str | None = None) -> dict:
        _tripwire(name)
        raise LaunchNotApproved(
            "This build never publishes. Publishing happens at CAMPAIGN level in Ads Manager by a human, "
            "after APPROVAL_LAUNCH and APPROVAL_AD_SPEND are granted in writing.")


class LiveMetaGateway:
    """Refuses every operation. No network code exists in this build."""

    def _refuse(self, op: str, name: str, payload: dict | None = None):
        _tripwire(name, payload)
        raise LiveCallBlocked(
            f"Live Meta operation {op!r} blocked: requires explicit human approval "
            f"(APPROVAL_LAUNCH={C.APPROVAL_LAUNCH}, APPROVAL_AD_SPEND={C.APPROVAL_AD_SPEND}) and a logged-in human in Ads Manager.")

    def create_draft_campaign(self, config: dict) -> dict:
        return self._refuse("create_draft_campaign", config.get("campaign", {}).get("name", ""), config)

    def get_campaign(self, name: str) -> dict:
        return self._refuse("get_campaign", name)

    def pause_campaign(self, name: str) -> dict:
        return self._refuse("pause_campaign", name)

    def restore_previous(self, name: str) -> dict:
        return self._refuse("restore_previous", name)

    def publish_campaign(self, name: str, approval_ref: str | None = None) -> dict:
        return self._refuse("publish_campaign", name)

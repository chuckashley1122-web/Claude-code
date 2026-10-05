"""Connector interfaces for GHL (CRM), Meta (ads) and the payment processor.

Each has a zero-cost local implementation that genuinely works offline and a
live implementation that refuses every call with LiveCallBlocked. Nothing in
this build performs a network call. DRY_RUN defaults to true.
"""
from __future__ import annotations

import copy
import itertools
import json
import os
from pathlib import Path
from typing import Protocol, runtime_checkable
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from tools import guardrails as G  # noqa: E402


class LiveCallBlocked(RuntimeError):
    """A live third-party call was attempted without the required human approval."""


class LaunchNotAuthorized(RuntimeError):
    """Activation was attempted while LAUNCH_AUTHORITY is 'none'."""


# ---------------------------------------------------------------------------- protocols
@runtime_checkable
class CRMGateway(Protocol):
    def find_contact_by_lead_id(self, lead_id: str): ...
    def find_contact(self, email: str | None, phone: str | None): ...
    def create_contact(self, fields: dict) -> str: ...
    def update_contact(self, contact_id: str, fields: dict) -> None: ...
    def get_contact(self, contact_id: str) -> dict: ...
    def open_opportunity(self, contact_id: str, offer: str): ...
    def create_opportunity(self, contact_id: str, offer: str, stage: str) -> str: ...
    def set_stage(self, opp_id: str, stage: str) -> None: ...
    def create_task(self, contact_id: str, title: str, created, due) -> str: ...
    def send_message(self, contact_id: str, channel: str, template_id: str, body: str, at) -> str: ...


@runtime_checkable
class AdsGateway(Protocol):
    def create_draft_campaign(self, name: str, daily_budget_usd: float, approval_ad_spend: bool) -> str: ...
    def pause_campaign(self, campaign_id: str) -> None: ...
    def get_campaign(self, campaign_id: str) -> dict: ...


@runtime_checkable
class PaymentGateway(Protocol):
    def create_product(self, name: str, amount_usd: float, recurring: bool, approval: bool) -> str: ...
    def get_product(self, product_id: str) -> dict: ...


# ---------------------------------------------------------------------------- local implementations
class LocalCRM:
    """In-memory CRM with JSON persistence. Mirrors the GHL objects the spec defines."""

    OPEN_STAGES_EXCLUDED = {"Lost", "Disqualified", "Active client"}

    def __init__(self):
        self.contacts: dict[str, dict] = {}
        self.opportunities: dict[str, dict] = {}
        self.tasks: list[dict] = []
        self.messages: list[dict] = []
        self._ids = itertools.count(1)

    def _id(self, kind: str) -> str:
        return f"{kind}-{next(self._ids):04d}"

    def find_contact_by_lead_id(self, lead_id):
        for c in self.contacts.values():
            if lead_id and lead_id in c["lead_ids"]:
                return c["id"]
        return None

    def find_contact(self, email, phone):
        email = (email or "").strip().lower()
        phone = "".join(ch for ch in (phone or "") if ch.isdigit())
        for c in self.contacts.values():
            if (email and c["email"] == email) or (phone and c["phone"] == phone):
                return c["id"]
        return None  # never match on name alone

    def create_contact(self, fields):
        cid = self._id("contact")
        self.contacts[cid] = {
            "id": cid, "name": fields.get("full_name", ""), "email": (fields.get("email") or "").strip().lower(),
            "phone": "".join(ch for ch in (fields.get("phone") or "") if ch.isdigit()),
            "custom": {}, "tags": [], "lead_ids": [], "attribution_history": [], "opted_out": [],
            "replied": False, "owner_notified": False,
        }
        return cid

    def update_contact(self, contact_id, fields):
        c = self.contacts[contact_id]
        for k, v in fields.items():
            if k == "custom":
                c["custom"].update(v)
            elif k == "tag":
                if v not in c["tags"]:
                    c["tags"].append(v)
            elif k == "lead_id":
                if v and v not in c["lead_ids"]:
                    c["lead_ids"].append(v)
            elif k == "attribution":
                c["attribution_history"].append(v)
            else:
                c[k] = v

    def get_contact(self, contact_id):
        return self.contacts[contact_id]

    def open_opportunity(self, contact_id, offer):
        for o in self.opportunities.values():
            if o["contact_id"] == contact_id and o["offer"] == offer and o["stage"] not in self.OPEN_STAGES_EXCLUDED:
                return o
        return None

    def opportunities_for(self, contact_id):
        return [o for o in self.opportunities.values() if o["contact_id"] == contact_id]

    def create_opportunity(self, contact_id, offer, stage):
        oid = self._id("opp")
        self.opportunities[oid] = {"id": oid, "contact_id": contact_id, "offer": offer, "stage": stage, "history": [stage]}
        return oid

    def set_stage(self, opp_id, stage):
        o = self.opportunities[opp_id]
        if o["stage"] != stage:
            o["stage"] = stage
            o["history"].append(stage)

    def create_task(self, contact_id, title, created, due):
        tid = self._id("task")
        self.tasks.append({"id": tid, "contact_id": contact_id, "title": title, "created": created, "due": due, "status": "open"})
        return tid

    def send_message(self, contact_id, channel, template_id, body, at):
        mid = self._id("msg")
        self.messages.append({"id": mid, "contact_id": contact_id, "channel": channel, "template": template_id, "body": body, "at": at})
        return mid

    def snapshot(self) -> dict:
        return json.loads(json.dumps({"contacts": self.contacts, "opportunities": self.opportunities,
                                      "tasks": self.tasks, "messages": self.messages}, default=str))

    def save(self, path: Path) -> Path:
        Path(path).write_text(json.dumps(self.snapshot(), indent=2) + "\n", encoding="utf-8")
        return Path(path)


class LocalAds:
    """Draft-only campaign store. Campaigns are created PAUSED and can never be activated here."""

    def __init__(self):
        self.campaigns: dict[str, dict] = {}
        self._ids = itertools.count(1)

    def create_draft_campaign(self, name, daily_budget_usd, approval_ad_spend):
        G.assert_new_campaign_name(name)
        G.assert_no_spend(daily_budget_usd, approval_ad_spend, item="campaign daily budget")
        cid = f"draft-campaign-{next(self._ids):03d}"
        self.campaigns[cid] = {"id": cid, "name": name, "status": "PAUSED", "daily_budget_usd": daily_budget_usd}
        return cid

    def pause_campaign(self, campaign_id):
        camp = self.campaigns[campaign_id]
        G.assert_not_frozen_campaign(camp["name"])
        camp["status"] = "PAUSED"

    def activate_campaign(self, campaign_id):
        raise LaunchNotAuthorized(f"LAUNCH_AUTHORITY is {C.LAUNCH_AUTHORITY!r}; activation is a human action after approval")

    def get_campaign(self, campaign_id):
        return copy.deepcopy(self.campaigns[campaign_id])


class LocalPayments:
    """Test-mode product records only; no processor is contacted."""

    def __init__(self):
        self.products: dict[str, dict] = {}
        self._ids = itertools.count(1)

    def create_product(self, name, amount_usd, recurring, approval):
        if approval is not True:
            raise G.SpendNotApproved("payment-product creation requires explicit human approval")
        if recurring:
            raise ValueError("no automatic subscription may be created")
        pid = f"test-product-{next(self._ids):03d}"
        self.products[pid] = {"id": pid, "name": name, "amount_usd": amount_usd, "recurring": False, "mode": "test"}
        return pid

    def get_product(self, product_id):
        return dict(self.products[product_id])


# ---------------------------------------------------------------------------- live implementations (refuse)
class _Refuser:
    service = "live service"
    approval = "explicit written human approval"

    def _refuse(self, op):
        raise LiveCallBlocked(f"{self.service}.{op}: live calls are disabled in this build (DRY_RUN default true). "
                              f"Requires {self.approval}; perform it as a human via ui-tasks/ instead.")


class LiveGHLCRM(_Refuser):
    service = "GoHighLevel"
    approval = f"a GHL API key for location {C.GHL_LOCATION_ID} and explicit written approval"

    def find_contact_by_lead_id(self, lead_id): self._refuse("find_contact_by_lead_id")
    def find_contact(self, email, phone): self._refuse("find_contact")
    def create_contact(self, fields): self._refuse("create_contact")
    def update_contact(self, contact_id, fields): self._refuse("update_contact")
    def get_contact(self, contact_id): self._refuse("get_contact")
    def open_opportunity(self, contact_id, offer): self._refuse("open_opportunity")
    def create_opportunity(self, contact_id, offer, stage): self._refuse("create_opportunity")
    def set_stage(self, opp_id, stage): self._refuse("set_stage")
    def create_task(self, contact_id, title, created, due): self._refuse("create_task")
    def send_message(self, contact_id, channel, template_id, body, at): self._refuse("send_message")


class LiveMetaAds(_Refuser):
    service = "Meta Ads"
    approval = "APPROVAL_AD_SPEND, APPROVAL_LAUNCH and an authorized ad account"

    def create_draft_campaign(self, name, daily_budget_usd, approval_ad_spend):
        G.assert_not_frozen_campaign(name)
        self._refuse("create_draft_campaign")

    def pause_campaign(self, campaign_id): self._refuse("pause_campaign")
    def get_campaign(self, campaign_id): self._refuse("get_campaign")


class LivePayments(_Refuser):
    service = "payment processor"
    approval = "a chosen processor (NEEDS_EVIDENCE) and explicit written approval"

    def create_product(self, name, amount_usd, recurring, approval): self._refuse("create_product")
    def get_product(self, product_id): self._refuse("get_product")


def dry_run_enabled(env=None) -> bool:
    env = os.environ if env is None else env
    return str(env.get("DRY_RUN", "true")).strip().lower() not in ("false", "0", "no")


def get_gateways(env=None) -> dict:
    if dry_run_enabled(env):
        return {"crm": LocalCRM(), "ads": LocalAds(), "payments": LocalPayments(), "mode": "local"}
    return {"crm": LiveGHLCRM(), "ads": LiveMetaAds(), "payments": LivePayments(), "mode": "live-refusing"}

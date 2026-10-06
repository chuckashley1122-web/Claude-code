"""CRM adapters for the inquiry handler.

``GHLAdapter`` is the live GoHighLevel adapter. The GHL API contract is
unverified (auth method, API version, scopes, base URL, endpoint path, contact
matching rule, custom field IDs, pipeline ID, stage ID), so every method raises
``LiveCallBlocked`` (a ``NotImplementedError``) naming the exact thing a human
must confirm. It never guesses an endpoint path or an ID and never silently
substitutes a similar tool.

``MockGHLAdapter`` is labelled MOCK - NOT PRODUCTION. It is an in-memory CRM
used only by tests and the local acceptance matrix. Its success is NOT evidence
that the real integration works.
"""

from __future__ import annotations

import itertools
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402

MOCK_LABEL = "MOCK — NOT PRODUCTION"


# ------------------------------------------------------------------ result + errors
@dataclass
class AdapterResult:
    outcome: str  # "saved" (confirmed CRM write) or "queued" (accepted by a durable queue)
    reference: str | None


class UpstreamError(Exception):
    retryable = False
    status = C.STATUS_UPSTREAM_BAD

    def __init__(self, message: str = "", retry_after: float | None = None):
        super().__init__(message or self.__class__.__name__)
        self.retry_after = retry_after


class UpstreamTimeout(UpstreamError):
    retryable = True
    status = C.STATUS_UPSTREAM_FAIL


class UpstreamUnavailable(UpstreamError):
    retryable = True
    status = C.STATUS_UPSTREAM_FAIL


class UpstreamThrottled(UpstreamError):
    retryable = True
    status = C.STATUS_UPSTREAM_FAIL


class UpstreamPermissionError(UpstreamError):
    """Rejected/expired token or missing scope. Never retried."""
    retryable = False
    status = C.STATUS_UPSTREAM_BAD


class UpstreamValidationError(UpstreamError):
    """Upstream rejected the payload. Never retried."""
    retryable = False
    status = C.STATUS_UPSTREAM_BAD


class LiveCallBlocked(NotImplementedError):
    """A live call needs a human-confirmed contract and approval before it can be implemented."""


class CRMAdapter(Protocol):
    durable_queue: bool
    label: str

    def save_inquiry(self, record: dict, submission_id: str, timeout_s: float) -> AdapterResult: ...


# ------------------------------------------------------------------ live adapter (blocked)
def _todo(thing: str) -> LiveCallBlocked:
    return LiveCallBlocked(
        f"TODO: confirm {thing} before implementing. The GHL API contract for location "
        f"{C.GHL_LOCATION_ID} is unverified; see ui-work-orders/005-005-ghl-crm-integration-and-field-mapping.md. "
        "No live call is made without human confirmation and approval.")


class GHLAdapter:
    durable_queue = False
    label = "GHL live adapter (BLOCKED until contract confirmed)"

    def auth_method(self) -> str:
        raise _todo("the GHL authentication method (private integration token vs OAuth)")

    def api_version(self) -> str:
        raise _todo("the GHL API version header value")

    def required_scopes(self) -> list[str]:
        raise _todo("the minimum required API scopes")

    def base_url(self) -> str:
        raise _todo("the GHL API base URL")

    def endpoint_path(self) -> str:
        raise _todo("the contact upsert endpoint path")

    def contact_matching_rule(self) -> str:
        raise _todo("the contact upsert/matching rule (email, phone, or both)")

    def custom_field_ids(self) -> dict[str, str]:
        raise _todo("the custom field IDs for service_interest, service_area, source_page and submission_id")

    def pipeline_id(self) -> str:
        raise _todo("the pipeline ID (only if the approved flow creates an opportunity)")

    def stage_id(self) -> str:
        raise _todo("the pipeline stage ID")

    def save_inquiry(self, record: dict, submission_id: str, timeout_s: float) -> AdapterResult:
        raise _todo("the full contact upsert + field mapping contract")


# ------------------------------------------------------------------ mock adapter (tests only)
@dataclass
class MockGHLAdapter:
    """MOCK — NOT PRODUCTION. In-memory CRM for local tests only.

    ``script`` is a list consumed one item per call: an exception instance to raise,
    the string "queued" (only meaningful with durable_queue=True), "unconfirmed"
    (upstream claims success without a reference) or None for a normal save.
    ``delay_s`` simulates a slow upstream for timeout tests.
    """

    script: list = field(default_factory=list)
    durable_queue: bool = False
    delay_s: float = 0.0
    label: str = MOCK_LABEL
    calls: list = field(default_factory=list)
    contacts: dict = field(default_factory=dict)
    inquiries: list = field(default_factory=list)
    _ids: itertools.count = field(default_factory=lambda: itertools.count(1))

    def save_inquiry(self, record: dict, submission_id: str, timeout_s: float) -> AdapterResult:
        self.calls.append({"submission_id": submission_id, "timeout_s": timeout_s})
        if self.delay_s:
            time.sleep(self.delay_s)
        step = self.script.pop(0) if self.script else None
        if isinstance(step, BaseException):
            raise step
        if step == "unconfirmed":
            return AdapterResult("saved", None)
        if step == "queued":
            return AdapterResult("queued", f"mockq_{next(self._ids)}")
        key = record.get("email") or record.get("phone")
        contact_id = self.contacts.setdefault(key, f"mockc_{len(self.contacts) + 1}")
        ref = f"mocki_{next(self._ids)}"
        self.inquiries.append({"ref": ref, "contact_id": contact_id, "submission_id": submission_id,
                               "location_id": record.get("location_id")})
        return AdapterResult("saved", ref)

"""Shared adapter plumbing: errors, endpoint checks, call logging, live refusal.

Every external service is used through an interface (``typing.Protocol``) with:

(a) a deterministic offline mock (``Mock*``) that genuinely works from
    ``data/fixtures`` and writes only under ``data/out``; and
(b) a live class (``Live*``) whose every method raises :class:`LiveCallBlocked`
    explaining the human approval required. Live classes never call out.

Mocks also raise :class:`LiveCallBlocked` if they are pointed at a real (non-local)
endpoint while ``DRY_RUN`` is true, so a misconfiguration can never leak a call.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from config import constants

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT / "data" / "fixtures"
OUT_DIR = ROOT / "data" / "out"

_LOCAL_HOSTS = {"", "localhost", "127.0.0.1", "::1", "example.com"}


class LiveCallBlocked(RuntimeError):
    """A real external call was requested. It is refused; a human must approve."""

    def __init__(self, service: str, operation: str, reason: str = ""):
        self.service = service
        self.operation = operation
        msg = (f"LIVE CALL BLOCKED: {service}.{operation}. "
               f"{reason or 'No live call is permitted from this suite.'} "
               "Human approval required: see docs/COST-AND-APPROVALS.md and "
               "docs/DEPLOY-RUNBOOK.md. No request was sent and nothing was charged.")
        super().__init__(msg)


class NotAuthorized(LiveCallBlocked):
    """Live call refused because no human has authorized this service."""


def endpoint_is_local(endpoint: Optional[str]) -> bool:
    """True when ``endpoint`` is absent, a file path, or a loopback/example host."""
    if not endpoint:
        return True
    parsed = urlparse(endpoint)
    if parsed.scheme in ("", "file"):
        return True
    host = (parsed.hostname or "").lower()
    return host in _LOCAL_HOSTS or host.endswith(".example.com") or host.endswith(".localhost")


def stable_id(prefix: str, *parts: Any) -> str:
    digest = hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()
    return f"{prefix}-{digest[:12]}"


def load_json_fixture(name: str, fixtures_dir: Path = FIXTURES_DIR) -> Any:
    return json.loads((fixtures_dir / name).read_text(encoding="utf-8"))


@dataclass
class CallRecord:
    service: str
    operation: str
    summary: dict


@dataclass
class MockAdapter:
    """Base for every mock. Subclasses set ``service``."""

    service: str = "mock"
    dry_run: bool = constants.DRY_RUN
    endpoint: Optional[str] = None
    fixtures_dir: Path = FIXTURES_DIR
    out_dir: Path = OUT_DIR
    calls: list[CallRecord] = field(default_factory=list)

    def _guard(self, operation: str, **summary: Any) -> None:
        if self.dry_run and not endpoint_is_local(self.endpoint):
            raise LiveCallBlocked(
                self.service, operation,
                f"DRY_RUN is true but a real endpoint is configured ({urlparse(self.endpoint).hostname}).")
        self.calls.append(CallRecord(self.service, operation, summary))

    def _out(self, *parts: str) -> Path:
        path = self.out_dir.joinpath(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return path


class LiveAdapter:
    """Base for every live adapter: each public method refuses."""

    service = "live"
    credential_env: tuple[str, ...] = ()

    def _refuse(self, operation: str) -> None:
        creds = ", ".join(self.credential_env) or "an account"
        raise NotAuthorized(
            self.service, operation,
            f"This service is paid and/or needs a logged-in account ({creds}).")

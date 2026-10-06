"""Mailer interface (Gmail / SMTP stand-in): writes .eml drafts to data/out/mail.

Nothing is sent. Every message is checked by the pricing and claim guards,
honours the suppression / opt-out list, and enforces the per-inbox daily cap.
Each .eml is marked as a draft awaiting human approval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from email.message import EmailMessage
from email.utils import make_msgid
from typing import Protocol

from adapters.base import LiveAdapter, MockAdapter, stable_id
from config import constants
from guardrails import claim_guard, pricing_guard


class Suppressed(ValueError):
    """Recipient is on the suppression / opt-out list."""


class CapExceeded(RuntimeError):
    """Daily per-inbox send cap reached."""


class MailerClient(Protocol):
    def send(self, to: str, subject: str, body: str, from_addr: str) -> dict: ...
    def has_reply(self, from_addr: str) -> bool: ...


@dataclass
class MockMailer(MockAdapter):
    service: str = "mailer"
    daily_cap: int = constants.DAILY_EMAIL_CAP_PER_INBOX
    suppressed: set = field(default_factory=set)
    replies: set = field(default_factory=set)
    sent_counts: dict = field(default_factory=dict)
    sent: list = field(default_factory=list)

    def suppress(self, addr: str) -> None:
        self.suppressed.add(addr.strip().lower())

    def record_reply(self, addr: str) -> None:
        self.replies.add(addr.strip().lower())

    def has_reply(self, from_addr: str) -> bool:
        self._guard("has_reply")
        return (from_addr or "").strip().lower() in self.replies

    def send(self, to: str, subject: str, body: str, from_addr: str) -> dict:
        self._guard("send")
        if not to or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", to):
            raise ValueError(f"invalid recipient address {to!r}")
        if constants.SUPPRESSION_CHECK_REQUIRED and to.strip().lower() in self.suppressed:
            raise Suppressed(f"{to} is suppressed / opted out")
        pricing_guard.assert_clean(subject, "email subject")
        pricing_guard.assert_clean(body, "email body")
        claim_guard.assert_no_claims(subject + "\n" + body, "email")
        key = (from_addr.lower(), date.today().isoformat())
        if self.sent_counts.get(key, 0) >= self.daily_cap:
            raise CapExceeded(f"daily cap {self.daily_cap} reached for inbox {from_addr}")
        self.sent_counts[key] = self.sent_counts.get(key, 0) + 1

        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = to
        msg["Subject"] = subject
        msg["Message-ID"] = make_msgid(domain="dry-run.example.com")
        msg["X-CAJ-Dry-Run"] = "true"
        msg["X-CAJ-Status"] = "DRAFT - not sent; human approval required"
        msg.set_content(body)
        n = len(self.sent) + 1
        slug = re.sub(r"[^a-z0-9]+", "-", to.lower()).strip("-")
        path = self._out("mail") / f"{n:03d}_{slug}_{stable_id('m', to, subject, n)}.eml"
        path.write_bytes(bytes(msg))
        record = {"to": to, "subject": subject, "path": str(path), "status": "draft_written_not_sent"}
        self.sent.append(record)
        return record


class LiveMailer(LiveAdapter):
    service = "mailer"
    credential_env = ("SMTP_HOST", "SMTP_USER", "SMTP_PASS", "GOOGLE_REFRESH_TOKEN")

    def send(self, to: str, subject: str, body: str, from_addr: str) -> dict:
        self._refuse("send")

    def has_reply(self, from_addr: str) -> bool:
        self._refuse("has_reply")

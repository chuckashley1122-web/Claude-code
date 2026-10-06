"""Server-side inquiry normalization and validation. Pure Python, stdlib only, no I/O.

Validate on the server even when the browser already validated. Privileged
CRM fields (location, pipeline, stage, tags, assignee, ...) are rejected when
the client supplies them; those values come from server configuration only.
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402

TEXT_FIELDS = ["submission_id", "name", "email", "phone", "service_interest", "service_area", "message",
               "source_page"]
SINGLE_LINE = {"submission_id", "name", "email", "phone", "service_interest", "service_area", "source_page"}
PII_KEYS = {"name", "email", "phone", "message", "service_area"}

EMAIL_RE = re.compile(r"^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
                      r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$")
PHONE_RE = re.compile(r"^\+?\d{10,15}$")
SUBMISSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
_EMAIL_IN_TEXT = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_IN_TEXT = re.compile(r"\+?\d[\d\s().-]{8,}\d")
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")
_TRUE = {"true", "1", "yes", "on"}
_FALSE = {"false", "0", "no", "off", ""}


def _list_or_empty(value: Any) -> list:
    if value == C.NEEDS_EVIDENCE or not value:
        return []
    return list(value)


def default_config() -> dict:
    return {
        "service_allowlist": _list_or_empty(C.SERVICE_ALLOWLIST),
        "allowed_source_origins": _list_or_empty(C.ALLOWED_SOURCE_ORIGINS),
        "max_name_len": C.MAX_NAME_LEN,
        "max_message_len": C.MAX_MESSAGE_LEN,
        "max_service_area_len": C.MAX_NAME_LEN,
        "max_payload_bytes": C.MAX_PAYLOAD_BYTES,
    }


def normalize(fields: dict) -> dict:
    """Trim, collapse whitespace, lowercase email, phone -> digits with optional leading '+'."""
    out: dict = {}
    for key, value in fields.items():
        if key in TEXT_FIELDS and isinstance(value, str):
            if key in SINGLE_LINE:
                value = re.sub(r"\s+", " ", value).strip()
            else:
                value = re.sub(r"[ \t\f\v]+", " ", value.replace("\r\n", "\n").replace("\r", "\n"))
                value = re.sub(r" *\n *", "\n", value)
                value = re.sub(r"\n{3,}", "\n\n", value).strip()
            if key == "email":
                value = value.lower()
            elif key == "phone":
                plus = value.startswith("+")
                value = ("+" if plus else "") + re.sub(r"\D", "", value)
                if value == "+":
                    value = ""
        elif key == "consent":
            if isinstance(value, str) and value.strip().lower() in _TRUE:
                value = True
            elif isinstance(value, str) and value.strip().lower() in _FALSE:
                value = False
        out[key] = value
    return out


def payload_size(fields: dict) -> int:
    return len(json.dumps(fields, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _origin(url: str) -> str | None:
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return None
    return f"{parts.scheme}://{parts.netloc}".lower()


def validate(fields: dict, config: dict | None = None) -> tuple[bool, list[dict]]:
    """Return (ok, errors). Errors carry field + code only, never the submitted value."""
    cfg = {**default_config(), **(config or {})}
    errors: list[dict] = []

    def err(field: str, code: str) -> None:
        errors.append({"field": field, "code": code})

    if not isinstance(fields, dict):
        return False, [{"field": "_body", "code": "not_an_object"}]
    if payload_size(fields) > cfg["max_payload_bytes"]:
        err("_body", "payload_too_large")

    for key in fields:
        if key in C.INQUIRY_PRIVILEGED_FIELDS_REJECTED:
            err(key, "privileged_field_rejected")
        elif key not in C.INQUIRY_ALLOWED_FIELDS:
            err(key, "unknown_field")

    for key in TEXT_FIELDS:
        if key in fields and fields[key] is not None and not isinstance(fields[key], str):
            err(key, "must_be_string")
    if "consent" in fields and not isinstance(fields["consent"], bool):
        err("consent", "must_be_boolean")

    def text(key: str) -> str:
        v = fields.get(key)
        return v if isinstance(v, str) else ""

    for key in C.INQUIRY_REQUIRED_FIELDS:
        if not text(key):
            err(key, "required")
    if text("submission_id") and not SUBMISSION_ID_RE.match(text("submission_id")):
        err("submission_id", "invalid_format")
    if len(text("name")) > cfg["max_name_len"]:
        err("name", "too_long")
    if len(text("message")) > cfg["max_message_len"]:
        err("message", "too_long")
    if len(text("service_area")) > cfg["max_service_area_len"]:
        err("service_area", "too_long")

    email, phone = text("email"), text("phone")
    email_ok = bool(email) and len(email) <= 254 and bool(EMAIL_RE.match(email))
    phone_ok = bool(phone) and bool(PHONE_RE.match(phone))
    if email and not email_ok:
        err("email", "invalid")
    if phone and not phone_ok:
        err("phone", "invalid")
    if not email and not phone:
        err("contact", "one_contact_method_required")

    service = text("service_interest")
    allow = cfg["service_allowlist"]
    if not service:
        err("service_interest", "required")
    elif not allow:
        err("service_interest", "service_allowlist_unconfigured")
    elif service not in allow:
        err("service_interest", "not_in_allowlist")

    source = text("source_page")
    if source:
        origin = _origin(source)
        origins = [o.rstrip("/").lower() for o in cfg["allowed_source_origins"]]
        if origin is None:
            err("source_page", "invalid_url")
        elif not origins:
            err("source_page", "source_origins_unconfigured")
        elif origin not in origins:
            err("source_page", "origin_not_allowed")

    return (not errors), errors


def escape_for_display(s: str) -> str:
    return html.escape(s, quote=True)


def _scrub(text: str) -> str:
    text = _EMAIL_IN_TEXT.sub("[REDACTED_EMAIL]", text)

    def phone(m: re.Match) -> str:
        chunk = m.group(0)
        if sum(ch.isdigit() for ch in chunk) < 10 or _ISO_DATE.match(chunk):
            return chunk
        return "[REDACTED_PHONE]"

    return _PHONE_IN_TEXT.sub(phone, text)


def redact_pii(obj: Any) -> Any:
    """Copy of obj safe for logs: PII keys replaced, emails/phones scrubbed from free text."""
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if k in PII_KEYS and v not in (None, ""):
                result[k] = "[REDACTED]"
            else:
                result[k] = redact_pii(v)
        return result
    if isinstance(obj, (list, tuple)):
        return [redact_pii(v) for v in obj]
    if isinstance(obj, str):
        return _scrub(obj)
    return obj

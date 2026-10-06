"""CRM / table-store interface: in-memory contact upsert (HubSpot stand-in) and
record tables (Airtable / Supabase stand-in), plus an email-finder lookup
(Hunter.io stand-in) that only knows what was explicitly seeded."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from adapters.base import LiveAdapter, MockAdapter, stable_id

_OPS = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "lt": lambda a, b: a is not None and a < b,
    "lte": lambda a, b: a is not None and a <= b,
    "gt": lambda a, b: a is not None and a > b,
    "gte": lambda a, b: a is not None and a >= b,
    "isTrue": lambda a, b: a is True,
    "isFalse": lambda a, b: not a,
}


class CRMClient(Protocol):
    def upsert_contact(self, email: str, properties: dict) -> dict: ...
    def upsert_record(self, table: str, key: str, fields: dict, increment: tuple = ()) -> dict: ...
    def query(self, table: str, where: list) -> list[dict]: ...
    def find_email(self, domain: str) -> Optional[str]: ...


@dataclass
class MockCRM(MockAdapter):
    service: str = "crm"
    contacts: dict[str, dict] = field(default_factory=dict)
    tables: dict[str, dict[str, dict]] = field(default_factory=dict)
    known_emails: dict[str, str] = field(default_factory=dict)

    def upsert_contact(self, email: str, properties: dict) -> dict:
        self._guard("upsert_contact")
        if not email:
            key = stable_id("anon", sorted(properties.items()))
        else:
            key = email.strip().lower()
        contact = self.contacts.setdefault(key, {"contact_id": stable_id("ct", key)})
        contact.update({k: v for k, v in properties.items() if v is not None})
        contact["email"] = email or None
        return dict(contact)

    def upsert_record(self, table: str, key: str, fields: dict, increment: tuple = ()) -> dict:
        self._guard("upsert_record", table=table)
        if key in (None, ""):
            raise ValueError(f"upsert into {table} needs a non-empty key")
        rows = self.tables.setdefault(table, {})
        row = rows.setdefault(str(key), {"_key": str(key)})
        row.update(fields)
        for name in increment:
            row[name] = int(row.get(name) or 0) + 1
        return dict(row)

    def query(self, table: str, where: list) -> list[dict]:
        self._guard("query", table=table)
        out = []
        for row in self.tables.get(table, {}).values():
            if all(_OPS[op](row.get(f), v) for f, op, v in where):
                out.append(dict(row))
        return out

    def find_email(self, domain: str) -> Optional[str]:
        self._guard("find_email", domain=domain)
        return self.known_emails.get((domain or "").lower())


class LiveCRM(LiveAdapter):
    service = "crm"
    credential_env = ("HUBSPOT_TOKEN", "AIRTABLE_TOKEN", "SUPABASE_SERVICE_KEY", "HUNTER_API_KEY")

    def upsert_contact(self, email: str, properties: dict) -> dict:
        self._refuse("upsert_contact")

    def upsert_record(self, table: str, key: str, fields: dict, increment: tuple = ()) -> dict:
        self._refuse("upsert_record")

    def query(self, table: str, where: list) -> list[dict]:
        self._refuse("query")

    def find_email(self, domain: str) -> Optional[str]:
        self._refuse("find_email")

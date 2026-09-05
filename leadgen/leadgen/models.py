"""The one shape every source normalises into."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from typing import Any


def _norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def normalize_domain(value: str | None) -> str:
    """Strip scheme, www and path so two spellings of a site collapse to one key."""
    raw = _norm(value).lower()
    if not raw:
        return ""
    raw = re.sub(r"^https?://", "", raw)
    raw = raw.split("/")[0].split("?")[0]
    return re.sub(r"^www\.", "", raw)


@dataclass
class Lead:
    # identity
    first_name: str = ""
    last_name: str = ""
    title: str = ""
    # company
    company: str = ""
    company_domain: str = ""
    industry: str = ""
    employee_count: int | None = None
    location: str = ""
    # contact
    email: str = ""
    phone: str = ""
    linkedin_url: str = ""
    website: str = ""
    # provenance — every lead must be able to answer "where did this come from?"
    source: str = ""
    source_ref: str = ""
    # pipeline output
    signals: dict[str, bool] = field(default_factory=dict)
    score: int = 0
    tier: str = "cold"
    notes: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        return _norm(f"{self.first_name} {self.last_name}")

    def dedupe_key(self) -> str:
        """Email wins; otherwise LinkedIn URL; otherwise name+domain."""
        if self.email:
            basis = self.email.strip().lower()
        elif self.linkedin_url:
            basis = self.linkedin_url.strip().lower().rstrip("/")
        else:
            basis = f"{self.full_name.lower()}|{normalize_domain(self.company_domain)}"
        return hashlib.sha1(basis.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["full_name"] = self.full_name
        data["signals"] = ",".join(sorted(k for k, v in self.signals.items() if v))
        data.pop("raw", None)
        return data

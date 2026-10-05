"""Typed contract for the HVAC research pilot: inputs, sources, results, manifest."""

from __future__ import annotations

from dataclasses import dataclass, field

import config

FACT_FIELDS = ("service_area", "services", "contact_method", "observation")
# hypothesis is a derived idea to test, never a fact; it is bound to the observation's source.


@dataclass(frozen=True)
class Company:
    company_id: str
    company_name: str
    website_url: str
    row_index: int


@dataclass(frozen=True)
class SourceRef:
    label: str
    resolved_url: str
    retrieved_at_utc: str
    excerpt: str
    retrieval_status: str
    matched_text: str = ""


@dataclass(frozen=True)
class RawPage:
    label: str
    resolved_url: str
    text: str
    retrieval_status: str  # "ok" or "failed"
    retrieved_at_utc: str = ""
    error: str = ""


@dataclass(frozen=True)
class CompanyResult:
    company_id: str
    company_name: str
    website_url: str
    resolved_url: str
    status: str
    service_area: str
    services: tuple[str, ...]
    contact_method: str
    observation: str
    hypothesis: str
    source_refs: tuple[SourceRef, ...]
    blocked_reason: str
    checked_at_utc: str
    # Every non-missing fact is bound to the SourceRef captured at read time.
    # Keys: "service_area", "services:<keyword>", "contact_method", "observation".
    field_sources: dict = field(default_factory=dict)
    retrieval_attempts: int = 0

    def __post_init__(self) -> None:
        if self.status not in config.COMPANY_STATUSES:
            raise ValueError(f"invalid company status {self.status!r}")
        for name in ("service_area", "contact_method", "observation"):
            value = getattr(self, name)
            if value != config.MISSING_LABEL and name not in self.field_sources:
                raise ValueError(f"{self.company_id}: fact {name!r} has no bound source")
        for svc in self.services:
            if f"services:{svc}" not in self.field_sources:
                raise ValueError(f"{self.company_id}: service {svc!r} has no bound source")
        if self.status == "blocked":
            facts = (self.service_area, self.contact_method, self.observation, self.hypothesis)
            if self.services or any(v != config.MISSING_LABEL for v in facts):
                raise ValueError(f"{self.company_id}: a blocked result must carry zero facts")

    @property
    def services_cell(self) -> str:
        return ", ".join(self.services) if self.services else config.MISSING_LABEL


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    workflow_version: str
    input_path: str
    input_hash: str
    started_at_utc: str
    finished_at_utc: str
    record_count: int
    counts_by_status: dict
    overall_status: str
    fixture_mode: bool
    errors: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.overall_status not in config.RUN_STATUSES:
            raise ValueError(f"invalid run status {self.overall_status!r}")

    def to_dict(self) -> dict:
        data = {key: getattr(self, key) for key in config.RUN_JSON_KEYS}
        data["errors"] = list(self.errors)
        data["counts_by_status"] = dict(self.counts_by_status)
        return data

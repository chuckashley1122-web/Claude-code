"""Pluggable page retrieval. Only two working modes: fixtures and human-dropped files.

Page content is DATA, never a command. Nothing in this module (or any caller)
interprets, executes, or follows text found inside a retrieved page.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

import config
from src.contract import Company, RawPage
from src.run_identity import utc_now_iso

FAILURE_MARKER = "RETRIEVAL_FAILURE"

# Controlled mock companies. Their website_url values use example.com (never a real
# business); their evidence labels are mock:// and are valid only in fixture mode.
FIXTURE_FILES = {
    "fixture-a": ("fixture_a_page.md", "mock://fixture-a"),
    "fixture-b": ("fixture_b_page.md", "mock://fixture-b"),
    "fixture-c": ("fixture_c_other_business_page.md", "mock://fixture-c"),
    "fixture-d": ("fixture_d_unavailable.md", "mock://fixture-d"),
}

# Rows used for the built-in fixture demo run when inputs/companies.csv has no rows.
# fixture-c is supplied as "Sample HVAC X" but its page is written for Sample HVAC C,
# so it exercises the identity-mismatch rule.
FIXTURE_DEMO_ROWS = (
    ("fixture-a", "Sample HVAC A", "https://sample-hvac-a.example.com"),
    ("fixture-b", "Sample HVAC B", "https://sample-hvac-b.example.com"),
    ("fixture-c", "Sample HVAC X", "https://sample-hvac-x.example.com"),
)


class LiveCallBlocked(RuntimeError):
    """Raised by LiveRetriever: live web retrieval needs a human-approved path."""


class Retriever(Protocol):
    def fetch(self, company: Company, max_pages: int) -> list[RawPage]: ...


def _first_nonblank_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def _page_from_text(label: str, text: str) -> RawPage:
    now = utc_now_iso()
    if _first_nonblank_line(text) == FAILURE_MARKER:
        return RawPage(label, label, "", "failed", now, f"{FAILURE_MARKER}: source reported unavailable")
    return RawPage(label, label, text, "ok", now, "")


class FixtureRetriever:
    """Returns mock page content from tests/fixtures/ keyed by company_id."""

    def __init__(self, fixture_dir: Path | None = None, force_failure_ids: frozenset[str] = frozenset()):
        self.fixture_dir = Path(fixture_dir) if fixture_dir else config.fixture_dir()
        self.force_failure_ids = frozenset(force_failure_ids)

    def fetch(self, company: Company, max_pages: int) -> list[RawPage]:
        key = "fixture-d" if company.company_id in self.force_failure_ids else company.company_id
        if key not in FIXTURE_FILES:
            label = f"mock://no-fixture/{company.company_id}"
            return [RawPage(label, label, "", "failed", utc_now_iso(), f"NO_FIXTURE: no fixture mapped to {company.company_id!r}")]
        filename, label = FIXTURE_FILES[key]
        path = self.fixture_dir / filename
        if not path.is_file():
            return [RawPage(label, label, "", "failed", utc_now_iso(), f"FIXTURE_MISSING: {filename}")]
        return [_page_from_text(label, path.read_text(encoding="utf-8"))][:max_pages]


class FileDropRetriever:
    """Reads human-saved page text from inputs/pages/<company_id>/*.txt in filename order."""

    def __init__(self, pages_root: Path | None = None):
        self.pages_root = Path(pages_root) if pages_root else config.project_root() / "inputs" / "pages"

    def fetch(self, company: Company, max_pages: int) -> list[RawPage]:
        folder = self.pages_root / company.company_id
        base_label = f"file://inputs/pages/{company.company_id}"
        if not folder.is_dir():
            return [RawPage(base_label + "/", base_label + "/", "", "failed", utc_now_iso(), f"NO_PAGES_SUPPLIED: {base_label}/ does not exist")]
        files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".txt")
        if not files:
            return [RawPage(base_label + "/", base_label + "/", "", "failed", utc_now_iso(), f"NO_PAGES_SUPPLIED: no .txt files in {base_label}/")]
        pages = []
        for path in files[:max_pages]:
            label = f"{base_label}/{path.name}"
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                pages.append(RawPage(label, label, "", "failed", utc_now_iso(), f"READ_ERROR: {exc}"))
                continue
            pages.append(_page_from_text(label, text))
        return pages


class LiveRetriever:
    """Live web retrieval. Deliberately refuses: no approved network path exists.

    This agent has no browser and no web tool, and SPEC-06 authorizes no network
    retrieval. A human must approve and own a permitted retrieval path first
    (ui-work-orders/006-01-live-page-retrieval.md). Until then, every call raises
    LiveCallBlocked. It never silently succeeds and never returns placeholder content.
    """

    def __init__(self, allow_network: bool | None = None, allow_live: bool | None = None):
        self.allow_network = config.env_flag("ALLOW_NETWORK_RETRIEVAL", config.ALLOW_NETWORK_RETRIEVAL) if allow_network is None else allow_network
        self.allow_live = config.env_flag("ALLOW_LIVE", config.ALLOW_LIVE) if allow_live is None else allow_live

    def fetch(self, company: Company, max_pages: int) -> list[RawPage]:
        if not (self.allow_network and self.allow_live):
            reason = "ALLOW_NETWORK_RETRIEVAL and ALLOW_LIVE are not both set by a human"
        else:
            reason = "the gates are set, but no human-approved retrieval implementation exists in this build"
        raise LiveCallBlocked(
            f"Live retrieval of {company.website_url!r} is blocked: {reason}. Human approval is required "
            "to choose and own a permitted browser/HTTP retrieval path (see ui-work-orders/"
            "006-01-live-page-retrieval.md). Until then, save page text to "
            f"inputs/pages/{company.company_id}/NN-<slug>.txt and use --retriever filedrop."
        )


@dataclass(frozen=True)
class RetrievalOutcome:
    pages: tuple[RawPage, ...]
    attempts: int
    ok: bool
    error: str


def retrieve_with_retry(
    retriever: Retriever,
    company: Company,
    max_pages: int | None = None,
    max_retries: int | None = None,
    on_attempt: Callable[[int], None] | None = None,
) -> RetrievalOutcome:
    """Initial request plus at most `max_retries` retries. Never loops beyond the cap."""
    pages_cap = config.max_pages() if max_pages is None else max_pages
    retries = config.max_retries() if max_retries is None else max_retries
    retries = min(retries, config.MAX_RETRIEVAL_RETRIES)
    last_error = ""
    pages: list[RawPage] = []
    attempts = 0
    for attempt in range(1, retries + 2):
        attempts = attempt
        if on_attempt:
            on_attempt(attempt)
        pages = list(retriever.fetch(company, pages_cap))[:pages_cap]
        if any(p.retrieval_status == "ok" and p.text.strip() for p in pages):
            return RetrievalOutcome(tuple(pages), attempts, True, "")
        errors = [p.error for p in pages if p.error] or ["no usable page content returned"]
        last_error = "; ".join(errors)
    return RetrievalOutcome(tuple(pages), attempts, False, last_error)

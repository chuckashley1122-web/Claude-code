"""Guardrails: price scan, source-claim scan, brand separation, release gate, Meta tripwire."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import config

# --- Price scanner (meeting-first: no price in generated copy) --------------------
_PRICE_WORDS = (
    r"setup fee",
    r"per month",
    r"dollars?",
    r"pricing",
    r"prices?",
    r"priced",
    r"fees?",
    r"monthly",
    r"costs?",
    r"usd",
)
_PRICE_PATTERNS = (
    re.compile(r"\d[\d,.]*\s*(?:usd|dollars?)\b", re.IGNORECASE),  # digits adjacent to currency word
    re.compile(r"(?:usd)\s*\d[\d,.]*", re.IGNORECASE),
    re.compile(r"\$\s*\d[\d,.]*(?:\s*/\s*\w+)?"),  # $650/mo, $250
    re.compile(r"\$"),
    re.compile(r"\b(?:" + "|".join(_PRICE_WORDS) + r")\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class Finding:
    kind: str
    start: int
    end: int
    text: str


def _scan(patterns, text: str, kind: str) -> list[Finding]:
    found: list[Finding] = []
    covered: list[tuple[int, int]] = []
    for pat in patterns:
        for m in pat.finditer(text):
            if any(s <= m.start() and m.end() <= e for s, e in covered):
                continue
            covered.append((m.start(), m.end()))
            found.append(Finding(kind, m.start(), m.end(), m.group(0)))
    return sorted(found, key=lambda f: f.start)


def scan_for_prices(text: str) -> list[Finding]:
    """Flag currency symbols, price words, and digit runs adjacent to a currency token."""
    return _scan(_PRICE_PATTERNS, text or "", "price")


# --- Source-author (presenter) claims -------------------------------------------------
# Copied from SPEC-06 section 8: presenter targets that are UNSUBSTANTIATED for CA&J.
UNSUBSTANTIATED = (
    "50 automations",
    "approximately 50 automations per year",
    "one hour",
    "one-hour MVP",
    "roughly one hour",
    "seven days",
    "seven-day improvement",
    "Agent OS",
)
_CLAIM_PATTERNS = tuple(
    re.compile(r"\b" + re.escape(p).replace(r"\ ", r"\s+") + r"\b", re.IGNORECASE) for p in UNSUBSTANTIATED
)


def scan_for_source_claims(text: str) -> list[Finding]:
    return _scan(_CLAIM_PATTERNS, text or "", "source_claim")


# --- Brand separation ------------------------------------------------------------------
_BRAND_PATTERNS = tuple(
    re.compile(re.escape(t).replace("'", "['’]"), re.IGNORECASE) for t in config.CONSUMER_BRAND_TERMS
)


def scan_for_consumer_brands(text: str) -> list[Finding]:
    """CA-J B2B output must never mention a consumer brand."""
    return _scan(_BRAND_PATTERNS, text or "", "consumer_brand")


# --- Frozen Meta campaign tripwire ---------------------------------------------------------
class FrozenCampaignViolation(RuntimeError):
    """Any action that targets the frozen live Meta campaign."""


def assert_meta_campaign_untouched(campaign_id: str, action: str) -> None:
    if campaign_id == config.FROZEN_META_CAMPAIGN_ID:
        raise FrozenCampaignViolation(
            f"Refused {action!r} on {campaign_id}: this live Meta campaign is frozen "
            "(editing resets its learning phase; spend is a financial action). No action of any kind is allowed."
        )


# --- Release gate ----------------------------------------------------------------------------
REQUIRED_TESTS = tuple(f"T0{i}" for i in range(1, 9))


@dataclass(frozen=True)
class GateEvidence:
    file_ops_ok: bool
    tests_passed: dict = field(default_factory=dict)  # "T01".."T08" -> bool, from an executed run
    real_runs_validated: int = 0  # non-fixture runs that passed structural validation
    live_pilots_source_checked: int = 0  # real runs whose source mappings a human inspected (T09)
    latest_two_runs_valid: bool = False
    seven_day_entries: int = 0  # recorded ledger rows, never backfilled
    user_review_received: bool = False


def release_gate_report(ev: GateEvidence) -> tuple[str, list[str]]:
    """Return (status, gate lines). Honest lower status unless every gate has evidence."""
    lines: list[str] = []
    if not ev.file_ops_ok:
        lines.append("file write/read probe: FAILED")
        return "ENVIRONMENT_BLOCKED", lines
    lines.append("file write/read probe: passed")

    missing = [t for t in REQUIRED_TESTS if ev.tests_passed.get(t) is not True]
    if missing:
        lines.append(f"T01-T08: not all passed (outstanding: {', '.join(missing)})")
        return "SPECIFICATION_READY", lines
    lines.append("T01-T08: all passed")

    if ev.real_runs_validated < 1:
        lines.append("real (non-fixture) run passing validation: none yet (INPUT_REQUIRED)")
        return "SPECIFICATION_READY", lines
    lines.append(f"real runs passing validation: {ev.real_runs_validated}")

    v1_gates = {
        "at least one live pilot source-checked": ev.live_pilots_source_checked >= 1,
        "latest two runs pass structural validation": ev.latest_two_runs_valid,
        "seven-day ledger has 7 recorded entries": ev.seven_day_entries >= 7,
    }
    for name, passed in v1_gates.items():
        lines.append(f"{name}: {'passed' if passed else 'outstanding'}")
    if all(v1_gates.values()):
        if ev.user_review_received:
            return "V1_READY", lines
        lines.append("usefulness feedback from Chuck: outstanding")
        return "USER_REVIEW_PENDING", lines
    if ev.seven_day_entries >= 1:
        return "PILOT_IN_PROGRESS", lines
    return "MVP_TESTED", lines


def release_gate_status(ev: GateEvidence) -> str:
    status, _ = release_gate_report(ev)
    assert status in config.HANDOFF_STATUSES
    return status

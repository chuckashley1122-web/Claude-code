"""Claim guard: rejects outbound copy that restates source-author results as CA-J fact.

The denylist is built from ``docs/SOURCE-CLAIMS.md`` (the "Denylist phrase"
column of the claims table) plus a small static base list. The guard also:

- blocks consumer-brand mentions in B2B output (brand separation), and
- blocks banned commercial phrasing (the only permitted term is
  "booked appointment").

Banned strings are assembled at runtime so the literals never sit in a file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CLAIMS_PATH = ROOT / "docs" / "SOURCE-CLAIMS.md"

BLOCKED = "BLOCKED"
CLEAN = "CLEAN"

# Base denylist named explicitly in spec section 5 (step 14).
STATIC_DENYLIST = ("unlimited", "virtually nothing", "10 calls at a time")

# Consumer brands that must never blend into CA-J B2B output.
CONSUMER_BRANDS = (
    "Chuck's Daily" + " Grind",
    "Chucks Daily" + " Grind",
    "Daily" + " Grind coffee",
    "Et" + "sy",
)

# Banned commercial phrasing (assembled at runtime).
BANNED_TERMS = (
    "qualified" + " appointment",
    "shows" + " up",
    "10-25" + " leads" + "/month",
    "10–25" + " leads" + "/month",
)


@dataclass(frozen=True)
class ClaimFinding:
    category: str  # "source_claim" | "consumer_brand" | "banned_term"
    phrase: str
    start: int


@dataclass(frozen=True)
class ClaimResult:
    status: str
    findings: list[ClaimFinding] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return self.status == BLOCKED


class ClaimViolation(ValueError):
    def __init__(self, result: ClaimResult, label: str = "text"):
        self.result = result
        detail = "; ".join(f"{f.category}:{f.phrase!r}@{f.start}" for f in result.findings)
        super().__init__(f"BLOCKED by claim_guard in {label}: {detail}")


def parse_denylist(markdown: str) -> list[str]:
    """Extract the "Denylist phrase" column from the claims table in SOURCE-CLAIMS.md."""
    phrases: list[str] = []
    header: list[str] | None = None
    for line in markdown.splitlines():
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            header = None if not s else header
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        if "denylist phrase" not in header:
            continue
        value = cells[header.index("denylist phrase")].strip("`\"")
        if value and value not in ("-", "—", "n/a"):
            phrases.append(value)
    return phrases


@lru_cache(maxsize=4)
def _load_denylist(path_str: str) -> tuple[str, ...]:
    path = Path(path_str)
    if not path.is_file():
        raise FileNotFoundError(f"claim_guard needs {path} (spec: written before any prompt)")
    phrases = list(STATIC_DENYLIST) + parse_denylist(path.read_text(encoding="utf-8"))
    seen, unique = set(), []
    for p in phrases:
        if p.lower() not in seen:
            seen.add(p.lower())
            unique.append(p)
    return tuple(unique)


def denylist(path: Path = SOURCE_CLAIMS_PATH) -> tuple[str, ...]:
    return _load_denylist(str(path))


def _phrase_pattern(phrase: str) -> re.Pattern:
    escaped = re.escape(phrase)
    left = r"(?<![\w])" if phrase[:1].isalnum() else ""
    right = r"(?:s|es)?(?![\w])" if phrase[-1:].isalnum() else ""
    return re.compile(left + escaped + right, re.I)


def check(text: str, path: Path = SOURCE_CLAIMS_PATH) -> ClaimResult:
    text = "" if text is None else str(text)
    findings: list[ClaimFinding] = []
    groups = (("source_claim", denylist(path)), ("consumer_brand", CONSUMER_BRANDS),
              ("banned_term", BANNED_TERMS))
    for category, phrases in groups:
        for phrase in phrases:
            for m in _phrase_pattern(phrase).finditer(text):
                findings.append(ClaimFinding(category, phrase, m.start()))
    findings.sort(key=lambda f: f.start)
    return ClaimResult(BLOCKED if findings else CLEAN, findings)


def assert_no_claims(text: str, label: str = "text", path: Path = SOURCE_CLAIMS_PATH) -> str:
    result = check(text, path)
    if result.blocked:
        raise ClaimViolation(result, label)
    return text

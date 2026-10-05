"""Claim guard.

Blocks text that restates a source author's results, numbers, or anchors as if
they were CA-J facts, plus the standing rules: no unlimited-usage claims, no
guarantees, no invented review counts or testimonials, no first-person
quantitative results, and no consumer-brand mentions in B2B copy.

The SC-xx ids mirror the claim table in docs/SOURCE-CLAIMS.md; a unit test keeps
the two in sync. The literal source figures appear here only as a denylist.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Source-claim denylist: (claim id from docs/SOURCE-CLAIMS.md, regex).
SOURCE_CLAIM_DENYLIST: tuple[tuple[str, str], ...] = (
    ("SC-01", r"\$\s?197\b"),  # source recurring-fee draft default
    ("SC-02", r"\$\s?0(?:\.00)?\s+(?:for\s+)?(?:standard\s+)?(?:set[\s-]?up|install)"),
    ("SC-03", r"\$\s?97\b"),  # trainer range lower bound
    ("SC-04", r"\$\s?297\b"),  # trainer range upper bound / attendee sale
    ("SC-05", r"\$\s?9\.99\b"),  # ambiguous upsell transcription
    ("SC-06", r"\bvirtually\s+nothing\b"),
    ("SC-07", r"\b(?:demo|demonstration)s?\b[^.!?\n]*\b(?:in|within|under)\s+(?:about\s+|just\s+)?15\s*-?\s*min"),
    ("SC-08", r"\b30\s*(?:-|–|to)\s*90\s+(?:emails?|messages?)\b"),
    ("SC-09", r"\b50\s+(?:calls|dials)\b"),
    ("SC-10", r"\b(?:low|no|zero|minimal)[\s-]churn\b"),
    ("SC-11", r"\bvaluations?\b"),
    ("SC-12", r"\$\s?1,?000\s+plus\s+\$\s?2,?000"),
    ("SC-13", r"\$\s?27\b|\$\s?397\b"),
    ("SC-14", r"\blow[\s-]maintenance\b"),
)

# Standing rules (not tied to one source line).
STANDING_RULES: tuple[tuple[str, str], ...] = (
    ("RULE-UNLIMITED", r"\bunlimited\b"),
    ("RULE-GUARANTEE", r"\bguarantee(?:d|s)?\b"),
    ("RULE-REVIEWS", r"\b\d[\d,]*\+?\s+(?:(?:five|5)[\s-]star\s+)?reviews?\b|\b[1-5](?:\.\d)?[\s-]stars?\b|\btestimonials?\b"),
    ("RULE-CONSUMER-BRAND", r"\bdaily\s+grind\b|\betsy\b|\bprintables?\b"),
)

_SUBJECT_RE = re.compile(r"\b(?:we|we've|we're|our|us|ca-?j|ca&j)\b", re.IGNORECASE)
_RESULT_RE = re.compile(
    r"\b(?:recover(?:ed|s)?|generat(?:ed|es)|earn(?:ed|s)?|made|sav(?:ed|es)|booked|closed|"
    r"gr[eo]w|grown|increas(?:ed|es)|doubled|tripled|revenue|profits?|roi|churn|valuations?|"
    r"results?|clients?|customers|leads)\b",
    re.IGNORECASE,
)
_QUANTITY_RE = re.compile(r"\d|\$|%")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

_COMPILED = [(cid, re.compile(p, re.IGNORECASE)) for cid, p in SOURCE_CLAIM_DENYLIST + STANDING_RULES]


@dataclass(frozen=True)
class ClaimHit:
    rule: str
    match: str


class ClaimViolation(ValueError):
    def __init__(self, hits: list[ClaimHit]):
        self.hits = hits
        found = "; ".join(f"{h.rule}: {h.match!r}" for h in hits)
        super().__init__(
            "Blocked claim(s): source-author results, unverified figures, or brand mixing "
            f"may not be stated as CA-J facts. {found}"
        )


def denylist_ids() -> set[str]:
    return {cid for cid, _ in SOURCE_CLAIM_DENYLIST}


def find_violations(text: str) -> list[ClaimHit]:
    text = text or ""
    hits = [ClaimHit(cid, m.group(0)) for cid, rx in _COMPILED for m in rx.finditer(text)]
    for sentence in _SENTENCE_SPLIT.split(text):
        if _SUBJECT_RE.search(sentence) and _RESULT_RE.search(sentence) and _QUANTITY_RE.search(sentence):
            hits.append(ClaimHit("RULE-ATTRIBUTION", sentence.strip()))
    return hits


def is_clean(text: str) -> bool:
    return not find_violations(text)


def assert_clean(text: str) -> str:
    hits = find_violations(text)
    if hits:
        raise ClaimViolation(hits)
    return text

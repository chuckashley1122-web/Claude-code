"""Scan every generated .md/.json/.jsonl/.html file for banned patterns.
Fails (exit 1) on any hit. Writes a per-file report to out/compliance_report.md.

Rules:
  secret          real secret/token patterns (sk-, EAAG, ghp_, AKIA, private keys, key=value tokens)
  stale_location  the disallowed (source) GHL location ID
  frozen_campaign the frozen live campaign name outside ui-tasks/ checklists
  mangled_id      a house GHL ID in the wrong case
  banned_phrase   banned phrasing or the forbidden phone number
  consumer_brand  a consumer brand inside B2B output
  meeting_first   any price/currency in prospect-facing copy
  unlabeled_money a currency figure in out/ that is not labeled assumption / source example /
                  unverified / locked CA-J term (internal files only), and not inside a
                  DO-NOT-USE-AS-PROOF block (i.e. a figure that could read as a CA-J result)
  roi_claim       an ROI multiple outside a DO-NOT-USE-AS-PROOF block
  forbidden_status an asset/test status of Live or Ready for launch

Run: python tools/compliance_scan.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from tools import guardrails as G  # noqa: E402

SCAN_DIRS = ["out", "config", "ui-tasks"]
SCAN_SUFFIXES = {".md", ".json", ".jsonl", ".html"}
REPORT_NAMES = {"compliance_report.md", "compliance_report.json"}
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\bEAAG[A-Za-z0-9]{10,}"),
    re.compile(r"\bEAA[A-Z][A-Za-z0-9]{30,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bxox[abpr]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|secret|password|bearer)\b\s*[:=]\s*[\"']?[A-Za-z0-9_\-\.]{16,}"),
    re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"),
]
MEETING_FIRST_PATHS = ("out/messages/", "out/copy/", "out/creatives/", "out/precall_page/", "out/welcome_page/")
MEETING_FIRST_FILES = {"out/form_spec.md", "out/qualification_logic.json", "out/positioning.md"}
INTERNAL_PRICING_FILES = {"out/offer_spec.md", "out/close_pack.md"}
MONEY_LABELS = ["assumption", "source example", "unverified"]
LOCKED_LABEL = "locked ca-j"
ROI_RE = re.compile(r"\b\d+(?:\.\d+)?\s*[xX]\s*ROI\b|\bROI\s+of\s+\d", re.IGNORECASE)
STATUS_RE = re.compile(r"\"(?:status|verdict)\"\s*:\s*\"(Live|Ready for launch)\"")


def _proof_mask(lines: list[str]) -> list[bool]:
    inside, mask = False, []
    for ln in lines:
        if "DO-NOT-USE-AS-PROOF:START" in ln:
            inside = True
        mask.append(inside)
        if "DO-NOT-USE-AS-PROOF:END" in ln:
            inside = False
    return mask


def scan_text(rel: str, text: str) -> list[dict]:
    hits: list[dict] = []
    lines = text.splitlines()
    mask = _proof_mask(lines)

    def hit(rule, lineno, detail):
        hits.append({"file": rel, "line": lineno, "rule": rule, "detail": detail})

    is_out = rel.startswith("out/")
    meeting_first = rel.startswith(MEETING_FIRST_PATHS) or rel in MEETING_FIRST_FILES
    for i, ln in enumerate(lines, 1):
        for pat in SECRET_PATTERNS:
            if pat.search(ln):
                hit("secret", i, pat.pattern)
        if C.DISALLOWED_LOCATION_ID.lower() in ln.lower():
            hit("stale_location", i, "disallowed GHL location ID")
        if C.FROZEN_CAMPAIGN_NAME.lower() in ln.lower() and not rel.startswith("ui-tasks/"):
            hit("frozen_campaign", i, "frozen campaign name outside checklists")
        for name, exact in C.HOUSE_IDS.items():
            for m in re.finditer(re.escape(exact), ln, re.IGNORECASE):
                if m.group(0) != exact:
                    hit("mangled_id", i, f"{name} in wrong case: {m.group(0)}")
        for p in G.find_banned_phrases(ln):
            hit("banned_phrase", i, p)
        for b in C.CONSUMER_BRANDS:
            if b.lower() in ln.lower():
                hit("consumer_brand", i, b)
        if STATUS_RE.search(ln):
            hit("forbidden_status", i, STATUS_RE.search(ln).group(1))
        if meeting_first:
            for m in G.find_price_mentions(ln):
                hit("meeting_first", i, m)
        if is_out and not mask[i - 1]:
            money = G.find_currency(ln)
            if money:
                low = ln.lower()
                labeled = any(lbl in low for lbl in MONEY_LABELS) or (LOCKED_LABEL in low and rel in INTERNAL_PRICING_FILES)
                if not labeled and not meeting_first:
                    hit("unlabeled_money", i, ", ".join(money))
            if ROI_RE.search(ln):
                hit("roi_claim", i, ROI_RE.search(ln).group(0))
    return hits


def iter_files(root: Path):
    for d in SCAN_DIRS:
        base = root / d
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.suffix in SCAN_SUFFIXES and p.name not in REPORT_NAMES:
                yield p


def scan_tree(root: Path = BUILD_ROOT) -> dict:
    report = {}
    for p in iter_files(root):
        rel = p.relative_to(root).as_posix()
        report[rel] = scan_text(rel, p.read_text(encoding="utf-8"))
    return report


def write_report(root: Path, report: dict) -> Path:
    total = sum(len(v) for v in report.values())
    lines = ["# Compliance scan report", "", f"Files scanned: {len(report)}. Hits: {total}.", "", "| File | Hits |", "|---|---|"]
    lines += [f"| {f} | {len(h)} |" for f, h in report.items()]
    if total:
        lines += ["", "## Hits", "", "| File | Line | Rule | Detail |", "|---|---|---|---|"]
        lines += [f"| {h['file']} | {h['line']} | {h['rule']} | {h['detail']} |" for hs in report.values() for h in hs]
    path = root / "out" / "compliance_report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    report = scan_tree(BUILD_ROOT)
    for f, hits in report.items():
        print(f"{'CLEAN' if not hits else 'HITS ' + str(len(hits))}  {f}")
        for h in hits:
            print(f"    line {h['line']}: {h['rule']} - {h['detail']}")
    write_report(BUILD_ROOT, report)
    total = sum(len(v) for v in report.values())
    print(f"compliance_scan: {len(report)} files, {total} hits")
    if not report:
        print("compliance_scan: nothing to scan; run tools/build_all.py first")
        return 1
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())

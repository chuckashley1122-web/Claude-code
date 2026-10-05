"""Structural validator for a run folder. Any finding means failure (non-zero exit).

Works from the files on disk alone, so it proves source binding rather than trusting
the in-memory pipeline. Usage: python -m src.output_validation outputs/<run_id>
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

import config
from src import guards

MISSING = config.MISSING_LABEL
ARTIFACTS = ("brief.md", "results.csv", "evidence.md", "run.json")
FACT_COLUMNS = ("service_area", "services", "contact_method", "observation")
_NEAR_MISSING = re.compile(r"^\s*(?:n/?a|none|unknown|not found.*|missing|-+)?\s*$", re.IGNORECASE)


def _split_row(line: str) -> list[str]:
    cells, buf, i = [], [], 0
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body):
            buf.append(body[i + 1])
            i += 2
            continue
        if ch == "|":
            cells.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
        i += 1
    cells.append("".join(buf).strip())
    return cells


def parse_evidence(text: str) -> tuple[list[dict], dict[str, dict]]:
    """Return (claims, excerpts by claim_id) from evidence.md."""
    lines = text.splitlines()
    claims: list[dict] = []
    excerpts: dict[str, dict] = {}
    section = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            section = line[3:].strip()
        elif section == "Claim-to-source mapping" and line.startswith("| C"):
            cells = _split_row(line)
            if len(cells) == 7:
                keys = ("claim_id", "company_id", "field", "value", "matched_text", "source_label", "retrieved_at_utc")
                claims.append(dict(zip(keys, cells)))
        elif section == "Verbatim excerpts" and line.startswith("### C"):
            cid = line[4:].strip()
            label, body = "", None
            j = i + 1
            while j < len(lines) and not lines[j].startswith("`"):
                if lines[j].startswith("source_label: "):
                    label = lines[j][len("source_label: "):].strip()
                j += 1
            if j < len(lines):
                fence = re.match(r"`+", lines[j]).group(0)
                k = j + 1
                buf = []
                while k < len(lines) and lines[k] != fence:
                    buf.append(lines[k])
                    k += 1
                body = "\n".join(buf)
                i = k
            excerpts[cid] = {"source_label": label, "excerpt": body or ""}
        i += 1
    return claims, excerpts


def validate_run_dir(run_dir: Path, expected_ids: list[str] | None = None) -> list[str]:
    run_dir = Path(run_dir)
    findings: list[str] = []
    for name in ARTIFACTS:
        if not (run_dir / name).is_file():
            findings.append(f"missing artifact: {name}")
    if findings:
        return findings

    # run.json
    try:
        manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"run.json is not valid JSON: {exc}"]
    if set(manifest) != set(config.RUN_JSON_KEYS):
        findings.append(f"run.json keys mismatch: {sorted(set(manifest) ^ set(config.RUN_JSON_KEYS))}")
    fixture_mode = manifest.get("fixture_mode")
    if not isinstance(fixture_mode, bool):
        findings.append("run.json fixture_mode must be a boolean")

    # results.csv
    with (run_dir / "results.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows or ",".join(rows[0]) != config.RESULTS_CSV_HEADER:
        findings.append("results.csv header does not match the contract")
        return findings
    records = [dict(zip(rows[0], r)) for r in rows[1:]]
    if any(len(r) != len(rows[0]) for r in rows[1:]):
        findings.append("results.csv has a row with the wrong number of cells")

    ids = [r["company_id"] for r in records]
    for cid, n in Counter(ids).items():
        if n != 1:
            findings.append(f"company_id {cid!r} appears {n} times")
    if expected_ids is not None and sorted(ids) != sorted(expected_ids):
        findings.append(f"accepted ids {sorted(expected_ids)} != CSV ids {sorted(ids)}")

    if manifest.get("record_count") != len(records):
        findings.append(f"record_count {manifest.get('record_count')} != CSV rows {len(records)}")
    tally = {s: 0 for s in config.COMPANY_STATUSES}
    for r in records:
        if r["status"] not in config.COMPANY_STATUSES:
            findings.append(f"{r['company_id']}: invalid status {r['status']!r}")
        else:
            tally[r["status"]] += 1
    if manifest.get("counts_by_status") != tally:
        findings.append(f"counts_by_status {manifest.get('counts_by_status')} != CSV tally {tally}")
    if manifest.get("overall_status") not in config.RUN_STATUSES:
        findings.append(f"invalid overall_status {manifest.get('overall_status')!r}")

    # evidence.md claim binding
    claims, excerpts = parse_evidence((run_dir / "evidence.md").read_text(encoding="utf-8"))
    by_key: dict[tuple[str, str], list[dict]] = {}
    for c in claims:
        by_key.setdefault((c["company_id"], c["field"]), []).append(c)
        ex = excerpts.get(c["claim_id"], {})
        if not c["source_label"]:
            findings.append(f"{c['claim_id']}: empty source label")
        if not ex.get("excerpt"):
            findings.append(f"{c['claim_id']}: no verbatim excerpt")
        elif c["matched_text"].casefold() not in ex["excerpt"].casefold():
            findings.append(f"{c['claim_id']}: matched text not found in its excerpt")
        if ex and ex.get("source_label") != c["source_label"]:
            findings.append(f"{c['claim_id']}: excerpt label differs from claim label")

    for r in records:
        cid = r["company_id"]
        for col in FACT_COLUMNS + ("hypothesis",):
            value = r[col]
            if value == MISSING:
                continue
            if _NEAR_MISSING.match(value):
                findings.append(f"{cid}.{col}: missing value must read exactly {MISSING!r}, got {value!r}")
                continue
            if r["status"] == "blocked":
                findings.append(f"{cid}.{col}: blocked company carries a fact")
                continue
            if col == "hypothesis":
                if r["observation"] == MISSING:
                    findings.append(f"{cid}.hypothesis present without a sourced observation")
                if not (value.startswith("If ") and ", then " in value):
                    findings.append(f"{cid}.hypothesis does not follow the If/then template")
                continue
            bound = by_key.get((cid, col), [])
            if not bound:
                findings.append(f"{cid}.{col}: factual value has no source claim in evidence.md")
                continue
            if col == "services":
                listed = [s.strip() for s in value.split(",")]
                if sorted(listed) != sorted(c["value"] for c in bound):
                    findings.append(f"{cid}.services: CSV list {listed} != sourced claims")
            elif not any(c["value"].casefold() in value.casefold() for c in bound):
                findings.append(f"{cid}.{col}: CSV value not supported by its claim")
        for col in ("observation", "hypothesis"):
            for f in guards.scan_for_prices(r[col]):
                findings.append(f"{cid}.{col}: price token {f.text!r}")
            for f in guards.scan_for_consumer_brands(r[col]):
                findings.append(f"{cid}.{col}: consumer brand {f.text!r}")
        labels = [s.strip() for s in r["source_urls"].split(";") if s.strip()]
        if fixture_mode is True and any(l.lower().startswith("http") for l in labels + [r["resolved_url"]]):
            findings.append(f"{cid}: fixture run has an http-resolved source label")

    # brief.md
    brief = (run_dir / "brief.md").read_text(encoding="utf-8")
    if "Draft for Chuck's review" not in brief:
        findings.append("brief.md lacks the review status line")
    for f in guards.scan_for_prices(brief):
        findings.append(f"brief.md: price token {f.text!r}")
    for f in guards.scan_for_source_claims(brief):
        findings.append(f"brief.md: source-author claim {f.text!r}")
    for f in guards.scan_for_consumer_brands(brief):
        findings.append(f"brief.md: consumer brand {f.text!r}")
    for cid in ids:
        if f"## {cid} - " not in brief:
            findings.append(f"brief.md: no section for {cid}")
    section = ""
    for line in brief.splitlines():
        if line.startswith("### "):
            section = line[4:].strip()
        elif section == "Verified facts" and line.startswith("- ") and line != "- None":
            if not re.search(r"\[source: [^\]]+\]", line):
                findings.append(f"brief.md: fact without a source: {line!r}")
        elif section == "Missing information" and line.startswith("- ") and line != "- None":
            if not line.endswith(": " + MISSING):
                findings.append(f"brief.md: missing field not labeled exactly: {line!r}")

    # fixture / live separation
    if fixture_mode is False:
        for name in ARTIFACTS:
            if "mock://" in (run_dir / name).read_text(encoding="utf-8"):
                findings.append(f"{name}: mock:// label in a non-fixture run")
    return findings


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python -m src.output_validation <run_dir>")
        return 2
    findings = validate_run_dir(Path(argv[0]))
    if findings:
        print(f"VALIDATION FAILED ({len(findings)} finding(s)):")
        for f in findings:
            print(f"  - {f}")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

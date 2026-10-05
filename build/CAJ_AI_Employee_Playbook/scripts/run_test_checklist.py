"""Record acceptance-test results (T01-T12) and report outstanding tests.

Non-interactive. The checklist definition lives in tests/T01-T12.csv (never
edited by this tool); results are written to records/Test_Results.csv, one row
per test (a re-record replaces the previous row and stamps retest_date).

Usage (from the build root):
    python3 scripts/run_test_checklist.py                      # report only
    python3 scripts/run_test_checklist.py --test-id T03 --result PASS \
        --evidence "GHL appointment id + screenshot path" --actual "booked 9am slot"
    python3 scripts/run_test_checklist.py --test-id T11 --result N/A --reason "voice not in scope"

Exit codes:
    0  every critical test is PASS (or N/A with a recorded reason)
    1  at least one critical test is outstanding (the default state of this repo)
    2  the submitted result was rejected (e.g. PASS without a real evidence reference)
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "tests" / "T01-T12.csv"
RESULTS = ROOT / "records" / "Test_Results.csv"
RESULT_COLUMNS = ["test_id", "pass_condition", "actual_result", "evidence_ref", "result", "fix", "retest_date"]
RESULTS_ALLOWED = ("PASS", "FAIL", "NOT_RUN", "N/A")

_SELF_REFERENCES = {
    "self", "same", "this", "this test", "see above", "above", "see test", "n/a", "na", "none",
    "nil", "null", "-", "--", "tbd", "todo", "pass", "passed", "ok", "okay", "yes", "true", "done",
    "verified", "works", "worked", "tested", "evidence", "needs_evidence", "it passed",
    "test_results.csv", "t01-t12.csv", "records/test_results.csv", "tests/t01-t12.csv",
}
_TRIVIAL_RE = re.compile(r"^(?:t\d{2}\s*[:\-]?\s*)?(?:pass(?:ed)?|ok|done|yes|verified|works?|tested)$")


class RejectedResult(ValueError):
    pass


def load_checklist(path: Path = CHECKLIST) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_results(path: Path = RESULTS) -> dict[str, dict]:
    if not path.is_file():
        return {}
    with path.open(newline="", encoding="utf-8") as fh:
        return {row["test_id"]: row for row in csv.DictReader(fh)}


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d * 2 > 9 else d * 2
        total += d
        alt = not alt
    return total % 10 == 0


def contains_card_number(text: str) -> bool:
    """True when ``text`` holds a 13-19 digit Luhn-valid run (card data must never be logged)."""
    for m in re.finditer(r"(?:\d[ -]?){13,19}", text):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            return True
    return False


def evidence_problem(evidence: str, test: dict) -> str | None:
    """Return why ``evidence`` is not acceptable for a PASS, or None if it is."""
    ev = (evidence or "").strip()
    norm = ev.lower()
    if not ev:
        return "evidence reference is empty"
    if not re.search(r"[A-Za-z0-9]", ev):
        return "evidence reference has no content"
    if norm in _SELF_REFERENCES or _TRIVIAL_RE.match(norm):
        return f"evidence reference {ev!r} is self-referential, not evidence"
    own = {test["test_id"].lower(), test["test_name"].lower(), test["pass_condition"].lower(),
           f"{test['test_id']} {test['test_name']}".lower()}
    if norm in own:
        return f"evidence reference {ev!r} only restates the test itself"
    if contains_card_number(ev):
        return "evidence reference appears to contain card data; never record card numbers"
    return None


def validate_submission(test: dict, result: str, evidence: str, reason: str) -> None:
    if result not in RESULTS_ALLOWED:
        raise RejectedResult(f"result must be one of {RESULTS_ALLOWED}")
    if result == "PASS":
        problem = evidence_problem(evidence, test)
        if problem:
            raise RejectedResult(f"PASS refused for {test['test_id']}: {problem}")
    if result == "N/A" and not (reason or "").strip():
        raise RejectedResult(f"N/A refused for {test['test_id']}: a reason (out-of-scope feature) is required")
    for text in (evidence, reason):
        if text and contains_card_number(text):
            raise RejectedResult("submission appears to contain card data; never record card numbers")


def record_result(test: dict, result: str, evidence: str, actual: str, fix: str, reason: str,
                  results_path: Path = RESULTS, today: date | None = None) -> dict:
    validate_submission(test, result, evidence, reason)
    results = load_results(results_path)
    previous = results.get(test["test_id"])
    row = {
        "test_id": test["test_id"],
        "pass_condition": test["pass_condition"],
        "actual_result": actual.strip() if result != "N/A" else f"N/A: {reason.strip()}",
        "evidence_ref": evidence.strip(),
        "result": result,
        "fix": fix.strip(),
        "retest_date": (today or date.today()).isoformat() if previous else "",
    }
    results[test["test_id"]] = row
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=RESULT_COLUMNS)
        writer.writeheader()
        for tid in sorted(results):
            writer.writerow({k: results[tid].get(k, "") for k in RESULT_COLUMNS})
    return row


def outstanding(checklist: list[dict], results: dict[str, dict]) -> list[tuple[dict, str]]:
    """Critical tests that are not PASS (N/A counts as resolved only with a reason)."""
    out = []
    for test in checklist:
        if test.get("critical", "yes").strip().lower() != "yes":
            continue
        row = results.get(test["test_id"])
        state = row["result"] if row else "NOT_RUN"
        if state == "PASS" and row and evidence_problem(row.get("evidence_ref", ""), test) is None:
            continue
        if state == "N/A" and row and row.get("actual_result", "").startswith("N/A: ") and len(row["actual_result"]) > 5:
            continue
        out.append((test, state))
    return out


def report(checklist: list[dict], results: dict[str, dict]) -> int:
    pending = outstanding(checklist, results)
    print(f"{'test':<5} {'name':<18} {'result':<8} evidence")
    print("-" * 60)
    for test in checklist:
        row = results.get(test["test_id"], {})
        print(f"{test['test_id']:<5} {test['test_name']:<18} {row.get('result', 'NOT_RUN'):<8} "
              f"{row.get('evidence_ref', '') or '-'}")
    if pending:
        print(f"OUTSTANDING: {len(pending)} critical test(s) not PASS: "
              + ", ".join(f"{t['test_id']}({s})" for t, s in pending))
        print("Activation is NOT allowed until every enabled-channel critical test passes.")
        return 1
    print("All critical tests PASS (or N/A with reason). Activation still requires human approval.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Record T01-T12 results; refuse PASS without evidence.")
    ap.add_argument("--test-id")
    ap.add_argument("--result", choices=RESULTS_ALLOWED)
    ap.add_argument("--evidence", default="")
    ap.add_argument("--actual", default="")
    ap.add_argument("--fix", default="")
    ap.add_argument("--reason", default="", help="required with --result N/A")
    ap.add_argument("--checklist", type=Path, default=CHECKLIST)
    ap.add_argument("--results", type=Path, default=RESULTS)
    args = ap.parse_args(argv)

    checklist = load_checklist(args.checklist)
    if args.test_id or args.result:
        if not (args.test_id and args.result):
            print("REJECTED: --test-id and --result must be given together")
            return 2
        test = next((t for t in checklist if t["test_id"] == args.test_id.upper()), None)
        if test is None:
            print(f"REJECTED: unknown test id {args.test_id!r}")
            return 2
        try:
            row = record_result(test, args.result, args.evidence, args.actual, args.fix, args.reason,
                                args.results)
        except RejectedResult as exc:
            print(f"REJECTED: {exc}")
            return 2
        print(f"RECORDED: {row['test_id']} = {row['result']} (evidence: {row['evidence_ref'] or '-'})")
    return report(checklist, load_results(args.results))


if __name__ == "__main__":
    sys.exit(main())

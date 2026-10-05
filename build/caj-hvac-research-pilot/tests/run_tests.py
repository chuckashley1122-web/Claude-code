"""Run the full stdlib unittest suite, print pass/fail counts, exit non-zero on any failure.

    python tests/run_tests.py

Also prints a per-test-ID (T01-T08) summary, the release-gate status those executed
results support, and saves the literal output to evidence/test_run_latest.txt.
"""

from __future__ import annotations

import io
import re
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from src.guards import REQUIRED_TESTS, GateEvidence, release_gate_report  # noqa: E402

T_ID = re.compile(r"test_(T0\d)_")


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes: list[tuple[str, str]] = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcomes.append((test.id(), "pass"))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcomes.append((test.id(), "FAIL"))

    def addError(self, test, err):
        super().addError(test, err)
        self.outcomes.append((test.id(), "ERROR"))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.outcomes.append((test.id(), "skip"))

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.outcomes.append((test.id(), "FAIL"))


def per_test_id(outcomes) -> dict[str, str]:
    summary: dict[str, list[str]] = {t: [] for t in REQUIRED_TESTS}
    for test_id, status in outcomes:
        m = T_ID.search(test_id)
        if m and m.group(1) in summary:
            summary[m.group(1)].append(status)
    return {t: ("not run" if not s else ("pass" if all(x == "pass" for x in s) else "FAIL")) + f" ({len(s)} test(s))"
            for t, s in summary.items()}


def file_probe_ok() -> bool:
    probe = ROOT / "evidence" / "file_probe.txt"
    return probe.is_file() and probe.read_text(encoding="utf-8").strip() == "FILE_OK"


def main() -> int:
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py", top_level_dir=str(ROOT / "tests"))
    runner = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordingResult)
    result = runner.run(suite)

    failed = len(result.failures) + len(result.errors)
    passed = result.testsRun - failed - len(result.skipped)
    by_id = per_test_id(result.outcomes)
    gate_status, gate_lines = release_gate_report(GateEvidence(
        file_ops_ok=file_probe_ok(),
        tests_passed={t: s.startswith("pass") for t, s in by_id.items()},
        real_runs_validated=0,  # no real company input exists yet (INPUT_REQUIRED)
    ))

    lines = [
        f"run_tests.py at {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} "
        f"(python {sys.version.split()[0]}, workflow {config.WORKFLOW_VERSION})",
        "",
        stream.getvalue().rstrip(),
        "",
        "Per-test-ID results:",
        *[f"  {t}: {s}" for t, s in by_id.items()],
        "  T09: not run (live pilot needs real URLs and human-supplied pages)",
        "",
        f"Release gate (from these executed results): {gate_status}",
        *[f"  - {ln}" for ln in gate_lines],
        "",
        f"Ran {result.testsRun} tests: {passed} passed, {failed} failed, {len(result.skipped)} skipped",
        "RESULT: " + ("OK" if failed == 0 else "FAILED"),
    ]
    output = "\n".join(lines)
    print(output)
    evidence = ROOT / "evidence" / "test_run_latest.txt"
    evidence.write_text(output + "\n", encoding="utf-8")
    return 0 if failed == 0 and result.testsRun > 0 else 1


if __name__ == "__main__":
    sys.exit(main())

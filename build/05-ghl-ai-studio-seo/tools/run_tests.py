"""Unit suite + T01-T14 acceptance matrix -> out/tests/.

Exit 0 only when every unit test passes and no matrix case is FAIL. BLOCKED
cases are reported as BLOCKED, never as passing.
"""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import acceptance_matrix, release_package  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import write_text  # noqa: E402


def run_unit_suite(paths: Paths) -> unittest.TestResult:
    suite = unittest.defaultTestLoader.discover(str(paths.root / "tests"))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    write_text(paths.out / "tests" / "unit_results.txt", stream.getvalue())
    return result


def main(argv: list[str] | None = None) -> int:
    paths = default_paths()
    result = run_unit_suite(paths)
    unit_ok = result.wasSuccessful()
    print(f"unit suite: {result.testsRun} run, {len(result.failures)} failures, {len(result.errors)} errors, "
          f"{len(result.skipped)} skipped -> out/tests/unit_results.txt")
    results = acceptance_matrix.run(paths)
    release_package.build(paths)
    counts = acceptance_matrix.counts(results)
    for r in results:
        print(f"{r['test_id']} {r['verdict']:<8} {r['name']}")
    print(f"matrix: PASS {counts['PASS']} / FAIL {counts['FAIL']} / BLOCKED {counts['BLOCKED']} -> out/tests/test_log.md")
    return 0 if unit_ok and counts["FAIL"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

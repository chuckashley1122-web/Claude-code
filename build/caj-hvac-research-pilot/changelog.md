# Changelog

## v0.1.0 — initial build (2026-10-05)

- Built the offline pipeline (input validation, run identity, fixture and file-drop
  retrieval, deterministic extraction, four-artifact render, structural validator),
  guards, scripts, fixtures, and the stdlib unittest suite.
- `LiveRetriever` raises `LiveCallBlocked` (human approval required).
- Test outcome for this revision: `python3 tests/run_tests.py` ran 76 tests, 76 passed,
  0 failed (literal output in `evidence/test_run_latest.txt`). T09 not run.

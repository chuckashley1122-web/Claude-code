# 006-04 Seven-day observation period

**Why:** The playbook releases version 1 only after a seven-day review of the same
workflow. The agent cannot run it and must never backfill it. Day 1 is the first
successful live run, not the document date.

**Where:** `build/caj-hvac-research-pilot/workflow.md` (Seven-day ledger) and
`tests/test_log.md`.

**Steps:**
1. After the first real run passes validation and 006-03 is done, add ledger row
   `1 | <today's date> | <what was reviewed> | outputs/<run_id>/`.
2. Day 2: inspect missing-field handling; fix one verified issue; rerun the affected test.
3. Day 3: record Chuck's usefulness feedback (006-03).
4. Day 4: run another input batch if available; check blocked pages and retries.
5. Day 5: run from a fresh session using only `runbook.md`.
6. Day 6: record elapsed time, tool errors, and manual edits (provider usage:
   `unavailable` unless shown; never estimate).
7. Day 7: run `python tests/run_tests.py`, review open defects, and decide: release
   version 1 or continue the same pilot.
8. Add a row only for a day that actually happened.

**Verify:** The ledger has seven real rows with evidence paths; the release gate in
`src/guards.py::release_gate_status` then reports `USER_REVIEW_PENDING` or `V1_READY`
instead of a lower status.

**Blocked by:** 006-01, 006-02, 006-03 (no live run exists yet).

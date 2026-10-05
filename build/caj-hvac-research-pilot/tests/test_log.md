# Test log

Only tests that actually ran are recorded as pass/fail. The evidence path holds the
literal output. A generated checklist without executed runs is not proof.

Executed run: `python3 tests/run_tests.py` at 2026-10-05T23:48:34Z (Python 3.11.15,
Linux) - 76 tests ran, 76 passed, 0 failed, 0 skipped. The same suite also passed via
`python3 -m unittest discover -s tests` (76 tests, OK).

| test id | date | workflow version | input | expected result | actual result | pass/fail | evidence path |
|---|---|---|---|---|---|---|---|
| T01 | 2026-10-05 | 0.1.0 | Fixture A (`mock://fixture-a`, Sample HVAC A) | `complete`; Round Rock; AC repair + heating maintenance; the supplied phone; nothing added | `complete`, `Round Rock`, `("AC repair", "heating maintenance")`, `phone: (512) 555-0142`; every excerpt is verbatim fixture text (2 tests) | pass | `evidence/test_run_latest.txt` |
| T02 | 2026-10-05 | 0.1.0 | Fixture B (`mock://fixture-b`, Sample HVAC B) | `partial`; omitted fields read exactly `Not found in reviewed pages` | `partial`; services `AC installation`; service_area, contact_method, observation, hypothesis = the exact missing label (1 test) | pass | `evidence/test_run_latest.txt` |
| T03 | 2026-10-05 | 0.1.0 | CSVs: missing header, duplicate id, empty URL, four rows | each `INPUT_INVALID` before retrieval; no output folder | each `INPUT_INVALID`; retriever call count 0; output root empty; row index and reason reported (2 tests) | pass | `evidence/test_run_latest.txt` |
| T04 | 2026-10-05 | 0.1.0 | rows fixture-a, fixture-d (Fixture D, `RETRIEVAL_FAILURE`), fixture-b | at most one retry; fixture-d `blocked`; other rows continue | fixture-d fetched exactly 2 times then `blocked`; fixture-a `complete`, fixture-b `partial`; transient failure recovers on the single retry; retries capped at 1 even when 5 requested (3 tests) | pass | `evidence/test_run_latest.txt` |
| T05 | 2026-10-05 | 0.1.0 | Fixture C (page for Sample HVAC C) supplied as `Sample HVAC X` | `blocked` / `IDENTITY_MISMATCH`; zero facts | `blocked`, `IDENTITY_MISMATCH`, no services, no field sources, every fact field = missing label (3 tests) | pass | `evidence/test_run_latest.txt` |
| T06 | 2026-10-05 | 0.1.0 | file-drop page listing three services; fixture demo run | commas survive CSV round-trip; `record_count` and `counts_by_status` match the CSV | services cell read back as `AC repair, heat pump, duct cleaning`; manifest counts equal CSV tallies; validator exit 0 (2 tests) | pass | `evidence/test_run_latest.txt` |
| T07 | 2026-10-05 | 0.1.0 | same fixture input run twice | new run folder; earlier files byte-identical (by hash) | second run in a different folder; SHA-256 of all four first-run files unchanged; same-second collision gets `-2`, `-3` (2 tests) | pass | `evidence/test_run_latest.txt` |
| T08 | 2026-10-05 | 0.1.0 | command read from `runbook.md`, run in a subprocess with a minimal environment | all four artifacts produced from the runbook alone | exit 0; `brief.md`, `results.csv`, `evidence.md`, `run.json` present; `fixture_mode: true`; runbook validator command prints `VALIDATION PASSED`; runbook contains every schema and rule (3 tests) | pass | `evidence/test_run_latest.txt` |
| T09 | - | 0.1.0 | one to three real company URLs | traceable facts or explicit gaps, manually source-checked | not run: no real URLs supplied (`INPUT_REQUIRED`) and no live retrieval (work orders 006-01, 006-02, 006-03) | not run | - |
| GUARDS | 2026-10-05 | 0.1.0 | `tests/test_guards.py` | price scanner blocks injected `$650/mo` in a hypothesis cell and in `brief.md`; source-claim and consumer-brand scanners fire; `release_gate_status` never returns `V1_READY` with any gate missing; tripwire fires for every action; check_env prints no values; repo_scan clean on the project and catches planted problems; no banned phrase in the tree | all assertions held | pass | `evidence/test_run_latest.txt` |
| EXTRA | 2026-10-05 | 0.1.0 | remaining tests in `test_extraction.py`, `test_input_validation.py`, `test_retrieval.py`, `test_output_validation.py`, `test_pipeline_endtoend.py` | extraction rules, input contract, retriever modes, `LiveRetriever` raises `LiveCallBlocked`, validator negative cases, CLI refusals | all assertions held | pass | `evidence/test_run_latest.txt` |

## Acceptance commands run (2026-10-05)

| command | expected | actual | pass/fail |
|---|---|---|---|
| `python3 scripts/run_research.py --retriever fixtures` | offline run; prints run id, paths, counts | exit 0; run `20261005T234642Z-ff5e491c`; complete=1 partial=1 blocked=1; output validation passed | pass |
| `python3 scripts/repo_scan.py` | exit 0; zero findings; tripwire fires | exit 0; `secret / ID / .env findings: 0`; `FrozenCampaignViolation raised as required`; `REPO SCAN PASSED` | pass |
| `python3 scripts/check_env.py` | `MISSING` per unset var; no values | exit 0; all 9 vars `MISSING`; `.env file: absent` | pass |
| `git check-ignore -v .env outputs/x` | both ignored | matched `.gitignore` lines 1 and 2 | pass |

# Handoff - CA-J HVAC research pilot

| Item | Value |
|---|---|
| Project path | `/home/user/Claude-code/build/caj-hvac-research-pilot` (repo path `build/caj-hvac-research-pilot/`; Chuck's pinned path in SPEC-06 section 4 is unconfirmed, work order 006-02) |
| Version | 0.1.0 (`config.WORKFLOW_VERSION`) |
| How to invoke | `python scripts/run_research.py --retriever fixtures` (mock run) or `python scripts/run_research.py --retriever filedrop --input inputs/companies.csv` (real run from saved pages). Full procedure: `runbook.md`. |
| Latest run | `20261005T234642Z-ff5e491c` - FIXTURE run (`fixture_mode: true`), overall_status `partial`, complete 1 / partial 1 / blocked 1, validation passed. Paths: `outputs/20261005T234642Z-ff5e491c/brief.md`, `results.csv`, `evidence.md`, `run.json`. `outputs/` is gitignored, so this folder exists only on the build machine. No real-company run exists. |
| Handoff status | **SPECIFICATION_READY** (from `release_gate_status()`; see evidence below) |
| Next review date | None scheduled. The seven-day review starts on the date of the first successful live run (work order 006-04); no date can be set honestly before then. |
| Source video | https://www.youtube.com/watch?v=YEBA9zdK7Lg |
| Source playbook | `docs/playbooks/06-single-workflow.md` |
| Spec | `specs/SPEC-06-single-workflow.md` |

## Evidence for the status

Computed by `tests/run_tests.py` from the executed suite (literal output in
`evidence/test_run_latest.txt`):

- file write/read probe: passed (`evidence/preflight.md`)
- T01-T08: all passed
- real (non-fixture) run passing validation: none yet (`INPUT_REQUIRED`)

`MVP_TESTED` needs pre-release tests **and a real run** to pass (playbook section 9).
The real run is missing, so the honest status is `SPECIFICATION_READY`. `V1_READY` is
not claimed: no live pilot has been source-checked and the seven-day ledger is empty.

## Unresolved issues

1. No real company rows: `inputs/companies.csv` is header-only (work order 006-02).
2. No real page text: live retrieval is blocked; pages must be saved by a human (006-01).
3. T09 live pilot: not run (needs 1 and 2, then Chuck's source check, 006-03).
4. Hermes provider preflight `PROVIDER_OK`: NOT EXECUTABLE in this environment (006-05).
5. Seven-day review: not started; Day 1 = first successful live run (006-04).
6. The identity check requires the supplied company name to appear on the page as
   written. Real sites that abbreviate their name will be blocked (`IDENTITY_MISMATCH`)
   until the input name matches the page; this is fail-closed by design.
7. Project path on Chuck's Windows machine not confirmed.

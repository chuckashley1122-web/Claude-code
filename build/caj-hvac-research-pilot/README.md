# CA-J HVAC research pilot (SPEC-06, v0.1.0)

An offline research pipeline for CA-J Enterprises: up to three supplied HVAC company
rows become one source-backed research brief and one draft marketing observation per
company. Every fact carries its source label and a verbatim excerpt; anything not found
reads exactly `Not found in reviewed pages`. Outputs are drafts for Chuck's review.

Built from `specs/SPEC-06-single-workflow.md` and its playbook
`docs/playbooks/06-single-workflow.md` (source video https://www.youtube.com/watch?v=YEBA9zdK7Lg).
The pilot is an implementation example chosen for CA-J, not the presenter's workflow, and
it has not yet been run on a real company.

## Run commands

From this folder (Chuck's Windows machine: `python`; Linux: `python3`):

```
python scripts/run_research.py --retriever fixtures      # mock companies, fixture_mode=true
python scripts/run_research.py --retriever filedrop      # human-saved pages in inputs/pages/
python -m src.output_validation outputs/<run_id>         # re-validate a run folder
python tests/run_tests.py                                # full suite + per-test-ID summary
python -m unittest discover -s tests                     # same suite, plain unittest
python scripts/check_env.py                              # SET/MISSING per env var, never values
python scripts/repo_scan.py                              # secrets, GHL ID hygiene, Meta tripwire
```

The full procedure is in `runbook.md`. Status and open items are in `handoff.md`.

## Approval gates (config.py) and defaults

| Gate | Default | Meaning |
|---|---|---|
| `DRY_RUN` | `True` | no network, no external write; local outputs still written. Off requires `ALLOW_LIVE=1` from a human |
| `ALLOW_LIVE` | `False` | human-only; not a substitute for approval |
| `ALLOW_NETWORK_RETRIEVAL` | `False` | set without `ALLOW_LIVE=1`: refusal banner, exit 3. Even with both set, `LiveRetriever` still refuses |
| `HUMAN_APPROVAL_REQUIRED` | `True` | |
| `SPEND_CAP_USD` | `0.00` | nothing in this project costs money |
| `REQUIRE_HUMAN_APPROVAL_FOR_SEND` / `_FOR_GHL` | `True` | |
| `SEND_ENABLED` / `GHL_WRITES_ENABLED` | `False` | constants, not env-tunable; no send or GHL code path exists |
| `FROZEN_META_CAMPAIGN_ID` | `CAJ_HVAC27_US_PURCHASE_TEST02` | any action raises `FrozenCampaignViolation` |
| Caps | 3 companies, 3 pages, 1 retry | env vars may lower them; raising them is refused |

## Refusing connectors (no stubs that pretend to work)

| Component | Behavior |
|---|---|
| `LiveRetriever` (`src/retrieval.py`) | Always raises `LiveCallBlocked` explaining that human approval is required for a retrieval path (work order 006-01). Never returns content. Tested in `tests/test_retrieval.py`. |
| LLM extractor | Not built. Extraction is deterministic regex/keyword matching over supplied text. Any LLM step needs a provider, a paid key, and approval. |

Working offline implementations: `FixtureRetriever` (tests/fixtures) and
`FileDropRetriever` (inputs/pages).

## Status strings

- Input: `INPUT_REQUIRED` (header-only), `INPUT_INVALID` (fails before retrieval).
- Company: `complete`, `partial`, `blocked` (`RETRIEVAL_FAILED` or `IDENTITY_MISMATCH`).
- Run: `completed`, `partial`, `failed`.
- Handoff: `SPECIFICATION_READY`, `ENVIRONMENT_BLOCKED`, `MVP_TESTED`, `PILOT_IN_PROGRESS`,
  `V1_READY`, `USER_REVIEW_PENDING` (computed by `src/guards.py::release_gate_status`).

## Absolute rules

- No send of any kind, no spend, no GHL read or write, no Meta change.
- No invented data: no invented businesses, URLs, facts, statistics, prices, or reviews.
- No source-author results restated as CA&J's. The presenter's one-hour MVP target, the
  "approximately 50 automations per year" figure, the seven-day improvement outcome, and
  the Agent OS narrative are UNSUBSTANTIATED and are not CA-J results.
- Meeting-first: no price appears in any generated output (the validator scans
  `observation`, `hypothesis`, and `brief.md`); pricing intent routes to
  https://ca-jenterprises.com/ai. Commercial constants in `config.py` are internal only.
- Brand separation: CA-J B2B output never mentions consumer brands; the validator blocks them.
- Public contact only: Chuck Ashley, 512-229-9199, chuck@ca-jconsulting.com.

## Spend items (all require approval; none are authorized)

| Service | What it is for | Approval | Cost |
|---|---|---|---|
| Hermes model provider (LLM subscription or API key) | The playbook's `PROVIDER_OK` preflight (work order 006-05) and any future LLM-based extraction | approval required | NEEDS_EVIDENCE |
| Automated web retrieval path (HTTP client host, scraping/browsing service, or browser automation) | Replacing human-saved page text with live retrieval (work order 006-01) | approval required | NEEDS_EVIDENCE |

The pipeline as built costs nothing to run.

## Layout

```
config.py            gates, locked facts, caps, statuses (single source of truth)
src/                 contract, input_validation, run_identity, retrieval, extraction,
                     guards, render, output_validation, pipeline
scripts/             run_research.py, check_env.py, repo_scan.py
tests/               fixtures, unittest modules (T01-T08 + guards + CLI), run_tests.py, test_log.md
inputs/              companies.csv (header-only), pages/ (human-saved page text)
outputs/             one folder per run (gitignored except .gitkeep)
evidence/            preflight.md, file_probe.txt, test_run_latest.txt
ui-work-orders/      (repo root) 006-01 .. 006-05
```

## Deviations from spec

1. **LiveRetriever raises `LiveCallBlocked`, not `NotImplementedError`.** Build rule 4
   requires a typed refusal explaining the human approval needed, never a bare stub.
   `LiveCallBlocked` is a `RuntimeError` subclass; it is tested.
2. **Handoff status is `SPECIFICATION_READY`, not `MVP_TESTED`.** The spec's step 23
   expects `MVP_TESTED` when T01-T08 pass, but the playbook defines `MVP_TESTED` as
   "pre-release tests and a real run pass". No real company run exists (`INPUT_REQUIRED`),
   so `release_gate_status()` returns the honest lower status. It returns `MVP_TESTED`
   automatically once a real run passes validation.
3. **Interpreter.** The spec says `python` and Windows paths; this build was run with
   `python3` on Linux and uses `pathlib` and `sys.executable` throughout. Commands in the
   docs use `python` (Chuck's machine) with forward slashes, which work on both.
4. **Extra evidence file.** `tests/run_tests.py` writes its literal output to
   `evidence/test_run_latest.txt` so `tests/test_log.md` has a real evidence path. No new
   top-level directory was added.
5. **Brand guard added.** `src/guards.py::scan_for_consumer_brands` and a validator check
   (build rule 8); not named in the spec.
6. **Fixture demo when the template is empty.** With `--retriever fixtures` and a
   header-only `inputs/companies.csv`, the CLI reports `INPUT_REQUIRED` for the live run
   and runs the three built-in fixture rows (`fixture_mode: true`), so the acceptance
   command prints a run id, paths, and counts. With `--retriever filedrop` an empty
   template exits 0 with `INPUT_REQUIRED` and creates nothing.
7. **Source provenance figures resolved.** The spec lists the playbook's character count
   and SHA-256 as NEEDS_EVIDENCE. Measured in this build for the repo copy
   `docs/playbooks/06-single-workflow.md`: 26,846 bytes, 279 lines (CRLF line endings),
   26,808 characters (Python, UTF-8, newlines preserved), SHA-256
   `d57a648f21f7a3851d6f23ae45e0fc2d7c9962d96af60a5f6ab76ca4c768d9c0`. The spec file
   itself was not edited.

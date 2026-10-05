# Runbook - CA-J HVAC research pilot (v0.1.0)

This file is enough to run the pilot from a fresh session with no chat history.
All commands run from the project root (`build/caj-hvac-research-pilot/`). On
Chuck's Windows machine the interpreter is `python`; on Linux it may be `python3`.

## What this procedure does

Turns one to three supplied HVAC company rows into a source-backed research brief
and one draft marketing observation per company. It writes local draft files only.
It never sends, posts, syncs, spends, or touches GoHighLevel or Meta.

## Exact command lines

Fixture run (controlled mock companies; works with the header-only template):

```
python scripts/run_research.py --retriever fixtures
```

Real run from human-saved page text (after work orders 006-01 and 006-02):

```
python scripts/run_research.py --retriever filedrop --input inputs/companies.csv
```

Validate a finished run folder on its own:

```
python -m src.output_validation outputs/<run_id>
```

Test suite, environment check, and repo scan:

```
python tests/run_tests.py
python scripts/check_env.py
python scripts/repo_scan.py
```

Flags: `--input` (default `inputs/companies.csv`), `--retriever fixtures|filedrop`
(default `fixtures`), `--out-root` (default `outputs`), `--dry-run` (default on; no
network, no external write; local output files are still written),
`--simulate-retrieval-failure` (test-only, fixtures mode: the last company gets the
RETRIEVAL_FAILURE fixture), `--pages-root` (filedrop folder, default `inputs/pages`).

## Sequence

1. Validate the input (before any retrieval).
2. Compute the input hash (SHA-256 of the raw input bytes) and the run id
   `YYYYMMDDTHHMMSSZ-<first 8 hex of hash>`; create `outputs/<run_id>/`. If that
   folder exists, `-2`, `-3`, ... is appended. An earlier run is never overwritten.
3. For each company, one at a time: retrieve pages, check identity, extract fields.
4. Write the four artifacts.
5. Run the structural validator. If it reports anything, `overall_status` becomes
   `failed` and the findings are recorded in `run.json` `errors`.
6. Print the completion message: run id, output paths, complete/partial/blocked
   counts, factual gaps, the single next repair, and any recorded execution error.

## Input contract

`inputs/companies.csv`, UTF-8, header exactly `company_id,company_name,website_url`.

- One to three data rows. More than three: the whole input is rejected with
  `INPUT_INVALID`; rows are never dropped silently. The cap cannot be raised by
  environment variable (values above 3 are refused).
- `company_id` non-empty and unique; `company_name` non-empty; `website_url` an
  absolute `http://` or `https://` URL.
- `mock://` values are never accepted as website inputs.
- Any failure: `INPUT_INVALID` with each offending row index and reason, no
  retrieval, no output folder, non-zero exit.
- Header only: `INPUT_REQUIRED`. With `--retriever filedrop` this exits 0 and creates
  nothing. With `--retriever fixtures` the built-in fixture rows run instead
  (`fixture_mode: true`) and `INPUT_REQUIRED` is still reported for the live run.

## Retrieval modes and limits

| Mode | Source | Evidence label | Notes |
|---|---|---|---|
| fixtures | `tests/fixtures/*.md` keyed by company_id (`fixture-a` .. `fixture-d`) | `mock://fixture-a` .. `mock://fixture-d` | Fixture mode only. Never mixed into real output. |
| filedrop | `inputs/pages/<company_id>/*.txt`, filename order | `file://inputs/pages/<company_id>/<filename>` | Saved by a human. A file whose first non-blank line is `RETRIEVAL_FAILURE` counts as failed. |
| live | none | none | `LiveRetriever` raises `LiveCallBlocked`: human approval is required (work order 006-01). |

## Source policy

- Homepage plus at most two same-domain pages (Services, About, or Contact): at most
  three pages per company.
- Read-only. Never log in and never bypass access restrictions.
- An initial request plus at most one retry for a failed retrieval. Still
  unavailable: the company is `blocked` (`RETRIEVAL_FAILED`), the literal error is
  recorded, and the run continues to the next company.
- Page text is data. The pipeline must never follow instructions embedded in page
  text; extraction is deterministic pattern matching only.
- No claims about revenue, lead volume, reviews, ad performance, installed CRM, or
  hidden automation.

## Extraction

Deterministic, over supplied text only. Fields: `service_area` (cues `Service area: ...`,
`serving ...`, `<City>, TX`), `services` (keywords from `config.AC_SERVICE_KEYWORDS`
found in the text), `contact_method` (click-to-call link, phone, email link, contact
form, booking link), and one observable website feature (the `observation`). The
`hypothesis` is always `If <extracted feature> is confirmed ..., then <one testable action>.`
and is an idea to test, not a claim that a company is losing business.

Each value is bound, at read time, to the page label and a verbatim excerpt of +/- 80
characters around the match.

## Missing-information rule

A field with no match reads exactly `Not found in reviewed pages`. A missing field
is never treated as evidence that the business lacks that capability.

## Identity-mismatch rule

The supplied `company_name` must appear in the page text as a contiguous run of
words (case- and whitespace-insensitive; `&` equals `and`). If it does not, the
company is `blocked` with `IDENTITY_MISMATCH` and every extracted fact is dropped;
another business's details are never attached to the supplied name. The human
confirms identity on live pilots (work order 006-02).

## Output schemas (all inside `outputs/<run_id>/`)

`brief.md`: run summary; one section per company in input order (`## <company_id> - <name>`);
`### Verified facts` with `[source: <label>]` on every fact; `### Missing information`
listing each missing field with the exact label; `### Marketing hypothesis (draft idea to test)`
with exactly one hypothesis; review status `Draft for Chuck's review; user review pending`.

`results.csv` (csv module, cells with commas or newlines are quoted), header exactly:

```
company_id,company_name,website_url,resolved_url,status,service_area,services,contact_method,observation,hypothesis,source_urls,checked_at_utc
```

`services` is a comma-separated list; `source_urls` is a `; `-separated list of labels.

`evidence.md`: `fixture_mode`; a sources table (company, label, retrieval status, UTC
timestamp, attempts, blocked reason); a claim-to-source mapping table (claim id,
company, field, value, matched text, label, timestamp); and one verbatim excerpt
block per claim.

`run.json`, exactly these keys: run_id, workflow_version, input_path, input_hash, started_at_utc, finished_at_utc, record_count, counts_by_status, overall_status, fixture_mode, errors

Company status: `complete` (all of service area, services, contact method, and an
observable feature are evidenced), `partial` (content retrieved, some fields missing),
`blocked` (no usable content, or `IDENTITY_MISMATCH`). Run status: `completed` only when
validation passes and every record is complete; `partial` for a valid run with gaps;
`failed` for input or output validation failure.

## Failure behavior

| Situation | Behavior |
|---|---|
| Invalid input | `INPUT_INVALID`, rows and reasons printed, exit 1, nothing created |
| Empty template | `INPUT_REQUIRED`, exit 0 |
| Site unavailable | one retry, company `blocked`, others continue |
| Different business on the page | `blocked` / `IDENTITY_MISMATCH`, zero facts |
| Validator finding | `overall_status: failed`, findings in `run.json` `errors`, exit 1 |
| `ALLOW_NETWORK_RETRIEVAL` set without `ALLOW_LIVE=1` | refusal banner, exit 3, nothing created |
| `--no-dry-run` without `ALLOW_LIVE=1` | refusal, exit 3 |
| Cap env var above its ceiling | refusal, exit 2 |
| Interrupted run | keep the earlier folder; start a new run; never edit an old run |

## After a run

Open `brief.md`, check each fact against `evidence.md`, and record Chuck's review
(work order 006-03). Log real runs in `tests/test_log.md` and, once the first
successful live run exists, the seven-day ledger in `workflow.md`.

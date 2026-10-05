# Preflight evidence

Recorded 2026-10-05. Literal outputs only. Nothing here is recorded as passed without
its output.

## 1. Provider / model test (`PROVIDER_OK`)

Status: `NOT EXECUTABLE — no Hermes session available to this agent`.

No provider call was made. The pipeline is deterministic and calls no model. The
Hermes preflight (`Reply with exactly PROVIDER_OK`, `hermes model`) is a human task:
`ui-work-orders/006-05-provider-preflight-hermes.md`.

## 2. File operation test

Wrote `FILE_OK` to `evidence/file_probe.txt`, then read it back:

```
$ python3 -c "...read evidence/file_probe.txt..."
path: /home/user/Claude-code/build/caj-hvac-research-pilot/evidence/file_probe.txt
readback: 'FILE_OK'
```

Result: passed (readback equals `FILE_OK`).

## 3. Retrieval test (supplied content, NOT a live fetch)

This agent has no web tool, so no public page was fetched. The retrieval path was
tested on a clearly labeled supplied-content page: mock Fixture A, served by
`FixtureRetriever`.

```
label: mock://fixture-a
resolved_url: mock://fixture-a
retrieval_status: ok
retrieved_at_utc: 2026-10-05T23:45:03Z
page title line: # Sample HVAC A
one supported fact: service_area = Round Rock | excerpt contains match: True
```

Live retrieval check (expected refusal):

```
LiveCallBlocked: Live retrieval of 'https://x.example.com' is blocked: ALLOW_NETWORK_RETRIEVAL and ALLOW_LIVE are not both set by a human. Human approval is required to choose and own a permitted browser/HTTP retrieval path (see ui-work-orders/006-01-live-page-retrieval.md). Until then, save page text to inputs/pages/x/NN-<slug>.txt and use --retriever filedrop.
```

Result: supplied-content retrieval works; live retrieval is blocked by design pending
work order 006-01. The real-site retrieval test from the playbook (step 8) is not run.

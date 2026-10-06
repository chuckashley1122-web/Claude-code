# SPEC-05 build: GHL AI Studio SEO + full-stack inquiry flow (draft package)

This folder turns SPEC-05 into a reviewable, draft-only package on disk. It covers the site plan and page copy, metadata, structured data, crawl files, static HTML mocks, the AI Studio prompt pack, and a working, locally tested inquiry back end. Every browser or logged-in step is written as a human work order.

**Nothing was published, deployed, sent or purchased. No GHL, DNS, Search Console or Meta object was touched.** The frozen Meta campaign is named only in `config/constants.py` and in the warning line of the HUMAN-DECISIONS work order. The build makes no network calls. This build spends $0.

## Run commands (from this folder)

Chuck's machine uses `python`. This environment uses `python3`. The code never hard-codes either one.

```
python tools/validate_config.py            # hard assertions on IDs, URLs, caps, approvals (exit 0)
python tools/build_all.py                  # idempotent, ordered build -> out/, config/, ../../ui-work-orders/005-*.md
python -m unittest discover -s tests       # full unit + end-to-end suite (includes the Node check of inquiry.ts)
python tools/run_tests.py                  # unit suite + T01-T14 matrix -> out/tests/
python tools/secret_scan.py                # exit 0 = no secret values anywhere
python tools/compliance_scan.py            # exit 0 = every guardrail clean on every file
```

Optional tools, which a human runs only when the inputs exist:

```
python tools/baseline_inventory.py --urls config/baseline_urls.txt --allow-network   # zero-cost unauthenticated GETs
python tools/fetch_raw_html.py <url> --allow-network                                 # one raw-HTML evidence file
python tools/fetch_raw_html.py --html-file out/site/index.html                       # parse a local file, no network
```

If no URL list is given, `baseline_inventory.py` exits BLOCKED (code 3). It never makes up a baseline.

## What gets generated

| Output | What it is |
|---|---|
| `config/business_facts.json`, `out/business_facts.md` | Facts register. Only house facts are verified. Everything else is `NEEDS_EVIDENCE`. Each row has a PUBLIC COPY ELIGIBILITY flag. |
| `config/route_inventory.json`, `out/route_inventory.md` | The 8 proposed routes (`PROPOSED_NOT_APPROVED`). The canonical origin is `NEEDS_EVIDENCE`. |
| `out/pages/*.md` | Draft copy that has passed the evidence gate. Unsourced sections are withheld. |
| `out/pages/service-area-merge.json` | The thin-content guard found the two location pages near-identical (0.96 > 0.80), so it refused to emit them and wrote this merge record instead. |
| `out/metadata.{json,md}` | One unique title, description and canonical per indexable route. `og:image` is `NEEDS_EVIDENCE`. |
| `out/structured_data/*.json` | JSON-LD built from verified facts only. Any unsourced property is listed in `_blocked_fields`. |
| `out/seo/` | sitemap.xml, robots.txt, indexability.md and the redirect map (empty until a human supplies old URLs). |
| `out/site/*.html` | Self-contained mocks: one per route, plus 404 and thank-you pages. They have no scripts and no CDNs, and each shows the STATIC CONTENT MOCK banner. |
| `out/ai_studio_prompt_pack.md` | Prompts 1-7, the master instruction and the final-status format, all verbatim, plus a block of placeholders to fill in. |
| `out/inquiry_contract.{json,md}` | The inquiry contract as data. It is authored guidance, not a platform endpoint. |
| `src/inquiry_validator.py`, `src/idempotency_store.py`, `src/inquiry_handler.py` | Working reference back end. It covers validation, sqlite idempotency, truthful status mapping, bounded retry and PII redaction. |
| `out/server_functions/inquiry.ts` | Paste-ready server function. It reads env vars by name and contains no secrets and no hard-coded IDs. |
| `src/ghl_adapter.py` | `GHLAdapter`: every method raises `LiveCallBlocked` (a `NotImplementedError`). `MockGHLAdapter` (MOCK - NOT PRODUCTION) is used for tests only. |
| `out/estimator/BLOCKED.md` | The estimator is disabled (`ESTIMATOR_ENABLED = False`). This file lists the missing inputs. |
| `out/tests/` | `test_log.md` plus `T01.json`-`T14.json`. Current result: PASS 7, FAIL 0, BLOCKED 7. |
| `out/release_package.md`, `out/asset_register.md`, `out/spend_items.json` | The release package, filled in using the source's final-status format. |
| `../../ui-work-orders/005-*.md` | 8 work orders plus `005-HUMAN-DECISIONS.md`. |

## Spend items (approval required for every one; cost = NEEDS_EVIDENCE)

| Service | What it is for | Approval | Cost |
|---|---|---|---|
| Domain registration/transfer (only if no owned domain) | Public origin for canonicals, sitemap, publish | approval required | NEEDS_EVIDENCE |
| GoHighLevel plan change / AI Studio add-on (only if needed for SSR, server functions, secrets) | Server rendering and server functions | approval required | NEEDS_EVIDENCE |
| GoHighLevel API access beyond the current plan (if required) | Inquiry -> CRM contact upsert | approval required | NEEDS_EVIDENCE |
| Paid SEO tool | Not needed. The zero-cost path is the design. | approval required | NEEDS_EVIDENCE |
| Ad spend | Out of scope (`AD_SPEND_CAP_USD = 0`) | approval required | NEEDS_EVIDENCE |

## Interpretations

- **Contact method.** The spec says "one valid contact method". This build requires at least one valid `email` or `phone`. Any contact method that is supplied must also be valid.
- **Status codes.** A payload over 16 KB returns `400`. A save that upstream claims succeeded but never confirmed returns `502`. A missing access token returns `503` ("integration not configured"). A rejected token returns `502` and is not retried. A duplicate that is still in flight returns `503` with `Retry-After`.
- **Retrying a failed submission.** A failed submission can be re-attempted with the same `submission_id` (this is the network-retry path). A saved or queued submission always replays its earlier outcome.
- **Verdicts.** A matrix case that needs a live site, a live CRM or a human review is reported as BLOCKED, even when all of its local checks pass. It is never reported as PASS.
- **Service area length.** `service_area` uses `MAX_NAME_LEN` (120) as its length bound, because section 6 gives no separate bound.

## Deviations from spec

1. **Work order location.** The build rules say UI work orders go in the repo-root `ui-work-orders/` folder with prefix `005`, not in `build/05-ghl-ai-studio-seo/ui-work-orders/`. They are therefore named `ui-work-orders/005-001-...md` through `005-008-...md`, plus `005-HUMAN-DECISIONS.md`. Inside each file, the spec's order numbers are kept (001-008).
2. **Interpreter.** The spec says to use `python` and never `python3`. The build rules override this: the code calls neither, and the commands above work with either.
3. **Location pages.** No verified local coverage exists. The thin-content guard therefore merged `/locations/austin` and `/locations/round-rock`, and no page copy is emitted for them. To keep "one mock per proposed route", each still has a mock, but it is a `noindex` "withheld" notice. Neither route is in the metadata set or the sitemap.
4. **404 mock.** `404.html` has no canonical link, because a canonical on an error page would be wrong. The T01 "canonical" check covers the route mocks and the thank-you mock.
5. **Extra files.** These files are not in the section 4 tree but were added:
   - `tools/paths.py`: lets tests build into a temporary directory.
   - `src/ui_work_orders.py`: generates the work orders.
   - `out/spend_items.json`: makes spend lines machine-checkable.
   - `out/pages/_content_model.json`
   - extra test modules
   - `__init__.py` files
   - `.gitignore`: ignores `out/` and `logs/`.
6. **Node check.** `node --check` cannot parse TypeScript. The test strips types with Node's built-in `module.stripTypeScriptTypes` and runs `node --check` on the result. It also runs a harness against the stripped module to check that it behaves the same as the Python handler. No npm packages are used.
7. **Live adapter error type.** The live GHL adapter raises `LiveCallBlocked`, a subclass of `NotImplementedError`. This satisfies both the spec's `NotImplementedError` requirement and the build rule's typed-refusal requirement.

# leadgen — lead sourcing for ca-jenterprises & ca-jconsulting

Sources leads, enriches them from the prospect's own website, scores them
against a per-brand ICP, and writes a CRM-ready CSV.

```
source  ->  dedupe  ->  enrich (Scrapling / Scrapegraph-ai)  ->  score  ->  CSV + JSON
```

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e leadgen/            # puts a `leadgen` command on your PATH
scrapling install                  # downloads the browsers Scrapling drives
cp leadgen/.env.example leadgen/.env   # then fill in the keys you have
```

```bash
leadgen sources                    # what is configured and what still needs a key
leadgen run --brand ca-jenterprises --source apollo --limit 100 --enrich
```

`python -m leadgen` also works, but **only from inside `leadgen/`** — the outer
folder shadows the package. The installed `leadgen` command works anywhere, so
prefer it.

Start with `leadgen sources`. It tells you which sources are live and which are
waiting on a key, and marks which ones involve LinkedIn data. `nmls` needs no
key at all, so you can get real output before you buy anything.

## Read this before you point it at LinkedIn

Scraping LinkedIn directly — logged in, or by driving a browser at profile
pages — breaks LinkedIn's User Agreement. That is not a technicality you can
engineer around:

- **Proxycurl, the best-known LinkedIn data API, shut down on 4 July 2025**
  after LinkedIn sued it in federal court. The founders closed the company
  rather than fight.
- *hiQ v. LinkedIn* established that scraping **public** data is not a CFAA
  crime. It did **not** make it contractually allowed. LinkedIn still uses the
  ToS breach to ban accounts, send cease-and-desists, and sue operators.
- The account that gets banned is normally the one running the automation —
  i.e. yours, with your network and your history in it.

So this pipeline gets LinkedIn-shaped data three ways that do not put your
account or your companies at risk:

| Source | What it is | Risk |
|---|---|---|
| `sales-nav-csv` | **Your own** Sales Navigator / LinkedIn export, read off disk | none — LinkedIn handed you the file |
| `apollo` | Apollo.io's own licensed contact database | none — you never touch LinkedIn |
| `brightdata` | Bright Data's licensed public-profile dataset | none — no login, they carry the compliance |
| `nmls` | The federal NMLS mortgage licensing registry | none — official public record |

`python -m leadgen sources` marks which sources involve LinkedIn data.

One thing to know about Agent-Reach: its LinkedIn channel wraps
`mcp-server-linkedin`, which asks for **your** LinkedIn session cookie and
drives your logged-in account. That is the risky path above. Every other
Agent-Reach channel (GitHub, YouTube, RSS, web) is fine.

Whatever you source, US outreach still has to clear CAN-SPAM (real postal
address, working opt-out) and, for the lending side, TCPA before any call or
text. Mortgage and business-lending outreach is a regulated space.

## The sources

### `sales-nav-csv` — your own export
Highest-quality and zero-risk. In Sales Navigator, build the search, save to a
lead list, export to CSV (Advanced Plus seats), then:

```bash
leadgen run --brand ca-jconsulting --source sales-nav-csv \
  --csv ~/Downloads/list.csv --enrich
```

Column headers vary between LinkedIn products and CRM re-exports, so the
parser matches headers fuzzily — `First Name`, `firstname` and `Given Name`
all land in the same field, and `51-200 employees` parses to `51`.

### `apollo` — licensed contact data
Set `APOLLO_API_KEY`. Search is included in your plan; revealing emails and
phone numbers costs credits, so it is behind `--reveal`:

```bash
leadgen run --brand ca-jenterprises --source apollo --limit 200 --reveal --enrich
```

### `brightdata` — licensed LinkedIn public-profile dataset
Set `BRIGHTDATA_API_KEY`. Defaults to the LinkedIn People Profiles dataset
(`gd_l1viktl72bvl7bjuj0`); override with `BRIGHTDATA_LINKEDIN_DATASET_ID`.
Async: the source triggers a job, polls it, then downloads the snapshot.

### `nmls` — mortgage licensing registry (ca-jconsulting)
Every licensed loan originator and mortgage broker in the US, published by
federal mandate under the SAFE Act. This is the best partner-sourcing list
that exists for the lending side, and it carries something LinkedIn never
will: a verified NMLS ID and current licence status.

```bash
leadgen run --brand ca-jconsulting --source nmls --state OH --limit 200
```

NMLS publishes no free API, so this drives the public site and parses the
result — expect to update selectors when the site changes. For volume, CSBS
sells an official B2B feed.

## Enrichment

`--enrich` crawls each prospect's **own** website (homepage, /about, /contact,
/careers) with Scrapling and pattern-matches for buying signals. Free, no LLM.

`--llm` additionally runs Scrapegraph-ai's `SmartScraperGraph` over the site to
pull what regex cannot: the named decision-maker, a direct email, what the
business actually sells. Needs `OPENAI_API_KEY`, or set
`LEADGEN_LLM_MODEL=ollama/llama3.2` to run locally for free.

`--stealth` swaps the plain HTTP fetcher for Scrapling's `StealthyFetcher`
(real browser, anti-bot evasion) for sites that block simple clients.

## Scoring

Each brand's ICP and signal weights live in `config/<brand>.yaml` — edit those,
not the code. Score = title match (20) + headcount fit (10) + industry (10) +
reachable (8) + the signal weights from the YAML.

The same lead scores differently per brand, which is the point. A trucking
founder is a hot lending lead and a lukewarm marketing lead:

```
$ leadgen explain --brand ca-jconsulting --csv list.csv

Priya Raghavan — Founder @ Raghavan Freight
   +20 title matches ICP (Founder)
   +10 headcount 80 in [3,300]
   +10 industry Transportation & Trucking
   +8 reachable
   = 48 (hot)
```

Signals that mark a competitor (`is_marketing_agency`, `is_lender_competitor`)
carry −40, so competitors sink to cold instead of cluttering the list.

## Output

`out/<brand>-<source>.csv` and `.json`, sorted best-first, with a `signals`
column recording why each lead scored what it did. `out/` is gitignored — lead
lists contain personal data and do not belong in the repo.

## Tests

```bash
cd leadgen
python -m pytest tests -q        # 17 tests, no network, no API keys
python tests/smoke_live.py       # live network check of the fetchers
```

The suite covers CSV header handling, dedupe, per-brand scoring and competitor
demotion, plus the Apollo and Bright Data response parsers against recorded
fixtures. Those two parsers cannot be exercised without a paid key, so their
edge cases are pinned instead: Apollo masks locked emails as
`email_not_unlocked@domain.com`, nulls out `organization` for people with no
current employer, and sends `primary_phone: null` rather than omitting the key.

## Known environment limitation

Scrapling's HTTP fetcher works by **spoofing a real browser's TLS
fingerprint**. That is incompatible with any TLS-terminating corporate or
sandbox proxy: the proxy re-terminates TLS, the spoofed handshake fails, and
you get `curl: (35) Recv failure` or `ERR_CERT_AUTHORITY_INVALID`. On a normal
machine there is no such proxy and it just works. Behind one, set
`LEADGEN_PROXY` and expect the browser fetchers to need the proxy's CA in the
Chromium trust store.

# Lead scraper (ScrapeGraphAI + local Ollama)

Walks every page of a directory or listing site, pulls public contact details
out of each listing with a **local** LLM, de-dupes by website domain, and
appends new leads to `leads.csv`.

The model runs on your machine through [Ollama](https://ollama.com): no API
key, no per-lead cost, and page content never leaves the machine.

```
lead_scraper.py       the scraper (crawl -> extract -> de-dupe -> CSV)
daily_leads.py        unattended daily run, logs failures to errors.log
test_scrape.py        smoke test: scrapes one page so you know it works
selftest.py           offline end-to-end test of the pipeline logic
config.yml            sources, crawl politeness, model settings
setup.sh              venv + packages + Chromium
install_schedule.sh   cron entry for 08:00 daily
```

## 1. Install

```bash
cd lead-scraper
./setup.sh
```

That creates `.venv`, installs the pinned packages, and downloads the Chromium
build Playwright needs.

Then install and start the local model:

```bash
# Install Ollama first: https://ollama.com
ollama serve &
ollama pull llama3.1
```

Swap `llama3.1` for any model you have pulled — set it in `config.yml` under
`llm.model` as `ollama/<model>`.

## 2. Check it works

```bash
.venv/bin/python test_scrape.py
```

This scrapes a single page and tests the three things that actually break,
reporting them separately: Playwright rendering, Ollama reachability and the
model being pulled, then ScrapeGraphAI extraction. Point it anywhere with
`--url`, or stop after the fetch with `--skip-llm`.

To check the crawl/de-dupe/CSV logic without a model at all — it runs against
a built-in fixture site and a stub Ollama server, fully offline:

```bash
.venv/bin/python selftest.py
```

## 3. Point it at a directory

Edit `config.yml` and set a source URL. Worthwhile targets:

* industry directories and association member lists
* local business listings by city and category
* conference exhibitor and speaker pages
* marketplace or agency partner directories
* job boards, when you want companies hiring for the problem you solve

```yaml
sources:
  - name: austin-trades
    url: "https://example.com/directory"
    city: "Austin"          # fallback when listings don't state one
```

**Pagination** is handled for you. By default the crawler follows the site's
"next page" link (`rel="next"`, or a link labelled Next / » / ›) until it runs
out or hits `crawl.max_pages`. Two overrides exist for awkward sites:

```yaml
    # Predictable query-string paging — walked until a page comes back empty.
    page_url_template: "https://example.com/directory?page={page}"
    start_page: 1

    # Or name the next-page link directly.
    next_page_selector: "a.pagination__next"
```

## 4. Run it

```bash
.venv/bin/python lead_scraper.py                      # every source in config.yml
.venv/bin/python lead_scraper.py --source "https://..."  # one-off URL
.venv/bin/python lead_scraper.py --max-pages 2 --dry-run # try before writing
```

Output looks like:

```
  page 1: 12 listings, 9 new  <- https://example.com/directory
  page 2: 12 listings, 4 new  <- https://example.com/directory?page=2

Added 13 new rows
Skipped 6 duplicates
Skipped 5 listings with no email
Pages crawled: 2
```

### What lands in `leads.csv`

Columns, created on first write:

`company_name, contact_name, role, email, phone, website, city, source_url`

The rules the scraper applies:

* **No email, no row.** Listings without a public email are skipped and counted.
* **De-duped by website domain**, case-insensitively and ignoring `www.`, so
  `https://www.acme.com/about` and `https://acme.com` are the same lead. When a
  listing has no website, the email's domain is used instead.
* De-duping is checked against everything already in `leads.csv`, so re-running
  is safe — it appends only genuinely new domains.

## 5. Schedule it for 8am

```bash
./install_schedule.sh              # every morning at 08:00 local time
./install_schedule.sh --time 07:30
./install_schedule.sh --remove
```

Re-running replaces the entry rather than duplicating it, and leaves the rest
of your crontab alone. `daily_leads.py` writes failures to `errors.log`, one
timestamped line each, and exits `0` clean / `1` finished with failures / `2`
could not start.

Not on cron? The equivalents are a systemd timer with
`OnCalendar=*-*-* 08:00:00` running `.venv/bin/python daily_leads.py` from this
directory, or on Windows:

```powershell
schtasks /create /tn "Daily leads" /sc daily /st 08:00 ^
  /tr "C:\path\to\lead-scraper\.venv\Scripts\python.exe C:\path\to\lead-scraper\daily_leads.py"
```

## Keeping it clean

The scraper reads `robots.txt` before each page and stops on that source if it
is disallowed, honours `Crawl-delay` when it is longer than your configured
`request_delay_seconds` (default 2s), and identifies itself with a
configurable user agent. A descriptive UA with a contact address is the polite
option:

```yaml
crawl:
  user_agent: "LeadScraper/1.0 (+mailto:you@yourcompany.com)"
```

Public contact details only. Respect each site's terms, keep request volume
reasonable, and honour opt-outs once you start emailing — the tool scales
faster than your sender reputation does.

## Notes and caveats

**Dependency pins are deliberate.** ScrapeGraphAI's own version ranges resolve
to a broken install: 1.72.0+ requires `langchain-community >= 0.4.0` but still
imports `ChatOllama` from it, which 0.4 removed, so the package will not import
at all; 1.65.0–1.71.x need `init_chat_model` from langchain-core 1.x while
requiring a community package that pins core `< 0.4`. `requirements.txt` pins
1.60.0 and the whole langchain 0.3 stack, which is self-consistent. Check
upstream before bumping any of them.

**One network call is not local.** ScrapeGraphAI sizes its text chunks with
tiktoken regardless of provider, and tiktoken downloads its encoding file once,
on first run, then caches it. Only the tokenizer is fetched — no page content
is sent anywhere. Everything after that first run is fully local.

**Small models miss things.** `llama3.1` is a reasonable default, but on dense
or unusual listing markup a bigger pulled model will extract more reliably.
Pages are converted to markdown before prompting, which cuts tokens a lot and
noticeably improves results on small models. The prompt tells the model to use
an empty string rather than guess, so blank fields are expected and preferable
to invented ones — spot-check a `--dry-run` before trusting a new source.

**Other ways to run ScrapeGraphAI.** `just-scrape` is their official CLI, and
`scrapegraph-mcp` exposes scraping to Claude as MCP tools rather than as
scripts. Both route through ScrapeGraphAI's hosted API and need an `SGAI_API_KEY`,
so they bill per request. This project is the free local path.

#!/usr/bin/env python3
"""Lead scraper built on ScrapeGraphAI driven by a local Ollama model.

Walks every page of a directory / listing site, extracts public contact
details for each listing, de-dupes by website domain, and appends new rows to
a CSV.

    python lead_scraper.py --source "https://example.com/directory"
    python lead_scraper.py --config config.yml

Because the model runs locally through Ollama there is no API key and no
per-lead cost, and page content never leaves the machine.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator, Sequence
from urllib.error import URLError
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

import yaml
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config.yml"

#: CSV column order. Also the schema the model is asked to fill in.
FIELDNAMES = [
    "company_name",
    "contact_name",
    "role",
    "email",
    "phone",
    "website",
    "city",
    "source_url",
]

EXTRACTION_PROMPT = """You are extracting business leads from one page of a
business directory or listing site.

Return JSON with a single key "listings" whose value is a list of objects.
Create one object per business listed on the page, using exactly these keys:

  company_name  - the business or organisation name
  contact_name  - the owner or named contact person, if shown
  role          - that person's role or job title, if shown
  email         - a public contact email address shown on the page
  phone         - a public contact phone number
  website       - the business's own website URL
  city          - the city or town the business is in

Rules:
- Only use information actually visible on the page. Never invent, guess or
  autocomplete a value. If a field is not shown, use an empty string "".
- Do not include the directory site's own contact details, navigation links,
  cookie banners, adverts or social media links as listings.
- If the page shows no business listings at all, return {"listings": []}.
"""

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

#: Placeholder / tracking addresses that turn up in page markup but are not leads.
JUNK_EMAIL_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "domain.com",
    "yourdomain.com",
    "email.com",
    "sentry.io",
    "wixpress.com",
    "sentry.wixpress.com",
}

NULLISH = {"", "n/a", "na", "none", "null", "not available", "unknown", "-"}

#: Accept the key spellings a small local model realistically produces.
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "company_name": ("company_name", "company", "business_name", "business",
                     "organisation", "organization", "firm", "name"),
    "contact_name": ("contact_name", "contact", "owner", "owner_name",
                     "contact_person", "person", "full_name"),
    "role": ("role", "title", "job_title", "position"),
    "email": ("email", "email_address", "public_email", "e_mail", "mail"),
    "phone": ("phone", "phone_number", "telephone", "tel", "mobile", "contact_number"),
    "website": ("website", "website_url", "url", "site", "web", "homepage"),
    "city": ("city", "town", "location", "locality"),
}

NEXT_TEXT_RE = re.compile(
    r"^(next|next page|next results|next\s*[»›>→]|older|older posts|more|[»›>→])$",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, Any] = {
    "sources": [],
    "crawl": {
        "max_pages": 25,
        "request_delay_seconds": 2.0,
        "respect_robots_txt": True,
        "user_agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "page_timeout_seconds": 45,
        "headless": True,
        "wait_until": "domcontentloaded",
        "settle_seconds": 0.0,
        "convert_to_markdown": True,
        # Escape hatches for unusual environments; normally left unset.
        "browser_executable_path": None,
        "proxy_server": None,
        "ignore_https_errors": False,
    },
    "llm": {
        "model": "ollama/llama3.1",
        "base_url": "http://localhost:11434",
        "temperature": 0,
        "format": "json",
    },
    "output": {
        "csv_path": "leads.csv",
        "error_log": "errors.log",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge ``override`` onto ``base`` without mutating either."""
    merged = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path | None = None) -> dict:
    """Load config.yml and layer it over the defaults."""
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        if path:
            raise FileNotFoundError(f"Config file not found: {config_path}")
        return dict(DEFAULT_CONFIG)
    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    return _deep_merge(DEFAULT_CONFIG, loaded)


def build_graph_config(llm_cfg: dict, verbose: bool = False) -> dict:
    """Translate our ``llm`` config block into a ScrapeGraphAI graph config."""
    llm: dict[str, Any] = {k: v for k, v in llm_cfg.items() if v is not None}
    return {"llm": llm, "verbose": verbose, "headless": True}


# --------------------------------------------------------------------------
# Politeness: robots.txt + rate limiting
# --------------------------------------------------------------------------

class RobotsPolicy:
    """Per-host robots.txt lookups, cached for the life of a run."""

    def __init__(self, user_agent: str, enabled: bool = True, timeout: int = 15):
        self.user_agent = user_agent
        self.enabled = enabled
        self.timeout = timeout
        self._cache: dict[str, RobotFileParser] = {}

    def _parser_for(self, url: str) -> RobotFileParser:
        parts = urlparse(url)
        root = f"{parts.scheme}://{parts.netloc}"
        if root not in self._cache:
            self._cache[root] = self._load(root)
        return self._cache[root]

    def _load(self, root: str) -> RobotFileParser:
        parser = RobotFileParser()
        parser.parse([])  # default: nothing disallowed
        request = Request(f"{root}/robots.txt", headers={"User-Agent": self.user_agent})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
            parser.parse(body.splitlines())
        except (URLError, OSError, ValueError):
            # Missing or unreachable robots.txt means no stated restrictions.
            pass
        return parser

    def allows(self, url: str) -> bool:
        if not self.enabled:
            return True
        try:
            return self._parser_for(url).can_fetch(self.user_agent, url)
        except Exception:
            return True

    def crawl_delay(self, url: str) -> float | None:
        if not self.enabled:
            return None
        try:
            delay = self._parser_for(url).crawl_delay(self.user_agent)
        except Exception:
            return None
        return float(delay) if delay else None


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------

class PageFetcher:
    """Renders pages with Playwright/Chromium so JS-built listings are visible."""

    def __init__(
        self,
        *,
        headless: bool = True,
        timeout_seconds: float = 45,
        user_agent: str | None = None,
        wait_until: str = "domcontentloaded",
        settle_seconds: float = 0.0,
        browser_executable_path: str | None = None,
        proxy_server: str | None = None,
        ignore_https_errors: bool = False,
    ):
        self.headless = headless
        self.timeout_ms = int(timeout_seconds * 1000)
        self.user_agent = user_agent
        self.wait_until = wait_until
        self.settle_seconds = settle_seconds
        self.browser_executable_path = browser_executable_path
        self.proxy_server = proxy_server
        self.ignore_https_errors = ignore_https_errors
        self._playwright = None
        self._browser = None
        self._context = None

    def __enter__(self) -> "PageFetcher":
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        launch_kwargs: dict[str, Any] = {"headless": self.headless}
        if self.browser_executable_path:
            launch_kwargs["executable_path"] = self.browser_executable_path
        if self.proxy_server:
            launch_kwargs["proxy"] = {"server": self.proxy_server}
        self._browser = self._playwright.chromium.launch(**launch_kwargs)

        context_kwargs: dict[str, Any] = {"ignore_https_errors": self.ignore_https_errors}
        if self.user_agent:
            context_kwargs["user_agent"] = self.user_agent
        self._context = self._browser.new_context(**context_kwargs)
        self._context.set_default_timeout(self.timeout_ms)
        return self

    def fetch(self, url: str) -> str:
        """Return the rendered HTML for ``url``."""
        page = self._context.new_page()
        try:
            page.goto(url, timeout=self.timeout_ms, wait_until=self.wait_until)
            if self.settle_seconds:
                page.wait_for_timeout(self.settle_seconds * 1000)
            return page.content()
        finally:
            page.close()

    def __exit__(self, *exc_info) -> None:
        for closer in (
            getattr(self._context, "close", None),
            getattr(self._browser, "close", None),
            getattr(self._playwright, "stop", None),
        ):
            if closer is None:
                continue
            try:
                closer()
            except Exception:
                pass


# --------------------------------------------------------------------------
# Pagination
# --------------------------------------------------------------------------

def _clean_href(href: str | None, current_url: str) -> str | None:
    """Resolve ``href`` against the current page, or None if it isn't a page link."""
    if not href:
        return None
    href = href.strip()
    if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
        return None
    absolute, _ = urldefrag(urljoin(current_url, href))
    if not absolute.startswith(("http://", "https://")):
        return None
    return absolute


def find_next_page_url(
    html: str, current_url: str, selector: str | None = None
) -> str | None:
    """Find the "next page" link, trying the most reliable signals first."""
    soup = BeautifulSoup(html, "html.parser")

    def _has_rel_next(tag) -> bool:
        rel = tag.get("rel") or []
        if isinstance(rel, str):
            rel = [rel]
        return any(str(value).lower() == "next" for value in rel)

    candidates: list[Any] = []
    if selector:
        candidates.extend(soup.select(selector))
    candidates.extend(t for t in soup.find_all(["link", "a"]) if _has_rel_next(t))
    for anchor in soup.find_all("a"):
        labels = (
            anchor.get_text(" ", strip=True),
            (anchor.get("aria-label") or "").strip(),
            (anchor.get("title") or "").strip(),
        )
        if any(NEXT_TEXT_RE.match(label) for label in labels if label):
            candidates.append(anchor)

    for tag in candidates:
        url = _clean_href(tag.get("href"), current_url)
        if url and url != current_url:
            return url
    return None


# --------------------------------------------------------------------------
# Record normalisation
# --------------------------------------------------------------------------

def _pick(raw: dict, aliases: Sequence[str]) -> str:
    """Pull the first populated value matching any alias for a field."""
    normalised = {
        str(key).strip().lower().replace(" ", "_").replace("-", "_"): value
        for key, value in raw.items()
    }
    for alias in aliases:
        if alias not in normalised:
            continue
        value = normalised[alias]
        if isinstance(value, (list, tuple)):
            value = value[0] if value else ""
        if value is None:
            continue
        text = str(value).strip()
        if text.lower() not in NULLISH:
            return text
    return ""


def clean_email(value: str) -> str:
    """Normalise an email, returning "" if it isn't a usable public address."""
    if not value:
        return ""
    text = str(value).strip()
    if text.lower().startswith("mailto:"):
        text = text[len("mailto:"):]
    text = text.split("?")[0]
    text = text.replace(" (at) ", "@").replace("[at]", "@").replace(" at ", "@")
    match = EMAIL_RE.search(text)
    if not match:
        return ""
    email = match.group(0).lower().rstrip(".")
    domain = email.rsplit("@", 1)[-1]
    if domain in JUNK_EMAIL_DOMAINS:
        return ""
    if domain.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")):
        return ""
    return email


def normalize_website(value: str, fallback_email: str = "") -> str:
    """Coerce a website value to an absolute URL, falling back to the email domain."""
    text = str(value or "").strip()
    if text and not text.lower().startswith(("http://", "https://")):
        text = "https://" + text.lstrip("/") if "." in text and " " not in text else ""
    if text and not urlparse(text).netloc:
        text = ""
    if not text and fallback_email and "@" in fallback_email:
        text = "https://" + fallback_email.rsplit("@", 1)[-1]
    return text


def domain_key(website: str, email: str = "") -> str:
    """The de-dupe key: the bare registrable host, lowercased and www-stripped."""
    host = urlparse(website).netloc.lower() if website else ""
    if not host and email:
        host = email.rsplit("@", 1)[-1].lower()
    host = host.rsplit("@", 1)[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return host


def normalize_record(raw: dict, page_url: str, default_city: str = "") -> dict | None:
    """Turn one model-produced object into a CSV row, or None if it has no email."""
    if not isinstance(raw, dict):
        return None
    email = clean_email(_pick(raw, FIELD_ALIASES["email"]))
    if not email:
        return None
    website = normalize_website(_pick(raw, FIELD_ALIASES["website"]), email)
    record = {
        "company_name": _pick(raw, FIELD_ALIASES["company_name"]),
        "contact_name": _pick(raw, FIELD_ALIASES["contact_name"]),
        "role": _pick(raw, FIELD_ALIASES["role"]),
        "email": email,
        "phone": _pick(raw, FIELD_ALIASES["phone"]),
        "website": website,
        "city": _pick(raw, FIELD_ALIASES["city"]) or default_city,
        "source_url": page_url,
    }
    return record


def coerce_records(result: Any) -> list[dict]:
    """Unwrap whatever shape the model returned into a flat list of dicts."""
    if result is None:
        return []
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (ValueError, TypeError):
            return []
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    if isinstance(result, dict):
        for key in ("listings", "leads", "results", "items", "data",
                    "businesses", "companies", "entries"):
            if isinstance(result.get(key), list):
                return [i for i in result[key] if isinstance(i, dict)]
        lists = [v for v in result.values() if isinstance(v, list)]
        if len(lists) == 1:
            return [i for i in lists[0] if isinstance(i, dict)]
        if any(k in result for k in ("email", "company_name", "company")):
            return [result]
    return []


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------

class ScrapeGraphExtractor:
    """Extracts listings from a page using ScrapeGraphAI and the local model.

    Called as ``extractor(html, page_url) -> list[dict]``.
    """

    def __init__(
        self,
        graph_config: dict,
        prompt: str = EXTRACTION_PROMPT,
        convert_to_markdown: bool = True,
    ):
        self.graph_config = graph_config
        self.prompt = prompt
        self.convert_to_markdown = convert_to_markdown

    def __call__(self, html: str, page_url: str) -> list[dict]:
        from scrapegraphai.graphs import SmartScraperGraph

        source = html
        if self.convert_to_markdown:
            # Markdown is far cheaper in tokens than raw HTML, which matters a
            # lot for a small local model. Links (incl. mailto:) survive.
            from scrapegraphai.utils import convert_to_md

            source = convert_to_md(html, page_url)
        graph = SmartScraperGraph(
            prompt=self.prompt, source=source, config=self.graph_config
        )
        return coerce_records(graph.run())


# --------------------------------------------------------------------------
# CSV output
# --------------------------------------------------------------------------

def load_existing_domains(csv_path: str | Path) -> set[str]:
    """Read the domains already present in the CSV so re-runs don't duplicate."""
    path = Path(csv_path)
    if not path.exists():
        return set()
    domains: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = domain_key(row.get("website", ""), row.get("email", ""))
            if key:
                domains.add(key)
    return domains


def append_rows(csv_path: str | Path, rows: Sequence[dict]) -> None:
    """Append rows, writing the header first if the file is new or empty."""
    if not rows:
        return
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})


# --------------------------------------------------------------------------
# Crawl
# --------------------------------------------------------------------------

@dataclass
class ScrapeResult:
    """Tally for one source, aggregated across all of its pages."""

    rows: list[dict] = field(default_factory=list)
    duplicates: int = 0
    skipped_no_email: int = 0
    pages_crawled: int = 0
    blocked_by_robots: int = 0
    errors: list[str] = field(default_factory=list)

    def merge(self, other: "ScrapeResult") -> None:
        self.rows.extend(other.rows)
        self.duplicates += other.duplicates
        self.skipped_no_email += other.skipped_no_email
        self.pages_crawled += other.pages_crawled
        self.blocked_by_robots += other.blocked_by_robots
        self.errors.extend(other.errors)


def _page_url_sequence(source: dict, max_pages: int) -> list[str] | None:
    """Build URLs up front when the source declares a page-URL template."""
    template = source.get("page_url_template")
    if not template:
        return None
    start = int(source.get("start_page", 1))
    step = int(source.get("page_step", 1))
    return [template.format(page=start + i * step) for i in range(max_pages)]


def scrape_source(
    source: dict,
    *,
    crawl_cfg: dict,
    extractor: Callable[[str, str], list[dict]],
    fetcher: PageFetcher,
    robots: RobotsPolicy,
    known_domains: set[str],
    max_pages: int | None = None,
    verbose: bool = True,
) -> ScrapeResult:
    """Crawl every result page of one source and collect new, de-duped leads."""
    result = ScrapeResult()
    limit = int(max_pages or crawl_cfg.get("max_pages", 25))
    delay = float(crawl_cfg.get("request_delay_seconds", 2.0))
    default_city = source.get("city", "")
    selector = source.get("next_page_selector")
    label = source.get("name") or source.get("url") or "source"

    templated = _page_url_sequence(source, limit)
    if templated:
        queue = list(templated)
        follow_links = False
    else:
        start_url = source.get("url")
        if not start_url:
            result.errors.append(f"[{label}] no 'url' or 'page_url_template' configured")
            return result
        queue = [start_url]
        follow_links = True

    visited: set[str] = set()
    index = 0

    while queue and result.pages_crawled < limit:
        page_url = queue.pop(0)
        if page_url in visited:
            break
        visited.add(page_url)

        if not robots.allows(page_url):
            result.blocked_by_robots += 1
            result.errors.append(f"[{label}] robots.txt disallows {page_url}")
            if verbose:
                print(f"  - blocked by robots.txt: {page_url}", file=sys.stderr)
            break

        if index:
            time.sleep(max(delay, robots.crawl_delay(page_url) or 0.0))
        index += 1

        try:
            html = fetcher.fetch(page_url)
        except Exception as exc:  # network/render failures shouldn't kill the run
            result.errors.append(f"[{label}] fetch failed for {page_url}: {exc}")
            if verbose:
                print(f"  ! fetch failed: {page_url}: {exc}", file=sys.stderr)
            break

        result.pages_crawled += 1

        try:
            raw_records = extractor(html, page_url)
        except Exception as exc:
            result.errors.append(f"[{label}] extraction failed for {page_url}: {exc}")
            if verbose:
                print(f"  ! extraction failed: {page_url}: {exc}", file=sys.stderr)
            raw_records = []

        page_new = 0
        for raw in raw_records:
            record = normalize_record(raw, page_url, default_city)
            if record is None:
                result.skipped_no_email += 1
                continue
            key = domain_key(record["website"], record["email"])
            if not key or key in known_domains:
                result.duplicates += 1
                continue
            known_domains.add(key)
            result.rows.append(record)
            page_new += 1

        if verbose:
            print(
                f"  page {result.pages_crawled}: {len(raw_records)} listings, "
                f"{page_new} new  <- {page_url}"
            )

        # A templated run stops at the first page that yields nothing at all,
        # which is how these sites signal "past the last page".
        if not follow_links:
            if not raw_records:
                break
            continue

        next_url = find_next_page_url(html, page_url, selector)
        if next_url and next_url not in visited:
            queue.append(next_url)

    return result


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def run(
    config: dict,
    *,
    sources: list[dict] | None = None,
    extractor: Callable[[str, str], list[dict]] | None = None,
    max_pages: int | None = None,
    dry_run: bool = False,
    verbose: bool = True,
) -> ScrapeResult:
    """Scrape every configured source and append new leads to the CSV."""
    crawl_cfg = config["crawl"]
    output_cfg = config["output"]
    targets = sources if sources is not None else config.get("sources") or []
    if not targets:
        raise ValueError(
            "No sources configured. Add one to config.yml or pass --source URL."
        )

    csv_path = Path(output_cfg["csv_path"])
    if not csv_path.is_absolute():
        csv_path = BASE_DIR / csv_path

    known_domains = load_existing_domains(csv_path)
    if verbose:
        print(f"Known domains already in {csv_path.name}: {len(known_domains)}")

    if extractor is None:
        extractor = ScrapeGraphExtractor(
            build_graph_config(config["llm"], verbose=False),
            convert_to_markdown=crawl_cfg.get("convert_to_markdown", True),
        )

    overall = ScrapeResult()
    fetcher = PageFetcher(
        headless=crawl_cfg.get("headless", True),
        timeout_seconds=crawl_cfg.get("page_timeout_seconds", 45),
        user_agent=crawl_cfg.get("user_agent"),
        wait_until=crawl_cfg.get("wait_until", "domcontentloaded"),
        settle_seconds=crawl_cfg.get("settle_seconds", 0.0),
        browser_executable_path=crawl_cfg.get("browser_executable_path"),
        proxy_server=crawl_cfg.get("proxy_server"),
        ignore_https_errors=crawl_cfg.get("ignore_https_errors", False),
    )
    robots = RobotsPolicy(
        user_agent=crawl_cfg.get("user_agent", ""),
        enabled=crawl_cfg.get("respect_robots_txt", True),
    )

    with fetcher:
        for source in targets:
            if verbose:
                print(f"\nSource: {source.get('name') or source.get('url')}")
            overall.merge(
                scrape_source(
                    source,
                    crawl_cfg=crawl_cfg,
                    extractor=extractor,
                    fetcher=fetcher,
                    robots=robots,
                    known_domains=known_domains,
                    max_pages=max_pages,
                    verbose=verbose,
                )
            )

    if not dry_run:
        append_rows(csv_path, overall.rows)

    return overall


def print_summary(result: ScrapeResult, dry_run: bool = False) -> None:
    """Report the counts the operator actually cares about."""
    verb = "would add" if dry_run else "Added"
    print()
    print(f"{verb} {len(result.rows)} new rows")
    print(f"Skipped {result.duplicates} duplicates")
    if result.skipped_no_email:
        print(f"Skipped {result.skipped_no_email} listings with no email")
    print(f"Pages crawled: {result.pages_crawled}")
    if result.errors:
        print(f"Errors: {len(result.errors)}")
        for message in result.errors:
            print(f"  - {message}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape leads from a directory site using a local Ollama model."
    )
    parser.add_argument("--config", help="Path to config.yml (default: alongside this script)")
    parser.add_argument("--source", help="Listing URL to scrape, overriding config sources")
    parser.add_argument("--name", default="cli", help="Label for the --source target")
    parser.add_argument("--city", default="", help="Fallback city for rows that omit one")
    parser.add_argument("--max-pages", type=int, help="Cap on result pages per source")
    parser.add_argument("--csv", help="Override the output CSV path")
    parser.add_argument("--dry-run", action="store_true", help="Extract but do not write the CSV")
    parser.add_argument("--quiet", action="store_true", help="Only print the final summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)
    if args.csv:
        config["output"]["csv_path"] = args.csv

    sources = None
    if args.source:
        sources = [{"name": args.name, "url": args.source, "city": args.city}]

    try:
        result = run(
            config,
            sources=sources,
            max_pages=args.max_pages,
            dry_run=args.dry_run,
            verbose=not args.quiet,
        )
    except Exception as exc:
        print(f"Run failed: {exc}", file=sys.stderr)
        return 1

    print_summary(result, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

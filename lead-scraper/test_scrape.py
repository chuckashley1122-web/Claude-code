#!/usr/bin/env python3
"""Smoke test: scrape a single page end to end and show what came back.

Run this first, before pointing the real scraper at anything:

    python test_scrape.py                       # scrapes a stable demo page
    python test_scrape.py --url https://...     # or a page of your choosing

It checks the three things that actually break, one at a time, and tells you
exactly which one failed:

  1. Playwright can launch Chromium and render a page
  2. Ollama is running and the configured model is pulled
  3. ScrapeGraphAI can drive the model and return structured data
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

from lead_scraper import (
    PageFetcher,
    ScrapeGraphExtractor,
    build_graph_config,
    load_config,
)

DEMO_URL = "https://scrapegraphai.com/"
DEMO_PROMPT = (
    "Return JSON describing this page with the keys: title (the page's main "
    "heading or title), summary (one sentence describing what the page is "
    "about), and emails (a list of any email addresses shown on the page, or "
    "an empty list). Only use what is visible on the page; never invent values."
)


def check_ollama(base_url: str, model: str) -> tuple[bool, str]:
    """Confirm the Ollama server is up and the model we want is pulled."""
    tags_url = base_url.rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(tags_url, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        return False, (
            f"Could not reach Ollama at {base_url} ({exc.reason}).\n"
            f"    Start it with:  ollama serve"
        )
    except Exception as exc:
        return False, f"Unexpected error talking to Ollama at {base_url}: {exc}"

    available = [m.get("name", "") for m in payload.get("models", [])]
    wanted = model.split("/", 1)[-1]
    # Ollama reports "llama3.1:latest" for a plain "llama3.1" pull.
    if any(name == wanted or name.split(":")[0] == wanted.split(":")[0]
           for name in available):
        return True, f"Ollama is up, model '{wanted}' is available."
    return False, (
        f"Ollama is running but '{wanted}' is not pulled.\n"
        f"    Pull it with:  ollama pull {wanted}\n"
        f"    Models present: {', '.join(available) or '(none)'}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEMO_URL, help=f"Page to scrape (default: {DEMO_URL})")
    parser.add_argument("--config", help="Path to config.yml")
    parser.add_argument("--prompt", default=DEMO_PROMPT, help="Extraction prompt")
    parser.add_argument(
        "--skip-llm", action="store_true", help="Only test the fetch step"
    )
    args = parser.parse_args(argv)

    config = load_config(args.config)
    crawl_cfg = config["crawl"]
    llm_cfg = config["llm"]

    # --- 1. Fetch -----------------------------------------------------------
    print(f"[1/3] Fetching {args.url} with Playwright ...")
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
    try:
        with fetcher:
            html = fetcher.fetch(args.url)
    except Exception as exc:
        print(f"      FAILED: {exc}", file=sys.stderr)
        print(
            "      If Chromium is missing, run:  playwright install chromium",
            file=sys.stderr,
        )
        return 1
    print(f"      OK - rendered {len(html):,} bytes of HTML")

    if args.skip_llm:
        print("\nSkipping the model steps (--skip-llm). Fetch works.")
        return 0

    # --- 2. Ollama ----------------------------------------------------------
    print(f"[2/3] Checking Ollama at {llm_cfg['base_url']} ...")
    ok, message = check_ollama(llm_cfg["base_url"], llm_cfg["model"])
    print(f"      {'OK - ' if ok else 'FAILED: '}{message}")
    if not ok:
        print(
            "\nThe fetch step works; only the local model is missing. "
            "Fix the above and re-run.",
            file=sys.stderr,
        )
        return 1

    # --- 3. Extract ---------------------------------------------------------
    print(f"[3/3] Extracting with {llm_cfg['model']} (first run can be slow) ...")
    extractor = ScrapeGraphExtractor(
        build_graph_config(llm_cfg, verbose=False),
        prompt=args.prompt,
        convert_to_markdown=crawl_cfg.get("convert_to_markdown", True),
    )
    try:
        from scrapegraphai.graphs import SmartScraperGraph
        from scrapegraphai.utils import convert_to_md

        source = convert_to_md(html, args.url) if extractor.convert_to_markdown else html
        graph = SmartScraperGraph(
            prompt=args.prompt, source=source, config=extractor.graph_config
        )
        result = graph.run()
    except Exception as exc:
        print(f"      FAILED: {exc}", file=sys.stderr)
        return 1

    print("      OK - model returned:\n")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    print("\nAll three steps passed. The install works.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Offline end-to-end test of the scraping pipeline.

Runs the real crawler, the real ScrapeGraphAI graph and the real CSV writer
against two local stand-ins:

  * a fixture directory site (3 paginated pages + robots.txt) on 127.0.0.1
  * a stub Ollama server that speaks the /api/chat protocol and answers
    deterministically, so the test needs no GPU, no model download and no
    internet access

It verifies pagination, robots.txt handling, the no-email skip, de-duplication
by website domain, CSV append-with-header, and the reported counts.

    python selftest.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from lead_scraper import (
    DEFAULT_CONFIG,
    ScrapeGraphExtractor,
    _deep_merge,
    build_graph_config,
    load_existing_domains,
    run,
)

# --------------------------------------------------------------------------
# Fixture directory site
# --------------------------------------------------------------------------

def _listing(company, owner, role, email, phone, website, city) -> str:
    email_html = (
        f'<p>Email: <a href="mailto:{email}">{email}</a></p>' if email
        else "<p>Email: not published</p>"
    )
    # Use the bare host as the link text: a bare-URL anchor becomes a markdown
    # autolink, which ScrapeGraphAI's cleanup strips before the model sees it.
    display = website.split("//", 1)[-1]
    return f"""
    <div class="listing">
      <h2>{company}</h2>
      <p>Owner: {owner}</p>
      <p>Role: {role}</p>
      {email_html}
      <p>Phone: {phone}</p>
      <p>Web: <a href="{website}">{display}</a></p>
      <p>City: {city}</p>
    </div>
    """


PAGES = {
    "/": [
        ("Acme Plumbing", "Jane Doe", "Managing Director", "jane@acmeplumbing.com",
         "+1 512 555 0101", "https://acmeplumbing.com", "Austin"),
        ("Brightside Roofing", "Sam Reed", "Owner", "sam@brightsideroofing.com",
         "+1 512 555 0102", "https://brightsideroofing.com", "Austin"),
        ("Cedar HVAC", "Alex Kim", "Founder", "alex@cedarhvac.com",
         "+1 512 555 0103", "https://cedarhvac.com", "Austin"),
    ],
    "/page/2": [
        # Same domain as page 1 -> must be counted as a duplicate.
        ("Acme Plumbing (Downtown)", "Jane Doe", "Managing Director",
         "info@acmeplumbing.com", "+1 512 555 0111", "https://www.acmeplumbing.com",
         "Austin"),
        # No email -> must be skipped.
        ("Delta Electric", "Pat Vance", "Owner", "",
         "+1 512 555 0104", "https://deltaelectric.com", "Austin"),
        ("Eastwood Landscaping", "Robin Fox", "Principal", "robin@eastwoodland.com",
         "+1 512 555 0105", "https://eastwoodland.com", "Austin"),
    ],
    "/page/3": [
        ("Fairview Dental", "Chris Lane", "Practice Manager", "chris@fairviewdental.com",
         "+1 512 555 0106", "https://fairviewdental.com", "Round Rock"),
        ("Granite Interiors", "Morgan Ellis", "Director", "morgan@graniteinteriors.com",
         "+1 512 555 0107", "https://graniteinteriors.com", "Round Rock"),
    ],
}

NEXT_LINK = {"/": "/page/2", "/page/2": "/page/3", "/page/3": None}


def render_page(path: str) -> str:
    body = "".join(_listing(*row) for row in PAGES[path])
    nxt = NEXT_LINK[path]
    nav = f'<a rel="next" href="{nxt}">Next</a>' if nxt else "<span>End of results</span>"
    return f"""<!doctype html>
<html><head><title>Fixture Directory</title></head>
<body><h1>Austin Trade Directory</h1>{body}<nav>{nav}</nav></body></html>"""


#: Flipped by the robots.txt check below so the fixture starts disallowing.
DISALLOW_ALL = False


class SiteHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        path = self.path.split("?")[0].rstrip("/") or "/"
        if path == "/robots.txt":
            rules = (
                "User-agent: *\nDisallow: /\n" if DISALLOW_ALL
                else "User-agent: *\nAllow: /\nCrawl-delay: 0\n"
            )
            return self._send(rules, "text/plain")
        if path in PAGES:
            return self._send(render_page(path), "text/html")
        self.send_error(404)

    def _send(self, body: str, content_type: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):  # silence request logging
        pass


# --------------------------------------------------------------------------
# Stub Ollama server
# --------------------------------------------------------------------------

#: Labels the fixture emits, used to find where each field's value ends.
LABELS = ("Owner", "Role", "Email", "Phone", "Web", "City")
LABEL_ALT = "|".join(LABELS)
LINK_RE = re.compile(r"\[(?P<text>[^\]]*)\]\([^)]*\)")


def _clean_value(value: str) -> str:
    # Markdown links arrive as [text](target); keep only the visible text.
    value = LINK_RE.sub(lambda m: m.group("text"), value).strip()
    return "" if value.lower() in {"not published", "na", ""} else value


def _field(block: str, label: str) -> str:
    match = re.search(
        rf"{label}:\s*(?P<value>.*?)(?=\s+(?:{LABEL_ALT}):|$)",
        block,
        re.IGNORECASE | re.DOTALL,
    )
    return _clean_value(match.group("value")) if match else ""


def extract_listings_from_prompt(prompt: str) -> list[dict]:
    """Deterministically parse the fixture content embedded in the prompt.

    ScrapeGraphAI embeds the page as the repr of a list of documents, so the
    markdown arrives hard-wrapped with newlines escaped to literal "\\n". Both
    are normalised to spaces here before parsing inline "## <company>" markers.
    """
    body = prompt.split("WEBSITE CONTENT:", 1)[-1]
    body = re.sub(r"\s+", " ", body.replace("\\n", " ").replace("\n", " "))
    # Drop the pagination nav so it can't bleed into the last listing's city.
    for marker in ("[Next](", "End of results"):
        cut = body.find(marker)
        if cut != -1:
            body = body[:cut]
    listings = []
    for segment in body.split("## ")[1:]:
        name_match = re.match(
            rf"(?P<company>.*?)(?=\s+(?:{LABEL_ALT}):|$)", segment, re.DOTALL
        )
        company = _clean_value(name_match.group("company") if name_match else segment)
        listings.append({
            "company_name": company,
            "contact_name": _field(segment, "Owner"),
            "role": _field(segment, "Role"),
            "email": _field(segment, "Email"),
            "phone": _field(segment, "Phone"),
            "website": _field(segment, "Web"),
            "city": _field(segment, "City"),
        })
    return listings


class OllamaHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path.startswith("/api/tags"):
            return self._json({"models": [{"name": "llama3.1:latest"}]})
        if self.path.startswith("/api/version"):
            return self._json({"version": "0.0.0-selftest"})
        self.send_error(404)

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {}

        if self.path.startswith("/api/show"):
            return self._json({"model_info": {}, "capabilities": ["completion"]})

        prompt = " ".join(
            str(message.get("content", ""))
            for message in payload.get("messages", [])
        )
        content = json.dumps({"listings": extract_listings_from_prompt(prompt)})
        message = {"role": "assistant", "content": content}
        body = {
            "model": payload.get("model", "llama3.1"),
            "created_at": "2024-01-01T00:00:00Z",
            "message": message,
            "done": True,
            "done_reason": "stop",
            "total_duration": 1,
            "eval_count": 1,
            "prompt_eval_count": 1,
        }
        if payload.get("stream"):
            chunks = [json.dumps(body).encode("utf-8") + b"\n"]
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.end_headers()
            for chunk in chunks:
                self.wfile.write(chunk)
            return
        return self._json(body)

    def _json(self, obj) -> None:
        payload = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


# --------------------------------------------------------------------------
# Test driver
# --------------------------------------------------------------------------

class Server:
    def __init__(self, handler):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"


def patch_tokenizer_for_offline_use() -> None:
    """Keep the test fully offline.

    ScrapeGraphAI sizes its chunks with tiktoken regardless of which provider
    is in use, and tiktoken downloads its encoding file from the network the
    first time it runs. That download is the only part of a real run that
    touches the internet, and it has nothing to do with the logic under test,
    so swap in a rough character-based estimate here.
    """
    import importlib

    # Note: scrapegraphai.utils re-exports the *function* under the same name
    # as its module, so import the module explicitly to patch its globals.
    chunker = importlib.import_module("scrapegraphai.utils.split_text_into_chunks")
    chunker.num_tokens_calculus = lambda text: max(1, len(text) // 4)


FAILURES: list[str] = []


def check(label: str, actual, expected) -> None:
    if actual == expected:
        print(f"  PASS  {label}: {actual}")
    else:
        print(f"  FAIL  {label}: got {actual!r}, expected {expected!r}")
        FAILURES.append(label)


def main() -> int:
    patch_tokenizer_for_offline_use()
    workdir = Path(tempfile.mkdtemp(prefix="leadscraper-selftest-"))
    csv_path = workdir / "leads.csv"

    try:
        with Server(SiteHandler) as site, Server(OllamaHandler) as ollama:
            config = _deep_merge(DEFAULT_CONFIG, {
                "crawl": {
                    "request_delay_seconds": 0.0,
                    "max_pages": 10,
                    "browser_executable_path": os.environ.get("LEADSCRAPER_CHROMIUM"),
                },
                "llm": {"base_url": ollama.base_url},
                "output": {"csv_path": str(csv_path)},
            })
            sources = [{"name": "fixture", "url": site.base_url + "/"}]
            extractor = ScrapeGraphExtractor(
                build_graph_config(config["llm"], verbose=False),
                convert_to_markdown=True,
            )

            print("Run 1 - fresh CSV")
            first = run(config, sources=sources, extractor=extractor, verbose=True)
            check("pages crawled", first.pages_crawled, 3)
            check("new rows", len(first.rows), 6)
            check("duplicates skipped", first.duplicates, 1)
            check("listings with no email skipped", first.skipped_no_email, 1)
            check("errors", first.errors, [])

            header = csv_path.read_text(encoding="utf-8").splitlines()[0]
            check(
                "csv header",
                header,
                "company_name,contact_name,role,email,phone,website,city,source_url",
            )
            check("csv data rows", len(csv_path.read_text().splitlines()) - 1, 6)
            check("domains loaded back", len(load_existing_domains(csv_path)), 6)

            print("\nRun 2 - same sources again, everything should de-dupe")
            second = run(config, sources=sources, extractor=extractor, verbose=False)
            check("new rows on re-run", len(second.rows), 0)
            check("duplicates on re-run", second.duplicates, 7)
            check("csv still has 6 data rows",
                  len(csv_path.read_text().splitlines()) - 1, 6)

            print("\nRun 3 - robots.txt disallow is honoured")
            globals()["DISALLOW_ALL"] = True
            try:
                third = run(config, sources=sources, extractor=extractor, verbose=False)
            finally:
                globals()["DISALLOW_ALL"] = False
            check("pages crawled while disallowed", third.pages_crawled, 0)
            check("blocked count", third.blocked_by_robots, 1)

    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) FAILED: {', '.join(FAILURES)}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

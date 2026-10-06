"""Zero-cost, unauthenticated, JavaScript-off HTML GET -> evidence JSON in out/baseline/.

* Plain GET only: no JavaScript execution, no cookies, no auth headers.
* At most 2 retries (3 attempts) on network errors / 5xx.
* Refuses non-http(s) schemes, URLs carrying credentials or key/token query
  parameters, and API-style hosts that may be metered or authenticated.
* DRY_RUN by default: the CLI only touches the network with --allow-network.
  ``--html-file`` parses a local file instead. Tests inject an opener.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qsl, urljoin, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.paths import Paths, default_paths  # noqa: E402

MAX_RETRIES = 2
USER_AGENT = "caj-spec05-raw-html-check/1.0 (no-js; unauthenticated)"
CREDENTIAL_PARAMS = {"key", "api_key", "apikey", "token", "access_token", "auth", "password", "secret", "sig",
                     "signature"}
API_HOST_PREFIXES = ("api.", "graph.", "rest.", "services.")
TRACKING_PATTERNS = {
    "google_analytics_4": re.compile(r"\bG-[A-Z0-9]{6,12}\b"),
    "google_tag_manager": re.compile(r"\bGTM-[A-Z0-9]{4,10}\b"),
    "universal_analytics": re.compile(r"\bUA-\d{4,10}-\d{1,4}\b"),
    "meta_pixel": re.compile(r"fbq\(\s*['\"]init['\"]\s*,\s*['\"](\d{6,20})['\"]"),
}


class FetchRefused(ValueError):
    """The URL is outside what this zero-cost, unauthenticated tool may fetch."""


def refuse_reason(url: str) -> str | None:
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        return f"scheme {parts.scheme or '(none)'!r} refused: only http(s)"
    if not parts.hostname:
        return "no host"
    if parts.username or parts.password:
        return "credentials in URL refused"
    for name, _ in parse_qsl(parts.query, keep_blank_values=True):
        if name.lower() in CREDENTIAL_PARAMS:
            return f"query parameter {name!r} looks like a credential; refused"
    if parts.hostname.lower().startswith(API_HOST_PREFIXES):
        return "API-style host refused: may be metered or require auth; this tool fetches public pages only"
    return None


class _RawHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.h1, self.canonical, self.meta_description = None, [], None, None
        self.robots, self.og, self.links, self.forms, self.iframes, self.scripts = None, {}, [], [], [], []
        self._in_title, self._h1_depth, self._h1_buf, self._text = False, 0, [], []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self._in_title = True
            self.title = ""
        elif tag == "h1":
            self._h1_depth += 1
            self._h1_buf = []
        elif tag == "link" and "canonical" in a.get("rel", "").lower().split():
            self.canonical = a.get("href")
        elif tag == "meta":
            name, prop = a.get("name", "").lower(), a.get("property", "").lower()
            if name == "description":
                self.meta_description = a.get("content")
            elif name == "robots":
                self.robots = a.get("content")
            elif prop.startswith("og:"):
                self.og[prop] = a.get("content")
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "form":
            self.forms.append({"action": a.get("action"), "method": a.get("method", "get").lower()})
        elif tag == "iframe" and a.get("src"):
            self.iframes.append(a["src"])
        elif tag == "script":
            self._skip += 1
            if a.get("src"):
                self.scripts.append(a["src"])
        elif tag == "style":
            self._skip += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "h1" and self._h1_depth:
            self._h1_depth -= 1
            self.h1.append(" ".join("".join(self._h1_buf).split()))
        elif tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._h1_depth:
            self._h1_buf.append(data)
        if not self._skip and not self._in_title:
            self._text.append(data)

    @property
    def visible_text(self) -> str:
        return " ".join(" ".join(self._text).split())


def parse_html(html: str, base_url: str) -> dict:
    p = _RawHTMLParser()
    p.feed(html)
    p.close()
    base_host = urlsplit(base_url).hostname
    internal = []
    for href in p.links:
        if href.startswith(("mailto:", "tel:", "#", "javascript:")):
            continue
        absolute = urljoin(base_url, href)
        host = urlsplit(absolute).hostname
        if host == base_host or urlsplit(href).scheme == "":
            if absolute not in internal:
                internal.append(absolute)
    tracking = {name: sorted(set(m if isinstance(m, str) else m[0] for m in pat.findall(html)))
                for name, pat in TRACKING_PATTERNS.items()}
    return {
        "title": (p.title or "").strip() or None,
        "h1": p.h1,
        "canonical": p.canonical,
        "meta_description": p.meta_description,
        "robots": p.robots,
        "og": p.og,
        "internal_links": internal,
        "forms": p.forms,
        "iframes": p.iframes,
        "script_srcs": p.scripts,
        "tracking_ids": {k: v for k, v in tracking.items() if v},
        "visible_text_chars": len(p.visible_text),
        "visible_text_sample": p.visible_text[:300],
    }


class _RecordRedirects(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.chain: list[dict] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.chain.append({"status": code, "location": newurl})
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def default_opener():
    """Opener with no cookie processor and no auth handlers; redirects are recorded."""
    redirects = _RecordRedirects()
    opener = urllib.request.OpenerDirector()
    for handler in (urllib.request.ProxyHandler(), urllib.request.HTTPHandler(), urllib.request.HTTPSHandler(),
                    urllib.request.HTTPDefaultErrorHandler(), urllib.request.HTTPErrorProcessor(), redirects):
        opener.add_handler(handler)
    opener.redirect_chain = redirects.chain
    return opener


def fetch(url: str, opener: Any = None, timeout: float = 15.0, sleep: Callable[[float], None] = time.sleep,
          max_retries: int = MAX_RETRIES) -> dict:
    reason = refuse_reason(url)
    if reason:
        raise FetchRefused(reason)
    max_retries = min(max_retries, MAX_RETRIES)
    opener = opener or default_opener()
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT,
                                                                 "Accept": "text/html"})
    for banned in ("Authorization", "Cookie"):
        request.remove_header(banned)
    attempts, last_error, status, body, final_url, headers = 0, None, None, b"", url, {}
    while attempts <= max_retries:
        attempts += 1
        try:
            resp = opener.open(request, timeout=timeout)
            status, body, final_url = resp.getcode(), resp.read(), resp.geturl()
            headers = dict(resp.headers.items()) if getattr(resp, "headers", None) else {}
            last_error = None
            break
        except urllib.error.HTTPError as exc:
            status, body, final_url = exc.code, exc.read() or b"", url
            headers = dict(exc.headers.items()) if exc.headers else {}
            last_error = None
            if exc.code >= 500 and attempts <= max_retries:
                sleep(0.5 * attempts)
                continue
            break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = f"{type(exc).__name__}: {getattr(exc, 'reason', exc)}"
            if attempts <= max_retries:
                sleep(0.5 * attempts)
                continue
    evidence = {
        "url": url,
        "final_url": final_url,
        "fetched_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": "GET (no JavaScript, no cookies, no auth)",
        "attempts": attempts,
        "status": status,
        "error": last_error,
        "redirect_chain": list(getattr(opener, "redirect_chain", [])),
        "content_type": headers.get("Content-Type") or headers.get("content-type"),
    }
    if body:
        charset = "utf-8"
        m = re.search(r"charset=([\w-]+)", evidence["content_type"] or "")
        if m:
            charset = m.group(1)
        evidence.update(parse_html(body.decode(charset, errors="replace"), final_url))
    return evidence


def slug_for_url(url: str) -> str:
    parts = urlsplit(url)
    raw = f"{parts.hostname or 'local'}{parts.path}".strip("/") or "root"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", raw)[:120]


def write_evidence(evidence: dict, paths: Paths) -> Path:
    target = paths.out / "baseline" / f"{slug_for_url(evidence['url'])}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8", newline="\n")
    return target


def main(argv: list[str] | None = None, paths: Paths | None = None, opener: Any = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("url", nargs="?")
    ap.add_argument("--allow-network", action="store_true", help="perform a real unauthenticated GET")
    ap.add_argument("--html-file", help="parse a local HTML file instead of fetching")
    args = ap.parse_args(argv)
    paths = paths or default_paths()
    if args.html_file:
        html = Path(args.html_file).read_text(encoding="utf-8")
        evidence = {"url": args.url or Path(args.html_file).resolve().as_uri(), "status": None,
                    "method": "local file parse", **parse_html(html, args.url or "file:///")}
    else:
        if not args.url:
            print("BLOCKED: no URL supplied")
            return 3
        reason = refuse_reason(args.url)
        if reason:
            print(f"REFUSED: {reason}")
            return 2
        if not (args.allow_network or opener):
            print("DRY_RUN: network fetch requires --allow-network (zero-cost unauthenticated GET)")
            return 3
        evidence = fetch(args.url, opener=opener)
    print(write_evidence(evidence, paths))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

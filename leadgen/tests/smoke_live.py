"""Live network smoke test — NOT run by pytest (needs outbound HTTP).

    python tests/smoke_live.py

Checks that Scrapling's HTTP fetcher, its browser fetcher, and the enrichment
signal pass all work in this environment.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from leadgen.browser import browser_kwargs, proxy  # noqa: E402
from leadgen.enrich import detect_signals  # noqa: E402
from leadgen.models import Lead  # noqa: E402

print(f"proxy={proxy() or '(none)'}  browser_kwargs={browser_kwargs()}")

print("\n[1] Scrapling Fetcher (plain HTTP)")
from scrapling.fetchers import Fetcher  # noqa: E402

kwargs = {"stealthy_headers": True, "timeout": 30}
if proxy():
    kwargs["proxy"] = proxy()
page = Fetcher.get("https://raw.githubusercontent.com/D4Vinci/Scrapling/main/README.md", **kwargs)
print(f"    status={page.status} h1={page.css_first('h1::text')}")
assert page.status == 200

print("\n[2] Scrapling parser (CSS + adaptive selectors)")
print(f"    links found: {len(page.css('a'))}")

print("\n[3] enrichment signal pass against a real site")
lead = Lead(company="Example", company_domain="raw.githubusercontent.com")
detect_signals(lead)
hits = sorted(k for k, v in lead.signals.items() if v)
print(f"    signals: {hits or '(none)'}")
print(f"    notes:   {lead.notes or '(none)'}")

print("\n[4] StealthyFetcher (real browser)")
try:
    from scrapling.fetchers import StealthyFetcher

    bpage = StealthyFetcher.fetch("https://raw.githubusercontent.com/D4Vinci/Scrapling/main/README.md", timeout=45000, **browser_kwargs())
    print(f"    status={bpage.status} title={bpage.css_first('title::text')}")
except Exception as exc:
    print(f"    SKIPPED/FAILED: {type(exc).__name__}: {str(exc)[:200]}")

print("\nsmoke test done")

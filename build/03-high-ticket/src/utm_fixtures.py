"""UTM / fbclid test-URL generator and attribution-parameter fixtures -> out/attribution_fixtures.json

Fixture values only (clearly labeled). Real campaign/ad IDs are NEEDS_EVIDENCE.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from tools import guardrails as G  # noqa: E402

ATTRIBUTION_KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "fbclid"]
FIXTURE_DATE = date(2026, 1, 1)  # fixture only; the real draft date is set by the human who creates the campaign


def build_test_url(base: str, campaign_name: str, ad_id: str, fbclid: str) -> str:
    G.assert_new_campaign_name(campaign_name)
    parts = urlsplit(base)
    query = urlencode({"utm_source": "facebook", "utm_medium": "paid_social", "utm_campaign": campaign_name,
                       "utm_content": ad_id, "fbclid": fbclid})
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


def parse_attribution(url: str) -> dict:
    q = parse_qs(urlsplit(url).query)
    out = {k: q[k][0] for k in ATTRIBUTION_KEYS if k in q}
    if "utm_campaign" in out:
        G.assert_not_frozen_campaign(out["utm_campaign"])
    return out


def fixtures() -> dict:
    name = G.new_campaign_name(FIXTURE_DATE)
    rows = []
    for i, ad in enumerate(["A01", "A02", "A03", "A04", "A05"], 1):
        url = build_test_url(C.BOOKING_URL, name, ad, f"TEST-FBCLID-{i:03d}")
        rows.append({"ad_id": ad, "url": url, "expected": parse_attribution(url)})
    return {"label": "FIXTURE - test attribution URLs, not real campaign data", "campaign_name_fixture": name,
            "real_campaign_id": C.NEEDS_EVIDENCE, "urls": rows}


def build(state) -> list[Path]:
    state.needs("real campaign and ad IDs", "out/attribution_fixtures.json", "Record after the human creates the draft campaign in Meta")
    return [state.write_json("out/attribution_fixtures.json", fixtures(), "ATTRIBUTION-FIXTURES", source="src/utm_fixtures.py")]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

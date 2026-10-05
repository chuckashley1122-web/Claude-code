"""Dummy fbclid / fbc / fbp / utm_* test-URL generator for the human CAPI test.

Output: out/test_urls.txt - 3 tracked variants + 1 no-parameter control URL.
Every value is deterministic dummy TEST DATA (seeded from the variant label),
never real click data. The control URL is expected NOT to fire a conversion.
"""
from __future__ import annotations

import hashlib
import string
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402

PLACEHOLDER_LANDING_URL = "https://offer.example.com/"
TEST_DATA_MARK = "TEST DATA — not for production traffic"
REQUIRED_PARAMS = ("fbclid", "fbc", "fbp", "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")
_ALNUM = string.ascii_letters + string.digits
_BASE_TS_MS = 1759622400000  # fixed dummy click timestamp (ms) so output is reproducible


def _digest(seed: str) -> bytes:
    return hashlib.sha256(seed.encode("utf-8")).digest() * 4


def _alnum(seed: str, n: int) -> str:
    return "".join(_ALNUM[b % len(_ALNUM)] for b in _digest(seed)[:n])


def _digits(seed: str, n: int) -> str:
    return "".join(str(b % 10) for b in _digest(seed)[:n])


def dummy_params(campaign_name: str, variant: str, content: str, term: str, index: int) -> dict:
    fbclid = "IwAR0TEST" + _alnum(f"{campaign_name}:{variant}:fbclid", 40)
    ts = _BASE_TS_MS + index * 60_000
    return {
        "utm_source": "facebook",
        "utm_medium": "paid_social",
        "utm_campaign": campaign_name,
        "utm_content": content,
        "utm_term": term,
        "fbclid": fbclid,
        "fbc": f"fb.1.{ts}.{fbclid}",
        "fbp": f"fb.1.{ts}.{_digits(campaign_name + variant + ':fbp', 10)}",
    }


def build_url(base_url: str, params: dict | None) -> str:
    parts = urlsplit(base_url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError(f"Landing-page URL must be absolute http(s): {base_url!r}")
    if parts.query:
        raise ValueError("Landing-page URL must be clean (no existing query string)")
    query = urlencode(params) if params else ""
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", query, ""))


def resolve_landing_url(config: dict) -> tuple[str, bool]:
    """Return (url, is_placeholder). Unknown landing URL -> example.com placeholder."""
    url = config.get("landing_page_url", C.NEEDS_EVIDENCE)
    if not url or url == C.NEEDS_EVIDENCE:
        return PLACEHOLDER_LANDING_URL, True
    return url, False


VARIANTS = [
    ("variant-1", "A01-pain-image", "hvac-owners"),
    ("variant-2", "A02-outcome-video", "hvac-owners"),
    ("variant-3", "A04-offer-image", "hvac-owners"),
]


def build_test_urls(base_url: str, campaign_name: str) -> list[dict]:
    rows = []
    for i, (label, content, term) in enumerate(VARIANTS, start=1):
        params = dummy_params(campaign_name, label, content, term, i)
        rows.append({"label": label, "url": build_url(base_url, params), "expect_conversion": True})
    rows.append({"label": "control-no-params", "url": build_url(base_url, None), "expect_conversion": False})
    return rows


def missing_params(url: str) -> list[str]:
    q = parse_qs(urlsplit(url).query)
    return [p for p in REQUIRED_PARAMS if p not in q or not q[p][0]]


def render(rows: list[dict], is_placeholder: bool) -> str:
    lines = [f"# {TEST_DATA_MARK}",
             "# Dummy tracking URLs for the human CAPI test (SPEC-04 step 5.6). Open in a private window, submit the",
             "# test form, then read the CAPI workflow Execution Logs in GHL. This build cannot do that step.",
             f"# Booking destination after the thank-you page: {C.BOOKING_URL}"]
    if is_placeholder:
        lines.append("# landing_page_url is NEEDS_EVIDENCE: URLs use the offer.example.com placeholder. Regenerate "
                     "after the verified subdomain is live.")
    lines.append("")
    for r in rows:
        expect = "expected to fire a Lead conversion" if r["expect_conversion"] else \
            "CONTROL: expected NOT to fire a conversion (no Facebook parameters)"
        lines.append(f"# {TEST_DATA_MARK} | {r['label']} | {expect}")
        lines.append(r["url"])
        lines.append("")
    return "\n".join(lines)


def build(ctx) -> Path:
    base, is_placeholder = resolve_landing_url(ctx.config)
    rows = build_test_urls(base, ctx.draft_campaign_name())
    if is_placeholder:
        ctx.state.record_blocker("landing_page_url", "Verified live subdomain URL",
                                 "test_urls.txt, campaign ad website URL, CAPI test",
                                 "Publish AI Studio page on the approved subdomain, set landing_page_url, rebuild")
    return ctx.write_asset("out/test_urls.txt", render(rows, is_placeholder), "test_urls", "tools/utm_builder.py")


if __name__ == "__main__":
    from tools.state import BuildContext
    print(build(BuildContext(ROOT)))

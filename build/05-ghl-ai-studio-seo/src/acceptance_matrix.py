"""The source's 14-case acceptance matrix -> out/tests/test_log.md + T01.json ... T14.json.

Verdict rule: a case whose pass condition can be fully evaluated offline gets
PASS or FAIL. A case whose pass condition is defined by a live site, a live CRM
or a human review gets BLOCKED when its local checks pass (and FAIL when they
do not). No BLOCKED case is ever reported as passing.

The inquiry cases use MockGHLAdapter (MOCK - NOT PRODUCTION) and a synthetic
service allowlist; a green mock run is not evidence that the real integration works.
"""

from __future__ import annotations

import io
import json
import re
import sys
import tempfile
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from src import page_plan, site_mock  # noqa: E402
from src.ghl_adapter import MockGHLAdapter, UpstreamPermissionError  # noqa: E402
from src.idempotency_store import IdempotencyStore  # noqa: E402
from src.inquiry_handler import InquiryHandler  # noqa: E402
from tools import fetch_raw_html as F  # noqa: E402
from tools import guardrails as G  # noqa: E402
from tools import secret_scan  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, emit  # noqa: E402

VERDICTS = ("PASS", "FAIL", "BLOCKED")
SYNTHETIC_CONFIG = {"service_allowlist": ["synthetic_test_service"],
                    "allowed_source_origins": ["https://example.com"]}


def synthetic_inquiry(submission_id: str = "synthetic-0001", **overrides) -> dict:
    body = {"submission_id": submission_id, "name": "Synthetic Tester", "email": "tester@example.com",
            "phone": "512-555-0100", "service_interest": "synthetic_test_service",
            "message": "Synthetic acceptance test inquiry.", "source_page": "https://example.com/contact",
            "consent": True}
    body.update(overrides)
    return body


class LocalSiteOpener:
    """Serves out/site/*.html as if fetched over HTTP, so T02 exercises fetch_raw_html offline."""

    def __init__(self, site_dir: Path):
        self.site_dir = Path(site_dir)
        self.requests: list[str] = []
        self.redirect_chain: list = []

    def open(self, request, timeout=None):
        url = request.full_url
        self.requests.append(url)
        if request.get_header("Authorization") or request.get_header("Cookie"):
            raise AssertionError("fetch sent credentials")
        path = url.split("://", 1)[1].split("/", 1)[1] if "/" in url.split("://", 1)[1] else ""
        target = self.site_dir / site_mock.file_for("/" + path if path else "/")
        if not target.exists():
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, io.BytesIO(b""))
        return _Resp(url, target.read_bytes())


class _Resp:
    def __init__(self, url: str, body: bytes):
        self.url, self.body = url, body
        self.headers = {"Content-Type": "text/html; charset=utf-8"}

    def getcode(self):
        return 200

    def read(self):
        return self.body

    def geturl(self):
        return self.url


def _case(test_id, name, inp, expected, actual, verdict, evidence, live_component=None, local_checks=None):
    assert verdict in VERDICTS
    return {"test_id": test_id, "name": name, "input": inp, "expected_result": expected,
            "actual_result": actual, "evidence_path": evidence, "verdict": verdict,
            "live_component": live_component, "local_checks": local_checks or {}}


def _local_then_blocked(ok: bool) -> str:
    return "BLOCKED" if ok else "FAIL"


def _handler(tmp: Path, adapter, name: str, **kwargs) -> InquiryHandler:
    sleeps: list = []
    h = InquiryHandler(adapter, IdempotencyStore(tmp / f"{name}.db"), config=SYNTHETIC_CONFIG,
                       sleep=sleeps.append, **kwargs)
    h.sleeps = sleeps
    return h


def run(paths: Paths | None = None) -> list[dict]:
    paths = paths or default_paths()
    out_tests = paths.out / "tests"
    rows = page_plan.load(paths)
    site = paths.out / "site"
    meta = json.loads((paths.out / "metadata.json").read_text(encoding="utf-8"))
    results: list[dict] = []
    ev = lambda tid: f"out/tests/{tid}.json"  # noqa: E731

    # T01 public routes
    checks = {}
    for row in rows:
        html = (site / site_mock.file_for(row["route"])).read_text(encoding="utf-8")
        parsed = F.parse_html(html, "file:///")
        checks[row["route"]] = all([parsed["title"], parsed["h1"], parsed["canonical"],
                                    parsed["visible_text_chars"] > 200, len(parsed["internal_links"]) >= 5,
                                    "STATIC CONTENT MOCK" in html, "<script" not in html.lower()])
    ok = all(checks.values())
    results.append(_case("T01", "Public routes", "every route mock in out/site/",
                         "200 and correct route content, no blank shell",
                         f"local mocks complete: {ok}; live direct load/refresh not possible (no site exists)",
                         _local_then_blocked(ok), ev("T01"), "direct load + refresh on the draft/live host",
                         checks))

    # T02 initial HTML via fetch_raw_html against a local opener (no JS)
    opener = LocalSiteOpener(site)
    checks = {}
    for row in [r for r in rows if r["indexable"]]:
        url = "https://mock.example.com" + row["route"]
        evidence = F.fetch(url, opener=opener)
        mrec = next(m for m in meta["records"] if m["route"] == row["route"])
        checks[row["route"]] = all([evidence["status"] == 200, evidence["title"] == row["title"],
                                    evidence["h1"] == [row["h1"]], evidence["canonical"] == row["canonical"],
                                    evidence["meta_description"] == mrec["meta_description"],
                                    evidence["visible_text_chars"] > 200, len(evidence["internal_links"]) >= 5])
    ok = all(checks.values()) and bool(checks)
    results.append(_case("T02", "Initial HTML", "raw GET without JavaScript of each indexable mock",
                         "main copy, H1, title, canonical, links present in raw markup",
                         f"{sum(checks.values())}/{len(checks)} routes complete in raw HTML",
                         "PASS" if ok else "FAIL", ev("T02"), None, checks))

    # T03 unknown route
    html404 = (site / "404.html").read_text(encoding="utf-8")
    p404 = F.parse_html(html404, "file:///")
    ok = bool(p404["h1"]) and len(p404["internal_links"]) >= 5 and "noindex" in (p404["robots"] or "") \
        and "HTTP 404" in html404
    results.append(_case("T03", "Unknown route", "out/site/404.html", "real 404 with useful navigation",
                         f"local 404 mock complete: {ok}; host 404 status cannot be observed offline",
                         _local_then_blocked(ok), ev("T03"), "request a made-up URL on the host; expect HTTP 404",
                         {"404_mock": ok}))

    # T04 metadata
    try:
        G.assert_canonical_unique(meta["records"])
        unique_ok = True
    except G.GuardrailViolation:
        unique_ok = False
    inv = {r["route"]: r for r in rows}
    canon_ok = all(m["canonical"] == inv[m["route"]]["canonical"] for m in meta["records"])
    intents = [inv[m["route"]]["search_intent"] for m in meta["records"]]
    preview_ok = all(m["og"]["og:image"] == C.NEEDS_EVIDENCE or m["og"]["og:image"].startswith("https://")
                     for m in meta["records"])
    ok = unique_ok and canon_ok and len(set(intents)) == len(intents) and preview_ok
    results.append(_case("T04", "Metadata", "out/metadata.json", "distinct intent, correct canonical and preview",
                         f"unique={unique_ok} canonical_match={canon_ok} distinct_intent="
                         f"{len(set(intents)) == len(intents)} preview_fields={preview_ok}",
                         "PASS" if ok else "FAIL", ev("T04")))

    # T05 crawl controls
    tree = ET.parse(paths.out / "seo" / "sitemap.xml")
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = sorted(e.text for e in tree.getroot().findall("s:url/s:loc", ns))
    expected_locs = sorted(r["canonical"] for r in rows if r["indexable"])
    robots = (paths.out / "seo" / "robots.txt").read_text(encoding="utf-8")
    ok = locs == expected_locs and not any("thank-you" in l or "404" in l for l in locs) \
        and "Disallow: /\n" not in robots
    results.append(_case("T05", "Crawl controls", "out/seo/sitemap.xml + robots.txt + indexability.md",
                         "only intended public URLs eligible", f"sitemap URLs={len(locs)} match indexable "
                         f"routes={locs == expected_locs}", "PASS" if ok else "FAIL", ev("T05")))

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # T06 form success (mock)
        mock = MockGHLAdapter()
        h = _handler(tmp, mock, "t06")
        r = h.handle(json.dumps(synthetic_inquiry()))
        ok = r.status == 201 and r.body.get("inquiry_reference", "").startswith("inq_") \
            and "mocki_" not in json.dumps(r.body) and len(mock.inquiries) == 1
        results.append(_case("T06", "Form success", "synthetic valid inquiry -> reference handler + MOCK adapter",
                             "confirmed saved record and truthful UI",
                             f"mock: status={r.status}, opaque reference only={ok}; live CRM record not verified",
                             _local_then_blocked(ok), ev("T06"),
                             "submit through the draft browser form and find the contact in GHL (005-006)",
                             {"mock_201": ok}))

        # T07 bad input
        mock = MockGHLAdapter()
        h = _handler(tmp, mock, "t07")
        cases = {
            "empty": h.handle(b"").status,
            "oversized": h.handle(json.dumps(synthetic_inquiry(message="x" * (C.MAX_PAYLOAD_BYTES + 1)))).status,
            "invalid_email": h.handle(json.dumps(synthetic_inquiry("synthetic-0702", email="nope", phone=""))).status,
            "long_name": h.handle(json.dumps(synthetic_inquiry("synthetic-0703", name="n" * (C.MAX_NAME_LEN + 1)))).status,
            "unknown_service": h.handle(json.dumps(synthetic_inquiry("synthetic-0704", service_interest="x"))).status,
            "privileged_field": h.handle(json.dumps(synthetic_inquiry("synthetic-0705", location_id="x"))).status,
        }
        ok = all(s in (400, 422) for s in cases.values()) and not mock.calls
        results.append(_case("T07", "Bad input", "empty, oversized and invalid inquiries",
                             "server rejection, no CRM write", f"statuses={cases}, adapter calls={len(mock.calls)}",
                             "PASS" if ok else "FAIL", ev("T07"), None, cases))

        # T08 retry with same submission_id
        mock = MockGHLAdapter()
        h = _handler(tmp, mock, "t08")
        first = h.handle(json.dumps(synthetic_inquiry("synthetic-0801")))
        second = h.handle(json.dumps(synthetic_inquiry("synthetic-0801")))
        ok = first.status == second.status == 201 and first.body == second.body and len(mock.inquiries) == 1
        results.append(_case("T08", "Retry", "same submission_id sent twice", "one intended submission and outcome",
                             f"statuses={first.status}/{second.status}, CRM records={len(mock.inquiries)}",
                             "PASS" if ok else "FAIL", ev("T08")))

        # T09 CRM outage: timeout and rejected token
        slow = MockGHLAdapter(delay_s=0.3)
        h = _handler(tmp, slow, "t09a", timeout_s=0.05)
        rt = h.handle(json.dumps(synthetic_inquiry("synthetic-0901")))
        denied = MockGHLAdapter(script=[UpstreamPermissionError("token rejected")])
        h2 = _handler(tmp, denied, "t09b")
        rd = h2.handle(json.dumps(synthetic_inquiry("synthetic-0902")))
        ok = (rt.status == 503 and len(slow.calls) == C.MAX_RETRIES + 1 and rd.status == 502
              and len(denied.calls) == 1 and rt.body["status"] == rd.body["status"] == "error")
        results.append(_case("T09", "CRM outage", "upstream timeout; rejected token",
                             "bounded failure, no false success",
                             f"timeout -> {rt.status} after {len(slow.calls)} attempts; rejected token -> "
                             f"{rd.status} after {len(denied.calls)} attempt", "PASS" if ok else "FAIL", ev("T09")))

    # T10 secret exposure
    hits = secret_scan.scan(paths)
    browser = " ".join(p.read_text(encoding="utf-8") for p in site.glob("*.html"))
    names_in_browser = [n for n in secret_scan.env_names(paths) if n in browser]
    ok = not hits and not names_in_browser
    results.append(_case("T10", "Secret exposure", "all generated files; browser HTML",
                         "no private credential disclosure",
                         f"secret hits={len(hits)}; env names in browser HTML={names_in_browser}",
                         "PASS" if ok else "FAIL", ev("T10")))

    # T11 private data
    results.append(_case("T11", "Private data", "unauthenticated and cross-user access",
                         "no unauthorized records returned",
                         "not testable offline: depends on the platform's actual auth model", "BLOCKED", ev("T11"),
                         "human verifies platform data access controls (005-006)"))

    # T12 mobile and keyboard heuristics (mock only)
    checks = {}
    for path in sorted(site.glob("*.html")):
        html = path.read_text(encoding="utf-8")
        ids = set(re.findall(r'<(?:input|select|textarea)[^>]*\bid="([^"]+)"', html))
        labels = set(re.findall(r'<label[^>]*\bfor="([^"]+)"', html))
        checks[path.name] = all(['name="viewport"' in html, ids <= labels, "tabindex=" not in html,
                                 ":focus-visible" in html, "font-size:16px" in html, "min-height:44px" in html,
                                 ('role="alert"' in html) if ids else True])
    ok = all(checks.values())
    results.append(_case("T12", "Mobile and keyboard", "mock heuristics (labelled): viewport, labels, focus, sizes",
                         "usable controls and readable errors",
                         f"mock heuristics pass={ok}; real device/keyboard review required",
                         _local_then_blocked(ok), ev("T12"), "human narrow-viewport + keyboard-only review", checks))

    # T13 regression
    cta_ok = all(C.BOOKING_URL in (site / site_mock.file_for(r["route"])).read_text(encoding="utf-8") for r in rows)
    results.append(_case("T13", "Regression", "/ai, CTAs, calendar, tracking",
                         "existing intended behaviour preserved",
                         f"local: every mock links {C.BOOKING_URL} unchanged={cta_ok}; live /ai, calendar and "
                         "tracking need live access", _local_then_blocked(cta_ok), ev("T13"),
                         "human rechecks /ai, calendar and tracking on the live site"))

    # T14 estimator
    blocked_md = (paths.out / "estimator" / "BLOCKED.md").exists()
    results.append(_case("T14", "Estimator if included", "approved worked examples",
                         "exact results and tampering resistance",
                         f"feature disabled (ESTIMATOR_ENABLED={C.ESTIMATOR_ENABLED}); BLOCKED.md present={blocked_md}",
                         "BLOCKED", ev("T14"), "business supplies versioned rules + three worked examples"))

    for case in results:
        emit(f"test:{case['test_id']}", out_tests / f"{case['test_id']}.json", case,
             STATUS.TESTED if case["verdict"] == "PASS" else STATUS.BLOCKED if case["verdict"] == "BLOCKED"
             else STATUS.DRAFT, paths, source="src/acceptance_matrix.py")
    emit("test_log", out_tests / "test_log.md", render_log(results), STATUS.TESTED, paths,
         source="src/acceptance_matrix.py")
    return results


def counts(results: list[dict]) -> dict[str, int]:
    return {v: sum(1 for r in results if r["verdict"] == v) for v in VERDICTS}


def render_log(results: list[dict]) -> str:
    c = counts(results)
    lines = ["# Acceptance test log (SPEC-05, source matrix T01-T14)", "",
             f"PASS {c['PASS']} | FAIL {c['FAIL']} | BLOCKED {c['BLOCKED']}. BLOCKED means the pass condition "
             "needs a live site, live CRM or human review; it is never counted as passing. Inquiry cases use the "
             "MOCK adapter; a mock pass is not evidence the real GHL integration works.", "",
             "| Test | Name | Expected | Actual | Verdict | Evidence |", "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['test_id']} | {r['name']} | {r['expected_result']} | {r['actual_result']} | "
                     f"{r['verdict']} | {r['evidence_path']} |")
    lines.append("")
    return "\n".join(lines)


def load_results(paths: Paths | None = None) -> list[dict]:
    paths = paths or default_paths()
    return [json.loads((paths.out / "tests" / f"T{i:02d}.json").read_text(encoding="utf-8")) for i in range(1, 15)
            if (paths.out / "tests" / f"T{i:02d}.json").exists()]


if __name__ == "__main__":
    print(counts(run()))

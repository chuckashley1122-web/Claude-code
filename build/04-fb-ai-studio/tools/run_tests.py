"""Acceptance test log T01-T14 -> out/tests/test_log.md + T01.json ... T14.json.

Run: python tools/run_tests.py   (builds first if outputs are missing)
Verdicts: PASS | FAIL | BLOCKED. Anything needing a live account or a UI action
is BLOCKED with the exact missing input - never reported as passing.
Exit code 1 if any case FAILs (BLOCKED does not fail the run).
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from tools import guardrails as G  # noqa: E402
from tools.compliance_scan import _fenced, target_files  # noqa: E402
from tools.meta_gateway import LaunchNotApproved, LiveCallBlocked, LiveMetaGateway, LocalDraftGateway  # noqa: E402
from tools.utm_builder import REQUIRED_PARAMS, TEST_DATA_MARK, missing_params  # noqa: E402

PASS, FAIL, BLOCKED = "PASS", "FAIL", "BLOCKED"
TOKEN_RE = re.compile(r"\{\{[^}]+\}\}")
MERGE_FLAG = "UNCONFIRMED MERGE SYNTAX"


class _Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags: list[tuple[str, dict]] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if "id" in a:
            self.ids.add(a["id"])


def _page(path: Path) -> _Page:
    p = _Page()
    p.feed(path.read_text(encoding="utf-8"))
    return p


def _spec_block(path: Path) -> dict:
    return json.loads(_fenced(path.read_text(encoding="utf-8"), "json workflow-spec")[0])


def _result(tid, inp, expected, actual, evidence, verdict) -> dict:
    return {"test_id": tid, "input": inp, "expected_result": expected, "actual_result": actual,
            "evidence_path": evidence, "verdict": verdict}


# ---------------------------------------------------------------------------
def t01(root: Path) -> dict:
    p = root / "out/landing/index.html"
    page = _page(p)
    text = p.read_text(encoding="utf-8")
    ctas = [a for t, a in page.tags if t == "a" and "cta" in (a.get("class") or "").split()]
    bad_cta = [a.get("href") for a in ctas if a.get("href") != "#lead-form"]
    external = [(t, a) for t, a in page.tags if t in ("script", "link", "iframe", "img", "object", "embed")
                or (t != "a" and any(str(v).startswith(("http:", "https:", "//")) for v in a.values() if v))]
    buttons = [a for t, a in page.tags if t == "button"]
    ok = (bool(ctas) and not bad_cta and not external and "lead-form" in page.ids
          and "STATIC CONTENT MOCK" in text and all(b.get("type") == "button" for b in buttons))
    return _result("T01", "out/landing/index.html parsed offline (file://)",
                   "Opens standalone; every CTA scrolls to #lead-form; no external script/resource; mock banner shown",
                   f"{len(ctas)} CTAs, non-form CTA hrefs={bad_cta}, external loads={len(external)}, "
                   f"buttons type=button={all(b.get('type') == 'button' for b in buttons)}",
                   "out/landing/index.html", PASS if ok else FAIL)


def t02(root: Path) -> dict:
    spec = json.loads((root / "out/landing/content_spec.json").read_text(encoding="utf-8"))
    page = _page(root / "out/landing/index.html")
    html_fields = [a.get("name") for t, a in page.tags if t in ("input", "select", "textarea") and a.get("name")]
    spec_fields = [f["name"] for f in spec["form"]["fields"]]
    html_text = (root / "out/landing/index.html").read_text(encoding="utf-8")
    consent = spec["form"]["consent_disclosure"]
    form_tag = [a for t, a in page.tags if t == "form"]
    ok = html_fields == spec_fields and "consent" in spec_fields and consent.split(".")[0] in html_text \
        and form_tag and "action" not in form_tag[0]
    return _result("T02", "content_spec.json form fields vs index.html inputs",
                   "Field-for-field match; consent disclosure present; form has no action",
                   f"spec={spec_fields} html={html_fields} consent_present={consent.split('.')[0] in html_text}",
                   "out/landing/content_spec.json; out/landing/index.html", PASS if ok else FAIL)


def t03(root: Path) -> dict:
    page = _page(root / "out/landing/thank-you.html")
    hrefs = [a.get("href") for t, a in page.tags if t == "a"]
    ok = C.BOOKING_URL in hrefs and C.BOOKING_URL == "https://ca-jenterprises.com/ai"
    return _result("T03", "out/landing/thank-you.html links", f"Booking CTA to {C.BOOKING_URL}",
                   f"hrefs={hrefs}", "out/landing/thank-you.html", PASS if ok else FAIL)


def t04(root: Path) -> dict:
    sp = _spec_block(root / "out/workflows/01-new-lead-automation.md")
    steps = sp["steps"]
    sends = [s for s in steps if s["type"] == "send_sms"]
    waits = [s["config"] for s in steps if s["type"] == "wait"]
    days = [s["day"] for s in sends]
    last = steps[-1]
    # every send is immediately preceded by a reply/opt-out check
    prechecked = all(steps[steps.index(s) - 1]["type"] == "if_else" for s in sends)
    ok = (6 <= len(sends) <= 7 and days == sorted(days) and days[:2] == [1, 1] and days[-1] == 14
          and waits[0] == "1 minute" and waits[1] == "2 hours" and waits[-1] == "1 day"
          and last["type"] == "create_update_opportunity" and "Stage=Lost" in last["config"] and prechecked
          and steps[0]["type"] == "create_update_opportunity" and "Stage=New Lead" in steps[0]["config"])
    return _result("T04", "Workflow 01 embedded spec", "6-7 touchpoints, waits 1 min / 2 h / ... / 1 day, final move to Lost",
                   f"sends={len(sends)} days={days} waits={waits} last={last['config']} prechecked={prechecked}",
                   "out/workflows/01-new-lead-automation.md", PASS if ok else FAIL)


def t05(root: Path) -> dict:
    sp = _spec_block(root / "out/workflows/02-hot-lead-replied.md")
    types = [s["type"] for s in sp["steps"]]
    ok = (types and types[0] == "remove_from_workflow" and "New Lead Automation" in sp["steps"][0]["config"]
          and sp["trigger"]["type"] == "Customer Replied" and "send_sms" not in types[:1])
    return _result("T05", "Workflow 02 embedded spec", "Remove from Workflow 01 is the first action, before any send",
                   f"action order={types}", "out/workflows/02-hot-lead-replied.md", PASS if ok else FAIL)


def t06(root: Path) -> dict:
    a = _spec_block(root / "out/workflows/03-landing-page-capi-lead.md")["action"]
    s = json.loads((root / "out/capi_settings.json").read_text(encoding="utf-8"))
    keys = ["event_type", "event_to_send", "custom_mapping", "currency", "test_code", "ltv"]
    diffs = {k: (a.get(k), s.get(k)) for k in keys if a.get(k) != s.get(k)}
    ok = not diffs and s["event_type"] == "Funnel Event" and s["event_to_send"] == "Lead" \
        and s["custom_mapping"] == "OFF" and s["currency"] == "USD"
    return _result("T06", "Workflow 03 action vs capi_settings.json", "event type / event / mapping / currency match",
                   f"differences={diffs}", "out/workflows/03-landing-page-capi-lead.md; out/capi_settings.json",
                   PASS if ok else FAIL)


def t07(root: Path) -> dict:
    offenders, asserted = [], []
    for p in (root / "out").rglob("*.md"):
        text = p.read_text(encoding="utf-8")
        if TOKEN_RE.search(text) and MERGE_FLAG not in text and "unconfirmed" not in text.lower():
            offenders.append(p.relative_to(root).as_posix())
        if re.search(r"(verified|valid|confirmed)\s+(ghl\s+)?merge\s+(syntax|token)", text, flags=re.I) and \
                not re.search(r"not\s+verified\s+ghl\s+syntax", text, flags=re.I):
            asserted.append(p.relative_to(root).as_posix())
    ok = not offenders and not asserted
    return _result("T07", "All out/**/*.md containing {{...}} tokens",
                   "Every file with a merge token carries the unconfirmed-syntax flag; none asserts valid GHL syntax",
                   f"unflagged={offenders} asserted_valid={asserted}", "out/messages/; out/workflows/", PASS if ok else FAIL)


def t08(root: Path) -> dict:
    s = json.loads((root / "out/capi_settings.json").read_text(encoding="utf-8"))
    secret_hits = {}
    for p in target_files(root):
        hits = G.find_secrets(p.read_text(encoding="utf-8"))
        if hits:
            secret_hits[p.name] = hits
    for p in (root / "config").glob("*.py"):
        hits = G.find_secrets(p.read_text(encoding="utf-8"))
        if hits:
            secret_hits[p.name] = hits
    env_lines = [ln for ln in (root / ".env.example").read_text(encoding="utf-8").splitlines()
                 if "=" in ln and not ln.startswith("#")]
    env_values = [ln for ln in env_lines if ln.split("=", 1)[1].strip()]
    by_name = s["pixel_id_env"] == C.PIXEL_ID_ENV and s["access_token_env"] == C.CAPI_ACCESS_TOKEN_ENV \
        and "pixel_id" not in s and "access_token" not in s
    ok = not secret_hits and not env_values and by_name
    return _result("T08", "capi_settings.json, .env.example and every scanned asset",
                   "Pixel and token referenced by env var name only; no value present anywhere",
                   f"secret-pattern hits={secret_hits} env values set={env_values} env-name refs ok={by_name}",
                   "out/capi_settings.json; .env.example", PASS if ok else FAIL)


def t09(root: Path) -> dict:
    c = json.loads((root / "out/campaign_config.json").read_text(encoding="utf-8"))
    ok = (c["draft"] is True and c["published_by_build"] is False and c["status"] == "DRAFT_UNPUBLISHED"
          and c["campaign"]["campaign_budget"] == "OFF" and c["ad_set"]["daily_budget"] == C.NEEDS_EVIDENCE
          and c["budget_exposure_usd"] == 0 and re.match(C.NEW_CAMPAIGN_NAME_REGEX, c["campaign"]["name"]))
    return _result("T09", "out/campaign_config.json", "Draft; campaign budget OFF; ad-set budget NEEDS_EVIDENCE",
                   f"status={c['status']} campaign_budget={c['campaign']['campaign_budget']} "
                   f"daily_budget={c['ad_set']['daily_budget']} name={c['campaign']['name']}",
                   "out/campaign_config.json", PASS if ok else FAIL)


def t10(root: Path) -> dict:
    from tools import validate_config
    import types
    good = {n: ok for n, ok, _ in validate_config.run_checks()}
    wrong_case = types.SimpleNamespace(**{k: getattr(C, k) for k in dir(C) if k.isupper()})
    wrong_case.GHL_LOCATION_ID = C.GHL_LOCATION_ID.lower()
    rejected_case = not dict((n, ok) for n, ok, _ in validate_config.run_checks(c=wrong_case))["ghl_location_id_exact_case"]
    disallowed = types.SimpleNamespace(**{k: getattr(C, k) for k in dir(C) if k.isupper()})
    disallowed.GHL_LOCATION_ID = C.DISALLOWED_LOCATION_ID
    rejected_disallowed = not dict((n, ok) for n, ok, _ in validate_config.run_checks(c=disallowed))["ghl_location_id_exact_case"]
    scan_hit = bool(G.find_location_id_problems("loc " + C.DISALLOWED_LOCATION_ID))
    ok = good.get("ghl_location_id_exact_case") and rejected_case and rejected_disallowed and scan_hit \
        and C.BOOKING_URL == "https://ca-jenterprises.com/ai"
    return _result("T10", "validate_config with real, lower-cased and disallowed (constants.DISALLOWED_LOCATION_ID) IDs",
                   "Exact case accepted; wrong case and the unverified ID rejected; booking URL literal exact",
                   f"exact_ok={good.get('ghl_location_id_exact_case')} wrong_case_rejected={rejected_case} "
                   f"disallowed_rejected={rejected_disallowed} scan_flags_disallowed={scan_hit}",
                   "tools/validate_config.py; config/constants.py", PASS if ok else FAIL)


def t11(root: Path) -> dict:
    hits = {}
    for p in sorted((root / "out/ads/copy").glob("A0*.md")):
        for block in _fenced(p.read_text(encoding="utf-8"), "json ad-copy"):
            d = json.loads(block)
            for s in [v["text"] for v in d["primary_texts"]] + d["headlines"]:
                h = G.find_ad_risk(s)
                if h:
                    hits.setdefault(p.name, []).extend(h)
    for block in _fenced((root / "out/ads/creative_specs.md").read_text(encoding="utf-8"), "json creative-records"):
        for rec in json.loads(block):
            h = G.find_ad_risk(" ".join(rec["on_image_text"]))
            if h:
                hits.setdefault(rec["asset_id"], []).extend(h)
    files = len(list((root / "out/ads/copy").glob("A0*.md")))
    ok = files == 4 and not hits
    return _result("T11", "Every primary text, headline and on-image text (A01-A04 + creative records)",
                   "No CA-J price, guarantee, scarcity, review count or client outcome",
                   f"files={files} hits={hits}", "out/ads/copy/; out/ads/creative_specs.md", PASS if ok else FAIL)


def t12(root: Path) -> dict:
    errors, recs = [], []
    for block in _fenced((root / "out/ads/creative_specs.md").read_text(encoding="utf-8"), "json creative-records"):
        recs = json.loads(block)
    for r in recs:
        try:
            G.assert_logo_not_first(r)
        except G.LogoFirstError as exc:
            errors.append(str(exc))
    types_ = sorted({r["opening_element"]["type"] for r in recs})
    ok = bool(recs) and not errors and set(types_) <= set(C.ALLOWED_OPENING_ELEMENT_TYPES)
    return _result("T12", f"{len(recs)} creative records", "assert_logo_not_first passes; every opening element is a pain or outcome",
                   f"errors={errors} opening types={types_}", "out/ads/creative_specs.md", PASS if ok else FAIL)


def t13(root: Path) -> dict:
    lines = (root / "out/test_urls.txt").read_text(encoding="utf-8").splitlines()
    urls = [ln for ln in lines if ln.startswith("http")]
    tracked, control = urls[:-1], urls[-1] if urls else ""
    missing = {u[:40]: missing_params(u) for u in tracked if missing_params(u)}
    control_params = parse_qs(urlsplit(control).query)
    marked = sum(1 for ln in lines if TEST_DATA_MARK in ln)
    ok = len(tracked) == 3 and not missing and control and not control_params and marked >= len(urls)
    return _result("T13", "out/test_urls.txt", f"3 URLs carry {', '.join(REQUIRED_PARAMS)}; control carries none; all marked TEST DATA",
                   f"tracked={len(tracked)} missing={missing} control_params={list(control_params)} test-data marks={marked}",
                   "out/test_urls.txt", PASS if ok else FAIL)


def t14(root: Path) -> dict:
    cfg = json.loads((root / "out/campaign_config.json").read_text(encoding="utf-8"))
    local = {}
    with tempfile.TemporaryDirectory() as tmp:
        gw = LocalDraftGateway(Path(tmp))
        name = cfg["campaign"]["name"]
        gw.create_draft_campaign(cfg)
        paused = gw.pause_campaign(name)["status"]
        restored = gw.restore_previous(name)
        local["pause"] = paused == LocalDraftGateway.STATUS_PAUSED
        local["prior_config_recoverable"] = restored["config"] == cfg and restored["status"] == LocalDraftGateway.STATUS_DRAFT
        try:
            gw.pause_campaign(C.FROZEN_CAMPAIGN_NAME)
            local["frozen_tripwire"] = False
        except G.FrozenCampaignError:
            local["frozen_tripwire"] = True
        try:
            gw.publish_campaign(name)
            local["publish_refused"] = False
        except LaunchNotApproved:
            local["publish_refused"] = True
    try:
        LiveMetaGateway().pause_campaign(cfg["campaign"]["name"])
        live_refused = False
    except LiveCallBlocked:
        live_refused = True
    local["live_refused"] = live_refused
    has_plan = all(k in cfg["rollback"] for k in ("pause", "stop_workflows", "recover_config"))
    actual = f"local rehearsal={local} rollback plan present={has_plan}"
    verdict = FAIL if not (all(local.values()) and has_plan) else BLOCKED
    return _result("T14", "Rollback: pause new campaign, stop affected workflows, recover prior config",
                   "Live pause and workflow stop verified in Ads Manager / GHL",
                   actual + ". BLOCKED: missing input = a live published draft campaign in Ads Manager and published "
                   "GHL workflows 01/03 (requires APPROVAL_LAUNCH + a logged-in human). Local rehearsal only.",
                   "out/campaign_config.json (rollback); tools/meta_gateway.py", verdict)


CASES = [t01, t02, t03, t04, t05, t06, t07, t08, t09, t10, t11, t12, t13, t14]


def run(root: Path = ROOT) -> list[dict]:
    root = Path(root)
    if not (root / "out/campaign_config.json").exists():
        from tools.build_all import run as build
        build(root, quiet=True)
    results = []
    for case in CASES:
        try:
            results.append(case(root))
        except Exception as exc:  # a crash is a FAIL, never a silent pass
            tid = case.__name__.upper()
            results.append(_result(tid, "-", "-", f"exception: {type(exc).__name__}: {exc}", "-", FAIL))
    out = root / "out/tests"
    out.mkdir(parents=True, exist_ok=True)
    for r in results:
        (out / f"{r['test_id']}.json").write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
    rows = ["# Test log (T01-T14)", "", "Verdicts: PASS | FAIL | BLOCKED. BLOCKED cases are never counted as passing.", "",
            "| Test | Verdict | Expected | Actual | Evidence |", "|---|---|---|---|---|"]
    for r in results:
        rows.append("| {test_id} | {verdict} | {expected_result} | {actual_result} | {evidence_path} |".format(
            **{k: str(v).replace("|", "/").replace("\n", " ") for k, v in r.items()}))
    counts = {v: sum(1 for r in results if r["verdict"] == v) for v in (PASS, FAIL, BLOCKED)}
    rows += ["", f"Totals: PASS {counts[PASS]}, FAIL {counts[FAIL]}, BLOCKED {counts[BLOCKED]}.", ""]
    (out / "test_log.md").write_text("\n".join(rows), encoding="utf-8")
    return results


def main() -> int:
    results = run()
    for r in results:
        print(f"{r['test_id']}  {r['verdict']:7}  {r['actual_result'][:150]}")
    counts = {v: sum(1 for r in results if r["verdict"] == v) for v in (PASS, FAIL, BLOCKED)}
    print(f"PASS {counts[PASS]}  FAIL {counts[FAIL]}  BLOCKED {counts[BLOCKED]}")
    return 1 if counts[FAIL] else 0


if __name__ == "__main__":
    sys.exit(main())

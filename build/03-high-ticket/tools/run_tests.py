"""T01-T14 acceptance cases -> out/tests/test_log.md + out/tests/T01.json ... T14.json

Each case runs its logic against the offline simulator (src/funnel_sim.py) and
the local connectors. The verdict is:
  FAIL    - the logic simulation did not produce the expected result
  BLOCKED - the logic passed but the case also needs a live account / UI action
            (recorded with the exact missing input); never reported as passing
  PASS    - fully verifiable offline and verified
Exit code is non-zero only if a case FAILs.

Run: python tools/run_tests.py
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src import funnel_sim as SIM  # noqa: E402
from src.common import OFFER_VERSION  # noqa: E402
from src.connectors import LocalAds  # noqa: E402
from tools import guardrails as G  # noqa: E402
from tools.state import State  # noqa: E402

T0 = datetime(2026, 10, 6, 15, 0, tzinfo=timezone.utc)  # Tuesday 10:00 America/Chicago (CDT) - fixture time
NE = C.NEEDS_EVIDENCE


def lead(n: int, answer: str = "Yes", **kw) -> dict:
    d = {"leadgen_id": f"TEST-LEAD-{n:03d}", "page_id": "TEST-PAGE", "form_id": "TEST-FORM", "full_name": f"Test Owner {n}",
         "email": f"owner{n}@example.com", "phone": f"512-555-01{n:02d}", "decision_maker_question": answer,
         "campaign_id": "TEST-CAMPAIGN", "ad_id": "A01"}
    d.update(kw)
    return d


def engine(**kw) -> SIM.FunnelEngine:
    kw.setdefault("working_hours", SIM.FIXTURE_HOURS)
    kw.setdefault("staffed_hours", SIM.FIXTURE_HOURS)
    return SIM.FunnelEngine(**kw)


def msgs(e, cid=None, template=None, channel=None):
    return [m for m in e.crm.messages if (cid is None or m["contact_id"] == cid) and (template is None or m["template"] == template)
            and (channel is None or m["channel"] == channel)]


def tasks(e, cid=None, contains=""):
    return [t for t in e.crm.tasks if (cid is None or t["contact_id"] == cid) and contains in t["title"]]


def stage(e, cid):
    return [o["stage"] for o in e.crm.opportunities_for(cid)]


def checks(*pairs) -> tuple[bool, list[str]]:
    lines = [f"{'ok' if ok else 'NOT OK'}: {desc}" for desc, ok in pairs]
    return all(ok for _, ok in pairs), lines


# ----------------------------------------------------------------------------- cases
def t01():
    e = engine()
    cid = e.submit_lead(lead(1), T0)
    now = T0 + timedelta(minutes=10)
    slot = e.slots(now)[0]
    aid = e.book(cid, slot, now)
    e.tick(T0 + timedelta(days=4))
    ok, lines = checks(
        ("exactly one contact", len(e.crm.contacts) == 1),
        ("one opportunity at Booked", stage(e, cid) == ["Booked"]),
        ("appointment saved on contact", e.crm.get_contact(cid)["custom"].get("appointment_id") == aid),
        ("confirmation sent once", len(msgs(e, cid, "confirmation")) == 1),
        ("no unbooked reminder/follow-up after booking", not msgs(e, cid, "unbooked_reminder") and not msgs(e, cid, "unbooked_followup")),
        ("no manual review task", not tasks(e, cid, "Manual review")))
    return dict(input="Qualified (Yes) lead, then self-books the first open slot", expected="One qualified contact+opportunity, correct calendar, unbooked follow-up stops",
                ok=ok, actual=lines, trace=e,
                missing=f"Live GHL calendar (sales_calendar_id {NE}), workflows 01-03 assembled in a test clone, and a Meta test lead submission")


def t02():
    e = engine()
    cid = e.submit_lead(lead(2), T0)
    call = tasks(e, cid, "Call new qualified lead")
    sat = datetime(2026, 10, 10, 15, 0, tzinfo=timezone.utc)  # Saturday, after staffed hours
    cid2 = e.submit_lead(lead(3), sat)
    call2 = tasks(e, cid2, "Call new qualified lead")
    e.tick(T0 + timedelta(days=4))
    ok, lines = checks(
        ("call task created immediately", len(call) == 1 and call[0]["created"] == T0),
        ("call task due within 5 minutes in staffed hours", call and call[0]["due"] - T0 <= timedelta(minutes=5)),
        ("after-hours task queued for next staffed window", call2 and call2[0]["created"] == sat
         and call2[0]["due"].astimezone(SIM.CENTRAL).weekday() == 0),
        ("permitted booking acknowledgment sent", len(msgs(e, cid, "booking_ack")) == 1),
        ("no appointment invented", not e.appointments and stage(e, cid) == ["Qualified unbooked"]),
        ("one +2h reminder", len(msgs(e, cid, "unbooked_reminder")) == 1),
        ("one +1d email", len(msgs(e, cid, "unbooked_followup")) == 1),
        ("+3d manual review then end", len(tasks(e, cid, "Manual review")) == 1 and not e.unbooked_active[cid]))
    return dict(input="Qualified (Yes) lead without booking, in and outside staffed hours", expected="Correct owner + 5-minute call task, permitted acknowledgment, no invented appointment",
                ok=ok, actual=lines, trace=e, missing=f"Staffed hours ({NE}), owner user in GHL, verified sending email and SMS eligibility ({NE})")


def t03():
    e = engine()
    cid = e.submit_lead(lead(4, answer="No"), T0)
    e.tick(T0 + timedelta(days=4))
    ok, lines = checks(
        ("stage Disqualified", stage(e, cid) == ["Disqualified"]),
        ("disqualified tag", "caj-ht-hvac-disqualified" in e.crm.get_contact(cid)["tags"]),
        ("no messages sent", not msgs(e, cid)),
        ("no call task", not tasks(e, cid, "Call new")),
        ("owner notified once", len(tasks(e, cid, "Owner notification")) == 1))
    return dict(input="Lead answers No to the decision-maker question", expected="Disqualified route, no sales booking nurture",
                ok=ok, actual=lines, trace=e, missing="Meta Instant Form with conditional ending (availability " + NE + ") and live GHL intake workflow")


def t04():
    e = engine()
    a = e.submit_lead(lead(5), T0)
    e.submit_lead(lead(5), T0 + timedelta(minutes=1))                                  # replay, same lead ID
    b = e.submit_lead(lead(6, email="owner5@example.com", phone="512-555-0199"), T0 + timedelta(minutes=2))  # same person, new lead
    c = e.submit_lead(lead(7, full_name="Test Owner 5"), T0 + timedelta(minutes=3))       # same name, different person
    e.tick(T0 + timedelta(days=4))
    ok, lines = checks(
        ("repeat lead matched to same contact", a == b),
        ("same name but different email/phone is a separate contact", c != a),
        ("one active opportunity for the contact", len(e.crm.opportunities_for(a)) == 1),
        ("attribution history updated", len(e.crm.get_contact(a)["attribution_history"]) == 2),
        ("no overlapping sequence: one acknowledgment", len(msgs(e, a, "booking_ack")) == 1),
        ("no overlapping sequence: one +2h reminder", len(msgs(e, a, "unbooked_reminder")) == 1))
    return dict(input="Replay of the same Meta lead ID, a repeat submission by the same person, and a same-name different person",
                expected="No duplicate active opportunity or overlapping sequence", ok=ok, actual=lines, trace=e,
                missing=f"GHL duplicate-match settings ({NE}) and the live Facebook integration's lead ID mapping")


def t05():
    e = engine()
    r = e.submit_lead(lead(8), T0)
    e.reply(r, "What does this involve?", T0 + timedelta(minutes=30))
    o = e.submit_lead(lead(9), T0)
    e.reply(o, "STOP", T0 + timedelta(minutes=30), channel="sms")
    e.tick(T0 + timedelta(days=4))
    after = T0 + timedelta(minutes=30)
    ok, lines = checks(
        ("reply routed to owner", len(tasks(e, r, "Reply received")) == 1),
        ("automation paused after reply", not [m for m in msgs(e, r) if m["at"] > after]),
        ("opted-out SMS channel sends nothing further", not [m for m in msgs(e, o, channel="sms") if m["at"] > after]),
        ("opt-out recorded", "sms" in e.crm.get_contact(o)["opted_out"]))
    return dict(input="One lead replies with a question; another replies STOP by SMS", expected="Reply routes to owner; opted-out channel sends nothing further",
                ok=ok, actual=lines, trace=e, missing=f"Live SMS sender with A2P eligibility ({NE}) and GHL reply/opt-out triggers in a test clone")


def t06():
    e = engine()
    cid = e.submit_lead(lead(10), T0)
    slots = e.slots(T0)
    old, new = slots[-1], slots[len(slots) // 2]
    aid = e.book(cid, old, T0)
    e.reschedule(aid, new, T0 + timedelta(minutes=5))
    cid2 = e.submit_lead(lead(11), T0)
    aid2 = e.book(cid2, slots[-5], T0)
    e.cancel(aid2, T0 + timedelta(minutes=5))
    e.tick(T0 + timedelta(days=4))
    rem = msgs(e, cid, "reminder_sms")
    expected_times = sorted(new - timedelta(hours=h) for h in (24, 2) if new - timedelta(hours=h) > T0 + timedelta(minutes=5))
    ok, lines = checks(
        ("reminders fire only for the new time", sorted(m["at"] for m in rem) == expected_times),
        ("no reminder for the old time", all(m["at"] not in (old - timedelta(hours=24), old - timedelta(hours=2)) for m in rem)),
        ("cancelled appointment gets no reminders", not msgs(e, cid2, "reminder_sms")),
        ("cancel creates reschedule-route task", len(tasks(e, cid2, "offer reschedule")) == 1))
    return dict(input="Book, then reschedule; separately book then cancel", expected="Old reminders stop; only current appointment reminders remain",
                ok=ok, actual=lines, trace=e, missing="Live GHL calendar reschedule/cancel events and workflow 03 in a test clone")


def t07():
    e = engine()
    cid = e.submit_lead(lead(12), T0)
    rejected = e.book(cid, T0 + timedelta(minutes=90), T0)
    aid = e.book(cid, T0 + timedelta(hours=3), T0)
    e.tick(T0 + timedelta(days=1))
    rem = msgs(e, cid, "reminder_sms")
    conf = msgs(e, cid, "confirmation")
    ok, lines = checks(
        ("booking inside 2-hour minimum notice rejected", rejected is None),
        ("near-term booking accepted", aid is not None),
        ("no expired 24h reminder", len(rem) == 1 and rem[0]["at"] == T0 + timedelta(hours=1)),
        ("confirmation shows timezone", bool(conf) and "America/Chicago" in conf[0]["body"] and "CDT" in conf[0]["body"]))
    return dict(input="Booking 90 minutes out (inside minimum notice) and 3 hours out", expected="No expired 24h reminder; correct timezone",
                ok=ok, actual=lines, trace=e, missing=f"Confirmed account timezone ({NE}) and live reminder timing in GHL")


def t08():
    e = engine(working_hours=None)
    a = e.submit_lead(lead(13), T0)
    b = e.submit_lead(lead(14), T0 + timedelta(minutes=1))
    e.tick(T0 + timedelta(days=4))
    ok, lines = checks(
        ("one owner task for empty calendar", len(tasks(e, None, "No calendar slots")) == 1),
        ("no booking links sent while no slots", not msgs(e, a, "booking_ack") and not msgs(e, b, "booking_ack")
         and not msgs(e, a, "unbooked_reminder")),
        ("recovery path: call tasks still created", len(tasks(e, a, "Call new")) == 1 and len(tasks(e, b, "Call new")) == 1))
    return dict(input="Two qualified leads while the calendar has no availability", expected="Owner task and usable recovery path; no empty-calendar loop",
                ok=ok, actual=lines, trace=e, missing=f"Real working hours ({NE}) in the live calendar")


def t09():
    e = engine()
    submitted = [lead(15), lead(16), lead(17)]
    for l in submitted[:2]:
        e.submit_lead(l, T0)  # third lead lost by the simulated sync interruption
    missing = SIM.reconcile_test_leads(submitted, e.crm)
    gate = SIM.launch_gate(missing, [])
    e.submit_lead(submitted[2], T0 + timedelta(hours=1))  # repaired sync
    missing_after = SIM.reconcile_test_leads(submitted, e.crm)
    ok, lines = checks(
        ("missing test lead detected", missing == ["TEST-LEAD-017"]),
        ("launch blocked while a lead is missing", gate["launch_allowed"] is False),
        ("reconciliation clean after repair", missing_after == []))
    return dict(input="Three test leads submitted; one dropped by a sync interruption", expected="Missing test lead detected before launch",
                ok=ok, actual=lines, trace=e, missing="Live Facebook-to-GHL integration and Meta lead form to submit real test leads")


def _paid_setup(e, n):
    cid = e.submit_lead(lead(n), T0)
    aid = e.book(cid, e.slots(T0)[0], T0)
    e.record_outcome(aid, "attended", T0 + timedelta(days=1))
    e.verbal_yes(cid, C.TECH_FEE_MONTHLY_USD, T0 + timedelta(days=1))
    return cid


def t10():
    e = engine()
    cid = _paid_setup(e, 18)
    st_before = stage(e, cid)
    res = e.payment_event({"contact_id": cid, "reference": "TEST-PAY-001", "status": "succeeded", "amount": C.TECH_FEE_MONTHLY_USD},
                          T0 + timedelta(days=1, hours=1))
    ok, lines = checks(
        ("verbal yes is Won pending payment only", st_before == ["Won pending payment"]),
        ("verified payment moves to Paid onboarding", res == "paid" and stage(e, cid) == ["Paid onboarding"]),
        ("one payment reference stored", e.crm.get_contact(cid)["custom"].get("payment_reference") == "TEST-PAY-001"),
        ("correct amount", e.processed_payments["TEST-PAY-001"]["amount"] == C.TECH_FEE_MONTHLY_USD),
        ("one onboarding enrollment", e.onboarding.get(cid) == 1 and len(tasks(e, cid, "onboarding")) == 1))
    return dict(input="Test-mode successful payment event for the agreed amount", expected="Correct amount, one reference, one onboarding enrollment",
                ok=ok, actual=lines, trace=e, missing=f"Payment processor ({NE}) test-mode product, created only after explicit approval")


def t11():
    e = engine()
    cid = _paid_setup(e, 19)
    failed = e.payment_event({"contact_id": cid, "reference": "TEST-PAY-002", "status": "failed", "amount": C.TECH_FEE_MONTHLY_USD}, T0 + timedelta(days=2))
    stage_after_fail = stage(e, cid)
    mismatch = e.payment_event({"contact_id": cid, "reference": "TEST-PAY-003", "status": "succeeded", "amount": 1}, T0 + timedelta(days=2))
    first = e.payment_event({"contact_id": cid, "reference": "TEST-PAY-004", "status": "succeeded", "amount": C.TECH_FEE_MONTHLY_USD}, T0 + timedelta(days=2))
    dup = e.payment_event({"contact_id": cid, "reference": "TEST-PAY-004", "status": "succeeded", "amount": C.TECH_FEE_MONTHLY_USD}, T0 + timedelta(days=2))
    ok, lines = checks(
        ("failed event does not mark Paid", failed == "ignored_not_succeeded" and stage_after_fail == ["Won pending payment"]),
        ("amount mismatch does not mark Paid", mismatch == "amount_mismatch"),
        ("duplicate success event ignored", first == "paid" and dup == "duplicate"),
        ("no duplicate onboarding enrollment", e.onboarding.get(cid) == 1 and len(tasks(e, cid, "onboarding")) == 1))
    return dict(input="Failed event, amount-mismatch event, then the same success event delivered twice", expected="No false Paid status, no duplicate enrollment",
                ok=ok, actual=lines, trace=e, missing=f"Processor webhook behavior in test mode ({NE})")


def t12(state: State):
    out = state.out_dir
    recs, problems = [], []
    for a in ("A01", "A02", "A03", "A04", "A05"):
        p = out / "creatives" / f"{a}.json"
        if not p.exists():
            problems.append(f"missing {p.name}")
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        recs.append(rec)
        try:
            G.assert_logo_not_first(rec)
            for k in ("on_image_words", "primary_text", "headline", "cta"):
                G.assert_prospect_copy(rec[k])
        except G.GuardrailViolation as exc:
            problems.append(f"{a}: {exc}")
        copy_md = out / "copy" / f"{a}.md"
        if not copy_md.exists() or rec["primary_text"] not in copy_md.read_text(encoding="utf-8"):
            problems.append(f"{a}: copy record missing or inconsistent")
    offer_md = (out / "offer_spec.md").read_text(encoding="utf-8") if (out / "offer_spec.md").exists() else ""
    missing_assets = [a["path"] for a in state.load_assets() if not (state.root / a["path"]).exists()]
    ok, lines = checks(
        ("five concept records readable with required keys", len(recs) == 5 and all(
            all(k in r for k in ("ad_id", "angle", "on_image_words", "visual_direction", "primary_text", "headline", "cta",
                                 "offer_reference", "version", "proof_points")) for r in recs)),
        ("unique ad IDs", len({r["ad_id"] for r in recs}) == 5),
        ("every concept references the current offer version", all(r["offer_reference"] == OFFER_VERSION for r in recs) and OFFER_VERSION in offer_md),
        ("guardrails and copy consistency clean", not problems),
        ("every registered asset path exists locally", not missing_assets))
    lines += [f"problem: {p}" for p in problems] + [f"missing asset: {m}" for m in missing_assets]
    lines.append("scope: local draft concepts and local links; image files and the external booking URL are human checks (ui-tasks)")
    return dict(input="Five creative JSON records, copy pack, offer spec and asset register", expected="Five concepts readable, links work, terms match",
                ok=ok, actual=lines, trace=None, missing=None)


def t13():
    cfg = {"mode": "live_transfer", "recipients": [{"name": "Fixture Recipient", "number": "512-555-0150", "verified": True}],
           "operating_hours": SIM.FIXTURE_HOURS, "timeout_seconds": 20, "fallback": {"type": "owner_task_and_callback", "tested": True}}
    unverified = dict(cfg, recipients=[{"name": "Unverified", "number": "512-555-0151", "verified": False}])
    untested = dict(cfg, fallback={"type": "voicemail", "tested": False})
    refused = []
    for bad in (unverified, untested):
        try:
            SIM.validate_routing(bad)
        except SIM.RoutingNotVerified:
            refused.append(True)
    sat = datetime(2026, 10, 10, 15, 0, tzinfo=timezone.utc)
    ok, lines = checks(
        ("unverified recipients or untested fallback refused", len(refused) == 2),
        ("answered call reaches verified recipient", SIM.route_call(cfg, "answered", T0)["destination"] == "Fixture Recipient"),
        ("busy goes to tested fallback", SIM.route_call(cfg, "busy", T0)["destination"] == "owner_task_and_callback"),
        ("unanswered goes to tested fallback", SIM.route_call(cfg, "unanswered", T0)["destination"] == "owner_task_and_callback"),
        ("after hours goes to fallback", SIM.route_call(cfg, "answered", sat)["destination"] == "owner_task_and_callback"))
    return dict(input="Fixture client routing config: verified, unverified and untested-fallback variants", expected="Correct calendar/transfer recipients, tested fallback",
                ok=ok, actual=lines, trace=None, missing="A sold client, a chosen telephony system and live answered/busy/unanswered/after-hours call tests")


def t14():
    ads = LocalAds()
    name = G.new_campaign_name(T0.date())
    frozen_refused = False
    try:
        ads.create_draft_campaign(C.FROZEN_CAMPAIGN_NAME, 0, False)
    except G.FrozenCampaignViolation:
        frozen_refused = True
    spend_refused = False
    try:
        ads.create_draft_campaign(name, 50, False)
    except G.SpendNotApproved:
        spend_refused = True
    cid = ads.create_draft_campaign(name, 0, False)
    with tempfile.TemporaryDirectory() as td:
        cfg = Path(td) / "build_config.json"
        cfg.write_text((BUILD_ROOT / "config" / "build_config.json").read_text(encoding="utf-8"), encoding="utf-8")
        backup = SIM.snapshot_config(cfg, Path(td) / "backup")
        changed = json.loads(cfg.read_text(encoding="utf-8"))
        changed["service_area"] = "changed-during-test"
        cfg.write_text(json.dumps(changed), encoding="utf-8")
        reg = SIM.WorkflowRegistry(["CAJ-HT-HVAC-01-Intake", "CAJ-HT-HVAC-02-Unbooked"])
        res = SIM.rollback(ads, cid, reg, ["CAJ-HT-HVAC-02-Unbooked"], cfg, backup)
    ok, lines = checks(
        ("frozen campaign name refused", frozen_refused),
        ("unapproved budget refused", spend_refused),
        ("new campaign paused", res["campaign_status"] == "PAUSED"),
        ("affected workflow stopped", res["workflows"] == {"CAJ-HT-HVAC-02-Unbooked": "stopped"}),
        ("prior config recoverable", res["config_restored"]))
    return dict(input="Draft campaign + workflow + config change, then rollback", expected="New campaign pauses, affected workflow stops, prior config recoverable",
                ok=ok, actual=lines, trace=None, missing="Live Meta draft campaign and GHL workflows to exercise pause/stop in the real accounts (human, approval required)")


CASES = [("T01", t01), ("T02", t02), ("T03", t03), ("T04", t04), ("T05", t05), ("T06", t06), ("T07", t07),
         ("T08", t08), ("T09", t09), ("T10", t10), ("T11", t11), ("T12", t12), ("T13", t13), ("T14", t14)]


def verdict(ok: bool, missing) -> str:
    if not ok:
        return "FAIL"
    return "BLOCKED" if missing else "PASS"


def run_all(state: State) -> list[dict]:
    tdir = state.out_dir / "tests"
    (tdir / "evidence").mkdir(parents=True, exist_ok=True)
    results = []
    for tid, fn in CASES:
        try:
            r = fn(state) if fn is t12 else fn()
        except Exception as exc:  # a crash is a failure, recorded with evidence
            r = dict(input=fn.__name__, expected="see spec", ok=False, actual=[f"exception: {type(exc).__name__}: {exc}"], trace=None, missing=None)
        ev = tdir / "evidence" / f"{tid}_trace.json"
        e = r.get("trace")
        ev.write_text(json.dumps({"checks": r["actual"], "trace": e.trace if e else [], "crm": e.crm.snapshot() if e else {}},
                                 indent=2, default=str) + "\n", encoding="utf-8")
        v = verdict(r["ok"], r["missing"])
        rec = {"test_id": tid, "input": r["input"], "expected_result": r["expected"], "actual_result": r["actual"],
               "logic_simulation": "PASS" if r["ok"] else "FAIL", "evidence_path": state.rel(ev), "verdict": v,
               "blocked_missing_input": r["missing"] if v == "BLOCKED" else None}
        state.write_json(f"out/tests/{tid}.json", rec, f"TEST-{tid}", status="Blocked" if v == "BLOCKED" else ("Tested" if v == "PASS" else "Draft"),
                         source="tools/run_tests.py")
        if v == "BLOCKED":
            state.record_blocker(f"live verification {tid}", r["missing"], f"test {tid}", "Run in a GHL/Meta test clone and record evidence",
                                 source_file=f"out/tests/{tid}.json")
        results.append(rec)
    if any(r["verdict"] == "BLOCKED" for r in results):
        state.record_blocker("live verification of BLOCKED T-cases", "Live GHL/Meta/processor test runs (see each BLOCKED row)",
                             "launch readiness", "Run each BLOCKED case in a test clone and record evidence", source_file="out/tests/test_log.md")
    lines = ["# Test log", "", "Verdicts: PASS | FAIL | BLOCKED. BLOCKED means the offline logic passed but live verification is still missing; it is not a pass.", "",
             "| Test | Verdict | Logic simulation | Expected | Evidence | Missing input (if BLOCKED) |", "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['test_id']} | {r['verdict']} | {r['logic_simulation']} | {r['expected_result']} | {r['evidence_path']} | {r['blocked_missing_input'] or ''} |")
    counts = {v: sum(1 for r in results if r["verdict"] == v) for v in ("PASS", "FAIL", "BLOCKED")}
    lines += ["", f"Totals: PASS {counts['PASS']}, FAIL {counts['FAIL']}, BLOCKED {counts['BLOCKED']}.", ""]
    state.write("out/tests/test_log.md", "\n".join(lines), "TEST-LOG", source="tools/run_tests.py")
    state.save_blockers()
    return results


def main() -> int:
    state = State()
    if not (state.out_dir / "creatives" / "A01.json").exists():
        from tools.build_all import generate, reset_generated
        reset_generated(state)  # drop stale register entries, then regenerate the drafts the cases inspect
        generate(state)
    results = run_all(state)
    for r in results:
        print(f"{r['test_id']}  {r['verdict']:<8} logic={r['logic_simulation']}  evidence={r['evidence_path']}")
    fails = [r for r in results if r["verdict"] == "FAIL"]
    print(f"run_tests: PASS {sum(r['verdict'] == 'PASS' for r in results)}, FAIL {len(fails)}, BLOCKED {sum(r['verdict'] == 'BLOCKED' for r in results)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

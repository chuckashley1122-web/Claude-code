import unittest
from datetime import datetime, time, timedelta, timezone

import _util  # noqa: F401
from config import constants as C
from src import calendar_spec as CAL
from src import connectors as X
from src import form_spec as FORM
from src import funnel_sim as SIM
from src import message_templates as MSG
from src import tz as TZ
from src import utm_fixtures as UTM
from src import risk_reversal as RR
from src import positioning as POS
from src import onboarding_pack as ONB
from tools import guardrails as G
from tools import run_tests as RT

T0 = RT.T0


class ConnectorTests(unittest.TestCase):
    def test_protocols_satisfied(self):
        self.assertIsInstance(X.LocalCRM(), X.CRMGateway)
        self.assertIsInstance(X.LocalAds(), X.AdsGateway)
        self.assertIsInstance(X.LocalPayments(), X.PaymentGateway)
        self.assertIsInstance(X.LiveGHLCRM(), X.CRMGateway)

    def test_live_implementations_refuse(self):
        with self.assertRaises(X.LiveCallBlocked):
            X.LiveGHLCRM().create_contact({})
        with self.assertRaises(X.LiveCallBlocked):
            X.LiveGHLCRM().send_message("c", "sms", "t", "b", None)
        with self.assertRaises(X.LiveCallBlocked):
            X.LiveMetaAds().create_draft_campaign("CAJ-HT-HVAC-Leads-20261005", 0, False)
        with self.assertRaises(G.FrozenCampaignViolation):
            X.LiveMetaAds().create_draft_campaign(C.FROZEN_CAMPAIGN_NAME, 0, False)
        with self.assertRaises(X.LiveCallBlocked):
            X.LivePayments().create_product("p", 1, False, True)

    def test_dry_run_default_true(self):
        self.assertTrue(X.dry_run_enabled({}))
        self.assertEqual(X.get_gateways({})["mode"], "local")
        g = X.get_gateways({"DRY_RUN": "false"})
        self.assertEqual(g["mode"], "live-refusing")
        with self.assertRaises(X.LiveCallBlocked):
            g["crm"].find_contact("a@example.com", None)

    def test_local_ads_draft_only(self):
        ads = X.LocalAds()
        cid = ads.create_draft_campaign("CAJ-HT-HVAC-Leads-20261005", 0, False)
        self.assertEqual(ads.get_campaign(cid)["status"], "PAUSED")
        with self.assertRaises(X.LaunchNotAuthorized):
            ads.activate_campaign(cid)
        with self.assertRaises(G.SpendNotApproved):
            ads.create_draft_campaign("CAJ-HT-HVAC-Leads-20261006", 10, False)

    def test_local_payments(self):
        p = X.LocalPayments()
        with self.assertRaises(G.SpendNotApproved):
            p.create_product("x", 650, False, False)
        with self.assertRaises(ValueError):
            p.create_product("x", 650, True, True)
        pid = p.create_product("x", 650, False, True)
        self.assertEqual(p.get_product(pid)["mode"], "test")

    def test_local_crm_never_matches_on_name(self):
        crm = X.LocalCRM()
        crm.create_contact({"full_name": "Same Name", "email": "a@example.com", "phone": "512-555-0101"})
        self.assertIsNone(crm.find_contact("b@example.com", "512-555-0102"))
        self.assertIsNotNone(crm.find_contact("A@EXAMPLE.COM", None))


class TimezoneTests(unittest.TestCase):
    def test_matches_zoneinfo_where_available(self):
        try:
            from zoneinfo import ZoneInfo
            zi = ZoneInfo("America/Chicago")
        except Exception:
            self.skipTest("system tz database unavailable")
        t = datetime(2026, 1, 1, tzinfo=timezone.utc)
        while t < datetime(2027, 1, 1, tzinfo=timezone.utc):
            self.assertEqual(t.astimezone(TZ.CENTRAL).utcoffset(), t.astimezone(zi).utcoffset(), t)
            t += timedelta(hours=7)
        for edge in (datetime(2026, 3, 8, 7, 59, tzinfo=timezone.utc), datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
                     datetime(2026, 11, 1, 6, 30, tzinfo=timezone.utc), datetime(2026, 11, 1, 7, 30, tzinfo=timezone.utc)):
            self.assertEqual(edge.astimezone(TZ.CENTRAL).utcoffset(), edge.astimezone(zi).utcoffset(), edge)

    def test_fmt_local(self):
        self.assertIn("10:00 AM CDT (America/Chicago)", TZ.fmt_local(T0))


class CalendarTests(unittest.TestCase):
    def test_unknown_hours_gives_no_slots(self):
        self.assertEqual(CAL.available_slots(T0, C.NEEDS_EVIDENCE, []), [])
        self.assertEqual(CAL.available_slots(T0, None, []), [])

    def test_min_notice_horizon_and_buffers(self):
        slots = CAL.available_slots(T0, SIM.FIXTURE_HOURS, [])
        self.assertTrue(slots)
        self.assertGreaterEqual(min(slots), T0 + timedelta(hours=2))
        self.assertLessEqual(max(slots), T0 + timedelta(days=3))
        busy_start = slots[0] + timedelta(hours=1)
        slots2 = CAL.available_slots(T0, SIM.FIXTURE_HOURS, [(busy_start, busy_start + timedelta(minutes=45))])
        for s in slots2:
            self.assertTrue(s + timedelta(minutes=45 + 15) <= busy_start or s >= busy_start + timedelta(minutes=45 + 15))


class EngineTests(unittest.TestCase):
    def test_all_acceptance_logic_passes(self):
        import shutil
        from tools.state import State
        root = _util.built_temp_root()
        try:
            for tid, fn in RT.CASES:
                r = fn(State(root)) if fn is RT.t12 else fn()
                self.assertTrue(r["ok"], f"{tid}: {r['actual']}")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_verdict_rules(self):
        self.assertEqual(RT.verdict(False, None), "FAIL")
        self.assertEqual(RT.verdict(False, "x"), "FAIL")
        self.assertEqual(RT.verdict(True, "x"), "BLOCKED")
        self.assertEqual(RT.verdict(True, None), "PASS")

    def test_intake_filter(self):
        e = RT.engine()
        self.assertIsNone(e.submit_lead(RT.lead(1, form_id="OTHER-FORM"), T0))
        self.assertFalse(e.crm.contacts)

    def test_payment_without_pending_won_is_not_paid(self):
        e = RT.engine()
        cid = e.submit_lead(RT.lead(1), T0)
        self.assertEqual(e.payment_event({"contact_id": cid, "reference": "R", "status": "succeeded", "amount": 650}, T0), "unexpected_stage")
        self.assertEqual(RT.stage(e, cid), ["Qualified unbooked"])

    def test_attended_never_auto_won(self):
        e = RT.engine()
        cid = e.submit_lead(RT.lead(1), T0)
        aid = e.book(cid, e.slots(T0)[0], T0)
        e.record_outcome(aid, "attended", T0 + timedelta(days=1))
        self.assertEqual(RT.stage(e, cid), ["Attended"])
        with self.assertRaises(ValueError):
            e.record_outcome(aid, "maybe", T0)

    def test_no_show_message_once(self):
        e = RT.engine()
        cid = e.submit_lead(RT.lead(1), T0)
        aid = e.book(cid, e.slots(T0)[0], T0)
        e.record_outcome(aid, "no_show", T0 + timedelta(days=1))
        e.record_outcome(aid, "no_show", T0 + timedelta(days=1))
        self.assertEqual(len(RT.msgs(e, cid, "no_show")), 1)

    def test_confirmation_reply_and_ambiguous(self):
        e = RT.engine()
        cid = e.submit_lead(RT.lead(1), T0)
        e.book(cid, e.slots(T0)[0], T0)
        e.reply(cid, "Maybe, not sure", T0)
        self.assertEqual(e.crm.get_contact(cid)["custom"]["appointment_confirmation"], "Ambiguous")
        e.reply(cid, "Confirmed!", T0)
        self.assertEqual(RT.stage(e, cid), ["Confirmed"])

    def test_launch_gate_blocked_by_authority(self):
        self.assertFalse(SIM.launch_gate([], [])["launch_allowed"])


class ContentLogicTests(unittest.TestCase):
    def test_form_evaluate(self):
        self.assertTrue(FORM.evaluate("Yes")["qualified"])
        self.assertTrue(FORM.evaluate(" yes ")["qualified"])
        for a in ("No", "", None, "maybe"):
            r = FORM.evaluate(a)
            self.assertFalse(r["qualified"])
            self.assertTrue(r["suppress_booking"])

    def test_form_logic_fallback_and_territory(self):
        d = FORM.logic({"privacy_policy_url": C.NEEDS_EVIDENCE})
        self.assertTrue(d["fallback_if_conditional_endings_unavailable"]["suppress_sales_booking_sequence"])
        self.assertNotIn("territory_claim", d)
        self.assertIn("territory_claim", FORM.logic({}, territory_policy_documented=True))
        self.assertEqual(d["qualified_ending"]["url"], C.BOOKING_URL)

    def test_message_render(self):
        MSG.check_all()
        with self.assertRaises(KeyError):
            MSG.render_message("booking_ack", {})
        out = MSG.render_message("reminder_sms", {"FIRST NAME": "Pat", "DATE/TIME/TIMEZONE": "x", "MEETING LINK": "https://example.com/m",
                                                  "RESCHEDULE LINK": "https://example.com/r"})
        self.assertTrue(out.endswith("Reply STOP to opt out."))

    def test_utm_round_trip(self):
        name = G.new_campaign_name(UTM.FIXTURE_DATE)
        url = UTM.build_test_url(C.BOOKING_URL, name, "A03", "TEST-1")
        self.assertEqual(UTM.parse_attribution(url)["utm_content"], "A03")
        with self.assertRaises(G.GuardrailViolation):
            UTM.build_test_url(C.BOOKING_URL, C.FROZEN_CAMPAIGN_NAME, "A01", "x")

    def test_guarantee_requires_all_terms(self):
        full = {k: "defined" for k in RR.REQUIRED_GUARANTEE_TERMS}
        RR.validate_guarantee(full, fee_prepaid=False)
        with self.assertRaises(RR.IncompleteGuarantee):
            RR.validate_guarantee(full, fee_prepaid=True)
        with self.assertRaises(RR.IncompleteGuarantee):
            RR.validate_guarantee({}, fee_prepaid=False)

    def test_positioning_guard(self):
        POS.check_positioning(POS.POSITIONING)
        with self.assertRaises(G.GuardrailViolation):
            POS.check_positioning("Guaranteed results for HVAC")

    def test_intake_has_no_password_fields(self):
        form = ONB.intake_form()
        self.assertEqual(len(form["fields"]), 14)
        self.assertFalse([f for f in form["fields"] if "password" in f["label"].lower()])


if __name__ == "__main__":
    unittest.main()

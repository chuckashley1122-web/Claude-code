import json
import shutil
import unittest
from datetime import date

import _util  # noqa: F401  (sys.path setup)
from config import constants as C
from tools import guardrails as G
from tools.state import State, Status, StatusForbidden


class StateTests(unittest.TestCase):
    def setUp(self):
        self.root = _util.make_temp_root()
        self.state = State(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_status_enum_values(self):
        self.assertEqual([s.value for s in Status],
                         ["Not started", "Draft", "Tested", "Ready for launch", "Live", "Blocked"])

    def test_live_and_ready_are_refused(self):
        for st in ("Live", Status.LIVE, "Ready for launch"):
            with self.assertRaises(StatusForbidden):
                self.state.log("k", "v", "test", st)
            with self.assertRaises(StatusForbidden):
                self.state.mark_asset("X", "out/x.md", st)

    def test_unknown_status_rejected(self):
        with self.assertRaises(ValueError):
            self.state.log("k", "v", "test", "Done")

    def test_log_appends_json_lines(self):
        self.state.log("a", 1, "src", "Draft")
        self.state.log("b", 2, "src", Status.BLOCKED)
        rows = [json.loads(l) for l in self.state.decision_log_path.read_text().splitlines()]
        self.assertEqual([r["key"] for r in rows], ["a", "b"])
        self.assertEqual(set(rows[0]), {"timestamp", "key", "value", "source", "status"})

    def test_record_blocker_dedupes_and_persists(self):
        self.state.record_blocker("x", "missing", "work", "next", source_file="out/a.md")
        self.state.record_blocker("x", "missing", "work", "next", source_file="out/a.md")
        self.assertEqual(len(self.state.blockers), 1)
        saved = json.loads(self.state.save_blockers().read_text())
        self.assertEqual(saved[0]["owner"], C.OWNER_NAME)

    def test_needs_returns_literal(self):
        self.assertEqual(self.state.needs("thing", "out/a.md", "do it"), "NEEDS_EVIDENCE")

    def test_mark_asset_upserts(self):
        self.state.mark_asset("A", "out/a.md", "Draft")
        self.state.mark_asset("A", "out/a.md", "Tested")
        assets = self.state.load_assets()
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0]["status"], "Tested")

    def test_write_registers_asset(self):
        p = self.state.write("out/sub/x.md", "hello", "X")
        self.assertTrue(p.exists())
        self.assertEqual(self.state.load_assets()[0]["path"], "out/sub/x.md")


class GuardrailTests(unittest.TestCase):
    def test_frozen_campaign_refused(self):
        for name in (C.FROZEN_CAMPAIGN_NAME, C.FROZEN_CAMPAIGN_NAME.lower(), C.FROZEN_CAMPAIGN_NAME + " - Copy"):
            with self.assertRaises(G.FrozenCampaignViolation):
                G.assert_not_frozen_campaign(name)
        self.assertEqual(G.assert_not_frozen_campaign("CAJ-HT-HVAC-Leads-20261005"), "CAJ-HT-HVAC-Leads-20261005")

    def test_new_campaign_name_pattern(self):
        self.assertEqual(G.new_campaign_name(date(2026, 10, 5)), "CAJ-HT-HVAC-Leads-20261005")
        self.assertEqual(G.new_campaign_name(date(2026, 10, 5), "SOURCE_REAL_ESTATE"), "CAJ-HT-RE-Leads-20261005")
        for bad in ("CAJ-HT-HVAC-Leads-2026105", "Random", "CAJ-HT-HVAC-Leads-20261399", C.FROZEN_CAMPAIGN_NAME):
            with self.assertRaises(G.GuardrailViolation):
                G.assert_new_campaign_name(bad)

    def test_no_spend(self):
        G.assert_no_spend(0, False)
        G.assert_no_spend(25, True)
        for amount, flag in ((1, False), (50, None), (50, "true"), (50, 1)):
            with self.assertRaises(G.SpendNotApproved):
                G.assert_no_spend(amount, flag)
        for bad in (-1, "50", True):
            with self.assertRaises(G.SpendNotApproved):
                G.assert_no_spend(bad, True)

    def test_meeting_first(self):
        G.assert_meeting_first("Book a strategy session at https://ca-jenterprises.com/ai")
        for text in ("Only $650 a month", "650 USD", "USD 300", "300 dollars", "250/appointment", "650 per month", "€99"):
            with self.assertRaises(G.MeetingFirstViolation, msg=text):
                G.assert_meeting_first(text)

    def test_logo_not_first_structured(self):
        good = {"visual_direction": [{"order": 1, "element": "outcome_headline"}, {"order": 2, "element": "logo", "placement": "footer", "size": "small"}]}
        G.assert_logo_not_first(good)
        bad_first = {"visual_direction": [{"order": 1, "element": "logo", "placement": "footer", "size": "small"}, {"order": 2, "element": "offer_line"}]}
        bad_big = {"visual_direction": [{"order": 1, "element": "offer_line"}, {"order": 2, "element": "logo", "placement": "header", "size": "large"}]}
        no_lead = {"visual_direction": [{"order": 1, "element": "cta"}]}
        for c in (bad_first, bad_big, no_lead, {"visual_direction": []}):
            with self.assertRaises(G.LogoFirstViolation):
                G.assert_logo_not_first(c)

    def test_logo_not_first_text(self):
        G.assert_logo_not_first("Outcome headline first, offer line, small logo in footer")
        with self.assertRaises(G.LogoFirstViolation):
            G.assert_logo_not_first("Big logo on top, then the outcome")
        with self.assertRaises(G.LogoFirstViolation):
            G.assert_logo_not_first("Outcome first then logo large in header")

    def test_brand_separation(self):
        G.assert_b2b_brand_clean("CA-J Enterprises helps HVAC businesses")
        for b in C.CONSUMER_BRANDS:
            with self.assertRaises(G.BrandBlendViolation):
                G.assert_b2b_brand_clean(f"Brought to you by {b}")

    def test_banned_phrases(self):
        G.assert_no_banned_phrases("booked appointment")
        for p in C.BANNED_PHRASES + ["call " + C.FORBIDDEN_PHONE]:
            with self.assertRaises(G.BannedPhraseViolation):
                G.assert_no_banned_phrases("text " + p.upper() + " text")


if __name__ == "__main__":
    unittest.main()

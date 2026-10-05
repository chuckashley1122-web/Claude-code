import contextlib
import io
import json
import tempfile
import types
import unittest
from pathlib import Path

from tests._helpers import ROOT  # noqa: F401
from config import constants as C
from tools import guardrails as G
from tools import validate_config as V
from tools.meta_gateway import LaunchNotApproved, LiveCallBlocked, LiveMetaGateway, LocalDraftGateway
from tools.state import STATUS, BuildState, StatusNotAllowed, check_status_allowed


def consts(**over):
    ns = types.SimpleNamespace(**{k: getattr(C, k) for k in dir(C) if k.isupper()})
    for k, v in over.items():
        setattr(ns, k, v)
    return ns


class StateLayer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = BuildState(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_status_enum(self):
        self.assertEqual([s.value for s in STATUS],
                         ["Not started", "Draft", "Tested", "Ready for launch", "Live", "Blocked"])

    def test_live_never_written(self):
        with self.assertRaises(StatusNotAllowed):
            self.state.mark_asset("x", "out/x.md", "Live")
        with self.assertRaises(StatusNotAllowed):
            self.state.log("k", "v", "test", STATUS.LIVE)
        with self.assertRaises(StatusNotAllowed):
            check_status_allowed("Ready for launch")
        self.assertIs(check_status_allowed("Ready for launch", approval_launch=True), STATUS.READY_FOR_LAUNCH)
        with self.assertRaises(ValueError):
            check_status_allowed("Shipped")

    def test_log_blocker_and_register(self):
        self.state.log("main_offer", "free session", "spec", "Draft")
        self.state.record_blocker("pixel_id", "pixel", "wf03", "create pixel")
        self.state.record_blocker("pixel_id", "pixel v2", "wf03", "create pixel")
        self.state.mark_asset("b", "out/b.md")
        self.state.mark_asset("a", "out\\a.md", "Tested")
        self.state.mark_asset("a", "out/a.md", "Draft")
        log = self.state.read_log()
        self.assertEqual(log[0]["key"], "main_offer")
        self.assertTrue(all({"timestamp", "key", "value", "source", "status"} <= set(e) for e in log))
        self.assertEqual(len(self.state.load_blockers()), 1)
        self.assertEqual(self.state.load_blockers()[0]["missing_input"], "pixel v2")
        assets = self.state.load_assets()
        self.assertEqual([a["id"] for a in assets], ["a", "b"])
        self.assertEqual(assets[0]["status"], "Draft")


class Validator(unittest.TestCase):
    def results(self, c=C, cfg=None):
        return {n: ok for n, ok, _ in V.run_checks(c=c, cfg=cfg)}

    def test_current_config_passes(self):
        self.assertTrue(all(self.results().values()))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(V.main(), 0)

    def test_each_hard_failure(self):
        cases = {
            "ghl_location_id_exact_case": consts(GHL_LOCATION_ID=C.GHL_LOCATION_ID.lower()),
            "ad_spend_cap_zero_without_approval": consts(AD_SPEND_CAP_USD=70),
            "launch_authority_none_without_approval": consts(LAUNCH_AUTHORITY="agent"),
            "domain_purchase_requires_approval_ref": consts(DOMAIN_PURCHASE_APPROVED=True),
            "frozen_campaign_protected": consts(FROZEN_CAMPAIGN_PROTECTED=False),
            "quote_price_in_message_false": consts(QUOTE_PRICE_IN_MESSAGE=True),
            "locked_commercial_terms": consts(TECH_FEE_MONTHLY_USD=500),
        }
        for check, c in cases.items():
            with self.subTest(check=check):
                self.assertFalse(self.results(c=c)[check])

    def test_approved_spend_and_domain_pass(self):
        r = self.results(c=consts(AD_SPEND_CAP_USD=70, APPROVAL_AD_SPEND=True, DOMAIN_PURCHASE_APPROVED=True,
                                  DOMAIN_PURCHASE_APPROVAL_REF="APPROVAL-1"))
        self.assertTrue(r["ad_spend_cap_zero_without_approval"])
        self.assertTrue(r["domain_purchase_requires_approval_ref"])

    def test_guessed_ids_and_invented_facts_rejected(self):
        cfg = V.load_config()
        for key, check in [("pixel_id", "no_guessed_ids_in_config"), ("review_count", "no_invented_proof_facts")]:
            bad = dict(cfg, **{key: "123"})
            with self.subTest(key=key):
                self.assertFalse(self.results(cfg=bad)[check])
        self.assertFalse(self.results(cfg=dict(cfg, extra_key="x"))["config_has_exact_key_set"])
        self.assertFalse(self.results(cfg=dict(cfg, usp=C.CONSUMER_BRAND_BLOCKLIST[0]))["no_consumer_brand_in_config"])
        self.assertFalse(self.results(cfg=dict(cfg, phone=C.FORBIDDEN_PHONE_NUMBERS[0]))["phone_is_public_contact"])


class GatewayTripwire(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.gw = LocalDraftGateway(Path(self.tmp.name))
        self.cfg = {"campaign": {"name": "CAJ-FB-HVAC-Leads-20261005-DRAFT"}, "ad_set": {"daily_budget": C.NEEDS_EVIDENCE}}

    def tearDown(self):
        self.tmp.cleanup()

    def test_frozen_campaign_never_a_target(self):
        for op in ("get_campaign", "pause_campaign", "restore_previous", "publish_campaign"):
            for gw in (self.gw, LiveMetaGateway()):
                with self.subTest(op=op, gw=type(gw).__name__), self.assertRaises(G.FrozenCampaignError):
                    getattr(gw, op)(C.FROZEN_CAMPAIGN_NAME)
        with self.assertRaises(G.FrozenCampaignError):
            self.gw.create_draft_campaign({"campaign": {"name": C.FROZEN_CAMPAIGN_NAME}})
        dup = json.loads(json.dumps(self.cfg))
        dup["campaign"]["duplicate_of"] = C.FROZEN_CAMPAIGN_NAME.lower()
        with self.assertRaises(G.FrozenCampaignError):
            self.gw.create_draft_campaign(dup)
        self.assertEqual(list(Path(self.tmp.name).glob("*")), [])

    def test_local_draft_pause_restore(self):
        doc = self.gw.create_draft_campaign(self.cfg)
        self.assertEqual(doc["status"], "DRAFT_UNPUBLISHED")
        self.assertFalse(doc["published_by_build"])
        self.gw.create_draft_campaign(self.cfg)  # idempotent: identical config adds no history
        self.assertEqual(self.gw.get_campaign(self.cfg["campaign"]["name"])["history"], [])
        self.assertEqual(self.gw.pause_campaign(self.cfg["campaign"]["name"])["status"], "PAUSED_DRAFT")
        restored = self.gw.restore_previous(self.cfg["campaign"]["name"])
        self.assertEqual(restored["status"], "DRAFT_UNPUBLISHED")
        self.assertEqual(restored["config"], self.cfg)
        with self.assertRaises(KeyError):
            self.gw.restore_previous(self.cfg["campaign"]["name"])

    def test_non_draft_name_refused(self):
        with self.assertRaises(G.FrozenCampaignError):
            self.gw.create_draft_campaign({"campaign": {"name": "Leads Campaign - LP"}})

    def test_publish_and_live_refused(self):
        self.gw.create_draft_campaign(self.cfg)
        with self.assertRaises(LaunchNotApproved):
            self.gw.publish_campaign(self.cfg["campaign"]["name"], approval_ref="APPROVAL-1")
        live = LiveMetaGateway()
        for call in (lambda: live.create_draft_campaign(self.cfg), lambda: live.pause_campaign("x"),
                     lambda: live.get_campaign("x"), lambda: live.publish_campaign("x", "APPROVAL-1")):
            with self.assertRaises(LiveCallBlocked):
                call()


if __name__ == "__main__":
    unittest.main()

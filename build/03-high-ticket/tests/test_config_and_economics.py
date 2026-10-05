import copy
import json
import subprocess
import sys
import unittest
from fractions import Fraction

import _util
from config import constants as C
from tools import break_even as B
from tools import margin_model as M
from tools import validate_config as V

CONFIG = json.loads((_util.ROOT / "config" / "build_config.json").read_text())
ENV = (_util.ROOT / ".env.example").read_text()


def failed(cfg, env=None):
    return [n for n, ok, _ in V.validate(cfg, C, env) if not ok]


class ValidatorTests(unittest.TestCase):
    def test_committed_config_passes(self):
        self.assertEqual(failed(CONFIG, ENV), [])

    def test_cli_exits_zero(self):
        r = subprocess.run([sys.executable, str(_util.ROOT / "tools" / "validate_config.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(all(l.startswith(("PASS", "validate_config")) for l in r.stdout.splitlines()))

    def mutate(self, **kw):
        cfg = copy.deepcopy(CONFIG)
        cfg.update(kw)
        return cfg

    def test_location_case_mangled(self):
        self.assertIn("ghl_location_id not case-mangled", failed(self.mutate(ghl_location_id=C.GHL_LOCATION_ID.lower())))

    def test_disallowed_location(self):
        self.assertTrue(failed(self.mutate(ghl_location_id=C.DISALLOWED_LOCATION_ID)))
        self.assertIn("disallowed location id absent from config", failed(self.mutate(notes=C.DISALLOWED_LOCATION_ID)))

    def test_spend_cap_requires_approval(self):
        self.assertTrue(failed(self.mutate(ad_spend_cap_usd=50)))
        self.assertFalse([f for f in failed(self.mutate(ad_spend_cap_usd=50, approval_ad_spend=True)) if "spend" in f.lower()])

    def test_launch_authority_requires_approval(self):
        self.assertTrue(failed(self.mutate(launch_authority="chuck")))

    def test_frozen_and_quote_flags(self):
        self.assertIn("FROZEN_CAMPAIGN_PROTECTED is true", failed(self.mutate(frozen_campaign_protected=False)))
        self.assertIn("QUOTE_PRICE_IN_MESSAGE is false", failed(self.mutate(quote_price_in_message=True)))

    def test_guessed_id_rejected(self):
        self.assertIn("facebook_page_id not guessed", failed(self.mutate(facebook_page_id="1234567890")))
        self.assertNotIn("facebook_page_id not guessed",
                         failed(self.mutate(facebook_page_id="1234567890", facebook_page_id_evidence="screenshot 2026-10-05")))

    def test_locked_pricing_must_match(self):
        sp = dict(CONFIG["service_price"], tech_fee_monthly_usd=2000)
        self.assertIn("service_price matches locked CA-J terms", failed(self.mutate(service_price=sp)))

    def test_env_example_values_rejected(self):
        self.assertIn(".env.example has names only (empty values)", failed(CONFIG, ENV + "META_ACCESS_TOKEN=abc\n"))

    def test_constants_locked_terms(self):
        self.assertEqual((C.TECH_FEE_MONTHLY_USD, C.SETUP_FEE_USD, C.PER_BOOKED_APPOINTMENT_MIN_USD, C.PER_BOOKED_APPOINTMENT_MAX_USD),
                         (650, 0, 250, 300))
        self.assertIn('GHL_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"', (_util.ROOT / "config" / "constants.py").read_text())


class BreakEvenTests(unittest.TestCase):
    def test_source_illustration(self):
        p = B.plan(**B.ILLUSTRATION)
        self.assertEqual(p, {"monthly_acquisition_cost": Fraction(2800), "required_sales": 1, "required_held": 4, "required_leads": 10})

    def test_exact_arithmetic_avoids_float_ceiling_error(self):
        self.assertEqual(B.required_leads(4, 0.4), 10)
        self.assertEqual(B.required_held(3, 0.3), 10)

    def test_formulas(self):
        self.assertEqual(B.monthly_acquisition_cost(650, 1000, 50), 1700)
        self.assertEqual(B.required_sales(1700, 1000), 2)
        self.assertEqual(B.required_held(2, 0.5), 4)
        self.assertEqual(B.required_leads(4, 0.25), 16)
        self.assertEqual(B.contribution(5000, 3200), 1800)

    def test_unknown_and_invalid_inputs(self):
        with self.assertRaises(B.InputUnknown):
            B.required_sales(C.NEEDS_EVIDENCE, 100)
        with self.assertRaises(ValueError):
            B.required_held(1, 0)
        with self.assertRaises(ValueError):
            B.required_sales(100, 0)
        self.assertFalse(B.try_plan(monthly_service_fee=C.NEEDS_EVIDENCE, media_spend=1, separately_charged_tools=0,
                                    contribution_per_sale=1, close_rate=0.5, lead_to_held_rate=0.5)["computable"])

    def test_render_labels_every_input(self):
        md = B.render()
        for f in ("monthly_acquisition_cost = monthly_service_fee + media_spend + separately_charged_tools",
                  "required_sales = ceil(acquisition_cost / contribution_per_sale)",
                  "required_held = ceil(required_sales / close_rate)",
                  "required_leads = ceil(required_held / lead_to_held_rate)"):
            self.assertIn(f, md)
        input_rows = [l for l in md.splitlines() if l.startswith("| ") and any(k in l for k in ("monthly_service_fee", "media_spend |",
                      "separately_charged_tools", "contribution_per_sale", "close_rate", "lead_to_held_rate"))]
        self.assertEqual(len(input_rows), 6)
        self.assertTrue(all("assumption — not a CA-J result" in l for l in input_rows))


class MarginTests(unittest.TestCase):
    def term(self, **kw):
        t = {"name": "t", "revenue": 10000, "scope": "defined", "agency_acquisition_cost": 1000,
             "costs": {k: 500 for k in M.COST_KEYS}}
        t.update(kw)
        return t

    def test_computes_when_all_known(self):
        r = M.model_margin(self.term())
        self.assertTrue(r["modelable"])
        self.assertEqual(r["margin"], 10000 - 3000 - 1000)

    def test_unknown_input_refuses_to_guess(self):
        r = M.model_margin(self.term(costs=dict({k: 1 for k in M.COST_KEYS}, editing=C.NEEDS_EVIDENCE)))
        self.assertFalse(r["modelable"])
        self.assertEqual(r["message"], "margin cannot be modeled with current inputs")
        self.assertIn("editing", r["unknown_inputs"])

    def test_unlimited_scope_refused(self):
        with self.assertRaises(M.UnlimitedScopeRefused):
            M.model_margin(self.term(scope="unlimited", costs={k: C.NEEDS_EVIDENCE for k in M.COST_KEYS}))

    def test_caj_revenue(self):
        self.assertEqual(M.caj_package_revenue(6, 10, 250), 650 * 6 + 2500)
        self.assertEqual(M.caj_package_revenue(C.NEEDS_EVIDENCE, 10, 250), C.NEEDS_EVIDENCE)
        with self.assertRaises(ValueError):
            M.caj_package_revenue(6, 10, 400)

    def test_render_states_cannot_model(self):
        self.assertIn("margin cannot be modeled with current inputs", M.render(CONFIG))


if __name__ == "__main__":
    unittest.main()

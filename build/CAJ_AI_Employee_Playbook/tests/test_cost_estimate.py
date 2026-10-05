import json
import shutil
import tempfile
import unittest
from pathlib import Path

from _paths import ROOT
from scripts import cost_estimate as ce
from scripts import mini_yaml

PRICING = json.loads((ROOT / "guardrails" / "locked_pricing.json").read_text(encoding="utf-8"))

VERIFIED = """currency: USD
booked_appointments_per_month: 2
booked_appointments_verified: true
included_usage_policy: allowance per contract
rates:
  - name: platform
    category: platform_allocation
    basis: fixed_monthly
    amount: 100
    quantity_per_month: 1
    verified: true
  - name: ai
    category: ai_usage
    basis: per_unit
    amount: 0.5
    quantity_per_month: 100
    verified: true
  - name: tel
    category: telephony
    basis: per_unit
    amount: 0.1
    quantity_per_month: 100
    verified: true
  - name: pay
    category: payment_fees
    basis: percent_of_revenue
    amount: 10
    verified: true
  - name: support
    category: support_labour
    basis: per_unit
    amount: 50
    quantity_per_month: 2
    verified: true
"""


class CostEstimateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _rates(self, text):
        p = self.tmp / "rates.yaml"
        p.write_text(text, encoding="utf-8")
        return p

    def test_locked_pricing_constants(self):
        self.assertEqual(PRICING["TECH_FEE_MONTHLY_USD"], 650)
        self.assertEqual(PRICING["SETUP_FEE_USD"], 0)
        self.assertEqual(PRICING["PER_BOOKED_APPOINTMENT_MIN_USD"], 250)
        self.assertEqual(PRICING["PER_BOOKED_APPOINTMENT_MAX_USD"], 300)
        self.assertIs(PRICING["MEETING_FIRST"], True)
        self.assertIs(PRICING["QUOTE_PRICE_IN_OUTBOUND"], False)
        self.assertEqual(PRICING["SPEND_CAP_USD"], 0.0)

    def test_contribution_math(self):
        est = ce.estimate(PRICING, mini_yaml.loads(VERIFIED))
        self.assertEqual(est.revenue_low, 650 + 2 * 250)
        self.assertEqual(est.revenue_high, 650 + 2 * 300)
        # costs low: 100 + 50 + 10 + 115 (10% of 1150) + 100 = 375
        self.assertAlmostEqual(sum(est.costs_low.values()), 375.0)
        self.assertAlmostEqual(est.contribution_low, 1150 - 375)
        self.assertAlmostEqual(est.contribution_high, 1250 - 385)
        self.assertEqual(est.unverified, [])
        self.assertEqual(ce.main(["--rates", str(self._rates(VERIFIED))]), 0)

    def test_repo_rates_unverified_exit_nonzero(self):
        self.assertEqual(ce.main([]), 3)

    def test_negative_contribution(self):
        neg = VERIFIED.replace("amount: 100\n", "amount: 5000\n")
        self.assertEqual(ce.main(["--rates", str(self._rates(neg))]), 1)

    def test_refuses_unlimited(self):
        unl = VERIFIED.replace("allowance per contract", "Unlimited minutes")
        self.assertEqual(ce.main(["--rates", str(self._rates(unl))]), 2)

    def test_malformed_rates(self):
        missing = VERIFIED.split("  - name: support")[0]
        self.assertEqual(ce.main(["--rates", str(self._rates(missing))]), 2)
        for bad in (VERIFIED.replace("category: telephony", "category: snacks"),
                    VERIFIED.replace("basis: fixed_monthly", "basis: yearly"),
                    VERIFIED.replace("amount: 10\n", "amount: 150\n"),
                    VERIFIED.replace("amount: 0.5", "amount: -1"),
                    VERIFIED.replace("booked_appointments_per_month: 2", "booked_appointments_per_month: x")):
            with self.subTest(bad=bad[:0]):
                with self.assertRaises(ce.RatesError):
                    ce.estimate(PRICING, mini_yaml.loads(bad))


if __name__ == "__main__":
    unittest.main()

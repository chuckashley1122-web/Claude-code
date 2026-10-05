import unittest
from urllib.parse import parse_qs, urlsplit

from tests._helpers import ROOT  # noqa: F401
from config import constants as C
from tools import guardrails as G
from tools import utm_builder as U

NAME = "CAJ-FB-HVAC-Leads-20261005-DRAFT"


class UtmBuilder(unittest.TestCase):
    def test_three_variants_plus_control(self):
        rows = U.build_test_urls("https://offer.example.com/", NAME)
        self.assertEqual(len(rows), 4)
        for r in rows[:3]:
            self.assertEqual(U.missing_params(r["url"]), [])
            q = parse_qs(urlsplit(r["url"]).query)
            self.assertEqual(q["utm_source"], ["facebook"])
            self.assertEqual(q["utm_medium"], ["paid_social"])
            self.assertEqual(q["utm_campaign"], [NAME])
            self.assertTrue(q["fbc"][0].startswith("fb.1.") and q["fbc"][0].endswith(q["fbclid"][0]))
            self.assertTrue(q["fbp"][0].startswith("fb.1."))
        self.assertEqual(urlsplit(rows[3]["url"]).query, "")
        self.assertFalse(rows[3]["expect_conversion"])

    def test_deterministic_and_distinct(self):
        a = U.build_test_urls("https://offer.example.com/", NAME)
        b = U.build_test_urls("https://offer.example.com/", NAME)
        self.assertEqual(a, b)
        self.assertEqual(len({r["url"] for r in a}), 4)

    def test_no_secret_shaped_values(self):
        text = U.render(U.build_test_urls("https://offer.example.com/", NAME), True)
        self.assertEqual(G.find_secrets(text), [])
        self.assertIn(U.TEST_DATA_MARK, text)
        self.assertNotIn(C.FROZEN_CAMPAIGN_NAME, text)

    def test_bad_base_urls(self):
        for bad in ("offer.example.com", "ftp://x.example.com", "https://offer.example.com/?a=1"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                U.build_url(bad, {"a": "b"})

    def test_placeholder_resolution(self):
        self.assertEqual(U.resolve_landing_url({"landing_page_url": C.NEEDS_EVIDENCE}), (U.PLACEHOLDER_LANDING_URL, True))
        self.assertEqual(U.resolve_landing_url({"landing_page_url": "https://offer.example.org/"}),
                         ("https://offer.example.org/", False))


if __name__ == "__main__":
    unittest.main()

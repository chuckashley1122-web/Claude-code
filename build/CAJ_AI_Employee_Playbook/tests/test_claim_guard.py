import re
import unittest

from _paths import ROOT
from guardrails import claim_guard as cg


class ClaimGuardTests(unittest.TestCase):
    def test_blocks_source_anchors_and_results(self):
        d = "$"
        samples = {
            "SC-01": f"Only {d}197 a month",
            "SC-03": f"from {d}97",
            "SC-04": f"{d}297 setup",
            "SC-05": f"a {d}9.99 add-on",
            "SC-06": "costs virtually nothing",
            "SC-07": "We build your demo in 15 minutes",
            "SC-08": "30 to 90 emails per day",
            "SC-09": "make 50 calls a day",
            "SC-10": "a low-churn service",
            "SC-11": "boost your agency valuation",
            "SC-12": f"normally {d}1,000 plus {d}2,000 setup",
            "SC-13": f"the {d}397 audit",
            "SC-14": "it is low maintenance",
            "RULE-UNLIMITED": "Unlimited minutes",
            "RULE-GUARANTEE": "Guaranteed bookings",
            "RULE-REVIEWS": "Rated by 120 five-star reviews",
            "RULE-ATTRIBUTION": "we recovered " + d + "40k in missed calls",
            "RULE-CONSUMER-BRAND": "Try Chuck's Daily " + "Grind coffee",
        }
        for rule, text in samples.items():
            with self.subTest(rule=rule):
                rules = {h.rule for h in cg.find_violations(text)}
                self.assertIn(rule, rules)
                with self.assertRaises(cg.ClaimViolation):
                    cg.assert_clean(text)

    def test_consumer_shop_blocked(self):
        self.assertFalse(cg.is_clean("See our " + "Et" + "sy" + " shop for print" + "ables"))

    def test_clean_b2b_copy_passes(self):
        for text in ("We help HVAC teams handle routine after-hours questions.",
                     "I can prepare a short AI demo using your business information.",
                     "Open to a 15-minute walkthrough?",
                     "No, we have not spoken before."):
            with self.subTest(text=text):
                self.assertTrue(cg.is_clean(text), cg.find_violations(text))

    def test_denylist_matches_source_claims_doc(self):
        doc = (ROOT / "docs" / "SOURCE-CLAIMS.md").read_text(encoding="utf-8")
        doc_ids = set(re.findall(r"^\| (SC-\d{2}) \|", doc, flags=re.M))
        self.assertEqual(doc_ids, cg.denylist_ids())


if __name__ == "__main__":
    unittest.main()

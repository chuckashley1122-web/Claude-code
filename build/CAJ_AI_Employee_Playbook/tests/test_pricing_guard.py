import unittest

from _paths import ROOT  # noqa: F401
from guardrails import pricing_guard as pg


class PricingGuardTests(unittest.TestCase):
    def test_blocks_amounts_and_terms_in_outbound(self):
        for text in ("$650 per month", "$" + "197", "setup fee", "$1,000 plus $2,000 setup", "$" + "9.99",
                     "650 USD", "six hundred dollars", "our monthly plan", "the fee is small",
                     "what does it cost", "pricing page", "250 per booked appointment", "99/mo"):
            with self.subTest(text=text):
                self.assertFalse(pg.is_clean(text, "email"))
                with self.assertRaises(pg.PricingViolation):
                    pg.assert_clean(text, "chat")

    def test_clean_outbound_passes_every_channel(self):
        text = "Open to a 15-minute walkthrough? You can pick a time here: https://ca-jenterprises.com/ai"
        for ch in pg.OUTBOUND_CHANNELS:
            self.assertEqual(pg.assert_clean(text, ch), text)

    def test_word_boundaries_avoid_false_positives(self):
        for text in ("Thanks for the feedback", "a costume party", "coffee", "priceless? no: precise"):
            with self.subTest(text=text):
                self.assertTrue(pg.is_clean(text, "email"), pg.find_violations(text, "email"))

    def test_internal_channel_blocks_amounts_only(self):
        self.assertTrue(pg.is_clean("Never state any price or fee.", "internal_instructions"))
        self.assertFalse(pg.is_clean("Tell them it is $650.", "internal_instructions"))
        self.assertEqual([v.kind for v in pg.find_amounts("650 dollars")], ["dollars"])

    def test_unknown_channel_rejected(self):
        with self.assertRaises(ValueError):
            pg.find_violations("hi", "carrier-pigeon")

    def test_violation_message_routes_to_booking_url(self):
        with self.assertRaises(pg.PricingViolation) as cm:
            pg.assert_clean("$650 per month", "email")
        self.assertIn(pg.BOOKING_URL, str(cm.exception))
        self.assertEqual(cm.exception.channel, "email")
        kinds = {v.kind for v in cm.exception.violations}
        self.assertTrue({"currency_symbol", "per_month"} <= kinds)


if __name__ == "__main__":
    unittest.main()

import unittest

from _paths import ROOT  # noqa: F401
from guardrails import meeting_first as mf
from guardrails import pricing_guard as pg


class MeetingFirstTests(unittest.TestCase):
    def test_detects_price_intent(self):
        for q in ("How much is it?", "What are your rates", "Any setup fee?", "Send a quote",
                  "Is it expensive?", "what do you charge", "Is it $500?", "monthly plan?"):
            with self.subTest(q=q):
                self.assertTrue(mf.detect_price_intent(q))

    def test_ignores_non_price_messages(self):
        for q in ("Can you call me tomorrow?", "Do you serve Round Rock?", "", "accurate info please"):
            with self.subTest(q=q):
                self.assertFalse(mf.detect_price_intent(q))
                self.assertIsNone(mf.respond(q))

    def test_reply_offers_meeting_and_is_price_free(self):
        reply = mf.respond("How much does this cost?", first_name="Alex")
        self.assertTrue(reply.startswith("Hi Alex."))
        self.assertIn("https://ca-jenterprises.com/ai", reply)
        for ch in pg.OUTBOUND_CHANNELS:
            self.assertTrue(pg.is_clean(reply, ch))

    def test_enforce_outbound_rewrites_only_priced_drafts(self):
        text, changed = mf.enforce_outbound("It is $650 per month plus setup fee.", "email")
        self.assertTrue(changed)
        self.assertEqual(text, mf.MEETING_REPLY)
        clean = "Would Tuesday work for a walkthrough?"
        self.assertEqual(mf.enforce_outbound(clean, "dm"), (clean, False))


if __name__ == "__main__":
    unittest.main()

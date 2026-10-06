import io
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import constants  # noqa: E402
from guardrails import claim_guard, meeting_first, pricing_guard  # noqa: E402
from scripts import check_guardrails  # noqa: E402


class PricingGuardTest(unittest.TestCase):
    def test_spec_acceptance_strings_blocked(self):
        for text in ("$650 per month", "setup fee", "$197", "250 to 300 per booked appointment"):
            with self.subTest(text=text):
                r = pricing_guard.check(text)
                self.assertEqual(r.status, pricing_guard.BLOCKED)
                self.assertTrue(r.findings)

    def test_locked_terms_never_pass_in_any_phrasing(self):
        lo, hi = constants.PER_BOOKED_APPOINTMENT_MIN_USD, constants.PER_BOOKED_APPOINTMENT_MAX_USD
        for text in (f"${constants.TECH_FEE_MONTHLY_USD}/mo", f"{constants.TECH_FEE_MONTHLY_USD} a month",
                     f"{lo}-{hi} per booked appointment", f"{lo} – {hi} per appointment",
                     f"${lo} to ${hi} each booked appointment", f"{constants.TECH_FEE_MONTHLY_USD} USD",
                     "The set-up fee is waived", "monthly plan", "our pricing", "what it costs",
                     "€99", "USD 40", "40 dollars"):
            with self.subTest(text=text):
                self.assertTrue(pricing_guard.check(text).blocked)

    def test_clean_copy_passes(self):
        for text in ("Worth a quick chat? Pick a time at https://ca-jenterprises.com/ai",
                     "Keep answers <25 words.", "9:16, 8 seconds", "Confirmed 2026-10-06 at 09:00.",
                     "Follow-up number 2 of the sequence", "fit_score 1-10"):
            with self.subTest(text=text):
                self.assertEqual(pricing_guard.check(text).status, pricing_guard.CLEAN, pricing_guard.check(text))

    def test_offending_span_reported(self):
        text = "Hello. It is $650 per month."
        r = pricing_guard.check(text)
        spans = [text[f.start:f.end] for f in r.findings]
        self.assertIn("$650", spans)
        self.assertIn("per month", spans)

    def test_assert_clean(self):
        self.assertEqual(pricing_guard.assert_clean("hello"), "hello")
        with self.assertRaises(pricing_guard.PricingViolation) as cm:
            pricing_guard.assert_clean("only $197", "email")
        self.assertIn("email", str(cm.exception))
        self.assertEqual(pricing_guard.check(None).status, pricing_guard.CLEAN)


class MeetingFirstTest(unittest.TestCase):
    def test_pricing_intent_routes_to_booking_url(self):
        for msg in ("How much does it cost?", "What are your rates", "Can you send a quote?",
                    "¿Cuánto cuesta?", "Quel est le prix ?", "Was kostet das?", "is it $$$"):
            with self.subTest(msg=msg):
                r = meeting_first.route(msg)
                self.assertTrue(r.pricing_intent)
                self.assertIn(constants.BOOKING_URL, r.reply)
                self.assertIsNone(re.search(r"\d", r.reply))
                self.assertFalse(pricing_guard.check(r.reply).blocked)

    def test_non_pricing_passes_through(self):
        for msg in ("What are your office hours?", "Can I reschedule?", ""):
            r = meeting_first.route(msg)
            self.assertFalse(r.pricing_intent)
            self.assertIsNone(r.reply)


class ClaimGuardTest(unittest.TestCase):
    def test_parse_denylist(self):
        md = ("intro\n\n| ID | Line | Verbatim claim | Denylist phrase | Status |\n|---|---|---|---|---|\n"
              "| C1 | 1 | \"x\" | foo bar | unverified |\n| C2 | 2 | \"y\" | - | unverified |\n\n"
              "| Other | Table |\n|---|---|\n| a | b |\n")
        self.assertEqual(claim_guard.parse_denylist(md), ["foo bar"])

    def test_denylist_built_from_source_claims(self):
        phrases = claim_guard.denylist()
        for p in ("unlimited", "virtually nothing", "10 calls at a time", "10x faster", "20+ languages",
                  "$300-400/mo", "unlimited/day"):
            self.assertIn(p, phrases)

    def test_blocks_source_claims_case_insensitive(self):
        for text in ("Answers 10 Calls At A Time", "UNLIMITED usage", "costs virtually nothing",
                     "UGC 10x faster", "support in 20+ languages", "fastest win"):
            with self.subTest(text=text):
                r = claim_guard.check(text)
                self.assertTrue(r.blocked)
                self.assertEqual(r.findings[0].category, "source_claim")

    def test_blocks_consumer_brands_in_b2b_copy(self):
        for brand in claim_guard.CONSUMER_BRANDS:
            r = claim_guard.check(f"CA-J Enterprises and {brand} together")
            self.assertTrue(r.blocked)
            self.assertEqual(r.findings[0].category, "consumer_brand")

    def test_blocks_banned_terms_including_plurals(self):
        for term in claim_guard.BANNED_TERMS:
            self.assertTrue(claim_guard.check(f"We promise {term}").blocked, term)
        self.assertTrue(claim_guard.check("We deliver " + "qualified" + " appointments").blocked)
        self.assertFalse(claim_guard.check("Each booked appointment is confirmed by email.").blocked)

    def test_word_boundaries(self):
        self.assertFalse(claim_guard.check("We build front desks for home service companies.").blocked)
        self.assertFalse(claim_guard.check("an unlimitedly long word is fine? no: unlimitedness").blocked)

    def test_assert_no_claims(self):
        with self.assertRaises(claim_guard.ClaimViolation):
            claim_guard.assert_no_claims("unlimited")
        self.assertEqual(claim_guard.assert_no_claims("plain"), "plain")

    def test_missing_source_claims_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                claim_guard.check("x", Path(tmp) / "missing.md")


class CheckGuardrailsScriptTest(unittest.TestCase):
    def run_main(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = check_guardrails.main(argv)
        return code, buf.getvalue()

    def test_self_test_passes(self):
        code, out = self.run_main([])
        self.assertEqual(code, 0, out)
        for text in check_guardrails.MUST_BLOCK_PRICING:
            self.assertIn(f"PASS  pricing_guard BLOCKED {text!r}", out)
        self.assertIn("pass on all 15 prompt files", out)

    def test_reinjected_price_exits_nonzero(self):
        code, out = self.run_main(["--inject-price"])
        self.assertEqual(code, 1)
        self.assertIn("02_cold_email.txt", out)

    def test_prompts_dir_scan(self):
        self.assertEqual(self.run_main(["--prompts-dir", str(ROOT / "prompts")])[0], 0)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "x.txt").write_text("Only $197 today", encoding="utf-8")
            self.assertEqual(self.run_main(["--prompts-dir", tmp])[0], 1)


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from tools import guardrails as G  # noqa: E402

VERIFIED = {"facts": [{"key": "review_count", "verified": True, "evidence_source": "https://example.com/proof"}]}
UNVERIFIED = {"facts": [{"key": "review_count", "verified": False, "evidence_source": ""}]}


class NoSpend(unittest.TestCase):
    def test_requires_written_reference(self):
        for ref in (None, "", "   ", C.NEEDS_EVIDENCE):
            with self.assertRaises(G.GuardrailViolation):
                G.assert_no_spend("domain", ref)

    def test_passes_with_reference(self):
        G.assert_no_spend("domain", "Email from Chuck 2026-10-05 approving the exact amount")

    def test_ad_cap_zero(self):
        self.assertEqual(C.AD_SPEND_CAP_USD, 0)


class NoPrice(unittest.TestCase):
    def test_rejects_each_price_form(self):
        for text in ("Only $650 a month", "650/mo plan", "from $250", "up to $300",
                     "billed per booked appointment", "$250 to $300", "no setup fee", "our tech fee"):
            with self.subTest(text=text), self.assertRaises(G.GuardrailViolation):
                G.assert_no_price_in_message(text)

    def test_allows_meeting_first_copy(self):
        G.assert_no_price_in_message("Pricing is discussed in a meeting. Book at " + C.BOOKING_URL)


class LogoNotFirst(unittest.TestCase):
    def test_rejects_logo_first(self):
        for creative in ({"opening_element": "logo", "elements": ["logo", "headline"]},
                         {"opening_element": "outcome_headline", "elements": ["brand_logo", "outcome_headline"]},
                         {"opening_element": "", "elements": []},
                         {"opening_element": "outcome", "elements": ["outcome"], "logo_position": "top"}):
            with self.subTest(creative=creative), self.assertRaises(G.GuardrailViolation):
                G.assert_logo_not_first(creative)

    def test_accepts_outcome_first(self):
        G.assert_logo_not_first({"opening_element": "outcome_headline",
                                 "elements": ["outcome_headline", "offer_line", "logo_footer_disclaimer"],
                                 "logo_position": "footer"})


class FrozenCampaign(unittest.TestCase):
    def test_rejects_target_mentions(self):
        for line in (f"Duplicate {C.FROZEN_CAMPAIGN_NAME} and raise budget",
                     f"target: {C.FROZEN_CAMPAIGN_NAME}", f"pause {C.FROZEN_CAMPAIGN_NAME}"):
            with self.subTest(line=line), self.assertRaises(G.GuardrailViolation):
                G.assert_frozen_campaign_untouched(line)

    def test_allows_warning_line(self):
        G.assert_frozen_campaign_untouched(f"WARNING: {C.FROZEN_CAMPAIGN_NAME} is FROZEN - never edit it.")
        G.assert_frozen_campaign_untouched("nothing relevant here")


class FabricatedFacts(unittest.TestCase):
    def test_rejects_unsourced_claims(self):
        claims = ["Rated 4.9 out of 5", "over 200 five-star reviews", "trusted by 300 clients",
                  "15 years in business", "fully licensed and insured", "visit us at 100 Congress Avenue",
                  "we reply within 5 minutes", "we guarantee results", "increase leads by 40%",
                  "Read our testimonials"]
        for text in claims:
            with self.subTest(text=text), self.assertRaises(G.GuardrailViolation):
                G.assert_no_fabricated_fact(text, UNVERIFIED)

    def test_allows_sourced_claim(self):
        G.assert_no_fabricated_fact("over 200 reviews", VERIFIED)
        with self.assertRaises(G.GuardrailViolation):
            G.assert_no_fabricated_fact("over 200 reviews", UNVERIFIED)

    def test_plain_copy_passes(self):
        G.assert_no_fabricated_fact("Every engagement starts with a meeting.", UNVERIFIED)


class CanonicalUnique(unittest.TestCase):
    def rec(self, route, title, desc, canonical, indexable=True):
        return {"route": route, "title": title, "meta_description": desc, "canonical": canonical,
                "indexable": indexable}

    def test_duplicates_rejected(self):
        base = self.rec("/a", "A", "desc a", "https://x.example.com/a")
        for dup in (self.rec("/b", "A", "desc b", "https://x.example.com/b"),
                    self.rec("/b", "B", "desc a", "https://x.example.com/b"),
                    self.rec("/b", "B", "desc b", "https://x.example.com/a"),
                    self.rec("/b", "B", "desc b", "")):
            with self.subTest(dup=dup), self.assertRaises(G.GuardrailViolation):
                G.assert_canonical_unique([base, dup])

    def test_non_indexable_ignored_and_unique_passes(self):
        G.assert_canonical_unique([self.rec("/a", "A", "a", "https://x.example.com/a"),
                                   self.rec("/b", "B", "b", "https://x.example.com/b"),
                                   self.rec("/c", "A", "a", "https://x.example.com/a", indexable=False)])


class LocationGuards(unittest.TestCase):
    def test_disallowed_location(self):
        with self.assertRaises(G.GuardrailViolation):
            G.assert_not_disallowed_location("use " + C.DISALLOWED_LOCATION_ID)
        G.assert_not_disallowed_location("use " + C.GHL_LOCATION_ID)

    def test_location_case(self):
        G.assert_location_id_exact_case("id " + C.GHL_LOCATION_ID)
        with self.assertRaises(G.GuardrailViolation):
            G.assert_location_id_exact_case("id " + C.GHL_LOCATION_ID.lower())


class BannedPhrasesBrandsContact(unittest.TestCase):
    def test_banned_phrases(self):
        for phrase in ("qualified" + " appointment", "it " + "shows" + " up", "10-25" + " leads" + "/month"):
            with self.subTest(phrase=phrase), self.assertRaises(G.GuardrailViolation):
                G.assert_no_banned_phrase("We sell " + phrase)
        G.assert_no_banned_phrase("We count each booked appointment.")

    def test_consumer_brand_blocked_in_b2b(self):
        for text in ("Chuck's Daily " + "Grind blend", "our Et" + "sy shop", "print" + "ables bundle",
                     "fresh cof" + "fee"):
            with self.subTest(text=text), self.assertRaises(G.GuardrailViolation):
                G.assert_no_consumer_brand(text)
        G.assert_no_consumer_brand("CA-J Enterprises lead generation")

    def test_public_contact_only(self):
        with self.assertRaises(G.GuardrailViolation):
            G.assert_public_contact_only("call " + str(8665663444 + 1))
        G.assert_public_contact_only("call " + C.OWNER_PHONE)

    def test_check_all_collects(self):
        problems = G.check_all("Only $650 and 4.9 stars", True, UNVERIFIED)
        self.assertEqual(len(problems), 2)
        self.assertEqual(G.check_all("Only $650", False, UNVERIFIED), [])


if __name__ == "__main__":
    unittest.main()

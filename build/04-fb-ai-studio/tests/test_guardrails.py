import unittest

from tests._helpers import ROOT  # noqa: F401  (puts build root on sys.path)
from config import constants as C
from tools import guardrails as G


class FrozenCampaignTripwire(unittest.TestCase):
    def test_exact_name_trips(self):
        with self.assertRaises(G.FrozenCampaignError):
            G.assert_not_frozen_campaign(f"Pause {C.FROZEN_CAMPAIGN_NAME} tonight")

    def test_case_and_separator_variants_trip(self):
        variants = [C.FROZEN_CAMPAIGN_NAME.lower(), C.FROZEN_CAMPAIGN_NAME.replace("_", "-"),
                    C.FROZEN_CAMPAIGN_NAME.replace("_", " "), "duplicate " + C.FROZEN_CAMPAIGN_NAME.title()]
        for v in variants:
            with self.subTest(v=v), self.assertRaises(G.FrozenCampaignError):
                G.assert_not_frozen_campaign(v)

    def test_banner_only_allowed_when_flag_set(self):
        text = f"{G.BANNER_START}\nWARNING {C.FROZEN_CAMPAIGN_NAME} is frozen\n{G.BANNER_END}\n# Steps\n- build new draft"
        G.assert_not_frozen_campaign(text, allow_banner=True)
        with self.assertRaises(G.FrozenCampaignError):
            G.assert_not_frozen_campaign(text)
        with self.assertRaises(G.FrozenCampaignError):
            G.assert_not_frozen_campaign(text + f"\nEdit {C.FROZEN_CAMPAIGN_NAME}", allow_banner=True)

    def test_draft_name_pattern(self):
        G.assert_campaign_name_is_draft("CAJ-FB-HVAC-Leads-20261005-DRAFT")
        for bad in ("CAJ-FB-HVAC-Leads-20261005", "My campaign", C.FROZEN_CAMPAIGN_NAME):
            with self.subTest(bad=bad), self.assertRaises(G.FrozenCampaignError):
                G.assert_campaign_name_is_draft(bad)


class Spend(unittest.TestCase):
    def test_refuses_without_reference(self):
        for ref in (None, "", "   ", C.NEEDS_EVIDENCE, "TBD", 123):
            with self.subTest(ref=ref), self.assertRaises(G.SpendNotApproved):
                G.assert_no_spend("ad_budget", ref)

    def test_accepts_explicit_reference(self):
        self.assertEqual(G.assert_no_spend("domain", "APPROVAL-2026-10-05-CA")["approval_ref"], "APPROVAL-2026-10-05-CA")


class Price(unittest.TestCase):
    def test_locked_prices_blocked(self):
        samples = [f"${C.TECH_FEE_MONTHLY_USD}/mo", f"only {C.TECH_FEE_MONTHLY_USD} a month",
                   f"{C.PER_BOOKED_APPOINTMENT_MIN_USD} to {C.PER_BOOKED_APPOINTMENT_MAX_USD} per booked appointment",
                   "setup fee waived", "50% off your first month", "a $100 discount", "1000 dollars", "199 per month"]
        for s in samples:
            with self.subTest(s=s), self.assertRaises(G.PriceInMessageError):
                G.assert_no_price_in_message(s)

    def test_clean_message_passes(self):
        G.assert_no_price_in_message("Hi there, book a free strategy session: " + C.BOOKING_URL)

    def test_meeting_first_rejects_other_links(self):
        G.assert_meeting_first("Book here " + C.BOOKING_URL)
        with self.assertRaises(G.PriceInMessageError):
            G.assert_meeting_first("Book here https://example.com/pricing")


class LogoNotFirst(unittest.TestCase):
    def rec(self, **kw):
        base = {"asset_id": "X", "opening_element": {"type": "pain", "description": "Missed call on a phone"},
                "logo_placement": "small footer disclaimer only", "on_image_text": ["Missed the call?"]}
        base.update(kw)
        return base

    def test_good_records_pass(self):
        G.assert_logo_not_first(self.rec())
        G.assert_logo_not_first(self.rec(opening_element={"type": "outcome", "description": "Full calendar"}))

    def test_logo_first_blocked(self):
        bad = [self.rec(opening_element={"type": "logo", "description": "CA-J logo"}),
               self.rec(opening_element={"type": "pain", "description": "Logo animation then phone"}),
               self.rec(opening_element={"type": "pain", "description": "CA-J Enterprises wordmark"}),
               self.rec(opening_element={"type": "offer", "description": "Free session"}),
               self.rec(logo_placement="top left, large"),
               self.rec(on_image_text=["CA-J Enterprises", "Missed the call?"]),
               {"asset_id": "Y"}]
        for r in bad:
            with self.subTest(r=r), self.assertRaises(G.LogoFirstError):
                G.assert_logo_not_first(r)

    def test_copy_lead(self):
        G.assert_copy_leads_with_pain_or_outcome({"lead": "pain", "text": "[LOCATION] HVAC owners: missed calls?"})
        with self.assertRaises(G.LogoFirstError):
            G.assert_copy_leads_with_pain_or_outcome({"lead": "pain", "text": "[LOCATION] HVAC owners: CA-J here!"})
        with self.assertRaises(G.LogoFirstError):
            G.assert_copy_leads_with_pain_or_outcome({"lead": "brand", "text": "Hello"})


class BrandBannedClaims(unittest.TestCase):
    def test_consumer_brands_blocked(self):
        for b in C.CONSUMER_BRAND_BLOCKLIST:
            with self.subTest(b=b), self.assertRaises(G.BrandBlendError):
                G.assert_no_consumer_brand(f"CA-J Enterprises and {b} together")
        with self.assertRaises(G.BrandBlendError):
            G.assert_no_consumer_brand("Call " + C.FORBIDDEN_PHONE_NUMBERS[0])
        G.assert_no_consumer_brand("CA-J Enterprises helps HVAC companies")

    def test_banned_phrases_blocked(self):
        for p in G.BANNED_PHRASES:
            with self.subTest(p=p), self.assertRaises(G.BannedPhraseError):
                G.assert_no_banned_phrases("We deliver " + p.upper())
        G.assert_no_banned_phrases("We count every booked appointment")

    def test_unverified_claims(self):
        for s in ["250+ reviews", "4.9 stars", "20 years in business", "500 customers", "40% more leads",
                  "our clients saw growth", "3x more leads", "ROI of 5"]:
            with self.subTest(s=s), self.assertRaises(G.UnverifiedClaimError):
                G.assert_no_unverified_claims(s)
        G.assert_no_unverified_claims("Make logo on header 1.8 times bigger; Day 14 follow-up")

    def test_ad_risk(self):
        for s in ["Guaranteed results", "Only 6 spots left", "Limited time", "Hurry", "Offer expires Friday"]:
            with self.subTest(s=s):
                self.assertTrue(G.find_ad_risk(s))
        self.assertEqual(G.find_ad_risk("Book a free, no-obligation strategy session."), [])

    def test_platform_names_in_headline(self):
        self.assertTrue(G.find_platform_names_in_headline("Top rated on Google"))
        self.assertFalse(G.find_platform_names_in_headline("More booked appointments"))


class SecretsAndIds(unittest.TestCase):
    def test_secret_patterns(self):
        fake = ["EAA" + "B" * 30, "sk-" + "a" * 20, "ghp_" + "x" * 30, "1" * 15, "api_key = " + "Z" * 16]
        for s in fake:
            with self.subTest(s=s[:6]):
                self.assertTrue(G.find_secrets(s))
        self.assertFalse(G.find_secrets("META_PIXEL_ID= fb.1.1759622400000.1234567890"))

    def test_location_ids(self):
        self.assertEqual(G.find_location_id_problems(C.GHL_LOCATION_ID), [])
        self.assertTrue(G.find_location_id_problems(C.GHL_LOCATION_ID.lower()))
        self.assertTrue(G.find_location_id_problems(C.DISALLOWED_LOCATION_ID))


if __name__ == "__main__":
    unittest.main()

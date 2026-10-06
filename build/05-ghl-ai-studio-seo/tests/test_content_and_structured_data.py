import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from src import business_facts, content_pages, page_plan, structured_data  # noqa: E402
from tools import guardrails as G  # noqa: E402


def facts(**verified):
    records = business_facts.fact_records()
    for r in records:
        if r["key"] in verified:
            r.update(value=verified[r["key"]], verified=True, evidence_source="https://example.com/evidence",
                     public_copy_eligible=True)
    return {"facts": records}


class ThinContentGuard(unittest.TestCase):
    def test_raises_on_near_identical_bodies(self):
        a = "Marketing support for service businesses in Austin with a meeting first and a written plan."
        b = a.replace("Austin", "Round Rock")
        with self.assertRaises(content_pages.ThinContentError) as ctx:
            content_pages.assert_not_thin({"/a": a, "/b": b})
        self.assertGreater(ctx.exception.pairs[0][2], C.THIN_CONTENT_SIMILARITY_MAX)

    def test_distinct_bodies_pass(self):
        content_pages.assert_not_thin({"/a": "lead generation pages forms follow up",
                                       "/b": "reputation listings feedback replies routine"})

    def test_similarity_metric(self):
        self.assertEqual(content_pages.similarity("a b c", "a b c"), 1.0)
        self.assertEqual(content_pages.similarity("a b", "c d"), 0.0)

    def test_location_pages_merge_but_service_pages_distinct(self):
        rows = page_plan.build_rows(C.NEEDS_EVIDENCE)
        f = facts()
        pages = {r: content_pages.apply_evidence_gate(m, f) for r, m in content_pages.page_models(rows).items()}
        bodies = {r: content_pages.public_body(p) for r, p in pages.items()}
        pairs = [(a, b) for a, b, s in content_pages.similarity_pairs(bodies) if s > C.THIN_CONTENT_SIMILARITY_MAX]
        self.assertEqual(pairs, [("/locations/austin", "/locations/round-rock")])


class EvidenceGate(unittest.TestCase):
    def test_unverified_claims_withheld(self):
        rows = page_plan.build_rows(C.NEEDS_EVIDENCE)
        model = content_pages.page_models(rows)["/"]
        gated = content_pages.apply_evidence_gate(model, facts())
        headings = [s["heading"] for s in gated["sections"]]
        self.assertNotIn("Results from client work", headings)
        self.assertIn("results", gated["withheld"][0]["missing_claims"])

    def test_verified_house_facts_filled(self):
        rows = page_plan.build_rows(C.NEEDS_EVIDENCE)
        gated = content_pages.apply_evidence_gate(content_pages.page_models(rows)["/contact"], facts())
        text = content_pages.public_text(gated)
        self.assertIn(C.OWNER_PHONE, text)
        self.assertIn(C.OWNER_EMAIL, text)
        self.assertNotIn("{", text)

    def test_public_copy_value_refuses_internal_pricing(self):
        with self.assertRaises(business_facts.UnsourcedClaim):
            business_facts.public_copy_value(facts(), "tech_fee_monthly_usd")
        with self.assertRaises(business_facts.UnsourcedClaim):
            business_facts.public_copy_value(facts(), "testimonials")

    def test_copy_with_unsourced_claim_fails(self):
        rows = page_plan.build_rows(C.NEEDS_EVIDENCE)
        page = content_pages.apply_evidence_gate(content_pages.page_models(rows)["/about"], facts())
        page = copy.deepcopy(page)
        page["sections"][0]["paragraphs"].append("Serving 500 clients since forever.")
        with self.assertRaises(G.GuardrailViolation):
            content_pages.assert_public_copy_clean(page, facts())
        page2 = copy.deepcopy(content_pages.apply_evidence_gate(content_pages.page_models(rows)["/about"], facts()))
        page2["lead"] += " Plans from $650."
        with self.assertRaises(G.GuardrailViolation):
            content_pages.assert_public_copy_clean(page2, facts())

    def test_all_shipped_pages_clean(self):
        rows = page_plan.build_rows(C.NEEDS_EVIDENCE)
        f = facts()
        for route, model in content_pages.page_models(rows).items():
            with self.subTest(route=route):
                page = content_pages.apply_evidence_gate(model, f)
                content_pages.assert_public_copy_clean(page, f)
                content_pages.assert_conversion_path(page)


class ConversionPath(unittest.TestCase):
    def test_exactly_one_cta_to_booking_url(self):
        page = {"route": "/x", "primary_cta": {"label": "Go", "href": "https://example.com/other"}}
        with self.assertRaises(content_pages.ConversionPathError):
            content_pages.assert_conversion_path(page)
        with self.assertRaises(content_pages.ConversionPathError):
            content_pages.assert_conversion_path({"route": "/x", "primary_cta": [
                {"label": "a", "href": C.BOOKING_URL}, {"label": "b", "href": C.BOOKING_URL}]})
        content_pages.assert_conversion_path({"route": "/x", "primary_cta": {"label": "a", "href": C.BOOKING_URL}})


class StructuredData(unittest.TestCase):
    def test_only_verified_fields_emitted(self):
        org, blocked = structured_data.build_organization(facts())
        self.assertEqual(org["telephone"], "+1-512-229-9199")
        for prop in ("aggregateRating", "review", "address", "openingHours", "priceRange", "url", "logo"):
            self.assertNotIn(prop, org)
            self.assertIn(prop, blocked)

    def test_verified_facts_unlock_fields_but_never_price_range(self):
        f = facts(review_rating="4.8", review_count="12", office_address="Example address",
                  site_origin="https://www.example.com")
        org, blocked = structured_data.build_organization(f)
        self.assertEqual(org["aggregateRating"]["reviewCount"], "12")
        self.assertEqual(org["url"], "https://www.example.com")
        self.assertIn("priceRange", blocked)
        self.assertNotIn("priceRange", org)

    def test_route_document(self):
        row = page_plan.build_rows(C.NEEDS_EVIDENCE)[1]
        doc = structured_data.build_route_document(row, facts())
        self.assertEqual(doc["@context"], "https://schema.org")
        self.assertTrue(any(b.startswith("Service") for b in doc["_blocked_fields"]))
        self.assertTrue(any(b.startswith("BreadcrumbList") for b in doc["_blocked_fields"]))
        crumbs = structured_data.build_route_document(row, facts(site_origin="https://www.example.com"))
        self.assertEqual(crumbs["@graph"][-1]["@type"], "BreadcrumbList")


if __name__ == "__main__":
    unittest.main()

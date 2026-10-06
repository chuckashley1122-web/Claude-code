import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from src import metadata, page_plan  # noqa: E402
from tools import guardrails as G  # noqa: E402


class MetadataUniqueness(unittest.TestCase):
    def setUp(self):
        self.rows = page_plan.build_rows(C.NEEDS_EVIDENCE)

    def test_shipped_set_is_unique_and_valid(self):
        records = metadata.build_records(self.rows)
        metadata.validate(records)
        self.assertEqual(len(records), len(C.PROPOSED_ROUTES))
        for r in records:
            self.assertEqual(r["og"]["og:image"], C.NEEDS_EVIDENCE)
            self.assertEqual(r["canonical"], C.NEEDS_EVIDENCE + r["route"])
            self.assertIsInstance(r["title_length_warning"], bool)

    def test_duplicate_title_detected(self):
        rows = copy.deepcopy(self.rows)
        rows[2]["title"] = rows[1]["title"]
        with self.assertRaises(G.GuardrailViolation):
            metadata.validate(metadata.build_records(rows))

    def test_duplicate_canonical_detected(self):
        rows = copy.deepcopy(self.rows)
        rows[3]["canonical"] = rows[0]["canonical"]
        with self.assertRaises(G.GuardrailViolation):
            metadata.validate(metadata.build_records(rows))

    def test_duplicate_description_detected(self):
        records = metadata.build_records(self.rows)
        records[1]["meta_description"] = records[0]["meta_description"]
        with self.assertRaises(G.GuardrailViolation):
            metadata.validate(records)

    def test_non_indexable_routes_excluded(self):
        rows = copy.deepcopy(self.rows)
        rows[4]["indexable"] = False
        self.assertNotIn(rows[4]["route"], [r["route"] for r in metadata.build_records(rows)])

    def test_social_image_must_be_absolute(self):
        with self.assertRaises(metadata.MetadataError):
            metadata.build_records(self.rows, og_image="/img/og.png")
        recs = metadata.build_records(self.rows, og_image="https://cdn.example.com/og.png")
        self.assertEqual(recs[0]["twitter"]["twitter:image"], "https://cdn.example.com/og.png")

    def test_verified_origin_used_for_canonical(self):
        rows = page_plan.build_rows("https://www.example.com")
        self.assertEqual(rows[1]["canonical"], "https://www.example.com/services/lead-generation")


if __name__ == "__main__":
    unittest.main()

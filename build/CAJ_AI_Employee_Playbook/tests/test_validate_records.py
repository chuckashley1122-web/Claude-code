import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from _paths import ROOT
from scripts import validate_records as vr

BUILD_ID = "UWc5vKBgFVPdxNTRAy2s"


class SchemaSubsetTests(unittest.TestCase):
    def test_validate_instance_keywords(self):
        schema = {"type": "object", "required": ["a"], "additionalProperties": False,
                  "properties": {"a": {"type": "string", "enum": ["X", "Y"]},
                                 "d": {"type": "string", "format": "date"},
                                 "t": {"type": "string", "format": "date-time"},
                                 "p": {"type": "string", "pattern": "^B\\d{3}$"},
                                 "l": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}}}}
        self.assertEqual(vr.validate_instance(schema, {"a": "X", "d": "2026-10-05", "t": "2026-10-05T12:00:00Z",
                                                       "p": "B001", "l": ["x"]}), [])
        errs = vr.validate_instance(schema, {"d": "2026-13-40", "t": "yesterday", "p": "X1", "l": [], "z": 1})
        joined = "\n".join(errs)
        for needle in ("missing required 'a'", "valid date", "valid date-time", "does not match",
                       "fewer than 1", "unexpected property 'z'"):
            self.assertIn(needle, joined)
        self.assertTrue(vr.validate_instance({"type": "string"}, 5))
        self.assertTrue(vr.validate_instance({"type": "integer"}, True))


class ContentCheckTests(unittest.TestCase):
    def test_location_ids(self):
        self.assertEqual(vr.find_foreign_location_ids(f"loc {BUILD_ID} ok"), [])
        stale = "nuhFUYu0ZF9" + "Eswiz9P79"  # built at runtime; never stored literally
        self.assertEqual(vr.find_foreign_location_ids(f"id={stale}"), [stale])
        flipped = BUILD_ID.swapcase()
        self.assertEqual(vr.find_foreign_location_ids(flipped), [flipped])
        self.assertEqual(vr.find_foreign_location_ids("abcdefghijklmnopqrst"), [])

    def test_placeholders(self):
        self.assertEqual(vr.find_placeholders("{{x}} [BUSINESS] <<FILL: y>> TBD"),
                         ["{{x}}", "[BUSINESS]", "<<FILL: y>>", "TBD"])
        self.assertEqual(vr.find_placeholders("source line 169"), [])


class RecordFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.records = self.tmp / "records"
        shutil.copytree(ROOT / "records", self.records)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _append(self, name, row):
        with (self.records / name).open("a", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow(row)

    def _report(self, name):
        return {r.name: r for r in vr.validate_all(self.records, ROOT / "schemas")}[name]

    def test_repo_records_are_clean(self):
        reports = vr.validate_all(ROOT / "records", ROOT / "schemas")
        self.assertEqual(len(reports), 5)
        for r in reports:
            self.assertTrue(r.ok, (r.name, r.schema_errors, r.findings))
        counts = {r.name: r.rows for r in reports}
        self.assertEqual(counts, {"Build_Log.csv": 0, "Asset_Register.csv": 0, "Business_Facts.csv": 14,
                                  "Test_Results.csv": 0, "Blockers.csv": 0})

    def test_business_facts_seed_rows(self):
        for path in (ROOT / "records" / "Business_Facts.csv", ROOT / "agent" / "business-facts-template.csv"):
            with path.open(newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 14)
            for row in rows:
                self.assertEqual(row["status"], "NEEDS_EVIDENCE")
                self.assertEqual(row["value"], "")
                self.assertEqual(row["evidence_url_or_owner_confirmation"], "")

    def test_pass_without_evidence_fails(self):
        self._append("Test_Results.csv", ["T03", "Real appointment ID in the correct calendar", "booked", "", "PASS", "", ""])
        r = self._report("Test_Results.csv")
        self.assertTrue(any("no evidence" in f for f in r.findings))

    def test_done_with_needs_evidence_fails(self):
        self._append("Build_Log.csv", ["11", "Build the demo calendar", "DONE", "", "", "2026-10-05T10:00:00Z",
                                       "created", "NEEDS_EVIDENCE", ""])
        r = self._report("Build_Log.csv")
        self.assertTrue(any("NEEDS_EVIDENCE" in f for f in r.findings))
        self.assertTrue(any("no evidence" in f for f in r.findings))

    def test_verified_without_date_fails(self):
        self._append("Asset_Register.csv", ["calendar", "CAJ HVAC AI Demo", "https://example.com/cal", "v1", "GHL",
                                            "VERIFIED", "Chuck", ""])
        r = self._report("Asset_Register.csv")
        self.assertTrue(any("verified_date" in f for f in r.findings))

    def test_price_location_and_placeholder_findings(self):
        stale = "nuhFUYu0ZF9" + "Eswiz9P79"
        self._append("Blockers.csv", ["B001", f"Fee is $650 and loc {stale} for {{{{business}}}}", "01",
                                      "Chuck", "", "REQUIRED", "", "OPEN"])
        f = "\n".join(self._report("Blockers.csv").findings)
        self.assertIn("price token", f)
        self.assertIn("foreign GHL location id", f)
        self.assertIn("unresolved placeholder", f)

    def test_schema_errors(self):
        self._append("Blockers.csv", ["X1", "desc", "99", "", "", "MAYBE", "", "OPEN"])
        errs = "\n".join(self._report("Blockers.csv").schema_errors)
        self.assertIn("does not match", errs)
        self.assertIn("'owner' is empty", errs)
        self.assertIn("MAYBE", errs)
        (self.records / "Build_Log.csv").write_text("step,title\n", encoding="utf-8")
        self.assertIn("header", self._report("Build_Log.csv").schema_errors[0])

    def test_valid_verified_fact_passes(self):
        self._append("Business_Facts.csv", ["timezone (test)", "America/Chicago", "owner email 2026-10-01",
                                            "2026-10-01", "VERIFIED", ""])
        self.assertTrue(self._report("Business_Facts.csv").ok)

    def test_cli_exit_codes(self):
        self.assertEqual(vr.main(["--records", str(self.records)]), 0)
        self._append("Test_Results.csv", ["T01", "x", "", "", "PASS", "", ""])
        self.assertEqual(vr.main(["--records", str(self.records)]), 1)

    def test_intake_validation(self):
        good = ROOT / "tests" / "fixtures" / "intake.synthetic.json"
        self.assertEqual(vr.main(["--intake", str(good)]), 0)
        data = json.loads(good.read_text(encoding="utf-8"))
        data["booking_permission"] = "anything"
        del data["phone_provider"]
        bad = self.tmp / "bad.json"
        bad.write_text(json.dumps(data), encoding="utf-8")
        errs = vr.validate_intake(bad, ROOT / "intake" / "intake.schema.json")
        self.assertTrue(any("phone_provider" in e for e in errs))
        self.assertTrue(any("anything" in e for e in errs))


if __name__ == "__main__":
    unittest.main()

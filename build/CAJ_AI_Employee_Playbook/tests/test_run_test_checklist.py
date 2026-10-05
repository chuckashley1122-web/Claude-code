import csv
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from _paths import ROOT
from scripts import run_test_checklist as rtc


class ChecklistDefinitionTests(unittest.TestCase):
    def test_twelve_rows_verbatim_not_run(self):
        rows = rtc.load_checklist()
        self.assertEqual([r["test_id"] for r in rows], [f"T{i:02d}" for i in range(1, 13)])
        source = (ROOT.parents[1] / "docs" / "playbooks" / "02-ai-employee-action-plan.md")
        if source.is_file():
            lines = source.read_text(encoding="utf-8").splitlines()
            block = "\n".join(lines[255:291])
            for r in rows:
                self.assertIn(f"{r['test_id']} {r['test_name']}", block)
                self.assertIn(f"| {r['pass_condition']}", block)
        for r in rows:
            self.assertEqual(r["result"], "NOT_RUN")
            self.assertEqual(r["critical"], "yes")
            self.assertEqual(r["evidence_ref"], "")


class RecordingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.results = self.tmp / "Test_Results.csv"
        shutil.copy(ROOT / "records" / "Test_Results.csv", self.results)
        self.checklist = rtc.load_checklist()
        self.t03 = next(t for t in self.checklist if t["test_id"] == "T03")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_cli(self, *args):
        return rtc.main(["--results", str(self.results), *args])

    def test_default_state_exits_nonzero(self):
        self.assertEqual(self.run_cli(), 1)

    def test_pass_without_evidence_refused(self):
        for ev in ("", "   ", "pass", "OK", "T03", "Booking success", "see above", "T03 passed", "---",
                   "Real appointment ID in the correct calendar", "test_results.csv"):
            with self.subTest(ev=ev):
                self.assertEqual(self.run_cli("--test-id", "T03", "--result", "PASS", f"--evidence={ev}"), 2)
        self.assertEqual(rtc.load_results(self.results), {})

    def test_card_data_refused(self):
        self.assertTrue(rtc.contains_card_number("4111 1111 1111 1111"))
        self.assertFalse(rtc.contains_card_number("appointment 1234567890123"))
        self.assertEqual(self.run_cli("--test-id", "T03", "--result", "PASS",
                                      "--evidence", "card 4111111111111111"), 2)

    def test_na_requires_reason(self):
        self.assertEqual(self.run_cli("--test-id", "T11", "--result", "N/A"), 2)

    def test_pass_with_evidence_recorded_and_retest_stamped(self):
        row = rtc.record_result(self.t03, "PASS", "GHL appointment id appt-001; out/t03.png", "booked", "",
                                "", self.results, today=date(2026, 10, 5))
        self.assertEqual(row["retest_date"], "")
        row2 = rtc.record_result(self.t03, "FAIL", "", "double booked", "fix capacity", "", self.results,
                                 today=date(2026, 10, 6))
        self.assertEqual(row2["retest_date"], "2026-10-06")
        with self.results.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["result"], "FAIL")

    def test_all_resolved_exits_zero(self):
        for t in self.checklist:
            if t["test_id"] == "T11":
                rtc.record_result(t, "N/A", "", "", "", "voice not in agreed scope", self.results)
            else:
                rtc.record_result(t, "PASS", f"evidence/{t['test_id'].lower()}-transcript.txt", "ok", "", "",
                                  self.results)
        self.assertEqual(self.run_cli(), 0)
        pending = rtc.outstanding(self.checklist, rtc.load_results(self.results))
        self.assertEqual(pending, [])

    def test_unknown_test_and_partial_args(self):
        self.assertEqual(self.run_cli("--test-id", "T99", "--result", "PASS", "--evidence", "x.png"), 2)
        self.assertEqual(self.run_cli("--test-id", "T01"), 2)


if __name__ == "__main__":
    unittest.main()

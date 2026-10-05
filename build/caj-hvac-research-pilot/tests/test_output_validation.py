"""T06 output integrity and T07 repeat execution, plus validator negative cases."""

import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from src.output_validation import main as validator_main  # noqa: E402
from src.output_validation import validate_run_dir  # noqa: E402
from src.pipeline import run_pipeline  # noqa: E402
from src.retrieval import FileDropRetriever, FixtureRetriever  # noqa: E402

FIX = ROOT / "tests" / "fixtures"
MISSING = config.MISSING_LABEL


def filedrop_run(tmp: Path, out: Path):
    pages = tmp / "pages" / "acme"
    pages.mkdir(parents=True)
    (pages / "01-home.txt").write_text(
        "# Acme Heating & Air\nAcme Heating & Air offers AC repair, heat pump service, and duct cleaning.\n"
        "Serving Austin.\nCall 512-555-0110 or use our contact form.\n", encoding="utf-8")
    inp = tmp / "companies.csv"
    inp.write_text("company_id,company_name,website_url\nacme,Acme Heating and Air,https://acme.example.com\n",
                   encoding="utf-8")
    return run_pipeline(inp, FileDropRetriever(tmp / "pages"), out, fixture_mode=False)


def fixture_run(tmp: Path, out: Path, inp: Path | None = None):
    inp = inp or (ROOT / "inputs" / "companies.csv")
    return run_pipeline(inp, FixtureRetriever(FIX), out, fixture_mode=True, use_fixture_demo_when_empty=True)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class T06OutputIntegrity(unittest.TestCase):
    def test_T06_commas_round_trip_and_manifest_agrees(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            report = filedrop_run(tmp, tmp / "out")
            self.assertEqual(report.validation_findings, [])
            with open(report.paths["results.csv"], encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(rows[0]["services"], "AC repair, heat pump, duct cleaning")
            self.assertEqual(rows[0]["status"], "complete")
            manifest = json.loads(report.paths["run.json"].read_text(encoding="utf-8"))
            self.assertEqual(manifest["record_count"], len(rows))
            self.assertEqual(manifest["counts_by_status"], {"complete": 1, "partial": 0, "blocked": 0})
            self.assertEqual(manifest["overall_status"], "completed")
            self.assertIs(manifest["fixture_mode"], False)
            for name in report.paths:
                self.assertNotIn("mock://", report.paths[name].read_text(encoding="utf-8"))

    def test_T06_fixture_run_manifest_matches_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = fixture_run(Path(tmp), Path(tmp) / "out")
            with open(report.paths["results.csv"], encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            manifest = json.loads(report.paths["run.json"].read_text(encoding="utf-8"))
            self.assertEqual(manifest["record_count"], 3)
            tally = {s: sum(r["status"] == s for r in rows) for s in config.COMPANY_STATUSES}
            self.assertEqual(manifest["counts_by_status"], tally)
            self.assertEqual(list(manifest), list(config.RUN_JSON_KEYS))
            self.assertIs(manifest["fixture_mode"], True)
            self.assertEqual(manifest["overall_status"], "partial")
            self.assertEqual(validator_main([str(report.run_dir)]), 0)


class T07RepeatExecution(unittest.TestCase):
    def test_T07_new_run_dir_and_earlier_files_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            first = fixture_run(tmp, tmp / "out")
            before = {n: sha(p) for n, p in first.paths.items()}
            second = fixture_run(tmp, tmp / "out")
            self.assertNotEqual(first.run_dir, second.run_dir)
            self.assertTrue(second.run_dir.is_dir())
            after = {n: sha(p) for n, p in first.paths.items()}
            self.assertEqual(before, after)
            same_hash = json.loads(second.paths["run.json"].read_text())["input_hash"]
            self.assertEqual(same_hash, json.loads(first.paths["run.json"].read_text())["input_hash"])

    def test_T07_existing_run_id_gets_suffix(self):
        from src.run_identity import create_run_dir
        with tempfile.TemporaryDirectory() as tmp:
            ids = [create_run_dir(Path(tmp), "20260101T000000Z-abcdef12")[0] for _ in range(3)]
            self.assertEqual(ids, ["20260101T000000Z-abcdef12", "20260101T000000Z-abcdef12-2",
                                   "20260101T000000Z-abcdef12-3"])


class ValidatorCatchesDefects(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.report = fixture_run(self.tmp, self.tmp / "out")
        self.run_dir = self.report.run_dir
        self.csv_path = self.run_dir / "results.csv"

    def tearDown(self):
        self._tmp.cleanup()

    def _rewrite_csv(self, mutate):
        with open(self.csv_path, encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        mutate(rows)
        with open(self.csv_path, "w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerows(rows)

    def test_clean_run_passes(self):
        self.assertEqual(validate_run_dir(self.run_dir), [])

    def test_near_miss_missing_label(self):
        self._rewrite_csv(lambda rows: rows[2].__setitem__(5, "N/A"))
        self.assertTrue(any("must read exactly" in f for f in validate_run_dir(self.run_dir)))

    def test_unsourced_fact(self):
        self._rewrite_csv(lambda rows: rows[2].__setitem__(5, "Austin"))
        self.assertTrue(any("no source claim" in f for f in validate_run_dir(self.run_dir)))

    def test_duplicate_company_and_count_mismatch(self):
        self._rewrite_csv(lambda rows: rows.append(list(rows[1])))
        findings = validate_run_dir(self.run_dir)
        self.assertTrue(any("appears 2 times" in f for f in findings))
        self.assertTrue(any("record_count" in f for f in findings))

    def test_blocked_row_with_fact(self):
        self._rewrite_csv(lambda rows: rows[3].__setitem__(6, "AC repair"))
        self.assertTrue(any("blocked company carries a fact" in f for f in validate_run_dir(self.run_dir)))

    def test_missing_artifact_and_bad_json(self):
        (self.run_dir / "run.json").write_text("{not json", encoding="utf-8")
        self.assertTrue(any("not valid JSON" in f for f in validate_run_dir(self.run_dir)))
        (self.run_dir / "evidence.md").unlink()
        self.assertEqual(validate_run_dir(self.run_dir), ["missing artifact: evidence.md"])
        self.assertEqual(validator_main([str(self.run_dir)]), 1)

    def test_tampered_excerpt(self):
        ev = self.run_dir / "evidence.md"
        ev.write_text(ev.read_text(encoding="utf-8").replace("Round Rock and nearby", "elsewhere and nearby"),
                      encoding="utf-8")
        self.assertTrue(any("matched text not found" in f for f in validate_run_dir(self.run_dir)))

    def test_mock_label_in_non_fixture_run(self):
        run_json = self.run_dir / "run.json"
        data = json.loads(run_json.read_text())
        data["fixture_mode"] = False
        run_json.write_text(json.dumps(data))
        self.assertTrue(any("mock:// label in a non-fixture run" in f for f in validate_run_dir(self.run_dir)))

    def test_http_label_in_fixture_run(self):
        self._rewrite_csv(lambda rows: rows[1].__setitem__(10, "https://real-site.example.com"))
        self.assertTrue(any("http-resolved" in f for f in validate_run_dir(self.run_dir)))

    def test_brief_fact_without_source(self):
        brief = self.run_dir / "brief.md"
        brief.write_text(brief.read_text(encoding="utf-8").replace(
            "- Service area: Round Rock [source: mock://fixture-a]", "- Service area: Round Rock"), encoding="utf-8")
        self.assertTrue(any("fact without a source" in f for f in validate_run_dir(self.run_dir)))


if __name__ == "__main__":
    unittest.main()

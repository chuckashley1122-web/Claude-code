"""T04 unavailable site, plus retriever modes and the LiveRetriever refusal."""

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from src.contract import Company, RawPage  # noqa: E402
from src.pipeline import run_pipeline  # noqa: E402
from src.retrieval import (FileDropRetriever, FixtureRetriever, LiveCallBlocked, LiveRetriever,  # noqa: E402
                           retrieve_with_retry)

FIX = ROOT / "tests" / "fixtures"
CO = Company("fixture-a", "Sample HVAC A", "https://sample-hvac-a.example.com", 1)


class Counting:
    def __init__(self, inner):
        self.inner, self.calls = inner, {}

    def fetch(self, company, max_pages):
        self.calls[company.company_id] = self.calls.get(company.company_id, 0) + 1
        return self.inner.fetch(company, max_pages)


class Flaky:
    """Fails on the first call, succeeds on the second (a transient failure)."""

    def __init__(self):
        self.calls = 0

    def fetch(self, company, max_pages):
        self.calls += 1
        if self.calls == 1:
            return [RawPage("mock://flaky", "mock://flaky", "", "failed", "", "TIMEOUT")]
        return [RawPage("mock://flaky", "mock://flaky", "# Sample HVAC A\nAC repair", "ok", "")]


class T04UnavailableSite(unittest.TestCase):
    def test_T04_one_retry_then_blocked_and_other_rows_continue(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            inp = tmp / "companies.csv"
            inp.write_text("company_id,company_name,website_url\n"
                           "fixture-a,Sample HVAC A,https://sample-hvac-a.example.com\n"
                           "fixture-d,Sample HVAC D,https://sample-hvac-d.example.com\n"
                           "fixture-b,Sample HVAC B,https://sample-hvac-b.example.com\n", encoding="utf-8")
            retriever = Counting(FixtureRetriever(FIX))
            report = run_pipeline(inp, retriever, tmp / "out", fixture_mode=True)
            self.assertEqual(retriever.calls["fixture-d"], 2, "initial request plus exactly one retry")
            self.assertEqual(retriever.calls["fixture-a"], 1)
            with open(report.paths["results.csv"], encoding="utf-8", newline="") as fh:
                rows = {r["company_id"]: r for r in csv.DictReader(fh)}
            self.assertEqual(list(rows), ["fixture-a", "fixture-d", "fixture-b"])
            self.assertEqual(rows["fixture-d"]["status"], "blocked")
            self.assertEqual(rows["fixture-a"]["status"], "complete")
            self.assertEqual(rows["fixture-b"]["status"], "partial")
            self.assertTrue(any("fixture-d: retrieval failed after 2 attempt(s)" in e for e in report.errors))
            self.assertEqual(report.validation_findings, [])

    def test_T04_transient_failure_recovers_on_the_single_retry(self):
        flaky = Flaky()
        outcome = retrieve_with_retry(flaky, CO, max_pages=3, max_retries=1)
        self.assertTrue(outcome.ok)
        self.assertEqual((outcome.attempts, flaky.calls), (2, 2))

    def test_T04_retries_never_exceed_locked_cap(self):
        always_fail = Counting(FixtureRetriever(FIX, force_failure_ids=frozenset({"fixture-a"})))
        outcome = retrieve_with_retry(always_fail, CO, max_pages=3, max_retries=5)
        self.assertFalse(outcome.ok)
        self.assertEqual(always_fail.calls["fixture-a"], 2)
        self.assertIn("RETRIEVAL_FAILURE", outcome.error)
        with self.assertRaises(config.CapRaiseRefused):
            config.max_retries({"CAJ_RESEARCH_MAX_RETRIES": "2"})


class FixtureMode(unittest.TestCase):
    def test_labels_are_mock(self):
        pages = FixtureRetriever(FIX).fetch(CO, 3)
        self.assertEqual([(p.label, p.retrieval_status) for p in pages], [("mock://fixture-a", "ok")])

    def test_unknown_company_has_no_fixture(self):
        pages = FixtureRetriever(FIX).fetch(Company("acme", "Acme", "https://acme.example.com", 1), 3)
        self.assertEqual(pages[0].retrieval_status, "failed")
        self.assertIn("NO_FIXTURE", pages[0].error)


class FileDropMode(unittest.TestCase):
    def test_reads_in_filename_order_capped_and_labeled(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "acme"
            folder.mkdir()
            for name in ("03-contact.txt", "01-home.txt", "02-services.txt", "04-about.txt", "notes.md"):
                (folder / name).write_text(f"# Acme\n{name}", encoding="utf-8")
            pages = FileDropRetriever(Path(tmp)).fetch(Company("acme", "Acme", "https://acme.example.com", 1), 3)
            self.assertEqual([p.label for p in pages], [
                "file://inputs/pages/acme/01-home.txt",
                "file://inputs/pages/acme/02-services.txt",
                "file://inputs/pages/acme/03-contact.txt",
            ])

    def test_retrieval_failure_marker_and_missing_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "acme"
            folder.mkdir()
            (folder / "01-home.txt").write_text("\n  RETRIEVAL_FAILURE\nblocked by site", encoding="utf-8")
            co = Company("acme", "Acme", "https://acme.example.com", 1)
            self.assertEqual(FileDropRetriever(Path(tmp)).fetch(co, 3)[0].retrieval_status, "failed")
            missing = FileDropRetriever(Path(tmp)).fetch(Company("none", "N", "https://n.example.com", 1), 3)
            self.assertIn("NO_PAGES_SUPPLIED", missing[0].error)


class LiveRetrieverRefuses(unittest.TestCase):
    def test_raises_typed_error_with_gates_off(self):
        with self.assertRaises(LiveCallBlocked) as ctx:
            LiveRetriever(allow_network=False, allow_live=False).fetch(CO, 3)
        msg = str(ctx.exception)
        self.assertIn("Human approval is required", msg)
        self.assertIn("006-01", msg)
        self.assertIn("not both set by a human", msg)

    def test_raises_even_when_gates_are_set(self):
        with self.assertRaises(LiveCallBlocked) as ctx:
            LiveRetriever(allow_network=True, allow_live=True).fetch(CO, 3)
        self.assertIn("no human-approved retrieval implementation", str(ctx.exception))

    def test_default_gates_come_from_config(self):
        self.assertFalse(config.ALLOW_NETWORK_RETRIEVAL)
        with self.assertRaises(LiveCallBlocked):
            LiveRetriever().fetch(CO, 3)

    def test_is_not_a_bare_not_implemented_error(self):
        self.assertFalse(issubclass(LiveCallBlocked, NotImplementedError))


if __name__ == "__main__":
    unittest.main()

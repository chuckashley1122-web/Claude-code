"""T03 invalid input fails before retrieval, plus the full input contract."""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from src.input_validation import validate_bytes, validate_file  # noqa: E402
from src.pipeline import run_pipeline  # noqa: E402
from src.retrieval import FixtureRetriever  # noqa: E402

HEADER = "company_id,company_name,website_url\n"


class CountingRetriever:
    def __init__(self):
        self.calls = 0
        self.inner = FixtureRetriever(ROOT / "tests" / "fixtures")

    def fetch(self, company, max_pages):
        self.calls += 1
        return self.inner.fetch(company, max_pages)


def row(i, url=None):
    return f"c{i},Company {i},{url if url is not None else f'https://c{i}.example.com'}\n"


class T03InvalidInput(unittest.TestCase):
    CASES = {
        "missing header": row(1),
        "duplicate id": HEADER + row(1) + row(1),
        "empty url": HEADER + row(1, url=""),
        "four rows": HEADER + "".join(row(i) for i in range(1, 5)),
    }

    def test_T03_each_case_invalid_before_retrieval_and_no_output_folder(self):
        for name, text in self.CASES.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                tmp = Path(tmp)
                inp = tmp / "companies.csv"
                inp.write_text(text, encoding="utf-8")
                out = tmp / "outputs"
                retriever = CountingRetriever()
                report = run_pipeline(inp, retriever, out, fixture_mode=True, use_fixture_demo_when_empty=True)
                self.assertEqual(report.state, "INPUT_INVALID")
                self.assertEqual(retriever.calls, 0)
                self.assertFalse(out.exists() and any(out.iterdir()), "an output folder was created")

    def test_T03_errors_carry_row_index_and_reason(self):
        res = validate_bytes((HEADER + row(1) + row(1)).encode())
        self.assertEqual(res.state, "INPUT_INVALID")
        self.assertEqual(res.errors[0].row_index, 2)
        self.assertIn("duplicate", res.errors[0].reason)
        res = validate_bytes((HEADER + "".join(row(i) for i in range(1, 5))).encode())
        self.assertIn("No rows were dropped", res.errors[0].reason)


class InputContract(unittest.TestCase):
    def test_header_only_is_input_required(self):
        self.assertEqual(validate_bytes(HEADER.encode()).state, "INPUT_REQUIRED")
        self.assertEqual(validate_file(ROOT / "inputs" / "companies.csv").state, "INPUT_REQUIRED")

    def test_valid_one_to_three_rows(self):
        for n in (1, 2, 3):
            res = validate_bytes((HEADER + "".join(row(i) for i in range(1, n + 1))).encode())
            self.assertTrue(res.ok)
            self.assertEqual([c.row_index for c in res.companies], list(range(1, n + 1)))

    def test_bom_is_accepted(self):
        self.assertTrue(validate_bytes(("﻿" + HEADER + row(1)).encode("utf-8")).ok)

    def test_other_rejections(self):
        cases = {
            "reordered header": "company_name,company_id,website_url\n" + row(1),
            "empty id": HEADER + ",Name,https://x.example.com\n",
            "empty name": HEADER + "c1,,https://x.example.com\n",
            "relative url": HEADER + row(1, url="www.example.com"),
            "ftp url": HEADER + row(1, url="ftp://example.com"),
            "mock url": HEADER + row(1, url="mock://fixture-a"),
            "extra column": HEADER + "c1,N,https://x.example.com,extra\n",
            "not utf-8": None,
        }
        for name, text in cases.items():
            raw = b"\xff\xfe\x00bad" if text is None else text.encode()
            with self.subTest(case=name):
                self.assertEqual(validate_bytes(raw).state, "INPUT_INVALID")

    def test_missing_file_is_invalid(self):
        self.assertEqual(validate_file(Path("/nonexistent/companies.csv")).state, "INPUT_INVALID")

    def test_cap_cannot_be_raised_by_env(self):
        with self.assertRaises(config.CapRaiseRefused):
            config.max_companies({"CAJ_RESEARCH_MAX_COMPANIES": "4"})
        self.assertEqual(config.max_companies({"CAJ_RESEARCH_MAX_COMPANIES": "2"}), 2)
        self.assertEqual(config.max_companies({}), 3)
        res = validate_bytes((HEADER + row(1) + row(2)).encode(), max_rows=1)
        self.assertEqual(res.state, "INPUT_INVALID")


if __name__ == "__main__":
    unittest.main()

import io
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import yaml_lite  # noqa: E402
from scripts import cost_estimate  # noqa: E402

SPEC_VENDORS = ["vapi", "openai_realtime", "apify", "apollo", "heygen", "elevenlabs", "createmate",
                "ayrshare", "openai_api", "sora_runway", "twilio"]


class YamlLiteTest(unittest.TestCase):
    def test_parses_subset(self):
        data = yaml_lite.loads(
            "# c\nname: 'x # not a comment'\ncount: 3\nratio: 0.5\nflag: true\nnothing: null\n"
            "items:\n  - id: a\n    v: ~\n  - id: \"b\"\n    v: false  # trailing\n")
        self.assertEqual(data["name"], "x # not a comment")
        self.assertEqual((data["count"], data["ratio"], data["flag"], data["nothing"]), (3, 0.5, True, None))
        self.assertEqual(data["items"], [{"id": "a", "v": None}, {"id": "b", "v": False}])

    def test_rejects_outside_subset(self):
        bad = ["key: [1, 2]\n", "key: {a: 1}\n", "items:\n  - a: 1\n      b: 2\n", "a: 1\na: 2\n",
               "  orphan: 1\n", "items:\n\t- a: 1\n", "items:\n  - a: 1\n    a: 2\n", "no colon here\n"]
        for text in bad:
            with self.subTest(text=text):
                with self.assertRaises(yaml_lite.YamlLiteError):
                    yaml_lite.loads(text)

    def test_pricing_yaml_rows(self):
        data = yaml_lite.load(ROOT / "config" / "pricing.yaml")
        rows = data["vendors"]
        self.assertEqual([r["id"] for r in rows], SPEC_VENDORS)
        for r in rows:
            self.assertIsNone(r["unit_cost"], r["id"])
            self.assertIsNone(r["worst_case_monthly_units"], r["id"])
            self.assertIs(r["verified"], False)
            self.assertEqual(r["source"], "01-8-best-ai-automations.md:117 (unverified)")

    def test_pricing_yaml_has_no_numeric_rate(self):
        text = (ROOT / "config" / "pricing.yaml").read_text(encoding="utf-8")
        self.assertNotIn("$", text)
        for figure in ("0.05", "0.06", "29", "22", "50-100", "300-400"):
            self.assertNotIn(figure, text)
        for line in text.splitlines():
            if re.match(r"\s*(unit_cost|worst_case_monthly_units):", line):
                self.assertTrue(line.rstrip().endswith("null"), line)


class CostEstimateTest(unittest.TestCase):
    def run_main(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pricing.yaml"
            path.write_text(text, encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = cost_estimate.main(["--pricing", str(path)])
            return code, buf.getvalue()

    def test_real_table_is_unbounded_and_exits_nonzero(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cost_estimate.main([])
        self.assertEqual(code, 1)
        self.assertIn("Monthly worst case: UNBOUNDED", buf.getvalue())
        self.assertIn("SPEND_CAP_USD = 0.00", buf.getvalue())

    def row(self, vid, cost, units, verified="false"):
        return (f"  - id: {vid}\n    unit: month\n    unit_cost: {cost}\n    worst_case_monthly_units: {units}\n"
                f"    verified: {verified}\n    source: \"test\"\n")

    def test_known_figures_sum_and_exceed_zero_cap(self):
        code, out = self.run_main("vendors:\n" + self.row("a", 2.5, 4) + self.row("b", 1, 3, "true"))
        self.assertEqual(code, 1)
        self.assertIn("Monthly worst case: $13.00", out)
        self.assertIn("UNVERIFIED figure", out)

    def test_all_zero_within_cap(self):
        code, out = self.run_main("vendors:\n" + self.row("a", 0, 10, "true"))
        self.assertEqual(code, 0)
        self.assertIn("within SPEND_CAP_USD", out)

    def test_estimate_against_custom_cap(self):
        table = yaml_lite.loads("vendors:\n" + self.row("a", 5, 2))
        self.assertFalse(cost_estimate.estimate(table, cap=20).exceeds_cap)
        self.assertTrue(cost_estimate.estimate(table, cap=9.99).exceeds_cap)

    def test_bad_tables_fail(self):
        for text in ("vendors:\n" + self.row("a", -1, 1), "vendors:\n" + self.row("a", 1, 1) + self.row("a", 1, 1),
                     "other: 1\n", "vendors:\n  - id: a\n"):
            with self.subTest(text=text):
                code, out = self.run_main(text)
                self.assertEqual(code, 2)
                self.assertIn("FAIL", out)


if __name__ == "__main__":
    unittest.main()

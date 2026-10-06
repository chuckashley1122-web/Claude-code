import inspect
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import estimator as E  # noqa: E402
from src import ghl_adapter as A  # noqa: E402
from tools.paths import BUILD_ROOT, scratch_paths  # noqa: E402


class GHLAdapterTests(unittest.TestCase):
    def test_every_live_method_refuses(self):
        adapter = A.GHLAdapter()
        methods = [name for name, fn in inspect.getmembers(A.GHLAdapter, inspect.isfunction)
                   if not name.startswith("_")]
        self.assertGreaterEqual(len(methods), 10)
        for name in methods:
            fn = getattr(adapter, name)
            args = [{}, "sub-00000001", 10] if name == "save_inquiry" else []
            with self.subTest(method=name):
                with self.assertRaises(NotImplementedError) as ctx:
                    fn(*args)
                self.assertIsInstance(ctx.exception, A.LiveCallBlocked)
                self.assertIn("TODO: confirm", str(ctx.exception))

    def test_no_guessed_endpoint_or_ids(self):
        source = (BUILD_ROOT / "src" / "ghl_adapter.py").read_text()
        for guess in ("leadconnectorhq", "/contacts/", "/opportunities", "Version: 20", "https://services."):
            self.assertNotIn(guess, source)

    def test_mock_is_labelled_and_works_offline(self):
        mock = A.MockGHLAdapter()
        self.assertEqual(mock.label, "MOCK — NOT PRODUCTION")
        self.assertIn("MOCK — NOT PRODUCTION", A.MockGHLAdapter.__doc__)
        r1 = mock.save_inquiry({"email": "tester@example.com"}, "sub-1", 10)
        r2 = mock.save_inquiry({"email": "tester@example.com"}, "sub-2", 10)
        self.assertEqual((r1.outcome, r2.outcome), ("saved", "saved"))
        self.assertEqual(len(mock.contacts), 1)  # contact matching by email
        self.assertEqual(len(mock.inquiries), 2)
        mock.script.append(A.UpstreamTimeout())
        with self.assertRaises(A.UpstreamTimeout):
            mock.save_inquiry({}, "sub-3", 10)


class EstimatorTests(unittest.TestCase):
    R = E.SYNTHETIC_DEMO_RULES

    def test_disabled_emits_only_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            paths = scratch_paths(Path(td))
            E.build(paths)
            files = sorted(p.name for p in (paths.out / "estimator").iterdir())
            self.assertEqual(files, ["BLOCKED.md"])
            text = (paths.out / "estimator" / "BLOCKED.md").read_text()
            for item in E.MISSING_INPUTS:
                self.assertIn(item, text)

    def test_enabled_emits_labelled_synthetic_demo(self):
        with tempfile.TemporaryDirectory() as td:
            paths = scratch_paths(Path(td))
            path = E.build(paths, enabled=True)
            self.assertIn("SYNTHETIC", path.read_text())

    def test_exact_decimal_math_ignores_browser_total(self):
        est = E.compute_estimate({"service": "demo_service", "quantity": "12", "browser_total": "0.01"}, self.R)
        # (12 * 2.00 + 1.00 + 1.00) = 26.00; * 1.10 = 28.60
        self.assertEqual((est.subtotal, est.total), ("26.00", "28.60"))
        self.assertEqual(est.label, self.R["label"])

    def test_minimum_and_rounding(self):
        self.assertEqual(E.compute_estimate({"service": "demo_service", "quantity": 1}, self.R).total, "11.00")
        self.assertEqual(E.compute_estimate({"service": "demo_service", "quantity": "3.333"}, self.R).total,
                         "11.00")
        self.assertEqual(E.compute_estimate({"service": "demo_service", "quantity": "4.005"}, self.R).subtotal,
                         "10.01000")
        self.assertEqual(E.compute_estimate({"service": "demo_service", "quantity": "4.005"}, self.R).total,
                         "11.01")

    def test_rejections(self):
        bad = [{"service": "nope", "quantity": 1}, {"service": "demo_service", "quantity": -1},
               {"service": "demo_service", "quantity": "abc"}, {"service": "demo_service", "quantity": float("nan")},
               {"service": "demo_service", "quantity": float("inf")}, {"service": "demo_service", "quantity": "Infinity"},
               {"service": "demo_service", "quantity": 10 ** 9}, {"service": "demo_service", "quantity": True},
               {"service": "demo_service", "quantity": 0}, {"service": "demo_service", "quantity": 2, "unit": "sqft"}]
        for req in bad:
            with self.subTest(req=req), self.assertRaises(E.EstimateRejected):
                E.compute_estimate(req, self.R)


if __name__ == "__main__":
    unittest.main()

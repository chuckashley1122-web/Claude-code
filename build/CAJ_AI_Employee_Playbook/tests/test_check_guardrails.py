import unittest

from _paths import ROOT  # noqa: F401
from scripts import check_guardrails as chk


class CheckGuardrailsTests(unittest.TestCase):
    def test_all_self_tests_pass(self):
        results = chk.run_checks()
        failed = [r for r in results if not r[1]]
        self.assertEqual(failed, [])
        self.assertEqual(chk.main(), 0)

    def test_required_samples_present(self):
        samples = {s for s, _, _ in chk.MUST_BLOCK}
        d = "$"
        for needed in (d + "650 per month", d + "197", "setup fee", d + "1,000 plus " + d + "2,000 setup",
                       d + "9.99", "we recovered " + d + "40k in missed calls"):
            self.assertIn(needed, samples)


if __name__ == "__main__":
    unittest.main()

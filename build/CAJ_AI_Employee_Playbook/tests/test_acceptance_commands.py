"""Runs the spec section 5 step 27 / section 7 commands as real subprocesses."""
import subprocess
import sys
import unittest

from _paths import ROOT


def run(*args):
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, timeout=60)


class AcceptanceCommandTests(unittest.TestCase):
    def test_validate_records(self):
        r = run("scripts/validate_records.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("all five records schema-valid", r.stdout)

    def test_check_guardrails(self):
        r = run("scripts/check_guardrails.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("FAIL", r.stdout)

    def test_run_test_checklist_default_is_blocking(self):
        r = run("scripts/run_test_checklist.py")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("OUTSTANDING: 12", r.stdout)
        r = run("scripts/run_test_checklist.py", "--test-id", "T01", "--result", "PASS", "--evidence", "")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("REJECTED", r.stdout)

    def test_render_templates(self):
        r = run("scripts/render_templates.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("zero unresolved placeholders", r.stdout)
        r = run("scripts/render_templates.py", "--omit", "business")
        self.assertNotEqual(r.returncode, 0)

    def test_cost_estimate(self):
        r = run("scripts/cost_estimate.py")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("contribution", r.stdout)
        self.assertIn("UNVERIFIED", r.stdout)


if __name__ == "__main__":
    unittest.main()

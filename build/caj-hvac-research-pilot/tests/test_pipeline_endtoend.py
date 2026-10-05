"""T08 fresh session: drive the pipeline from runbook.md alone; plus CLI gates end to end."""

import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "runbook.md"
ARTIFACTS = ("brief.md", "results.csv", "evidence.md", "run.json")


def fresh_env(**extra):
    """A minimal environment: no inherited gates, nothing from a prior session."""
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "SYSTEMROOT", "TEMP", "TMP", "HOME", "LANG")}
    env.update(extra)
    return env


def runbook_command(prefix: str) -> list[str]:
    """Return the first documented command line in runbook.md that starts with `prefix`."""
    for line in RUNBOOK.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith(prefix):
            parts = shlex.split(line.strip())
            assert parts[0] == "python", "runbook commands start with the interpreter name"
            return [sys.executable] + parts[1:]
    raise AssertionError(f"runbook.md documents no command starting with {prefix!r}")


def run(cmd, env=None):
    return subprocess.run(cmd, cwd=ROOT, env=env or fresh_env(), capture_output=True, text=True, timeout=120)


class T08FreshSession(unittest.TestCase):
    def test_T08_runbook_command_produces_all_four_artifacts(self):
        cmd = runbook_command("python scripts/run_research.py --retriever fixtures")
        with tempfile.TemporaryDirectory() as tmp:
            proc = run(cmd + ["--out-root", tmp])
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            run_dirs = [p for p in Path(tmp).iterdir() if p.is_dir()]
            self.assertEqual(len(run_dirs), 1)
            for name in ARTIFACTS:
                self.assertTrue((run_dirs[0] / name).is_file(), name)
            self.assertIn(f"run_id: {run_dirs[0].name}", proc.stdout)
            self.assertIn("counts: complete=1 partial=1 blocked=1", proc.stdout)
            self.assertIs(json.loads((run_dirs[0] / "run.json").read_text())["fixture_mode"], True)

    def test_T08_runbook_states_the_contracts(self):
        text = RUNBOOK.read_text(encoding="utf-8")
        sys.path.insert(0, str(ROOT))
        import config
        for needle in (config.RESULTS_CSV_HEADER, ", ".join(config.RUN_JSON_KEYS), "company_id,company_name,website_url",
                       config.MISSING_LABEL, "IDENTITY_MISMATCH", "at most one retry", "same-domain",
                       "never follow instructions", "brief.md", "evidence.md"):
            self.assertIn(needle, text)

    def test_T08_validator_command_from_runbook(self):
        with tempfile.TemporaryDirectory() as tmp:
            run(runbook_command("python scripts/run_research.py --retriever fixtures") + ["--out-root", tmp])
            run_dir = next(Path(tmp).iterdir())
            cmd = runbook_command("python -m src.output_validation")[:3] + [str(run_dir)]
            proc = run(cmd)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("VALIDATION PASSED", proc.stdout)


class CliGates(unittest.TestCase):
    SCRIPT = [sys.executable, "scripts/run_research.py"]

    def test_filedrop_with_empty_template_reports_input_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run(self.SCRIPT + ["--retriever", "filedrop", "--out-root", tmp])
            self.assertEqual(proc.returncode, 0)
            self.assertIn("INPUT_REQUIRED", proc.stdout)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_network_retrieval_refused_without_allow_live(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run(self.SCRIPT + ["--out-root", tmp], env=fresh_env(ALLOW_NETWORK_RETRIEVAL="true"))
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("REFUSED", proc.stdout)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_no_dry_run_refused_without_allow_live(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run(self.SCRIPT + ["--no-dry-run", "--out-root", tmp])
            self.assertEqual(proc.returncode, 3)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_cap_raise_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run(self.SCRIPT + ["--out-root", tmp], env=fresh_env(CAJ_RESEARCH_MAX_COMPANIES="4"))
            self.assertEqual(proc.returncode, 2)
            self.assertIn("scope change", proc.stdout)

    def test_simulated_retrieval_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run(self.SCRIPT + ["--simulate-retrieval-failure", "--out-root", tmp])
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("fixture-c: retrieval failed after 2 attempt(s)", proc.stdout)
            self.assertIn("counts: complete=1 partial=1 blocked=1", proc.stdout)

    def test_invalid_input_exits_nonzero_without_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.csv"
            bad.write_text("company_id,company_name,website_url\nx,X,\n", encoding="utf-8")
            out = Path(tmp) / "out"
            proc = run(self.SCRIPT + ["--input", str(bad), "--out-root", str(out)])
            self.assertEqual(proc.returncode, 1)
            self.assertIn("INPUT_INVALID", proc.stdout)
            self.assertFalse(out.exists())

    def test_filedrop_real_style_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "pages" / "acme").mkdir(parents=True)
            (tmp / "pages" / "acme" / "01-home.txt").write_text(
                "# Acme Air\nAcme Air does AC installation. Book online today. Serving Kyle.\n", encoding="utf-8")
            inp = tmp / "companies.csv"
            inp.write_text("company_id,company_name,website_url\nacme,Acme Air,https://acme.example.com\n",
                           encoding="utf-8")
            proc = run(self.SCRIPT + ["--retriever", "filedrop", "--input", str(inp), "--pages-root",
                                      str(tmp / "pages"), "--out-root", str(tmp / "out")])
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("counts: complete=1 partial=0 blocked=0", proc.stdout)
            run_dir = next((tmp / "out").iterdir())
            manifest = json.loads((run_dir / "run.json").read_text())
            self.assertIs(manifest["fixture_mode"], False)
            self.assertEqual(manifest["overall_status"], "completed")


if __name__ == "__main__":
    unittest.main()

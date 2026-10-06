import copy
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import constants  # noqa: E402
from scripts import check_env, validate_workflows as vw  # noqa: E402

WF = ROOT / "workflows"


class ValidateWorkflowsTest(unittest.TestCase):
    def load(self, stem):
        return json.loads((WF / f"{stem}.json").read_text(encoding="utf-8"))

    def test_real_workflows_pass(self):
        errs, checked = vw.validate_dir(WF)
        self.assertEqual(errs, [])
        self.assertEqual(checked, 9)

    def test_main_passes_on_repo(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = vw.main([])
        self.assertEqual(code, 0, buf.getvalue())
        self.assertIn("Validated 9 workflow files", buf.getvalue())
        self.assertIn("Secret scan of automation-suite: 0 finding(s)", buf.getvalue())

    def assert_finding(self, wf, fragment, automation=True):
        errs = vw.validate_workflow(wf, "x.json", automation)
        self.assertTrue(any(fragment in e for e in errs), errs)

    def test_mutations_are_caught(self):
        base = self.load("01_voice_call_agent")
        cases = []
        wf = copy.deepcopy(base); del wf["meta"]; cases.append((wf, "missing top-level key 'meta'"))
        wf = copy.deepcopy(base); wf["meta"]["verified"] = "no"; cases.append((wf, "meta.verified must be present and boolean"))
        wf = copy.deepcopy(base); wf["meta"]["verified"] = True; cases.append((wf, "must be false"))
        wf = copy.deepcopy(base); wf["meta"]["source_line"] = "17"; cases.append((wf, "source_line must be an int"))
        wf = copy.deepcopy(base); wf["settings"].pop("errorWorkflow"); cases.append((wf, "errorWorkflow"))
        wf = copy.deepcopy(base); wf["nodes"][1]["name"] = wf["nodes"][0]["name"]; cases.append((wf, "duplicate node names"))
        wf = copy.deepcopy(base); wf["nodes"][2]["notes"] = " "; cases.append((wf, "has no notes"))
        wf = copy.deepcopy(base); wf["nodes"][2]["type"] = "n8n-nodes-base.mystery"; cases.append((wf, "no offline handler"))
        wf = copy.deepcopy(base); wf["connections"]["Call Webhook"]["main"][0][0]["node"] = "Ghost"
        cases.append((wf, "unknown node 'Ghost'"))
        wf = copy.deepcopy(base)
        next(n for n in wf["nodes"] if n["name"] == "Transfer Call (Twilio)")["parameters"]["url"] = "https://evil.invalid/x"
        cases.append((wf, "no offline adapter"))
        wf = copy.deepcopy(base)
        next(n for n in wf["nodes"] if n["name"] == "Call Agent")["parameters"]["promptVariables"].pop("business_name")
        cases.append((wf, "promptVariables missing ['business_name']"))
        wf = copy.deepcopy(base)
        next(n for n in wf["nodes"] if n["name"] == "Call Agent")["parameters"]["promptId"] = "99_missing"
        cases.append((wf, "no prompt file"))
        wf = copy.deepcopy(base)
        wf["connections"]["Compose Confirmation"]["main"][0] = [{"node": "Send Confirmation Email", "type": "main", "index": 0}]
        wf["nodes"] = [n for n in wf["nodes"] if n["name"] != "Pricing Guard (confirmation)"]
        wf["connections"].pop("Pricing Guard (confirmation)")
        cases.append((wf, "no pricing guard upstream"))
        for wf, fragment in cases:
            with self.subTest(fragment=fragment):
                self.assert_finding(wf, fragment)

    def test_directory_level_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            for p in WF.glob("*.json"):
                shutil.copy(p, d / p.name)
            (d / "08_avatar_generator.json").unlink()
            (d / "03_ugc_ads_spy.json").write_text("{not json", encoding="utf-8")
            errs, _ = vw.validate_dir(d)
            self.assertTrue(any("expected 8 automation workflows, found 7" in e for e in errs))
            self.assertTrue(any("invalid JSON" in e for e in errs))

    def test_secret_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "clean.py").write_text(f"API_KEY = ''\nGHL = '{constants.GHL_BUILD_LOCATION_ID}'\n"
                                        "name = 'token_count'\n", encoding="utf-8")
            self.assertEqual(vw.scan_secrets(d), [])
            fake = "sk-" + "AbC123dEf456GhI789jKl0"
            (d / "a.py").write_text(f"x = '{fake}'\n", encoding="utf-8")
            (d / "b.json").write_text('{"api_token": "' + "aB3" * 10 + '"}\n', encoding="utf-8")
            (d / "c.md").write_text("call " + "866" + "-566-" + "3445\n", encoding="utf-8")
            (d / ".env").write_text("X=1\n", encoding="utf-8")
            (d / "out").mkdir()
            (d / "out" / "ignored.txt").write_text("xoxb-" + "1234567890-abcdef", encoding="utf-8")
            findings = vw.scan_secrets(d)
            joined = "\n".join(findings)
            self.assertIn("a.py:1: secret-like prefix", joined)
            self.assertIn("b.json:1: long mixed alphanumeric run near 'token'", joined)
            self.assertIn("forbidden phone number", joined)
            self.assertIn(".env is present", joined)
            self.assertNotIn("ignored.txt", joined)
            self.assertEqual(len(findings), 4)
            self.assertNotIn(fake, joined)  # findings never echo the full secret


class CheckEnvTest(unittest.TestCase):
    def setUp(self):
        self.saved = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.saved)

    def test_reports_set_missing_never_values(self):
        value = "value-that-must-never-print-123"
        os.environ["OPENAI_API_KEY"] = value
        os.environ.pop("DRY_RUN", None)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = check_env.main()
        out = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertNotIn(value, out)
        self.assertRegex(out, r"OPENAI_API_KEY\s+SET")
        self.assertRegex(out, r"VAPI_API_KEY\s+MISSING\s+APPROVAL")
        self.assertIn("Mode: DRY_RUN", out)

    def test_ghl_mismatch_warning_and_live_refusal(self):
        os.environ["GHL_LOCATION_ID"] = constants.GHL_BUILD_LOCATION_ID.lower()
        os.environ["DRY_RUN"] = "false"
        os.environ.pop("ALLOW_LIVE", None)
        buf = io.StringIO()
        import contextlib
        with redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = check_env.main()
        self.assertEqual(code, 2)
        self.assertIn("case-sensitive", buf.getvalue())


if __name__ == "__main__":
    unittest.main()

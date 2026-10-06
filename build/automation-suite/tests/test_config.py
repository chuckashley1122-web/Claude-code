import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import constants, settings  # noqa: E402


class ConstantsTest(unittest.TestCase):
    def test_locked_commercial_terms(self):
        self.assertEqual(constants.TECH_FEE_MONTHLY_USD, 650)
        self.assertEqual(constants.SETUP_FEE_USD, 0)
        self.assertEqual(constants.PER_BOOKED_APPOINTMENT_MIN_USD, 250)
        self.assertEqual(constants.PER_BOOKED_APPOINTMENT_MAX_USD, 300)

    def test_locked_facts_and_gates(self):
        self.assertEqual(constants.BOOKING_URL, "https://ca-jenterprises.com/ai")
        self.assertTrue(constants.MEETING_FIRST)
        self.assertTrue(constants.DRY_RUN)
        self.assertEqual(constants.SPEND_CAP_USD, 0.00)
        self.assertEqual(constants.OWNER_NAME, "Chuck Ashley")
        self.assertEqual(constants.LEGAL_ENTITY, "CA&J Enterprises LLC")
        for gate in ("SPEND", "OUTBOUND", "PUBLISH", "GHL"):
            self.assertIs(getattr(constants, f"REQUIRE_HUMAN_APPROVAL_FOR_{gate}"), True)
        self.assertEqual(constants.DAILY_EMAIL_CAP_PER_INBOX, 30)
        self.assertEqual(constants.FOLLOWUP_SEQUENCE_MAX, 2)

    def test_ghl_location_id_byte_identical(self):
        text = (ROOT / "config" / "constants.py").read_text(encoding="utf-8")
        self.assertIn('GHL_BUILD_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"', text)

    def test_docstring_rules(self):
        doc = constants.__doc__.lower()
        self.assertIn("case-sensitive", doc)
        self.assertIn("ui-only", doc)
        self.assertIn("no charges or purchases", doc)

    def test_workflow_vars_exclude_prices(self):
        v = constants.workflow_vars()
        self.assertNotIn("TECH_FEE_MONTHLY_USD", v)
        self.assertFalse(any("USD" in k or "FEE" in k for k in v))
        self.assertEqual(v["BOOKING_URL"], constants.BOOKING_URL)


class SettingsTest(unittest.TestCase):
    def load(self, env):
        with tempfile.TemporaryDirectory() as tmp:
            return settings.load_settings(env, Path(tmp) / ".env")

    def test_dry_run_defaults_true(self):
        self.assertTrue(self.load({}).dry_run)
        self.assertTrue(self.load({"DRY_RUN": "garbage"}).dry_run)
        self.assertFalse(self.load({"DRY_RUN": "false"}).dry_run)

    def test_parse_bool(self):
        self.assertTrue(settings.parse_bool("YES", False))
        self.assertFalse(settings.parse_bool("0", True))
        self.assertTrue(settings.parse_bool(None, True))

    def test_live_refused_without_allow_live(self):
        s = self.load({"DRY_RUN": "false"})
        buf = io.StringIO()
        with self.assertRaises(settings.LiveModeRefused) as cm:
            settings.enforce_run_mode(s, buf)
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("REFUSED", buf.getvalue())

    def test_live_allowed_only_with_allow_live_1(self):
        settings.enforce_run_mode(self.load({"DRY_RUN": "false", "ALLOW_LIVE": "1"}), io.StringIO())
        with self.assertRaises(settings.LiveModeRefused):
            settings.enforce_run_mode(self.load({"DRY_RUN": "false", "ALLOW_LIVE": "true"}), io.StringIO())

    def test_require_credential_fails_closed(self):
        s = self.load({})
        with self.assertRaises(settings.MissingCredential) as cm:
            settings.require_credential("OPENAI_API_KEY", s)
        self.assertIn("BLOCKED", str(cm.exception))
        self.assertIn("human action required", str(cm.exception).lower())
        value = "fixture-value-not-a-secret"
        s2 = self.load({"OPENAI_API_KEY": value})
        self.assertEqual(settings.require_credential("OPENAI_API_KEY", s2), value)

    def test_env_status_never_returns_values(self):
        value = "fixture-value-not-a-secret"
        status = settings.env_status(self.load({"HUBSPOT_TOKEN": value}))
        self.assertEqual(status["HUBSPOT_TOKEN"], "SET")
        self.assertEqual(status["OPENAI_API_KEY"], "MISSING")
        self.assertNotIn(value, repr(status))
        self.assertNotIn(value, repr(self.load({"HUBSPOT_TOKEN": value})))

    def test_env_file_parsing_and_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / ".env"
            env.write_text("# comment\nDRY_RUN=false\nSLACK_WEBHOOK_URL='https://hooks.example.com/x'\nbad line\n",
                           encoding="utf-8")
            parsed = settings.parse_env_file(env)
            self.assertEqual(parsed["SLACK_WEBHOOK_URL"], "https://hooks.example.com/x")
            self.assertNotIn("bad line", parsed)
            s = settings.load_settings({"DRY_RUN": "true"}, env)
            self.assertTrue(s.dry_run)  # process env wins over .env

    def test_ghl_location_case_sensitive(self):
        self.assertIsNone(settings.ghl_location_mismatch(self.load({"GHL_LOCATION_ID": constants.GHL_BUILD_LOCATION_ID})))
        self.assertIsNotNone(settings.ghl_location_mismatch(
            self.load({"GHL_LOCATION_ID": constants.GHL_BUILD_LOCATION_ID.lower()})))

    def test_env_example_lists_exactly_spec_names_with_empty_values(self):
        lines = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
        pairs = [l.split("=", 1) for l in lines if l and not l.startswith("#")]
        self.assertEqual([k for k, _ in pairs], list(settings.ENV_VAR_NAMES))
        self.assertTrue(all(v == "" for _, v in pairs))
        self.assertEqual(len(settings.ENV_VAR_NAMES), 31)

    def test_gitignore(self):
        gi = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
        for entry in (".env", "data/out/", "*.log", ".venv/", "__pycache__/"):
            self.assertIn(entry, gi)
        self.assertFalse((ROOT / ".env").exists())


if __name__ == "__main__":
    unittest.main()

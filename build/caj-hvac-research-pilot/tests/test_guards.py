"""Price scanner, source-claim scanner, brand guard, release gate refusals, Meta tripwire, scripts."""

import contextlib
import csv
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_env  # noqa: E402
import config  # noqa: E402
import repo_scan  # noqa: E402
from src import guards  # noqa: E402
from src.guards import GateEvidence, release_gate_status  # noqa: E402
from src.output_validation import validate_run_dir  # noqa: E402
from src.pipeline import run_pipeline  # noqa: E402
from src.retrieval import FixtureRetriever  # noqa: E402

ALL_PASS = {f"T0{i}": True for i in range(1, 9)}


class PriceScanner(unittest.TestCase):
    def test_flags_price_tokens(self):
        for text in ("Only $650/mo", "650 USD", "250 dollars", "see our pricing", "no setup fee",
                     "billed per month", "a monthly plan", "low cost", "price list", "USD 300"):
            with self.subTest(text=text):
                self.assertTrue(guards.scan_for_prices(text), text)

    def test_returns_offending_span(self):
        text = "Try it for $650/mo today"
        f = guards.scan_for_prices(text)[0]
        self.assertEqual(text[f.start:f.end], f.text)
        self.assertEqual(f.text, "$650/mo")

    def test_clean_copy_passes(self):
        self.assertEqual(guards.scan_for_prices(
            "If a contact form is confirmed, then test a shorter form. Call (512) 555-0142."), [])

    def test_injected_price_blocked_in_hypothesis_cell_and_brief(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = run_pipeline(ROOT / "inputs" / "companies.csv", FixtureRetriever(ROOT / "tests" / "fixtures"),
                                  Path(tmp), fixture_mode=True, use_fixture_demo_when_empty=True)
            run_dir = report.run_dir
            self.assertEqual(validate_run_dir(run_dir), [])
            injected = "$650/mo"
            csv_path = run_dir / "results.csv"
            with open(csv_path, encoding="utf-8", newline="") as fh:
                rows = list(csv.reader(fh))
            rows[1][9] = rows[1][9][:-1] + f" at {injected}."
            with open(csv_path, "w", encoding="utf-8", newline="") as fh:
                csv.writer(fh).writerows(rows)
            findings = validate_run_dir(run_dir)
            self.assertTrue(any("fixture-a.hypothesis: price token" in f for f in findings), findings)
            brief = run_dir / "brief.md"
            brief.write_text(brief.read_text(encoding="utf-8") + f"\nOffer: {injected}\n", encoding="utf-8")
            self.assertTrue(any(f.startswith("brief.md: price token '$650/mo'") for f in validate_run_dir(run_dir)))


class SourceClaimAndBrandScanners(unittest.TestCase):
    def test_flags_presenter_claims(self):
        for text in ("Build an MVP in one hour", "about 50 automations a year", "improve over seven days",
                     "our Agent OS", "a one-hour MVP"):
            with self.subTest(text=text):
                self.assertTrue(guards.scan_for_source_claims(text))
        self.assertEqual(guards.scan_for_source_claims("Serving Round Rock."), [])

    def test_consumer_brands_blocked_in_b2b_output(self):
        for text in ("Visit Chuck’s Daily Grind", "our Etsy shop", "new printables"):
            self.assertTrue(guards.scan_for_consumer_brands(text), text)
        self.assertEqual(guards.scan_for_consumer_brands("CA-J Enterprises research brief"), [])

    def test_brand_leak_into_brief_fails_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = run_pipeline(ROOT / "inputs" / "companies.csv", FixtureRetriever(ROOT / "tests" / "fixtures"),
                                  Path(tmp), fixture_mode=True, use_fixture_demo_when_empty=True)
            brief = report.run_dir / "brief.md"
            brief.write_text(brief.read_text(encoding="utf-8") + "\nSee our Etsy shop.\n", encoding="utf-8")
            self.assertTrue(any("consumer brand" in f for f in validate_run_dir(report.run_dir)))


class ReleaseGate(unittest.TestCase):
    def test_never_v1_without_every_gate(self):
        full = dict(file_ops_ok=True, tests_passed=ALL_PASS, real_runs_validated=2, live_pilots_source_checked=1,
                    latest_two_runs_valid=True, seven_day_entries=7, user_review_received=True)
        self.assertEqual(release_gate_status(GateEvidence(**full)), "V1_READY")
        removals = {
            "live_pilots_source_checked": 0,
            "latest_two_runs_valid": False,
            "seven_day_entries": 6,
            "real_runs_validated": 0,
            "tests_passed": {**ALL_PASS, "T08": False},
            "file_ops_ok": False,
        }
        for key, bad in removals.items():
            with self.subTest(missing=key):
                self.assertNotEqual(release_gate_status(GateEvidence(**{**full, key: bad})), "V1_READY")

    def test_honest_lower_statuses(self):
        self.assertEqual(release_gate_status(GateEvidence(file_ops_ok=False)), "ENVIRONMENT_BLOCKED")
        self.assertEqual(release_gate_status(GateEvidence(file_ops_ok=True)), "SPECIFICATION_READY")
        fixtures_only = GateEvidence(file_ops_ok=True, tests_passed=ALL_PASS)
        self.assertEqual(release_gate_status(fixtures_only), "SPECIFICATION_READY")
        real = GateEvidence(file_ops_ok=True, tests_passed=ALL_PASS, real_runs_validated=1)
        self.assertEqual(release_gate_status(real), "MVP_TESTED")
        started = GateEvidence(file_ops_ok=True, tests_passed=ALL_PASS, real_runs_validated=1, seven_day_entries=3)
        self.assertEqual(release_gate_status(started), "PILOT_IN_PROGRESS")
        no_feedback = GateEvidence(file_ops_ok=True, tests_passed=ALL_PASS, real_runs_validated=2,
                                   live_pilots_source_checked=1, latest_two_runs_valid=True, seven_day_entries=7)
        self.assertEqual(release_gate_status(no_feedback), "USER_REVIEW_PENDING")

    def test_status_is_always_a_handoff_status(self):
        for ev in (GateEvidence(file_ops_ok=False), GateEvidence(file_ops_ok=True, tests_passed=ALL_PASS)):
            self.assertIn(release_gate_status(ev), config.HANDOFF_STATUSES)


class FrozenCampaignTripwire(unittest.TestCase):
    def test_fires_for_every_action(self):
        for action in ("read", "edit", "pause", "duplicate", "delete", "budget"):
            with self.subTest(action=action), self.assertRaises(guards.FrozenCampaignViolation):
                guards.assert_meta_campaign_untouched(config.FROZEN_META_CAMPAIGN_ID, action)

    def test_other_ids_pass_through(self):
        self.assertIsNone(guards.assert_meta_campaign_untouched("SOME_OTHER_CAMPAIGN", "read"))

    def test_config_freeze_constants(self):
        self.assertEqual(config.FROZEN_META_CAMPAIGN_ID, "CAJ_HVAC27_US_PURCHASE_TEST02")
        self.assertFalse(config.FROZEN_META_CAMPAIGN_EDITABLE)


class LockedConfig(unittest.TestCase):
    def test_gates_and_terms(self):
        self.assertTrue(config.DRY_RUN)
        self.assertFalse(config.ALLOW_LIVE or config.ALLOW_NETWORK_RETRIEVAL or config.SEND_ENABLED
                         or config.GHL_WRITES_ENABLED)
        self.assertEqual(config.SPEND_CAP_USD, 0.0)
        self.assertEqual((config.TECH_FEE_MONTHLY_USD, config.SETUP_FEE_USD, config.PER_BOOKED_APPOINTMENT_MIN_USD,
                          config.PER_BOOKED_APPOINTMENT_MAX_USD), (650, 0, 250, 300))
        self.assertEqual(config.BOOKING_URL, "https://ca-jenterprises.com/ai")
        self.assertEqual(config.GHL_BUILD_LOCATION_ID, "UWc5vKBgFVPdxNTRAy2s")
        self.assertEqual(config.OWNER_PHONE, "512-229-9199")
        self.assertEqual(config.MISSING_LABEL, "Not found in reviewed pages")
        for kw in ("AC repair", "AC installation", "heating maintenance", "furnace repair", "heat pump",
                   "duct cleaning", "HVAC installation", "emergency HVAC"):
            self.assertIn(kw, config.AC_SERVICE_KEYWORDS)

    def test_env_flag_parsing(self):
        self.assertTrue(config.env_flag("X", False, {"X": "1"}))
        self.assertFalse(config.env_flag("X", True, {"X": "false"}))
        self.assertTrue(config.env_flag("X", True, {"X": "  "}))


class Scripts(unittest.TestCase):
    def test_check_env_never_prints_values(self):
        sentinel = "do-not-print-this-value-123"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            check_env.main({"ALLOW_LIVE": sentinel})
        out = buf.getvalue()
        self.assertNotIn(sentinel, out)
        self.assertIn("ALLOW_LIVE: SET", out)
        self.assertIn("DRY_RUN: MISSING", out)
        self.assertEqual(len([ln for ln in out.splitlines() if ln.endswith(("SET", "MISSING"))]), len(config.ENV_VARS))

    def test_repo_scan_passes_on_project_root(self):
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            code = repo_scan.main(ROOT)
        self.assertEqual(code, 0, buf.getvalue())
        self.assertIn("FrozenCampaignViolation raised", buf.getvalue())

    def test_repo_scan_finds_planted_problems(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            fake_key = "sk" + "-" + "A1b2C3d4E5" + "f6G7h8J9k0"
            wrong_id = "Zz9" + "QwErTy" + "UiOp1234AsDf"[:11]
            mangled = config.GHL_BUILD_LOCATION_ID.lower()
            (tmp / "leak.txt").write_text(f"{fake_key}\n{wrong_id}\n{mangled}\n", encoding="utf-8")
            (tmp / ".env").write_text("", encoding="utf-8")
            findings = repo_scan.scan_root(tmp)
            joined = "\n".join(findings)
            self.assertIn("openai-style key", joined)
            self.assertIn("unexpected GHL-location-like ID", joined)
            self.assertIn("case-mangled GHL location ID", joined)
            self.assertIn(".env exists", joined)
            self.assertIn(".gitignore does not list .env", joined)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(repo_scan.main(tmp), 1)


class BannedPhrases(unittest.TestCase):
    """No banned phrase appears in any file of the build root (strings built at runtime)."""

    def test_no_banned_phrases_in_tree(self):
        banned = ["qualified" + " appointment", "shows" + " up", "10-25" + " leads/month",
                  "10–" + "25 leads/month", "866" + "-566-3445"]
        for path in ROOT.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and "outputs" not in path.relative_to(ROOT).parts:
                text = path.read_text(encoding="utf-8", errors="ignore").lower()
                for phrase in banned:
                    self.assertNotIn(phrase.lower(), text, f"{phrase!r} in {path}")


if __name__ == "__main__":
    unittest.main()

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from tools import state, validate_config  # noqa: E402
from tools.paths import BUILD_ROOT, default_paths, scratch_paths  # noqa: E402


class StateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.paths = scratch_paths(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_status_enum_values(self):
        self.assertEqual([s.value for s in state.STATUS],
                         ["Not started", "Draft", "Tested", "Ready for human action", "Published-by-human",
                          "Blocked"])

    def test_no_script_may_set_published(self):
        with self.assertRaises(state.StatusNotAllowed):
            state.mark_asset("x", "out/x.md", state.STATUS.PUBLISHED_BY_HUMAN, paths=self.paths)
        with self.assertRaises(state.StatusNotAllowed):
            state.log("k", "v", "s", "Published-by-human", self.paths)
        with self.assertRaises(state.StatusNotAllowed):
            state.log("k", "v", "s", "Deployed", self.paths)

    def test_log_is_append_only_and_idempotent(self):
        self.assertTrue(state.log("k", "v1", "src", state.STATUS.DRAFT, self.paths))
        self.assertFalse(state.log("k", "v1", "src", state.STATUS.DRAFT, self.paths))
        self.assertTrue(state.log("k", "v2", "src", state.STATUS.DRAFT, self.paths))
        entries = state.read_decision_log(self.paths)
        self.assertEqual([e["value"] for e in entries], ["v1", "v2"])
        self.assertEqual(set(entries[0]), {"timestamp", "key", "value", "source", "status"})

    def test_blockers_and_assets(self):
        state.record_blocker("domain", "owned domain", "canonicals", "confirm", self.paths)
        self.assertEqual(state.blockers(self.paths)["domain"]["missing_input"], "owned domain")
        state.mark_asset("a1", self.paths.out / "a.md", state.STATUS.DRAFT, paths=self.paths)
        reg = json.loads(self.paths.asset_register.read_text())
        self.assertEqual(reg["a1"], {"id": "a1", "path": "out/a.md", "status": "Draft", "owner": "build"})


class ValidateConfigTests(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((BUILD_ROOT / "config" / "build_config.json").read_text())

    def failed(self, **overrides):
        k = validate_config.constants_namespace(**overrides)
        return [name for name, ok, _ in validate_config.run_checks(k, self.cfg) if not ok]

    def test_shipped_constants_pass(self):
        self.assertEqual(self.failed(), [])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(validate_config.main([], default_paths()), 0)
        self.assertIn("17/17 checks passed", out.getvalue())

    def test_each_violation_detected(self):
        cases = {
            "GHL_LOCATION_ID exact": {"GHL_LOCATION_ID": C.GHL_LOCATION_ID.lower()},
            "BOOKING_URL": {"BOOKING_URL": "https://example.com/other"},
            "NO_SPEND_DEFAULT is True": {"NO_SPEND_DEFAULT": False},
            "AD_SPEND_CAP_USD == 0": {"AD_SPEND_CAP_USD": 5},
            "PUBLISH_AUTHORITY == none": {"PUBLISH_AUTHORITY": "agent"},
            "SITE_PUBLISH_APPROVED needs approval ref": {"SITE_PUBLISH_APPROVED": True},
            "DOMAIN_PURCHASE_APPROVED needs approval ref": {"DOMAIN_PURCHASE_APPROVED": True},
            "FROZEN_CAMPAIGN_PROTECTED is True": {"FROZEN_CAMPAIGN_PROTECTED": False},
            "QUOTE_PRICE_IN_MESSAGE is False": {"QUOTE_PRICE_IN_MESSAGE": True},
            "LOGO_NEVER_FIRST is True": {"LOGO_NEVER_FIRST": False},
            "inquiry bounds": {"MAX_NAME_LEN": 5000},
        }
        for check, override in cases.items():
            with self.subTest(check=check):
                self.assertIn(check, self.failed(**override))
        self.assertIn("inquiry bounds", self.failed(MAX_RETRIES=None))
        self.assertNotIn("SITE_PUBLISH_APPROVED needs approval ref",
                         self.failed(SITE_PUBLISH_APPROVED=True, SITE_PUBLISH_APPROVAL_REF="email 2026-10-05"))

    def test_disallowed_location_as_target(self):
        cfg = dict(self.cfg, ghl_project_id=C.DISALLOWED_LOCATION_ID)
        k = validate_config.constants_namespace()
        failed = [n for n, ok, _ in validate_config.run_checks(k, cfg) if not ok]
        self.assertIn("DISALLOWED_LOCATION_ID not a target", failed)

    def test_constants_file_has_exact_location_line(self):
        text = (BUILD_ROOT / "config" / "constants.py").read_text()
        self.assertIn('GHL_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"', text)
        self.assertEqual((C.AD_SPEND_CAP_USD, C.TOTAL_BUILD_SPEND_USD, C.DOMAIN_PURCHASE_APPROVED,
                          C.SITE_PUBLISH_APPROVED), (0, 0, False, False))
        self.assertEqual((C.TECH_FEE_MONTHLY_USD, C.SETUP_FEE_USD, C.PER_BOOKED_APPOINTMENT_MIN_USD,
                          C.PER_BOOKED_APPOINTMENT_MAX_USD), (650, 0, 250, 300))

    def test_build_config_key_set(self):
        expected = ("build_mode, site_origin, business_name, primary_location, service_areas, services_verified, "
                    "primary_service, additional_services, main_offer, offer_url, primary_cta, cta_destination, "
                    "phone, contact_email, logo_path, hero_image_path, og_image_path, review_rating, review_count, "
                    "years_in_business, customers_served, guarantee, license_info, privacy_policy_url, "
                    "ghl_project_id, ghl_project_name, ghl_form_id, ghl_draft_url, ghl_live_url, ghl_version_id, "
                    "ai_studio_ssr_supported, ghl_api_version, ghl_api_scopes, ghl_pipeline_id, ghl_stage_id, "
                    "ghl_custom_field_ids, search_console_property, analytics_id, a2p_status, dns_records")
        self.assertEqual(list(self.cfg), expected.split(", "))

    def test_env_example_names_only(self):
        lines = (BUILD_ROOT / ".env.example").read_text().splitlines()
        assignments = [l for l in lines if "=" in l and not l.startswith("#")]
        self.assertEqual(len(assignments), 21)
        self.assertTrue(all(l.endswith("=") for l in assignments))
        self.assertTrue(lines[0].startswith("# Never commit real values"))


if __name__ == "__main__":
    unittest.main()

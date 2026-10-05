"""Acceptance criteria (spec section 7) checked against a full build in a temp root,
plus repository-wide string checks on the committed build root."""
import contextlib
import hashlib
import io
import json
import re
import shutil
import unittest
from pathlib import Path

import _util
from config import constants as C
from tools import build_all, compliance_scan
from tools import guardrails as G

SPEC_PATHS = [
    "README.md", ".env.example", "config/build_config.json", "config/decision_log.jsonl", "config/asset_register.json",
    "config/constants.py", "tools/state.py", "tools/guardrails.py", "tools/validate_config.py", "tools/break_even.py",
    "tools/margin_model.py", "tools/compliance_scan.py", "tools/build_all.py", "tools/run_tests.py",
    "src/niche_brief.py", "src/offer_spec.py", "src/positioning.py", "src/risk_reversal.py", "src/crm_schema.py",
    "src/calendar_spec.py", "src/creative_pack.py", "src/copy_pack.py", "src/form_spec.py", "src/integration_spec.py",
    "src/workflow_specs.py", "src/message_templates.py", "src/precall_page.py", "src/sales_guide.py",
    "src/onboarding_pack.py", "src/delivery_scope.py", "src/launch_review.py",
    "out/economics/client_break_even.md", "out/economics/agency_margin.md", "out/tests/test_log.md",
    "out/niche_brief.md", "out/offer_spec.md", "out/positioning.md", "out/risk_reversal.md", "out/ghl_pipeline_spec.md",
    "out/ghl_custom_fields.json", "out/calendar_spec.md", "out/form_spec.md", "out/qualification_logic.json",
    "out/ghl_facebook_integration.md", "out/field_map.json", "out/workflows/01-intake.md", "out/workflows/02-unbooked.md",
    "out/workflows/03-booked.md", "out/workflows/04-outcome.md", "out/messages/booking_ack.md", "out/messages/confirmation.md",
    "out/messages/reminder_sms.md", "out/messages/no_show.md", "out/precall_page/index.html", "out/sales_call_guide.md",
    "out/close_pack.md", "out/welcome_page/index.html", "out/intake_form.json", "out/delivery_scope.md",
    "out/launch_review.md", "out/asset_register.md", "ui-tasks/GHL-BUILD-CHECKLIST.md", "ui-tasks/META-BUILD-CHECKLIST.md",
    "ui-tasks/HUMAN-DECISIONS.md", "logs/build.log",
] + [f"out/tests/T{i:02d}.json" for i in range(1, 15)] + [f"out/creatives/A0{i}.{x}" for i in range(1, 6) for x in ("md", "json")] \
  + [f"out/copy/A0{i}.md" for i in range(1, 6)]
TEXT_SUFFIXES = {".py", ".md", ".json", ".jsonl", ".html", ".example", ".log", ".gitignore", ""}


def text_files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and (p.suffix in TEXT_SUFFIXES or p.name.startswith(".")):
            yield p


class BuildOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = _util.built_temp_root()
        for rel in ("README.md", "config/constants.py", "tools", "src"):
            src = _util.ROOT / rel
            dst = cls.root / rel
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy2(src, dst)
        cls.out = cls.root / "out"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def read(self, rel):
        return (self.root / rel).read_text(encoding="utf-8")

    def test_every_spec_path_exists(self):
        missing = [p for p in SPEC_PATHS if not (self.root / p).exists()]
        self.assertEqual(missing, [])

    def test_compliance_scan_clean(self):
        report = compliance_scan.scan_tree(self.root)
        hits = [h for hs in report.values() for h in hs]
        self.assertGreater(len(report), 60)
        self.assertEqual(hits, [])

    def test_creatives_logo_not_first(self):
        for i in range(1, 6):
            rec = json.loads(self.read(f"out/creatives/A0{i}.json"))
            G.assert_logo_not_first(rec)
            first = sorted(rec["visual_direction"], key=lambda e: e["order"])[0]["element"]
            self.assertIn(first, ("outcome_headline", "offer_line"))
            self.assertEqual(rec["proof_points"], "NONE")

    def test_meeting_first_assets(self):
        files = list((self.out / "messages").glob("*.md")) + list((self.out / "copy").glob("*.md")) + [self.out / "form_spec.md"]
        self.assertGreaterEqual(len(files), 10)
        for p in files:
            G.assert_meeting_first(p.read_text(encoding="utf-8"))

    def test_dollar_figures_absent_in_prospect_assets(self):
        for d in ("creatives", "copy", "messages"):
            for p in (self.out / d).iterdir():
                for ln in p.read_text(encoding="utf-8").splitlines():
                    if G.find_currency(ln):
                        self.assertIn("assumption", ln.lower(), f"{p}: {ln}")
        self.assertEqual(G.find_currency(self.read("out/form_spec.md")), [])

    def test_committed_config_spend_flags(self):
        cfg = json.loads((_util.ROOT / "config" / "build_config.json").read_text())
        self.assertEqual(cfg["ad_spend_cap_usd"], 0)
        self.assertIs(cfg["approval_ad_spend"], False)
        self.assertEqual(C.AD_SPEND_CAP_USD, 0)
        self.assertIs(C.APPROVAL_AD_SPEND, False)

    def test_test_log_has_exactly_t01_to_t14(self):
        log = self.read("out/tests/test_log.md")
        ids = re.findall(r"^\| (T\d\d) \| (\w+) \|", log, re.M)
        self.assertEqual([i for i, _ in ids], [f"T{i:02d}" for i in range(1, 15)])
        self.assertTrue(all(v in ("PASS", "FAIL", "BLOCKED") for _, v in ids))
        for i in range(1, 15):
            d = json.loads(self.read(f"out/tests/T{i:02d}.json"))
            self.assertEqual(set(d) >= {"test_id", "input", "expected_result", "actual_result", "evidence_path", "verdict"}, True)
            self.assertTrue((self.root / d["evidence_path"]).exists())
            if d["verdict"] == "BLOCKED":
                self.assertTrue(d["blocked_missing_input"])
            self.assertNotEqual(d["verdict"], "FAIL")

    def test_no_live_or_ready_status(self):
        assets = json.loads(self.read("config/asset_register.json"))["assets"]
        self.assertTrue(assets)
        self.assertFalse([a for a in assets if a["status"] in ("Live", "Ready for launch")])
        for line in self.read("config/decision_log.jsonl").splitlines():
            self.assertNotIn(json.loads(line)["status"], ("Live", "Ready for launch"))

    def test_ui_checklist_items_complete(self):
        for name in ("GHL-BUILD-CHECKLIST.md", "META-BUILD-CHECKLIST.md"):
            text = self.read(f"ui-tasks/{name}")
            blocks = text.split("\n### ")[1:]
            self.assertGreater(len(blocks), 10)
            for b in blocks:
                for field in ("- Object:", "- Field:", "- Value:", f"- Target location: `{C.GHL_LOCATION_ID}`", "- Verify by:", "- Status: Not started"):
                    self.assertIn(field, b, f"{name}: {b[:60]}")
        meta = self.read("ui-tasks/META-BUILD-CHECKLIST.md")
        top = meta.split("### ")[0]
        self.assertIn(C.FROZEN_CAMPAIGN_NAME, top)
        self.assertIn("FROZEN", top)
        self.assertIn("learning phase", top)
        for b in meta.split("\n### ")[1:] + self.read("ui-tasks/GHL-BUILD-CHECKLIST.md").split("\n### ")[1:]:
            if "budget" in b.lower() or "payment method" in b.lower():
                self.assertIn("REQUIRES EXPLICIT HUMAN APPROVAL", b)

    def test_break_even_and_risk_reversal(self):
        be = self.read("out/economics/client_break_even.md")
        self.assertIn("required_leads = ceil(required_held / lead_to_held_rate)", be)
        self.assertIn("| required_leads | 10 |", be)
        self.assertIn("Default policy: No numerical guarantee.", self.read("out/risk_reversal.md"))
        self.assertIn("margin cannot be modeled with current inputs", self.read("out/economics/agency_margin.md"))

    def test_no_testimonial_or_case_study_claims(self):
        for p in self.out.rglob("*"):
            if not p.is_file() or p.suffix not in (".md", ".json", ".html"):
                continue
            text = p.read_text(encoding="utf-8")
            inside = False
            for ln in text.splitlines():
                if "DO-NOT-USE-AS-PROOF:START" in ln:
                    inside = True
                low = ln.lower()
                if not inside and ("testimonial" in low or "case stud" in low):
                    self.assertTrue(re.search(r"\b(no|not|never|unavailable)\b", low), f"{p}: {ln}")
                if "DO-NOT-USE-AS-PROOF:END" in ln:
                    inside = False

    def test_human_decisions_cover_every_needs_evidence(self):
        hd = self.read("ui-tasks/HUMAN-DECISIONS.md")
        cfg = json.loads(self.read("config/build_config.json"))
        for k, v in cfg.items():
            if v == C.NEEDS_EVIDENCE:
                self.assertRegex(hd, rf"\| {k} \| .+ \| {C.OWNER_NAME} \|")
        blockers = json.loads(self.read("out/blockers.json"))
        sources = {b["source_file"] for b in blockers}
        for b in blockers:
            self.assertTrue(b["next_action"] and b["owner"])
            self.assertIn(f"| {b['item']} |", hd)
        uncovered = []
        for p in self.out.rglob("*"):
            if not p.is_file() or "NEEDS_EVIDENCE" not in p.read_text(encoding="utf-8") or p.name in ("blockers.json",) or "evidence" in p.parts:
                continue
            rel = p.relative_to(self.root).as_posix()
            stem = rel.rsplit(".", 1)[0]
            if not any(rel == s or (s.endswith("/") and rel.startswith(s)) or s.rsplit(".", 1)[0] == stem for s in sources):
                uncovered.append(rel)
        self.assertEqual(uncovered, [])

    def test_readme_states_nothing_launched(self):
        readme = (_util.ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Nothing was launched", readme)
        self.assertIn("No GHL, Meta or payment object was touched", readme)
        for cmd in ("python tools/build_all.py", "python tools/run_tests.py", "python tools/compliance_scan.py"):
            self.assertIn(cmd, readme)

    def test_build_is_idempotent(self):
        def digest():
            h = {}
            for p in sorted(self.out.rglob("*")):
                if p.is_file():
                    h[p.relative_to(self.out).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
            return h
        before = digest()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(build_all.run(self.root), 0)
        self.assertEqual(digest(), before)


class RepositoryStringTests(unittest.TestCase):
    """String rules across the committed build root and this build's UI work orders."""

    def files(self):
        yield from text_files(_util.ROOT)
        yield from sorted((_util.ROOT.parents[1] / "ui-work-orders").glob("003-*.md"))

    def test_disallowed_location_only_in_constants(self):
        offenders = [p for p in self.files() if C.DISALLOWED_LOCATION_ID in p.read_text(encoding="utf-8", errors="ignore")]
        self.assertEqual([p.relative_to(_util.ROOT).as_posix() for p in offenders], ["config/constants.py"])
        line = [l for l in (_util.ROOT / "config" / "constants.py").read_text().splitlines() if C.DISALLOWED_LOCATION_ID in l][0]
        self.assertTrue(line.startswith("DISALLOWED_LOCATION_ID"))

    def test_frozen_campaign_only_in_guards_and_checklists(self):
        allowed = ("config/constants.py", "ui-tasks/", "ui-work-orders/")
        for p in self.files():
            if C.FROZEN_CAMPAIGN_NAME in p.read_text(encoding="utf-8", errors="ignore"):
                rel = p.as_posix()
                self.assertTrue(any(a in rel for a in allowed), rel)

    def test_banned_phrases_brands_and_phone_absent(self):
        for p in self.files():
            text = p.read_text(encoding="utf-8", errors="ignore")
            if p.name == "constants.py":
                continue  # defines the lists (by concatenation for phrases)
            self.assertEqual(G.find_banned_phrases(text), [], p)
            if p.suffix in (".md", ".json", ".html", ".jsonl"):
                G.assert_b2b_brand_clean(text)

    def test_contact_details(self):
        self.assertEqual((C.OWNER_NAME, C.OWNER_PHONE, C.OWNER_EMAIL), ("Chuck Ashley", "512-229-9199", "chuck@ca-jconsulting.com"))


class ComplianceRuleTests(unittest.TestCase):
    def rules(self, rel, text):
        return {h["rule"] for h in compliance_scan.scan_text(rel, text)}

    def test_each_rule_fires(self):
        self.assertIn("secret", self.rules("out/x.md", "token sk-" + "a" * 24))
        self.assertIn("secret", self.rules("out/x.md", "EAAG" + "B" * 20))
        self.assertIn("stale_location", self.rules("out/x.md", C.DISALLOWED_LOCATION_ID))
        self.assertIn("frozen_campaign", self.rules("out/x.md", "edit " + C.FROZEN_CAMPAIGN_NAME))
        self.assertNotIn("frozen_campaign", self.rules("ui-tasks/META-BUILD-CHECKLIST.md", C.FROZEN_CAMPAIGN_NAME + " is FROZEN"))
        self.assertIn("mangled_id", self.rules("out/x.md", C.GHL_LOCATION_ID.lower()))
        self.assertIn("banned_phrase", self.rules("out/x.md", C.BANNED_PHRASES[0]))
        self.assertIn("consumer_brand", self.rules("out/x.md", C.CONSUMER_BRANDS[0]))
        self.assertIn("meeting_first", self.rules("out/messages/x.md", "only $650"))
        self.assertIn("unlabeled_money", self.rules("out/niche_brief.md", "we generated $40,000"))
        self.assertIn("unlabeled_money", self.rules("out/launch_review.md", "$650/mo (locked CA-J term)"))
        self.assertIn("roi_claim", self.rules("out/x.md", "clients see 2x ROI"))
        self.assertIn("forbidden_status", self.rules("config/asset_register.json", '"status": "Live"'))

    def test_exemptions(self):
        self.assertEqual(self.rules("out/offer_spec.md", "$650/mo tech fee (locked CA-J term)"), set())
        self.assertEqual(self.rules("out/x.md", "| fee | $1,300 | assumption |"), set())
        block = "<!-- DO-NOT-USE-AS-PROOF:START -->\n2x ROI and $12,000\n<!-- DO-NOT-USE-AS-PROOF:END -->"
        self.assertEqual(self.rules("out/x.md", block), set())
        self.assertEqual(self.rules("out/x.md", "Clean text with " + C.GHL_LOCATION_ID), set())


if __name__ == "__main__":
    unittest.main()

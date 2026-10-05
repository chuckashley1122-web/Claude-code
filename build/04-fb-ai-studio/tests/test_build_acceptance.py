"""End-to-end: build into a temp copy, then check SPEC-04 §4 tree and §7 acceptance criteria."""
import ast
import contextlib
import io
import json
import re
import unittest
from pathlib import Path

from tests._helpers import ROOT, TempBuild
from config import constants as C
from tools import compliance_scan, guardrails as G, run_tests

SPEC_TREE = [
    "README.md", ".env.example",
    "config/build_config.json", "config/constants.py", "config/decision_log.jsonl", "config/asset_register.json",
    "tools/state.py", "tools/guardrails.py", "tools/validate_config.py", "tools/utm_builder.py",
    "tools/compliance_scan.py", "tools/build_all.py", "tools/run_tests.py",
    "src/offer.py", "src/landing_content.py", "src/landing_mock.py", "src/ai_studio_prompts.py", "src/pipeline_spec.py",
    "src/workflow_new_lead.py", "src/workflow_hot_lead.py", "src/workflow_capi.py", "src/message_templates.py",
    "src/ad_angles.py", "src/ad_copy.py", "src/creative_specs.py", "src/pixel_capi_spec.py", "src/campaign_spec.py",
    "src/launch_review.py",
    "out/offer.md", "out/landing/content_spec.md", "out/landing/content_spec.json", "out/landing/index.html",
    "out/landing/thank-you.html", "out/landing/ai_studio_prompt_pack.md", "out/pipeline_spec.md", "out/pipeline.json",
    "out/workflows/01-new-lead-automation.md", "out/workflows/02-hot-lead-replied.md",
    "out/workflows/03-landing-page-capi-lead.md",
    *[f"out/messages/sms_0{i}.md" for i in range(1, 7)], "out/messages/internal_alerts.md",
    "out/ads/angles.md", "out/ads/angles.json", *[f"out/ads/copy/A0{i}.md" for i in range(1, 5)],
    "out/ads/creative_specs.md", "out/pixel_capi_spec.md", "out/capi_settings.json", "out/campaign_spec.md",
    "out/campaign_config.json", "out/launch_review.md", "out/asset_register.md", "out/test_urls.txt",
    "out/tests/test_log.md", *[f"out/tests/T{i:02d}.json" for i in range(1, 15)],
    "ui-tasks/META-CHECKLIST.md", "ui-tasks/GHL-CHECKLIST.md", "ui-tasks/AI-STUDIO-CHECKLIST.md",
    "ui-tasks/DNS-CHECKLIST.md", "ui-tasks/HUMAN-DECISIONS.md", "logs/build.log",
]


def text_files(base: Path):
    for p in base.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
            yield p


class BuildAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tb = TempBuild()
        cls.root = cls.tb.root
        cls.written = cls.tb.build()
        cls.results = run_tests.run(cls.root)
        cls.scan = compliance_scan.scan(cls.root, cls.tb.work_orders)

    @classmethod
    def tearDownClass(cls):
        cls.tb.cleanup()

    def read(self, rel):
        return (self.root / rel).read_text(encoding="utf-8")

    def test_every_spec_path_exists(self):
        missing = [p for p in SPEC_TREE if not (self.root / p).exists()]
        self.assertEqual(missing, [])

    def test_work_orders_written(self):
        names = sorted(p.name for p in self.tb.work_orders.glob("*.md"))
        self.assertEqual(len(names), 4)
        self.assertTrue(all(n.startswith("004-") for n in names))

    def test_compliance_scan_clean(self):
        self.assertEqual({f: h for f, h in self.scan.items() if h}, {})
        self.assertGreater(len(self.scan), 40)

    def test_test_log_t01_to_t14(self):
        self.assertEqual([r["test_id"] for r in self.results], [f"T{i:02d}" for i in range(1, 15)])
        verdicts = {r["test_id"]: r["verdict"] for r in self.results}
        self.assertTrue(set(verdicts.values()) <= {"PASS", "FAIL", "BLOCKED"})
        self.assertNotIn("FAIL", verdicts.values(), verdicts)
        self.assertEqual(verdicts["T14"], "BLOCKED")
        log = self.read("out/tests/test_log.md")
        self.assertEqual(re.findall(r"^\| (T\d\d) \|", log, flags=re.M), [f"T{i:02d}" for i in range(1, 15)])
        for r in self.results:
            self.assertEqual(set(json.loads(self.read(f"out/tests/{r['test_id']}.json"))),
                             {"test_id", "input", "expected_result", "actual_result", "evidence_path", "verdict"})

    def test_idempotent_rebuild(self):
        skip = {"logs/build.log", "config/decision_log.jsonl", "out/launch_review.md"}
        def snap():
            return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in text_files(self.root)
                    if p.relative_to(self.root).as_posix() not in skip and "tests" not in p.parts}
        before = snap()
        self.tb.build()
        self.assertEqual(snap(), before)

    def test_frozen_campaign_only_in_allowed_places(self):
        allowed = {"config/constants.py", "ui-tasks/META-CHECKLIST.md"}
        found = set()
        for base in (self.root, ROOT):
            for p in text_files(base):
                if C.FROZEN_CAMPAIGN_NAME in p.read_text(encoding="utf-8", errors="ignore"):
                    found.add(p.relative_to(base).as_posix())
        for p in self.tb.work_orders.glob("*.md"):
            self.assertNotIn(C.FROZEN_CAMPAIGN_NAME, p.read_text(encoding="utf-8"))
        self.assertTrue(found <= allowed | {"config/decision_log.jsonl"} and "config/decision_log.jsonl" not in found, found)
        G.assert_not_frozen_campaign(self.read("ui-tasks/META-CHECKLIST.md"), allow_banner=True)
        self.assertTrue(self.read("ui-tasks/META-CHECKLIST.md").startswith(G.BANNER_START))

    def test_disallowed_location_id_only_in_constants(self):
        found = {p.relative_to(base).as_posix() for base in (self.root, ROOT) for p in text_files(base)
                 if C.DISALLOWED_LOCATION_ID in p.read_text(encoding="utf-8", errors="ignore")}
        self.assertEqual(found, {"config/constants.py"})
        line = [ln for ln in self.read("config/constants.py").splitlines() if C.DISALLOWED_LOCATION_ID in ln]
        self.assertEqual(len(line), 1)
        self.assertTrue(line[0].startswith("DISALLOWED_LOCATION_ID"))
        self.assertIn('GHL_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"', self.read("config/constants.py"))

    def test_banned_phrases_and_consumer_brands_absent_everywhere(self):
        bases = [self.root, ROOT, self.tb.work_orders]
        for base in bases:
            for p in text_files(base):
                t = p.read_text(encoding="utf-8", errors="ignore")
                with self.subTest(p=str(p)):
                    self.assertEqual(G.find_banned_phrases(t), [])
                    if p.name != "constants.py":
                        self.assertEqual(G.find_consumer_brand(t), [])

    def test_budget_and_draft(self):
        self.assertEqual(C.AD_SPEND_CAP_USD, 0)
        self.assertEqual(C.DAILY_BUDGET_USD, C.NEEDS_EVIDENCE)
        camp = json.loads(self.read("out/campaign_config.json"))
        self.assertEqual(camp["status"], "DRAFT_UNPUBLISHED")
        md = self.read("out/campaign_spec.md")
        self.assertIn("NEW DRAFT", md)
        self.assertIn("**OFF** - budget is set at the ad-set level (ABO)", md)
        self.assertIn("## Ad-set level (budget lives here)", md)
        self.assertTrue(5 <= len(camp["ads"]) <= 7)

    def test_no_live_or_ready_status(self):
        statuses = {a["status"] for a in json.loads(self.read("config/asset_register.json"))["assets"]}
        self.assertFalse(statuses & {"Live", "Ready for launch"}, statuses)
        for line in self.read("config/decision_log.jsonl").splitlines():
            self.assertNotIn(json.loads(line)["status"], ("Live", "Ready for launch"))

    def test_index_banner_and_dns_gate(self):
        self.assertIn("STATIC CONTENT MOCK", self.read("out/landing/index.html"))
        self.assertNotIn("<script", self.read("out/landing/index.html").lower())
        self.assertIn("DOMAIN PURCHASE REQUIRES EXPLICIT HUMAN APPROVAL", self.read("ui-tasks/DNS-CHECKLIST.md"))

    def test_human_decisions_lists_every_needs_evidence(self):
        hd = self.read("ui-tasks/HUMAN-DECISIONS.md")
        cfg = json.loads(self.read("config/build_config.json"))
        for k, v in cfg.items():
            if v == C.NEEDS_EVIDENCE:
                with self.subTest(k=k):
                    self.assertIn(f"build_config.{k} |", hd)
        for s in C.SPEND_ITEMS:
            self.assertIn(s["service"], hd)
        rows = [ln for ln in hd.splitlines() if ln.startswith("| build_config.")]
        self.assertTrue(all(ln.rstrip().endswith(f"| {C.OWNER_NAME} |") for ln in rows))

    def test_readme_statements(self):
        readme = self.read("README.md")
        self.assertIn("Nothing was launched", readme)
        self.assertIn("No Meta, GHL, domain, DNS or payment object was touched", readme)
        self.assertIn("Deviations from spec", readme)
        for s in C.SPEND_ITEMS:
            self.assertIn(s["service"], readme)

    def test_message_and_ad_copy_guards(self):
        from src.ad_copy import COPY
        from src.message_templates import INTERNAL_ALERTS, SMS_STEPS, full_sms
        for s in SMS_STEPS:
            G.assert_meeting_first(full_sms(s))
            self.assertTrue(full_sms(s).endswith("Reply STOP to opt out."))
            self.assertNotIn("landing page", full_sms(s).lower())
        for a in INTERNAL_ALERTS:
            G.assert_no_price_in_message(a["body"])
        for angle, pack in COPY.items():
            self.assertEqual(len(pack["primary_texts"]), 5)
            for v in pack["primary_texts"]:
                G.assert_no_price_in_message(v["text"])
                G.assert_copy_leads_with_pain_or_outcome(v)
                self.assertNotRegex(v["text"].splitlines()[0], r"(?i)^\W*(ca-?j|logo)")

    def test_no_network_code(self):
        banned = {"urllib.request", "http.client", "socket", "requests", "httpx", "aiohttp", "subprocess", "smtplib"}
        for p in list((ROOT / "tools").glob("*.py")) + list((ROOT / "src").glob("*.py")):
            tree = ast.parse(p.read_text(encoding="utf-8"))
            mods = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    mods |= {a.name for a in node.names}
                elif isinstance(node, ast.ImportFrom) and node.module:
                    mods.add(node.module)
            with self.subTest(p=p.name):
                self.assertFalse(mods & banned, mods & banned)

    def test_scan_catches_injected_violations(self):
        bad = {
            "out/ads/copy/A01.md": lambda t: t.replace("Book a free strategy session.", "Book now for $" + str(C.TECH_FEE_MONTHLY_USD) + "/mo.", 1),
            "out/offer.md": lambda t: t + "\nNext: duplicate " + C.FROZEN_CAMPAIGN_NAME + "\n",
            "out/pipeline_spec.md": lambda t: t + "\nlocation " + C.GHL_LOCATION_ID.upper() + "\n",
            "out/campaign_config.json": lambda t: json.dumps(dict(json.loads(t), budget_exposure_usd=70)),
            "out/landing/content_spec.md": lambda t: t + "\nRated 4.9 stars from 250+ reviews\n",
            "ui-tasks/GHL-CHECKLIST.md": lambda t: t + "\ntoken EAA" + "Q" * 30 + "\n",
            "out/messages/sms_02.md": lambda t: t.replace("Reply STOP", "We offer a 10% off deal. Reply STOP", 1),
        }
        originals = {}
        try:
            for rel, fn in bad.items():
                originals[rel] = self.read(rel)
                (self.root / rel).write_text(fn(originals[rel]), encoding="utf-8")
            results = compliance_scan.scan(self.root, self.tb.work_orders)
            for rel in bad:
                with self.subTest(rel=rel):
                    self.assertTrue(results[rel], f"scan missed injected violation in {rel}")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(compliance_scan.main(self.root, self.tb.work_orders), 1)
        finally:
            for rel, t in originals.items():
                (self.root / rel).write_text(t, encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(compliance_scan.main(self.root, self.tb.work_orders), 0)


if __name__ == "__main__":
    unittest.main()

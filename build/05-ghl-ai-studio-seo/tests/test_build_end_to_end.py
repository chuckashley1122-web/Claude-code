"""Full build into a throwaway directory, then the spec's acceptance criteria against it."""

import contextlib
import hashlib
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from src import acceptance_matrix, ai_studio_prompts  # noqa: E402
from tools import build_all, compliance_scan, secret_scan  # noqa: E402
from tools.paths import BUILD_ROOT, REPO_ROOT, Paths, scratch_paths  # noqa: E402

TMP = None
PATHS: Paths = None


def setUpModule():
    global TMP, PATHS
    TMP = tempfile.TemporaryDirectory()
    PATHS = scratch_paths(Path(TMP.name) / "build")
    assert build_all.run(PATHS, quiet=True) == 0, (PATHS.logs / "build.log").read_text()


def tearDownModule():
    TMP.cleanup()


def snapshot(paths: Paths) -> dict:
    result = {}
    for base in (paths.out, paths.config, paths.ui_work_orders):
        for p in sorted(base.rglob("*")):
            if p.is_file():
                result[paths.rel(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def quiet(fn, *a, **kw):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **kw)


class BuildOutputs(unittest.TestCase):
    def test_section4_tree_present(self):
        self.assertTrue((BUILD_ROOT / "config" / "constants.py").exists())
        expected = [".env.example", "config/build_config.json", "config/business_facts.json",
                    "config/route_inventory.json", "config/decision_log.jsonl", "config/asset_register.json",
                    "out/business_facts.md", "out/route_inventory.md", "out/metadata.json", "out/metadata.md",
                    "out/seo/sitemap.xml", "out/seo/robots.txt", "out/seo/indexability.md",
                    "out/seo/redirect_map.json", "out/seo/redirect_map.md", "out/site/404.html",
                    "out/site/thank-you.html", "out/ai_studio_prompt_pack.md", "out/inquiry_contract.md",
                    "out/inquiry_contract.json", "out/server_functions/inquiry.ts", "out/estimator/BLOCKED.md",
                    "out/tests/test_log.md", "out/release_package.md", "out/asset_register.md", "logs/build.log"]
        expected += [f"out/tests/T{i:02d}.json" for i in range(1, 15)]
        for rel in expected:
            self.assertTrue((PATHS.root / rel).exists(), rel)
        tools = ["state", "guardrails", "validate_config", "fetch_raw_html", "baseline_inventory", "secret_scan",
                 "compliance_scan", "build_all", "run_tests"]
        srcs = ["business_facts", "page_plan", "content_pages", "metadata", "structured_data", "seo_files",
                "redirect_map", "site_mock", "ai_studio_prompts", "inquiry_contract", "inquiry_validator",
                "idempotency_store", "inquiry_handler", "ghl_adapter", "estimator", "acceptance_matrix",
                "release_package"]
        for name in tools:
            self.assertTrue((BUILD_ROOT / "tools" / f"{name}.py").exists(), name)
        for name in srcs:
            self.assertTrue((BUILD_ROOT / "src" / f"{name}.py").exists(), name)
        for name in ("test_guardrails", "test_inquiry_validator", "test_idempotency_store", "test_inquiry_handler",
                     "test_metadata_uniqueness"):
            self.assertTrue((BUILD_ROOT / "tests" / f"{name}.py").exists(), name)
        self.assertTrue((BUILD_ROOT / "README.md").exists())

    def test_rebuild_is_idempotent(self):
        before = snapshot(PATHS)
        self.assertEqual(build_all.run(PATHS, quiet=True), 0)
        self.assertEqual(snapshot(PATHS), before)

    def test_scanners_clean(self):
        self.assertEqual(secret_scan.scan(PATHS), [])
        report = compliance_scan.scan(PATHS)
        self.assertEqual({k: v for k, v in report.items() if v}, {})
        self.assertEqual(quiet(secret_scan.main, [], PATHS), 0)
        self.assertEqual(quiet(compliance_scan.main, [], PATHS), 0)

    def test_mocks(self):
        site = PATHS.out / "site"
        expected = {"index.html", "services-lead-generation.html", "services-reputation-management.html",
                    "services-paid-advertising.html", "locations-austin.html", "locations-round-rock.html",
                    "about.html", "contact.html", "404.html", "thank-you.html"}
        self.assertEqual({p.name for p in site.glob("*.html")}, expected)
        for p in site.glob("*.html"):
            html = p.read_text()
            with self.subTest(page=p.name):
                self.assertIn("STATIC CONTENT MOCK — NOT THE LIVE SITE; does not submit anywhere.", html)
                self.assertNotIn("<script", html.lower())
                self.assertIsNone(re.search(r'(src|href)="(https?:)?//(?!ca-jenterprises\.com/ai)', html))
                self.assertNotIn('rel="stylesheet"', html)
                self.assertNotIn("<form action", html)
                self.assertIn(C.BOOKING_URL, html) if p.name != "404.html" else None
        contact = (site / "contact.html").read_text()
        self.assertIn('type="button"', contact)
        self.assertNotIn("action=", contact)
        self.assertIn('content="noindex', (site / "thank-you.html").read_text())

    def test_location_pages_merged_not_emitted(self):
        merge = json.loads((PATHS.out / "pages" / "service-area-merge.json").read_text())
        self.assertEqual(merge["merged_routes"], ["/locations/austin", "/locations/round-rock"])
        self.assertFalse((PATHS.out / "pages" / "locations-austin.md").exists())
        sitemap = (PATHS.out / "seo" / "sitemap.xml").read_text()
        self.assertNotIn("locations", sitemap)
        self.assertNotIn("thank-you", sitemap)
        self.assertIn('content="noindex', (PATHS.out / "site" / "locations-austin.html").read_text())

    def test_every_page_record_cta(self):
        model = json.loads((PATHS.out / "pages" / "_content_model.json").read_text())
        for page in model["pages"].values():
            self.assertEqual(page["primary_cta"]["href"], C.BOOKING_URL)
        contract = json.loads((PATHS.out / "inquiry_contract.json").read_text())
        self.assertEqual(contract["escalation_path"], C.BOOKING_URL)

    def test_matrix_log(self):
        results = acceptance_matrix.load_results(PATHS)
        self.assertEqual([r["test_id"] for r in results], [f"T{i:02d}" for i in range(1, 15)])
        self.assertTrue(all(r["verdict"] in ("PASS", "FAIL", "BLOCKED") for r in results))
        verdicts = {r["test_id"]: r["verdict"] for r in results}
        for tid in ("T01", "T03", "T06", "T11", "T12", "T13", "T14"):
            self.assertEqual(verdicts[tid], "BLOCKED", tid)
        self.assertNotIn("FAIL", verdicts.values())
        log = (PATHS.out / "tests" / "test_log.md").read_text()
        self.assertEqual(re.findall(r"^\| (T\d\d) ", log, re.M), [f"T{i:02d}" for i in range(1, 15)])
        for r in results:
            self.assertEqual(set(r) >= {"test_id", "input", "expected_result", "actual_result", "evidence_path",
                                        "verdict"}, True)

    def test_release_package(self):
        text = (PATHS.out / "release_package.md").read_text()
        for label in ("Project and location verified", "Draft/live URL", "Saved version and rollback target",
                      "Completed steps", "Test results", "CRM persistence", "Outstanding inputs",
                      "Production status", "Next executable action"):
            self.assertIn(f"**{label}:**", text)
        self.assertIn("- **Draft/live URL:** NEEDS_EVIDENCE", text)
        for action in ("Domain change", "paid dependency", "Outbound workflow", "Publish", "Migration"):
            self.assertIn(action, text)
        spend = json.loads((PATHS.out / "spend_items.json").read_text())
        self.assertTrue(all(i["approval_required"] and not i["approved"] and i["cost_usd"] == "NEEDS_EVIDENCE"
                            for i in spend["items"]))
        self.assertNotIn("Published-by-human |", (PATHS.out / "asset_register.md").read_text())

    def test_work_orders(self):
        wo = PATHS.ui_work_orders
        names = sorted(p.name for p in wo.glob("005-*.md"))
        self.assertEqual(len(names), 9)
        for p in wo.glob("005-*.md"):
            text = p.read_text()
            with self.subTest(order=p.name):
                for heading in ("**Why:**", "**Where:**", "**Steps:**", "**Verify:**", "**Blocked by:**"):
                    self.assertIn(heading, text)
                self.assertNotRegex(text.lower(), r"configure (the )?settings")
        o7 = (wo / "005-007-domain-dns-and-publish.md").read_text()
        self.assertIn("DOMAIN PURCHASE OR ANY PAID DEPENDENCY REQUIRES EXPLICIT WRITTEN HUMAN APPROVAL", o7)
        self.assertIn("spend $0 until approved", o7)
        self.assertIn("| Dollar amount |", o7)
        o5 = (wo / "005-005-ghl-crm-integration-and-field-mapping.md").read_text()
        self.assertIn(C.GHL_LOCATION_ID, o5)
        self.assertIn(C.TEST_TAG, (wo / "005-006-synthetic-inquiry-end-to-end-test.md").read_text())
        o4 = (wo / "005-004-server-function-secrets-deploy.md").read_text()
        self.assertIn("`GHL_ACCESS_TOKEN`", o4)
        self.assertIn("out/server_functions/inquiry.ts", o4)
        hd = (wo / "005-HUMAN-DECISIONS.md").read_text()
        warning = [l for l in hd.splitlines() if C.FROZEN_CAMPAIGN_NAME in l]
        self.assertEqual(len(warning), 1)
        self.assertIn("STRIPE", warning[0])
        self.assertIn("FROZEN", warning[0])

    @unittest.skipUnless((REPO_ROOT / "docs" / "playbooks" / "05-ghl-ai-studio-seo.md").exists(), "playbook absent")
    def test_prompt_pack_verbatim(self):
        playbook = (REPO_ROOT / "docs" / "playbooks" / "05-ghl-ai-studio-seo.md").read_text(encoding="utf-8")
        pack = (PATHS.out / "ai_studio_prompt_pack.md").read_text()
        for _, _, text in ai_studio_prompts.PROMPTS:
            self.assertIn(text, playbook)
            self.assertIn(text, pack)
        self.assertIn(ai_studio_prompts.MASTER_INSTRUCTION, playbook)
        self.assertIn(ai_studio_prompts.FINAL_STATUS_FORMAT, playbook)
        self.assertEqual(len(ai_studio_prompts.PROMPTS), 7)
        self.assertIn("20-prompt revised playbook\" was never supplied", pack)
        self.assertIn("INAPPLICABLE", pack.split("## Prompt 4")[1].split("## Prompt 5")[0])
        self.assertIn("INAPPLICABLE", pack.split("## Prompt 6")[1].split("## Prompt 7")[0])


class PlantedViolations(unittest.TestCase):
    """The scanners must actually catch things (not just pass on clean input)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name) / "build"
        shutil.copytree(PATHS.root, root)
        self.paths = Paths(root=root, ui_work_orders=root / "ui-work-orders")

    def tearDown(self):
        self.tmp.cleanup()

    def plant(self, rel, text):
        p = self.paths.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(p.read_text() + "\n" + text if p.exists() else text)

    def hits(self):
        return {k: v for k, v in compliance_scan.scan(self.paths).items() if v}

    def test_secret_value_detected(self):
        self.plant("out/notes.md", "Authorization: Bearer " + "a1B2" * 10)
        self.plant("out/env.txt", "GHL_ACCESS_TOKEN" + "=" + "pit-" + "x" * 30)
        kinds = {h.kind for h in secret_scan.scan(self.paths)}
        self.assertTrue({"bearer_token", "GHL_ACCESS_TOKEN_with_value"} <= kinds)
        self.assertTrue(all(len(h.redacted) <= 5 for h in secret_scan.scan(self.paths)))

    def test_needs_evidence_replacement_detected(self):
        cfg = json.loads(self.paths.build_config.read_text())
        cfg["review_count"] = "212"
        self.paths.build_config.write_text(json.dumps(cfg))
        self.assertIn("needs_evidence_replaced:review_count", {h.kind for h in secret_scan.scan(self.paths)})

    def test_price_and_fact_and_brand_in_customer_copy(self):
        self.plant("out/pages/about.md", "Plans from $650 per month.")
        self.plant("out/pages/contact.md", "Rated 4.9 out of 5 by our clients.")
        self.plant("out/pages/index.md", "Try our cof" + "fee too.")
        hits = self.hits()
        self.assertIn("no-price-in-message", " ".join(hits["out/pages/about.md"]))
        self.assertIn("no-fabricated-fact", " ".join(hits["out/pages/contact.md"]))
        self.assertIn("brand-separation", " ".join(hits["out/pages/index.md"]))

    def test_frozen_campaign_and_locations(self):
        self.plant("out/plan.md", "Duplicate " + C.FROZEN_CAMPAIGN_NAME + " for the next test")
        self.plant("out/loc.md", "location " + C.GHL_LOCATION_ID.lower())
        self.plant("out/site/index.html", "<p>" + C.DISALLOWED_LOCATION_ID + "</p>")
        hits = self.hits()
        self.assertIn("frozen-campaign", " ".join(hits["out/plan.md"]))
        self.assertIn("location-case", " ".join(hits["out/loc.md"]))
        self.assertTrue(any("disallowed" in h for h in hits["out/site/index.html"]))

    def test_logo_first_canonical_dup_and_unapproved_spend(self):
        meta = json.loads((self.paths.out / "metadata.json").read_text())
        meta["records"][0]["og_creative"]["opening_element"] = "logo"
        meta["records"][1]["canonical"] = meta["records"][0]["canonical"]
        (self.paths.out / "metadata.json").write_text(json.dumps(meta))
        spend = json.loads((self.paths.out / "spend_items.json").read_text())
        spend["items"][0]["approved"] = True
        (self.paths.out / "spend_items.json").write_text(json.dumps(spend))
        hits = self.hits()
        joined = " ".join(hits["out/metadata.json"])
        self.assertIn("logo-not-first", joined)
        self.assertIn("canonical-unique", joined)
        self.assertIn("no-spend", " ".join(hits["out/spend_items.json"]))


class RealTreeStringPlacement(unittest.TestCase):
    """Acceptance: sensitive literals appear only where the spec allows, in source and generated files."""

    def files(self):
        roots = [secret_scan.files_to_scan(PATHS)]
        real = Paths(root=BUILD_ROOT, ui_work_orders=REPO_ROOT / "ui-work-orders")
        roots.append(secret_scan.files_to_scan(real))
        for group, paths in zip(roots, (PATHS, real)):
            for f in group:
                yield paths.rel(f), f.read_text(encoding="utf-8", errors="replace")

    def test_disallowed_location_only_in_constant(self):
        offenders = {rel for rel, text in self.files() if C.DISALLOWED_LOCATION_ID in text}
        self.assertEqual(offenders, {"config/constants.py"})

    def test_frozen_campaign_only_in_constant_and_warning(self):
        for rel, text in self.files():
            if C.FROZEN_CAMPAIGN_NAME in text:
                self.assertTrue(rel == "config/constants.py" or rel.endswith("005-HUMAN-DECISIONS.md"), rel)

    def test_source_files_pass_compliance(self):
        real = Paths(root=BUILD_ROOT, ui_work_orders=REPO_ROOT / "ui-work-orders")
        report = compliance_scan.scan(real)
        source_hits = {rel: v for rel, v in report.items() if v and not rel.startswith(("out/", "logs/"))}
        self.assertEqual(source_hits, {})

    def test_readme_statements(self):
        readme = (BUILD_ROOT / "README.md").read_text()
        self.assertIn("Nothing was published, deployed, sent or purchased", readme)
        self.assertIn("No GHL, DNS, Search Console or Meta object was touched", readme)


if __name__ == "__main__":
    unittest.main()

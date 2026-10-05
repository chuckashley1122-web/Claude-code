"""Repository-wide checks for spec section 7 acceptance criteria and build rules."""
import csv
import re
import unittest
from pathlib import Path

from _paths import ROOT
from guardrails import claim_guard, pricing_guard
from scripts import render_templates, validate_records

REPO = ROOT.parents[1]
UI_WORK_ORDERS = sorted((REPO / "ui-work-orders").glob("002-*.md"))

SPEC_FILES = {
    "README.md", ".env.example", ".gitignore",
    "records/Build_Log.csv", "records/Asset_Register.csv", "records/Business_Facts.csv",
    "records/Test_Results.csv", "records/Blockers.csv",
    "schemas/build_log.schema.json", "schemas/asset_register.schema.json",
    "schemas/business_facts.schema.json", "schemas/test_results.schema.json", "schemas/blockers.schema.json",
    "agent/system-prompt.md", "agent/demo-questions.md", "agent/handoff-rule.md",
    "agent/business-facts-template.csv",
    "tests/T01-T12.csv", "tests/test-run-protocol.md",
    "workflows/WF01_demo_preparation.md", "workflows/WF02_client_onboarding.md",
    "workflows/WF03_human_followup.md", "workflows/WF04_knowledge_maintenance.md",
    "pipeline/stages.md", "pipeline/prospects.template.csv",
    "outreach/email-draft.txt", "outreach/email-post-demo.txt", "outreach/dm-draft.txt",
    "outreach/call-script.txt", "outreach/followup-cadence.md", "outreach/gatekeeper-questions.md",
    "intake/client-intake-form.md", "intake/intake.schema.json", "intake/discovery-questions.md",
    "guardrails/pricing_guard.py", "guardrails/meeting_first.py", "guardrails/claim_guard.py",
    "runbooks/ghl-account-and-snapshot.md", "runbooks/demo-page-and-calendar.md",
    "runbooks/widget-install.md", "runbooks/phone-routing.md", "runbooks/payment-product.md",
    "runbooks/rollback.md",
    "scripts/validate_records.py", "scripts/render_templates.py", "scripts/check_guardrails.py",
    "scripts/run_test_checklist.py", "scripts/cost_estimate.py",
    "docs/DEPLOY-RUNBOOK.md", "docs/UI-ONLY-CHECKLIST.md", "docs/COST-AND-APPROVALS.md",
    "docs/SOURCE-CLAIMS.md",
}
# Documented in README "Deviations from spec" item 1.
EXTRA_FILES = {
    "guardrails/locked_pricing.json", "rates.yaml", "scripts/mini_yaml.py",
    "outreach/render-vars.example.json", "guardrails/__init__.py", "scripts/__init__.py",
    "tests/_paths.py", "tests/fixtures/intake.synthetic.json",
}
IGNORED_PARTS = {"out", "__pycache__", ".venv"}


def build_files() -> list[Path]:
    out = []
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if p.is_file() and not (set(rel.parts) & IGNORED_PARTS) and p.name != ".env" and p.suffix != ".pyc":
            out.append(p)
    return out


def all_texts() -> dict[str, str]:
    files = {str(p.relative_to(ROOT).as_posix()): p for p in build_files()}
    files.update({f"../ui-work-orders/{p.name}": p for p in UI_WORK_ORDERS})
    return {k: p.read_text(encoding="utf-8") for k, p in files.items()}


class FileTreeTests(unittest.TestCase):
    def test_file_set_matches_spec_plus_documented_extras(self):
        actual = {p.relative_to(ROOT).as_posix() for p in build_files()}
        tests = {a for a in actual if re.fullmatch(r"tests/test_[a-z_]+\.py", a)}
        self.assertEqual(SPEC_FILES - actual, set(), "missing spec files")
        self.assertEqual(actual - SPEC_FILES - EXTRA_FILES - tests, set(), "undocumented files")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for extra in EXTRA_FILES:
            self.assertIn(extra, readme)

    def test_gitignore_and_env_example(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
        for entry in (".env", "out/", "*.log", "__pycache__/", ".venv/"):
            self.assertIn(entry, ignore)
        for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#"):
                self.assertRegex(line, r"^[A-Z_]+=$", "env example must hold names only")


class ContentRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = all_texts()

    def test_ui_work_orders_exist(self):
        self.assertGreaterEqual(len(UI_WORK_ORDERS), 5)

    def test_banned_phrases_absent(self):
        banned = ["qualified" + " appointment", "shows" + " up", "10-25" + " leads/month",
                  "10–25" + " leads/month", "866-566" + "-3445"]
        for name, text in self.texts.items():
            low = text.lower()
            for phrase in banned:
                self.assertNotIn(phrase, low, f"{phrase!r} in {name}")

    def test_no_foreign_location_ids(self):
        stale = "nuhFUYu0ZF9" + "Eswiz9P79"
        for name, text in self.texts.items():
            self.assertNotIn(stale, text, name)
            self.assertEqual(validate_records.find_foreign_location_ids(text), [], name)

    def test_source_prices_only_in_allowed_files(self):
        allowed = {"docs/SOURCE-CLAIMS.md", "guardrails/claim_guard.py", "scripts/check_guardrails.py"}
        rx = re.compile(r"\$\s?(?:197|97|297|9\.99)\b")
        for name, text in self.texts.items():
            if name not in allowed:
                self.assertIsNone(rx.search(text), f"source price in {name}")
        claims = self.texts["docs/SOURCE-CLAIMS.md"]
        for fig in ("197", "97", "297", "9.99"):
            fig = "$" + fig
            self.assertIn(fig, claims)

    def test_consumer_brands_absent(self):
        rx = re.compile("daily " + "grind|et" + "sy|print" + "able", re.IGNORECASE)
        for name, text in self.texts.items():
            if name == "guardrails/claim_guard.py":
                continue
            self.assertIsNone(rx.search(text), f"consumer brand in {name}")

    def test_booking_url_is_the_only_cta_destination(self):
        rx = re.compile(r"https?://(?:www\.)?ca-jenterprises\.com[^\s)`|\"']*")
        for name, text in self.texts.items():
            for m in rx.finditer(text):
                self.assertEqual(m.group(0).rstrip(".,;:"), pricing_guard.BOOKING_URL, name)
        for name in ("email-draft.txt", "email-post-demo.txt", "dm-draft.txt", "call-script.txt"):
            body, _ = render_templates.parse_template(self.texts[f"outreach/{name}"])
            urls = re.findall(r"https?://\S+", body)
            self.assertTrue(urls, name)
            self.assertEqual({u.rstrip(".,") for u in urls}, {pricing_guard.BOOKING_URL}, name)

    def test_public_contact_only(self):
        phone_rx = re.compile(r"(?<!\d)\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}(?!\d)")
        email_rx = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        for name, text in self.texts.items():
            for m in phone_rx.finditer(text):
                num = re.sub(r"\D", "", m.group(0))
                self.assertTrue(num == "5122299199" or re.fullmatch(r"\d{3}55501\d\d", num), f"{m.group(0)} in {name}")
            for m in email_rx.finditer(text):
                e = m.group(0).lower()
                self.assertTrue(e == "chuck@ca-jconsulting.com" or e.endswith("@example.com") or
                                e == "noreply@anthropic.com", f"{e} in {name}")

    def test_outbound_templates_are_price_and_claim_free(self):
        for name in ("email-draft.txt", "email-post-demo.txt", "dm-draft.txt", "call-script.txt"):
            body, directives = render_templates.parse_template(self.texts[f"outreach/{name}"])
            channel = directives["channel"][0]
            self.assertIn(channel, pricing_guard.OUTBOUND_CHANNELS)
            self.assertEqual(pricing_guard.find_violations(body, channel), [], name)
            self.assertEqual(claim_guard.find_violations(body), [], name)

    def test_no_network_or_sending_code(self):
        rx = re.compile(r"^\s*(?:import|from)\s+(?:urllib\.request|http\.client|socket|smtplib|requests|ftplib)\b", re.M)
        for name, text in self.texts.items():
            if name.endswith(".py"):
                self.assertIsNone(rx.search(text), name)


class DocTests(unittest.TestCase):
    def read(self, rel):
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_ui_only_checklist(self):
        text = self.read("docs/UI-ONLY-CHECKLIST.md")
        steps = re.findall(r"^\| (\d{2}) \|", text, flags=re.M)
        self.assertEqual(steps, [f"{i:02d}" for i in range(1, 52)])
        for needed in ("GoHighLevel", "Meta Ads Manager", "subaccount creation", "snapshots", "calendars",
                       "AI agents", "knowledge base crawling", "chat widgets", "phone number settings",
                       "A2P messaging registration", "payment", "workflows", "logged-in UI",
                       "coding agent cannot"):
            self.assertIn(needed, text)

    def test_deploy_runbook_covers_51_steps(self):
        text = self.read("docs/DEPLOY-RUNBOOK.md")
        rows = re.findall(r"^\| (\d{2}) [^|]+\|(.*)$", text, flags=re.M)
        self.assertEqual([r[0] for r in rows], [f"{i:02d}" for i in range(1, 52)])
        for _, rest in rows:
            self.assertEqual(rest.count("|"), 6)
        self.assertIn("| Step | Platform | Exact action | Object to create | Spend | Approval required | Evidence to capture |", text)

    def test_cost_and_approvals(self):
        text = self.read("docs/COST-AND-APPROVALS.md")
        self.assertIn("No charges or purchases of any kind are authorized by this spec.", text)
        self.assertIn("$650/mo", text)
        self.assertIn("WAIVED", text)
        self.assertIn("$250 to $300", text)
        self.assertIn("Higgsfield", text)
        spend_rows = [l for l in text.splitlines() if l.endswith("| approval required | NEEDS_EVIDENCE |")]
        self.assertGreaterEqual(len(spend_rows), 10)

    def test_source_claims(self):
        text = self.read("docs/SOURCE-CLAIMS.md")
        rows = [l for l in text.splitlines() if re.match(r"^\| (SC|PV)-\d{2} \|", l)]
        for row in rows:
            self.assertTrue("unverified" in row or "stale" in row, row)
        sc = {re.match(r"^\| (SC-\d{2})", r).group(1): r for r in rows if r.startswith("| SC")}
        expectations = {"SC-01": "108", "SC-02": "112", "SC-03": "131", "SC-04": "131", "SC-05": "131",
                        "SC-06": "133", "SC-07": "154", "SC-08": "299", "SC-09": "310", "SC-10": "359",
                        "SC-11": "359", "SC-12": "321"}
        for cid, line in expectations.items():
            self.assertIn(f"| {line}", sc[cid])
        for phrase in ("virtually nothing", "15 minutes", "30–90 emails daily across three domains",
                       "50 calls daily", "low-churn", "valuation", "$1,000 plus $2,000 setup"):
            self.assertIn(phrase, text)

    def test_workflows(self):
        files = sorted((ROOT / "workflows").glob("*.md"))
        self.assertEqual([f.name[:4] for f in files], ["WF01", "WF02", "WF03", "WF04"])
        keys = {"WF01": "Appointment ID", "WF02": "Subscription ID", "WF03": "Interaction ID", "WF04": "weekly"}
        for f in files:
            text = f.read_text(encoding="utf-8")
            for field in ("| Trigger |", "| Filter |", "| Dedupe key |", "| Action |",
                          "| Notification destination permission |", "| Failure / review route |"):
                self.assertIn(field, text, f.name)
            self.assertIn("human-executed", text)
            self.assertIn("GoHighLevel", text)
            self.assertIn(keys[f.name[:4]].lower(), text.lower())
        self.assertIn("review", (ROOT / "workflows/WF02_client_onboarding.md").read_text(encoding="utf-8"))

    def test_runbooks(self):
        rollback = self.read("runbooks/rollback.md")
        for needed in ("Previous forwarding destination", "Previous schedule", "Previous voicemail behaviour",
                       "Provider-specific restoration steps", "Responsible person", "one inbound call"):
            self.assertIn(needed, rollback)
        phone = self.read("runbooks/phone-routing.md")
        for needed in ("Do not invent carrier dial codes", "voicemail does not answer before the AI",
                       "does not forward back to the AI number"):
            self.assertIn(needed, phone)

    def test_pipeline(self):
        text = self.read("pipeline/stages.md")
        forward = ["Qualified", "Contacted", "Replied", "Demo booked", "Demo held", "Proposal sent",
                   "Paid and onboarding", "Active"]
        for i, stage in enumerate(forward, start=1):
            self.assertIn(f"| {i} | {stage} |", text)
        for terminal in ("| Not now |", "| Lost |"):
            self.assertIn(terminal, text)
        with (ROOT / "pipeline/prospects.template.csv").open(newline="", encoding="utf-8") as fh:
            header = next(csv.reader(fh))
        for col in ("domain", "phone", "opt_out"):
            self.assertIn(col, header)

    def test_outreach_rules(self):
        cadence = self.read("outreach/followup-cadence.md")
        for needed in ("Not specified in the source", "3 business days", "7 business days", "opt-out",
                       "simultaneous", "launch authorization"):
            self.assertIn(needed, cadence)
        email = self.read("outreach/email-draft.txt")
        self.assertIn("I can prepare a short AI demo", email)
        self.assertNotIn("already built", email.split("\n", 4)[-1])
        self.assertIn("relationship", self.read("outreach/dm-draft.txt"))
        self.assertIn("personal relationship", self.read("outreach/call-script.txt"))
        gk = self.read("outreach/gatekeeper-questions.md")
        self.assertIn("Who handles your after-hours calls?", gk)

    def test_agent_prompt_preserves_source_constraints(self):
        prompt = self.read("agent/system-prompt.md")
        source = REPO / "docs" / "playbooks" / "02-ai-employee-action-plan.md"
        if source.is_file():
            src_lines = source.read_text(encoding="utf-8").splitlines()[170:174]
            for para in src_lines:
                for sentence in re.split(r"(?<=\.)\s+", para.replace("’", "'")):
                    self.assertIn(sentence.strip(), prompt)
        self.assertIn("https://ca-jenterprises.com/ai", prompt)
        self.assertIn("Never state any price", prompt)
        questions = re.findall(r"^\| (\d) \|", self.read("agent/demo-questions.md"), flags=re.M)
        self.assertEqual(questions, ["1", "2", "3", "4", "5", "6"])

    def test_intake_covers_source_line_208(self):
        import json
        schema = json.loads(self.read("intake/intake.schema.json"))
        for key in ("hours", "holidays", "covered_areas", "services_offered", "approved_price_statements",
                    "escalation_instructions", "dispatcher_contact", "website_admin_access", "calendar_owner",
                    "phone_provider", "booking_permission", "handoff_recipient", "handoff_response_time"):
            self.assertIn(key, schema["required"])
            self.assertIn(f"`{key}`", self.read("intake/client-intake-form.md"))
        disc = self.read("intake/discovery-questions.md")
        self.assertIn("What happens when someone calls after the office closes?", disc)

    def test_readme(self):
        text = self.read("README.md")
        for needed in ("No charges or purchases of any kind", "NEEDS_EVIDENCE", "Meeting-first",
                       "Source results are not CA-J results", "Chuck Ashley", "512-229-9199",
                       "chuck@ca-jconsulting.com", "CA&J Enterprises LLC", "UWc5vKBgFVPdxNTRAy2s",
                       "https://ca-jenterprises.com/ai", "Deviations from spec"):
            self.assertIn(needed, text)


if __name__ == "__main__":
    unittest.main()

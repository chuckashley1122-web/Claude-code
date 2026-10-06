"""Repo-wide checks for spec section 7 acceptance criteria and the build rules."""

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import constants  # noqa: E402
from guardrails import claim_guard  # noqa: E402

SPEC_FILES = """README.md .env.example .gitignore requirements.txt
config/constants.py config/settings.py config/pricing.yaml
guardrails/pricing_guard.py guardrails/meeting_first.py guardrails/claim_guard.py
prompts/01_voice_receptionist_system.txt prompts/02_lead_enrich.txt prompts/02_cold_email.txt prompts/02_followup.txt
prompts/03_ad_deconstruction.txt prompts/03_sora_prompt_format.txt prompts/04_faceless_script.txt
prompts/04_trending_topics.txt prompts/05_content_script.txt prompts/06_language_detect.txt prompts/06_faq_rag.txt
prompts/06_translate.txt prompts/07_youtube_analysis.txt prompts/07_youtube_ideas.txt prompts/08_heygen_script.txt
workflows/01_voice_call_agent.json workflows/02_lead_generation.json workflows/03_ugc_ads_spy.json
workflows/04_faceless_video.json workflows/05_content_agent.json workflows/06_faq_chatbot.json
workflows/07_youtube_ideas.json workflows/08_avatar_generator.json workflows/_common_error_handler.json
adapters/mock_openai.py adapters/mock_calendar.py adapters/mock_crm.py adapters/mock_mailer.py
adapters/mock_video_gen.py adapters/mock_apify.py adapters/mock_publisher.py
data/fixtures/leads.sample.json data/fixtures/ad_transcript.sample.json data/fixtures/faqs.sample.md
data/fixtures/youtube_top.sample.json
scripts/check_env.py scripts/validate_workflows.py scripts/render_prompts.py scripts/run_dry.py
scripts/cost_estimate.py scripts/check_guardrails.py
docs/DEPLOY-RUNBOOK.md docs/UI-ONLY-CHECKLIST.md docs/COST-AND-APPROVALS.md docs/SOURCE-CLAIMS.md""".split()

SPEC_TOP_LEVEL_DIRS = {"config", "guardrails", "prompts", "workflows", "adapters", "data", "scripts", "docs"}
# Documented in README "Deviations from spec".
EXTRA_TOP_LEVEL_DIRS = {"tests"}
EXTRA_FILES = {"adapters/base.py", "adapters/mock_youtube.py", "config/yaml_lite.py"}
SKIP = {"__pycache__", "out"}


def repo_files():
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT)
        if p.is_file() and not any(part in SKIP for part in rel.parts[:-1]):
            yield p, rel.as_posix()


def read(p):
    return p.read_text(encoding="utf-8")


class FileTreeTest(unittest.TestCase):
    def test_spec_files_present(self):
        missing = [f for f in SPEC_FILES if not (ROOT / f).is_file()]
        self.assertEqual(missing, [])

    def test_no_unexpected_top_level_dirs(self):
        dirs = {p.name for p in ROOT.iterdir() if p.is_dir() and p.name not in SKIP}
        self.assertEqual(dirs, SPEC_TOP_LEVEL_DIRS | EXTRA_TOP_LEVEL_DIRS)

    def test_no_unexpected_files(self):
        allowed = set(SPEC_FILES) | EXTRA_FILES
        for _, rel in repo_files():
            if rel.startswith("tests/") or rel.endswith("__init__.py"):
                continue
            self.assertIn(rel, allowed)

    def test_env_absent(self):
        self.assertFalse((ROOT / ".env").exists())


class ContentRulesTest(unittest.TestCase):
    def test_no_banned_phrases_anywhere(self):
        banned = [t.lower() for t in claim_guard.BANNED_TERMS]
        for p, rel in repo_files():
            text = read(p).lower()
            for term in banned:
                self.assertNotIn(term, text, rel)

    def test_no_consumer_brand_literals(self):
        for p, rel in repo_files():
            text = read(p)
            for brand in claim_guard.CONSUMER_BRANDS:
                self.assertNotIn(brand, text, rel)

    def test_contacts_only_locked_or_synthetic(self):
        email_re = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
        phone_re = re.compile(r"(?<![\d-])\d{3}-\d{3}-\d{4}(?![\d-])")
        forbidden = "866" + "-566-" + "3445"
        for p, rel in repo_files():
            text = read(p)
            self.assertNotIn(forbidden, text, rel)
            for m in email_re.finditer(text):
                addr = m.group(0)
                domain = addr.split("@", 1)[1].lower()
                ok = domain == "example.com" or domain.endswith(".example.com")
                if rel == "config/constants.py" and addr == constants.OWNER_EMAIL:
                    ok = True
                self.assertTrue(ok, f"{rel}: {addr}")
            for m in phone_re.finditer(text):
                num = m.group(0)
                ok = num[4:10] == "555-01" or (rel == "config/constants.py" and num == constants.OWNER_PHONE)
                self.assertTrue(ok, f"{rel}: {num}")

    def test_ghl_location_id_only_in_constants(self):
        the_id = constants.GHL_BUILD_LOCATION_ID
        for p, rel in repo_files():
            if rel in ("config/constants.py", "tests/test_config.py"):
                continue
            self.assertNotIn(the_id, read(p), rel)
            self.assertNotIn(the_id.lower(), read(p).lower(), rel)

    def test_all_workflows_unverified(self):
        for p in (ROOT / "workflows").glob("*.json"):
            wf = json.loads(read(p))
            self.assertIs(wf["meta"]["verified"], False, p.name)
            for n in wf["nodes"]:
                self.assertTrue(n["notes"].strip(), (p.name, n["name"]))

    def test_fixtures_synthetic(self):
        leads = json.loads(read(ROOT / "data/fixtures/leads.sample.json"))["leads"]
        for lead in leads:
            self.assertIn("(synthetic)", lead["company"])
            self.assertTrue(lead["website"].endswith(".example.com"))
            self.assertTrue(lead["phone"][4:10] == "555-01")
            if lead["email"]:
                self.assertTrue(lead["email"].endswith(".example.com"))


class DocsTest(unittest.TestCase):
    def test_source_claims(self):
        text = read(ROOT / "docs/SOURCE-CLAIMS.md")
        rows = [l for l in text.splitlines() if re.match(r"\| C\d+ \|", l)]
        self.assertTrue(all(r.rstrip().endswith("| unverified |") for r in rows))
        lines = {int(r.split("|")[2]) for r in rows}
        self.assertTrue({15, 61, 107, 117} <= lines)
        for figure in ("$0.05/min", "$0.06/min", "$30/day", "$50/mo", "$100/mo", "$29/mo", "$22/mo",
                       "$30/mo", "$50-100/mo", "$300-400/mo", "10 calls at a time, unlimited/day"):
            self.assertIn(figure, text)

    def test_ui_only_checklist(self):
        text = read(ROOT / "docs/UI-ONLY-CHECKLIST.md")
        for n, title in enumerate(["AI Voice Call Agent", "Lead Generation AI", "AI UGC Ads Spy Generator",
                                   "Animated Faceless AI Videos", "Content Creation Agent",
                                   "Multilingual FAQ Chatbot", "Viral YouTube Video Idea Generator",
                                   "AI Avatar Generator"], 1):
            self.assertIn(f"## {n:02d} {title}", text)
        for name in ("GoHighLevel", "Meta Ads Manager", "Vapi", "Twilio", "Apify", "HeyGen", "ElevenLabs",
                     "Creatomate", "Ayrshare", "OpenAI", "Pinecone", "HubSpot", "Airtable", "Supabase",
                     "Slack", "Hunter.io", "Instantly", "Perplexity", "n8n Cloud", "coding-agent-inaccessible"):
            self.assertIn(name, text)

    def test_cost_and_approvals(self):
        text = read(ROOT / "docs/COST-AND-APPROVALS.md")
        self.assertIn("$650/mo", text)
        self.assertIn("waived", text)
        self.assertIn("$250 to $300 per booked appointment", text)
        self.assertIn("No purchase of any kind is authorized by this spec", text)
        self.assertIn("https://ca-jenterprises.com/ai", text)
        self.assertNotIn("setup fee of", text.lower())

    def test_runbook_columns(self):
        text = read(ROOT / "docs/DEPLOY-RUNBOOK.md")
        self.assertIn("| # | Action | Account | Cost | Approval required | Evidence to capture |", text)
        for word in ("n8n", "Vapi", "Twilio", "Apify", "HeyGen", "ElevenLabs", "Ayrshare", "Creatomate",
                     "OAuth", "HubSpot", "Supabase", "Airtable", "GoHighLevel"):
            self.assertIn(word, text)

    def test_readme(self):
        text = read(ROOT / "README.md")
        for needle in ("python3 -m unittest discover -s tests", "Deviations from spec", "scripts/run_dry.py",
                       "no charges", "meeting-first"):
            self.assertIn(needle, text.lower() if needle.islower() else text)


if __name__ == "__main__":
    unittest.main()

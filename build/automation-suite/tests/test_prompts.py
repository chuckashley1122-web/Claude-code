import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from guardrails import claim_guard, pricing_guard  # noqa: E402
from scripts import render_prompts as rp  # noqa: E402

SPEC_PROMPTS = sorted([
    "01_voice_receptionist_system", "02_lead_enrich", "02_cold_email", "02_followup", "03_ad_deconstruction",
    "03_sora_prompt_format", "04_faceless_script", "04_trending_topics", "05_content_script",
    "06_language_detect", "06_faq_rag", "06_translate", "07_youtube_analysis", "07_youtube_ideas",
    "08_heygen_script"])


class PromptFilesTest(unittest.TestCase):
    def test_exact_prompt_set(self):
        self.assertEqual(rp.list_prompt_ids(), SPEC_PROMPTS)

    def test_headers_and_mandatory_clauses(self):
        for pid in SPEC_PROMPTS:
            with self.subTest(pid=pid):
                p = rp.load_prompt(pid)
                self.assertEqual(p.id, pid)
                self.assertRegex(p.version, r"^\d+\.\d+\.\d+$")
                self.assertTrue(p.source.startswith("01-8-best-ai-automations.md:"))
                body = p.body
                self.assertIn("{{booking_url}}", body)  # (a) pricing intent -> booking URL
                self.assertIn("Never state, estimate, or hint at any amount of money", body)  # (a)
                self.assertIn("Never invent data", body)  # (c)
                self.assertIn("Never claim results, metrics, or case studies for CA-J", body)  # (d)
                self.assertNotIn("[result]", body)  # (b)
                self.assertNotIn("[pain]", body)

    def test_voice_prompt_keeps_source_rules_verbatim(self):
        body = rp.load_prompt("01_voice_receptionist_system").body
        for rule in ("Never invent times.", "Confirm email before sending.",
                     "If user repeats confusion 2x, escalate_to_human.", "Keep answers <25 words."):
            self.assertIn(rule, body)

    def test_every_prompt_passes_guards(self):
        for pid in SPEC_PROMPTS:
            text = (ROOT / "prompts" / f"{pid}.txt").read_text(encoding="utf-8")
            pricing_guard.assert_clean(text, pid)
            claim_guard.assert_no_claims(text, pid)


class RenderTest(unittest.TestCase):
    def test_render_fills_placeholders(self):
        p = rp.parse_prompt("id: t\nversion: 1.0.0\nsource: s\n---\nHi {{name}}, see {{ link }}.\n")
        self.assertEqual(p.placeholders, ["name", "link"])
        self.assertEqual(rp.render(p, {"name": "A", "link": "B", "extra": 1}), "Hi A, see B.\n")

    def test_missing_or_none_variable_hard_fails(self):
        p = rp.parse_prompt("id: t\nversion: 1\nsource: s\n---\nHi {{name}} {{x}}\n")
        with self.assertRaises(rp.UnresolvedPlaceholder) as cm:
            rp.render(p, {"name": None})
        self.assertEqual(cm.exception.names, ["name", "x"])

    def test_braces_left_after_render_fail(self):
        p = rp.parse_prompt("id: t\nversion: 1\nsource: s\n---\nHi {{name}}\n")
        with self.assertRaises(rp.UnresolvedPlaceholder):
            rp.render(p, {"name": "{{sneaky}}"})

    def test_bad_header(self):
        with self.assertRaises(rp.PromptFormatError):
            rp.parse_prompt("no header here")
        with self.assertRaises(rp.PromptFormatError):
            rp.parse_prompt("id: a\n---\nbody")
        with self.assertRaises(rp.PromptFormatError):
            rp.parse_prompt("id: a\nversion: 1\nsource: s\n---\nbody", expected_id="b")

    def test_fixture_bindings_cover_every_prompt(self):
        b = rp.fixture_bindings()
        for pid in SPEC_PROMPTS:
            rendered = rp.render(rp.load_prompt(pid), b[pid])
            self.assertNotIn("{{", rendered)

    def run_main(self, argv):
        with tempfile.TemporaryDirectory() as tmp:
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = rp.main(argv + ["--out-dir", tmp])
            files = sorted(p.name for p in (Path(tmp) / "prompts").glob("*"))
            return code, buf.getvalue(), files

    def test_main_renders_all(self):
        code, out, files = self.run_main([])
        self.assertEqual(code, 0, out)
        self.assertEqual(len(files), 15)
        self.assertIn("15/15 prompts rendered; 0 failed", out)

    def test_main_withheld_variable_exits_nonzero(self):
        code, out, _ = self.run_main(["--withhold", "trending_topic"])
        self.assertEqual(code, 1)
        self.assertIn("UNRESOLVED placeholders in 04_faceless_script: trending_topic", out)
        code, _, _ = self.run_main(["--prompt", "02_cold_email", "--withhold", "booking_url"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()

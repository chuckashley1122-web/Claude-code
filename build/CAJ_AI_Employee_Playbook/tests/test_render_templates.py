import json
import shutil
import tempfile
import unittest
from pathlib import Path

from _paths import ROOT
from scripts import render_templates as rt

VARS = {
    "business": "Example Heating and Air (synthetic)",
    "first_name": "Alex",
    "specific_available_time": "Tuesday at 10 a.m. Central",
    "sender_mailing_address": "Mailing line (synthetic)",
    "demo_evidence_ref": "out/demo-log.txt",
    "handoff_rule": "the transfer rule in agent/handoff-rule.md",
    "followup_task": "a callback task for the dispatcher",
}


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _vars(self, data):
        p = self.tmp / "vars.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_default_email_renders_with_zero_placeholders(self):
        out = self.tmp / "email.txt"
        self.assertEqual(rt.main(["--out", str(out)]), 0)
        text = out.read_text(encoding="utf-8")
        self.assertNotIn("{{", text)
        self.assertNotIn("#!", text)
        self.assertIn("I can prepare a short AI demo", text)
        self.assertIn("Owner: Chuck Ashley | 512-229-9199 | chuck@ca-jconsulting.com", text)
        self.assertIn("CA&J Enterprises LLC", text)
        self.assertIn("If this is not relevant, reply no and I will stop following up.", text)
        self.assertIn("https://ca-jenterprises.com/ai", text)

    def test_withheld_variable_fails(self):
        self.assertEqual(rt.main(["--omit", "first_name", "--out", str(self.tmp / "x")]), 3)
        partial = dict(VARS)
        del partial["business"]
        self.assertEqual(rt.main(["--vars", str(self._vars(partial)), "--out", str(self.tmp / "x")]), 3)

    def test_price_in_vars_is_blocked(self):
        priced = dict(VARS, business="Only $650 per month")
        self.assertEqual(rt.main(["--vars", str(self._vars(priced)), "--out", str(self.tmp / "x")]), 4)

    def test_claim_in_vars_is_blocked(self):
        bad = dict(VARS, first_name="Alex, we recovered 40 calls for clients")
        with self.assertRaises(rt.ClaimBlocked):
            rt.render_text((ROOT / "outreach" / "dm-draft.txt").read_text(encoding="utf-8"), bad)

    def test_nested_placeholder_in_value_rejected(self):
        with self.assertRaises(rt.UnresolvedPlaceholder):
            rt.load_vars(self._vars({"business": "{{first_name}}"}))

    def test_post_demo_email_requires_evidence(self):
        raw = (ROOT / "outreach" / "email-post-demo.txt").read_text(encoding="utf-8")
        with self.assertRaises(rt.EvidenceGate):
            rt.render_text(raw, dict(VARS, demo_evidence_ref="NEEDS_EVIDENCE"))
        self.assertIn("I prepared a demo for", rt.render_text(raw, VARS).text)

    def test_for_send_refuses_needs_evidence(self):
        raw = (ROOT / "outreach" / "email-draft.txt").read_text(encoding="utf-8")
        v = dict(VARS, sender_mailing_address="NEEDS_EVIDENCE: address")
        self.assertTrue(rt.render_text(raw, v).warnings)
        with self.assertRaises(rt.EvidenceGate):
            rt.render_text(raw, v, for_send=True)

    def test_system_prompt_bracket_placeholders(self):
        raw = (ROOT / "agent" / "system-prompt.md").read_text(encoding="utf-8")
        for b in ("[BUSINESS]", "[HANDOFF RULE]", "[FOLLOWUP TASK]"):
            self.assertIn(b, raw)
        result = rt.render_text(raw, VARS)
        self.assertEqual(result.channel, "internal_instructions")
        self.assertIn("You are the AI assistant for Example Heating and Air (synthetic).", result.text)
        self.assertNotIn("[HANDOFF RULE]", result.text)
        missing = {k: v for k, v in VARS.items() if k != "handoff_rule"}
        with self.assertRaises(rt.UnresolvedPlaceholder):
            rt.render_text(raw, missing)

    def test_all_outreach_templates_render(self):
        for name in ("email-draft.txt", "email-post-demo.txt", "dm-draft.txt", "call-script.txt"):
            with self.subTest(name=name):
                res = rt.render_text((ROOT / "outreach" / name).read_text(encoding="utf-8"), VARS)
                self.assertIn("https://ca-jenterprises.com/ai", res.text)

    def test_missing_channel_and_unknown_channel(self):
        with self.assertRaises(rt.RenderError):
            rt.render_text("Hi {{first_name}}", VARS)
        with self.assertRaises(ValueError):
            rt.render_text("Hi {{first_name}}", VARS, channel="fax")

    def test_facts_form(self):
        out = self.tmp / "form.md"
        self.assertEqual(rt.main(["--facts-form", "--out", str(out)]), 0)
        text = out.read_text(encoding="utf-8")
        self.assertEqual(text.count("- Answer:"), 14)
        self.assertIn("## 9. Approved pricing language", text)


if __name__ == "__main__":
    unittest.main()

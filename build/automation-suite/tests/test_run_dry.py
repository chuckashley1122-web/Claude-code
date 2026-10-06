import copy
import io
import json
import socket
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import constants  # noqa: E402
from scripts import run_dry  # noqa: E402

WF = ROOT / "workflows"


def ctx_for(out_dir, **kw):
    return run_dry.RunContext("test", run_dry.make_adapters(True, out_dir), out_dir, "run-test", **kw)


class TmpOut(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def run_wf(self, stem, **kw):
        report, path = run_dry.run_one(WF / f"{stem}.json", self.out, **kw)
        return report

    def executed(self, report, node):
        return [s for s in report["steps"] if s["node"] == node]

    def terminal(self, report):
        return [i for items in report["terminal_items"].values() for i in items]


class ExpressionTest(TmpOut):
    def test_paths_subscripts_vars_math(self):
        ctx = ctx_for(self.out, today=date(2026, 10, 5))
        item = {"a": {"b": [10, 20]}, "n": 3, "s": "x", "likes": 50, "views": 200}
        ev = lambda e: run_dry.eval_expression(e, item, ctx)  # noqa: E731
        self.assertEqual(ev("$json.a.b[1]"), 20)
        self.assertIsNone(ev("$json.a.missing"))
        self.assertIsNone(ev("$json.a.b[9]"))
        self.assertEqual(ev("$json.n + 1"), 4)
        self.assertEqual(ev("$json.likes / $json.views"), 0.25)
        self.assertIsNone(ev("$json.n / 0"))
        self.assertEqual(ev("$json.s + ' and ' + $json.n"), "x and 3")
        self.assertEqual(ev("$vars.BOOKING_URL"), constants.BOOKING_URL)
        self.assertEqual(ev("$today"), "2026-10-05")
        self.assertEqual(ev("$today.plusDays(3)"), "2026-10-08")
        self.assertEqual(ev("$today.plusDays(-30)"), "2026-09-05")
        self.assertEqual(ev("-$json.n"), -3)

    def test_rejects_unsafe_syntax(self):
        ctx = ctx_for(self.out)
        for expr in ("__import__('os')", "$json.__class__", "open('x')", "[1,2]", "$json.n if 1 else 2",
                     "lambda: 1", "$json.s.upper()"):
            with self.subTest(expr=expr):
                with self.assertRaises(run_dry.ExpressionError):
                    run_dry.eval_expression(expr, {"n": 1, "s": "x"}, ctx)

    def test_resolve(self):
        ctx = ctx_for(self.out)
        item = {"name": "Pat", "n": 2, "lst": [1]}
        self.assertEqual(run_dry.resolve("=Hi {{ $json.name }} x{{ $json.n }}", item, ctx), "Hi Pat x2")
        self.assertEqual(run_dry.resolve("={{ $json.lst }}", item, ctx), [1])  # raw value kept
        self.assertEqual(run_dry.resolve({"a": ["={{ $json.n }}", "plain {{ $json.n }}"]}, item, ctx),
                         {"a": [2, "plain {{ $json.n }}"]})


class NetworkBlockTest(unittest.TestCase):
    def test_no_network_blocks_and_restores(self):
        counter = run_dry.EgressCounter()
        original = socket.create_connection
        with run_dry.no_network(counter):
            with self.assertRaises(run_dry.NetworkBlocked):
                socket.create_connection(("example.com", 443), timeout=1)
            with self.assertRaises(run_dry.NetworkBlocked):
                socket.getaddrinfo("example.com", 443)
            with socket.socket() as sock, self.assertRaises(run_dry.NetworkBlocked):
                sock.connect(("127.0.0.1", 9))
        self.assertEqual(counter.attempts, 3)
        self.assertIs(socket.create_connection, original)


class AllWorkflowsTest(TmpOut):
    def test_main_runs_all_eight_offline_and_writes_eight_reports(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_dry.main(["--out-dir", str(self.out)])
        self.assertEqual(code, 0, buf.getvalue())
        reports = sorted((self.out / "runs").glob("*.json"))
        self.assertEqual(len(reports), 8)
        for path in reports:
            r = json.loads(path.read_text())
            self.assertEqual(r["status"], "success", path.name)
            self.assertEqual(r["network_egress_attempts"], 0)
            self.assertTrue(r["dry_run"])
            self.assertTrue(r["synthetic"])
            # every node in the workflow graph that is reachable was walked at least once
            wf = json.loads((WF / r["file"]).read_text())
            walked = {s["node"] for s in r["steps"]}
            # The reply-stop branch needs a seeded reply; test_02_reply_stops_sequence covers it.
            not_hit = {"02_lead_generation.json": {"Stop Sequence (replied)"}}.get(r["file"], set())
            self.assertEqual(walked, {n["name"] for n in wf["nodes"]} - not_hit, r["file"])
        self.assertIn("8/8 workflows completed offline", buf.getvalue())

    def test_main_selects_one_workflow(self):
        with redirect_stdout(io.StringIO()):
            code = run_dry.main(["--out-dir", str(self.out), "--workflow", "07_youtube_ideas"])
        self.assertEqual(code, 0)
        self.assertEqual(len(list((self.out / "runs").glob("*.json"))), 1)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(run_dry.main(["--out-dir", str(self.out), "--workflow", "nope"]), 1)


class BranchBehaviourTest(TmpOut):
    def test_01_voice_branches(self):
        r = self.run_wf("01_voice_call_agent")
        by_call = {i["call_id"]: i for i in self.terminal(r)}
        self.assertEqual(len(by_call), 4)
        booked = by_call["dryrun-call-001"]
        self.assertEqual(booked["event"]["time"], "09:00")  # first offered slot, never invented
        self.assertEqual(booked["email_record"]["status"], "draft_written_not_sent")
        pricing = by_call["dryrun-call-002"]
        self.assertTrue(pricing["pricing_intent"])
        self.assertIn(constants.BOOKING_URL, pricing["agent_reply"])
        self.assertNotIn("event", pricing)
        confused = by_call["dryrun-call-003"]
        self.assertEqual(confused["transfer"]["kind"], "call_transfer_intent")
        faq = by_call["dryrun-call-004"]
        self.assertIn("Fixture City", faq["agent_reply"])
        self.assertTrue(all("crm_contact_id" in i for i in by_call.values()))
        emls = list((self.out / "mail").glob("*.eml"))
        self.assertEqual(len(emls), 1)

    def test_02_qualify_outreach_followup(self):
        r = self.run_wf("02_lead_generation")
        qualify = self.executed(r, "Qualify Leads")
        self.assertEqual(sum(s["outputs"][0] for s in qualify), 2)
        sent = self.executed(r, "Send Outreach Email")[0]
        self.assertEqual(sent["outputs"], [2])
        follow = self.executed(r, "Send Follow-up")[0]
        self.assertEqual(follow["outputs"], [2])
        updated = r["terminal_items"]["Update Follow-up State"]
        self.assertTrue(all(i["followup_count"] == 1 for i in updated))
        bodies = [p.read_text() for p in (self.out / "mail").glob("*.eml")]
        self.assertEqual(len(bodies), 4)
        self.assertTrue(all("no thanks" in b for b in bodies))
        recipients = {i["email"] for i in r["terminal_items"]["Mark Contacted"]}
        self.assertEqual(recipients, {"owner@hvac01.example.com", "team@hvac05.example.com"})

    def test_02_reply_stops_sequence(self):
        wf = json.loads((WF / "02_lead_generation.json").read_text())
        ctx = ctx_for(self.out)
        ctx.adapters.mailer.record_reply("owner@hvac01.example.com")
        r = run_dry.execute(wf, ctx)
        stopped = r["terminal_items"]["Stop Sequence (replied)"]
        self.assertEqual([i["email"] for i in stopped], ["owner@hvac01.example.com"])

    def test_02_daily_cap_limits_sends(self):
        wf = json.loads((WF / "02_lead_generation.json").read_text())
        ctx = ctx_for(self.out)
        ctx.vars = {**ctx.vars, "DAILY_EMAIL_CAP_PER_INBOX": 1}
        r = run_dry.execute(wf, ctx)
        self.assertEqual(self.executed(r, "Send Outreach Email")[0]["items_in"], 1)
        self.assertTrue(any("capped 2 items to 1" in n for n in ctx.notes))

    def test_03_five_prompts_five_stub_jobs(self):
        r = self.run_wf("03_ugc_ads_spy")
        self.assertEqual(self.executed(r, "Create UGC Video (Sora)")[0]["outputs"], [5])
        self.assertEqual(len(list((self.out / "video_jobs").glob("sora-video-*.json"))), 5)

    def test_04_metrics_are_null_not_invented(self):
        r = self.run_wf("04_faceless_video")
        logged = r["terminal_items"]["Log Performance (Airtable)"]
        self.assertEqual(len(logged), 3)
        self.assertTrue(all(i["views"] is None and i["status"] == "not_published_dry_run" for i in logged))

    def test_05_loop_iterations(self):
        r1 = self.run_wf("05_content_agent")
        self.assertEqual(len(self.executed(r1, "Topic Research")), 1)
        self.assertTrue(r1["loops_halted"])
        r2 = self.run_wf("05_content_agent", loop_iterations=3)
        self.assertEqual(len(self.executed(r2, "Topic Research")), 3)

    def test_06_chat_paths(self):
        r = self.run_wf("06_faq_chatbot")
        replies = {i["session_id"]: i["reply_text"] for i in self.terminal(r)}
        self.assertIn(constants.BOOKING_URL, replies["chat-003"])
        self.assertIn("Open times: 09:00", replies["chat-001"])
        self.assertTrue(replies["chat-002"].startswith("[es] "))
        self.assertIn("team member will follow up", replies["chat-004"])
        self.assertEqual(len(self.executed(r, "Escalate to Human (Slack)")), 1)

    def test_07_engagement_and_ideas(self):
        r = self.run_wf("07_youtube_ideas")
        item = r["terminal_items"]["Email Report"][0]
        self.assertEqual(len(item["ideas"]), 10)
        ratios = [a["engagement_ratio"] for a in item["analyses"]]
        self.assertAlmostEqual(ratios[0], 450 / 15000)

    def test_08_avatar_pipeline(self):
        r = self.run_wf("08_avatar_generator")
        self.assertEqual(self.executed(r, "Done?")[0]["outputs"], [1, 0])
        self.assertEqual(len(list((self.out / "exports").glob("*.json"))), 1)


class ErrorPathTest(TmpOut):
    def load(self, stem):
        return json.loads((WF / f"{stem}.json").read_text())

    def run_with_handler(self, wf, dry_run=True):
        ctx = run_dry.RunContext("t", run_dry.make_adapters(dry_run, self.out), self.out, "run-err", dry_run=dry_run)
        return run_dry.execute(wf, ctx, None, self.load("_common_error_handler"))

    def error_record(self, report):
        files = report["error_handler"]["error_records"]
        self.assertEqual(len(files), 1)
        return json.loads(Path(files[0]).read_text())

    def test_unknown_http_endpoint_routes_to_error_workflow(self):
        wf = self.load("04_faceless_video")
        node = next(n for n in wf["nodes"] if n["name"] == "Voiceover (ElevenLabs)")
        node["parameters"]["url"] = "https://api.unknown-vendor.invalid/v1/x"
        r = self.run_with_handler(wf)
        self.assertEqual(r["status"], "error")
        self.assertEqual(r["error"]["node"], "Voiceover (ElevenLabs)")
        rec = self.error_record(r)
        self.assertEqual(rec["workflow"], wf["name"])
        self.assertEqual(rec["node"], "Voiceover (ElevenLabs)")
        self.assertIn("no offline adapter", rec["message"])
        self.assertIs(rec["synthetic"], True)
        self.assertEqual(rec["external_action"], "none")
        self.assertTrue(rec["timestamp"])
        self.assertTrue(Path(r["error_handler"]["error_records"][0]).parent.name == "errors")

    def test_injected_price_is_blocked_before_send(self):
        wf = self.load("01_voice_call_agent")
        node = next(n for n in wf["nodes"] if n["name"] == "Compose Confirmation")
        node["parameters"]["assignments"]["confirmation_body"] = "Confirmed. Our tech fee is $650 per month."
        r = self.run_with_handler(wf)
        self.assertEqual(r["status"], "error")
        self.assertEqual(r["error"]["node"], "Pricing Guard (confirmation)")
        self.assertEqual(r["error"]["type"], "PricingViolation")
        self.assertFalse((self.out / "mail").exists())

    def test_guard_inside_mailer_catches_bypass(self):
        wf = self.load("01_voice_call_agent")
        node = next(n for n in wf["nodes"] if n["name"] == "Send Confirmation Email")
        node["parameters"]["message"] = "Setup fee waived!"
        r = self.run_with_handler(wf)
        self.assertEqual(r["error"]["node"], "Send Confirmation Email")
        self.assertEqual(r["error"]["type"], "PricingViolation")

    def test_unsupported_node_type(self):
        wf = self.load("07_youtube_ideas")
        wf["nodes"][1]["type"] = "n8n-nodes-base.somethingNew"
        r = self.run_with_handler(wf)
        self.assertEqual(r["error"]["type"], "UnsupportedNode")
        self.error_record(r)

    def test_live_mode_adapters_refuse(self):
        r = self.run_with_handler(self.load("07_youtube_ideas"), dry_run=False)
        self.assertEqual(r["status"], "error")
        self.assertEqual(r["error"]["type"], "NotAuthorized")
        self.assertIn("LIVE CALL BLOCKED", r["error"]["message"])

    def test_apollo_actor_is_refused(self):
        wf = self.load("02_lead_generation")
        node = next(n for n in wf["nodes"] if n["name"] == "Scrape Leads (Apify)")
        node["parameters"]["actorId"] = "apollo-io-scraper"
        r = self.run_with_handler(wf)
        self.assertEqual(r["error"]["type"], "ActorNotApproved")

    def test_main_refuses_live_without_allow_live(self):
        import os
        saved = dict(os.environ)
        try:
            os.environ["DRY_RUN"] = "false"
            os.environ.pop("ALLOW_LIVE", None)
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as cm:
                import contextlib
                with contextlib.redirect_stderr(io.StringIO()):
                    run_dry.main(["--out-dir", str(self.out)])
            self.assertEqual(cm.exception.code, 2)
        finally:
            os.environ.clear()
            os.environ.update(saved)

    def test_step_limit_and_unknown_connection(self):
        wf = copy.deepcopy(self.load("07_youtube_ideas"))
        wf["connections"]["Weekly Monday 7am"]["main"][0].append({"node": "Ghost", "type": "main", "index": 0})
        with self.assertRaises(run_dry.WorkflowError):
            run_dry.execute(wf, ctx_for(self.out))


if __name__ == "__main__":
    unittest.main()

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from src import inquiry_handler as H  # noqa: E402
from src.ghl_adapter import (GHLAdapter, MockGHLAdapter, UpstreamPermissionError, UpstreamThrottled,  # noqa: E402
                             UpstreamTimeout, UpstreamUnavailable, UpstreamValidationError)
from src.idempotency_store import IdempotencyStore  # noqa: E402

CFG = {"service_allowlist": ["synthetic_test_service"], "allowed_source_origins": ["https://example.com"]}
NODE = shutil.which("node")


def body(submission_id="synthetic-0001", **overrides):
    b = {"submission_id": submission_id, "name": "Synthetic Tester", "email": "tester@example.com",
         "phone": "512-555-0100", "service_interest": "synthetic_test_service",
         "message": "Synthetic test.", "source_page": "https://example.com/contact"}
    b.update(overrides)
    return json.dumps(b)


class HandlerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.sleeps = []

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, adapter, name="h", **kw):
        store = IdempotencyStore(Path(self.tmp.name) / f"{name}.db")
        return H.InquiryHandler(adapter, store, config=CFG, sleep=self.sleeps.append, **kw)

    def test_saved_returns_201_with_opaque_reference_only(self):
        mock = MockGHLAdapter()
        r = self.make(mock).handle(body())
        self.assertEqual(r.status, 201)
        self.assertTrue(r.body["inquiry_reference"].startswith("inq_"))
        self.assertNotIn("mocki_", json.dumps(r.body))
        self.assertEqual(r.body["next_step"], C.BOOKING_URL)
        self.assertEqual(mock.inquiries[0]["location_id"], C.GHL_LOCATION_ID)  # from server config

    def test_replay_returns_prior_outcome_without_second_record(self):
        mock = MockGHLAdapter()
        h = self.make(mock)
        first, second = h.handle(body()), h.handle(body())
        self.assertEqual((first.status, first.body), (second.status, second.body))
        self.assertEqual(second.headers.get("Idempotent-Replay"), "true")
        self.assertEqual(len(mock.inquiries), 1)
        self.assertEqual(len(mock.calls), 1)

    def test_validation_errors_never_reach_adapter(self):
        mock = MockGHLAdapter()
        h = self.make(mock)
        self.assertEqual(h.handle(b"").status, 400)
        self.assertEqual(h.handle(b"[1,2]").status, 400)
        self.assertEqual(h.handle(b"x" * (C.MAX_PAYLOAD_BYTES + 1)).status, 400)
        r = h.handle(body(location_id="other", tags="vip"))
        self.assertEqual(r.status, 422)
        self.assertIn({"field": "location_id", "code": "privileged_field_rejected"}, r.body["errors"])
        self.assertEqual(mock.calls, [])

    def test_shipped_config_rejects_everything_until_allowlist_supplied(self):
        mock = MockGHLAdapter()
        h = H.InquiryHandler(mock, IdempotencyStore(Path(self.tmp.name) / "d.db"), sleep=self.sleeps.append)
        r = h.handle(body())
        self.assertEqual(r.status, 422)
        self.assertEqual(mock.calls, [])

    def test_transient_failures_retried_twice_with_backoff_same_id(self):
        mock = MockGHLAdapter(script=[UpstreamUnavailable(), UpstreamTimeout()])
        r = self.make(mock).handle(body())
        self.assertEqual(r.status, 201)
        self.assertEqual([c["submission_id"] for c in mock.calls], ["synthetic-0001"] * 3)
        self.assertEqual(self.sleeps, [0.5, 1.0])
        self.assertEqual(mock.calls[0]["timeout_s"], C.UPSTREAM_TIMEOUT_S)

    def test_retries_bounded_then_503_no_false_success(self):
        mock = MockGHLAdapter(script=[UpstreamUnavailable()] * 5)
        h = self.make(mock)
        r = h.handle(body())
        self.assertEqual(r.status, 503)
        self.assertEqual(len(mock.calls), C.MAX_RETRIES + 1)
        self.assertEqual(r.body["fallback_booking_url"], C.BOOKING_URL)
        self.assertTrue(r.body["retain_form_values"])
        # network retry with the same id is allowed after a failure and succeeds once
        mock.script.clear()
        self.assertEqual(h.handle(body()).status, 201)
        self.assertEqual(len(mock.inquiries), 1)

    def test_permission_and_validation_errors_not_retried(self):
        for exc in (UpstreamPermissionError("token rejected"), UpstreamValidationError("bad field")):
            with self.subTest(exc=type(exc).__name__):
                mock = MockGHLAdapter(script=[exc])
                r = self.make(mock, name=type(exc).__name__).handle(body())
                self.assertEqual(r.status, 502)
                self.assertEqual(len(mock.calls), 1)

    def test_upstream_retry_after_respected(self):
        mock = MockGHLAdapter(script=[UpstreamThrottled(retry_after=3)])
        self.assertEqual(self.make(mock).handle(body()).status, 201)
        self.assertEqual(self.sleeps, [3])
        mock2 = MockGHLAdapter(script=[UpstreamThrottled(retry_after=120)])
        r = self.make(mock2, name="long").handle(body())
        self.assertEqual(r.status, 503)
        self.assertEqual(r.headers["Retry-After"], "120")
        self.assertEqual(len(mock2.calls), 1)

    def test_timeout_is_enforced_by_handler(self):
        slow = MockGHLAdapter(delay_s=0.3)
        r = self.make(slow, timeout_s=0.05).handle(body())
        self.assertEqual(r.status, 503)
        self.assertEqual(len(slow.calls), C.MAX_RETRIES + 1)

    def test_202_only_with_durable_queue(self):
        no_queue = MockGHLAdapter(script=["queued"])
        r = self.make(no_queue, name="nq").handle(body())
        self.assertEqual(r.status, 502)
        queue = MockGHLAdapter(script=["queued"], durable_queue=True)
        r = self.make(queue, name="q").handle(body())
        self.assertEqual(r.status, 202)
        self.assertIn("received for processing", r.body["message"])
        self.assertNotIn("saved", r.body["message"].lower())

    def test_unconfirmed_save_is_not_success(self):
        r = self.make(MockGHLAdapter(script=["unconfirmed"])).handle(body())
        self.assertEqual(r.status, 502)

    def test_live_adapter_blocked_maps_to_503_without_retry(self):
        r = self.make(GHLAdapter()).handle(body())
        self.assertEqual(r.status, 503)
        self.assertEqual(r.body["error"], "crm_integration_not_configured")
        self.assertEqual(self.sleeps, [])

    def test_rate_limiter_429(self):
        t = [0.0]
        limiter = H.FixedWindowRateLimiter(1, 60, clock=lambda: t[0])
        h = self.make(MockGHLAdapter(), rate_limiter=limiter)
        self.assertEqual(h.handle(body(), client_key="ip1").status, 201)
        self.assertEqual(h.handle(body("synthetic-0002"), client_key="ip1").status, 429)
        t[0] = 61
        self.assertEqual(h.handle(body("synthetic-0002"), client_key="ip1").status, 201)

    def test_in_flight_duplicate(self):
        store = IdempotencyStore(Path(self.tmp.name) / "if.db")
        store.begin("synthetic-0001")
        h = H.InquiryHandler(MockGHLAdapter(), store, config=CFG, sleep=self.sleeps.append)
        r = h.handle(body())
        self.assertEqual(r.status, 503)
        self.assertEqual(r.body["error"], "submission_in_progress")

    def test_logs_contain_no_pii(self):
        mock = MockGHLAdapter(script=[UpstreamUnavailable()])
        h = self.make(mock)
        h.handle(body())
        h.handle(body("synthetic-0009", email="bad"))
        dumped = json.dumps(h.log_records)
        for pii in ("Synthetic Tester", "tester@example.com", "5125550100", "512-555-0100"):
            self.assertNotIn(pii, dumped)


class TypeScriptServerFunction(unittest.TestCase):
    def test_no_secrets_or_hardcoded_ids(self):
        ts = H.render_ts()
        self.assertIn("process.env.GHL_ACCESS_TOKEN", ts)
        for forbidden in (C.GHL_LOCATION_ID, C.DISALLOWED_LOCATION_ID, "Bearer "):
            self.assertNotIn(forbidden, ts)
        self.assertNotIn("__", ts.replace("__proto__", ""))  # every template slot filled

    @unittest.skipUnless(NODE, "node not installed")
    def test_node_syntax_check_and_runtime_parity(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            ts_path = td / "inquiry.ts"
            ts_path.write_text(H.render_ts(), encoding="utf-8")
            js_path = td / "inquiry.mjs"
            strip = ("const m=require('node:module');const fs=require('fs');"
                     "fs.writeFileSync(process.argv[2], m.stripTypeScriptTypes(fs.readFileSync(process.argv[1],'utf8')));")
            done = subprocess.run([NODE, "--no-warnings", "-e", strip, str(ts_path), str(js_path)],
                                  capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            check = subprocess.run([NODE, "--check", str(js_path)], capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stderr)

            # a broken TS file must fail the same pipeline (proves the check is real)
            bad = td / "bad.ts"
            bad.write_text("export function f(a: number {", encoding="utf-8")
            broken = subprocess.run([NODE, "--no-warnings", "-e", strip, str(bad), str(td / "bad.mjs")],
                                    capture_output=True, text=True)
            self.assertNotEqual(broken.returncode, 0)

            harness = td / "harness.mjs"
            harness.write_text(HARNESS, encoding="utf-8")
            env = {k: v for k, v in os.environ.items()
                   if not k.startswith(("GHL_", "SERVICE_ALLOWLIST", "ALLOWED_SOURCE_ORIGINS"))}
            run = subprocess.run([NODE, "--no-warnings", str(harness)], capture_output=True, text=True, cwd=td,
                                 timeout=60, env=env)
            self.assertEqual(run.returncode, 0, run.stderr)
            out = json.loads(run.stdout)
            self.assertEqual(out["saved"]["status"], 201)
            self.assertTrue(out["saved"]["ref"].startswith("inq_"))
            self.assertEqual(out["replay"], {"status": 201, "same": True, "records": 1, "replayHeader": "true"})
            self.assertEqual(out["privileged"], 422)
            self.assertEqual(out["empty"], 400)
            self.assertEqual(out["retry"], {"status": 201, "calls": 3, "sleeps": [500, 1000]})
            self.assertEqual(out["permission"], {"status": 502, "calls": 1})
            self.assertEqual(out["notConfigured"], 503)
            self.assertEqual(out["noStore"], 503)
            self.assertEqual(out["queuedNoDurable"], 502)
            self.assertEqual(out["queuedDurable"], 202)
            self.assertEqual(out["unsetAllowlist"], 422)
            self.assertNotIn("Synthetic Tester", json.dumps(out["logs"]))


HARNESS = r"""
import * as fn from "./inquiry.mjs";
const cfg = { serviceAllowlist: ["synthetic_test_service"], allowedSourceOrigins: ["https://example.com"] };
function memStore() {
  const m = new Map();
  return {
    async begin(id) {
      const p = m.get(id);
      if (!p || p.state === "failed") { m.set(id, { state: "in_flight", status: null, body: null }); return { claimed: true, prior: p || null }; }
      return { claimed: false, prior: p };
    },
    async complete(id, o) { m.set(id, o); },
  };
}
function mockAdapter(script = [], durableQueue = false) {
  const a = { durableQueue, calls: 0, records: 0,
    async saveInquiry() {
      a.calls++;
      const step = script.shift();
      if (step instanceof Error) throw step;
      if (step === "queued") return { outcome: "queued", reference: "q1" };
      a.records++;
      return { outcome: "saved", reference: "c" + a.records };
    } };
  return a;
}
const logs = [];
function deps(adapter, store = memStore(), sleeps = []) {
  return { adapter, store, config: cfg, serverConfig: { location_id: "from-env" },
           sleep: async (ms) => { sleeps.push(ms); }, log: (e) => logs.push(e) };
}
const good = (id = "synthetic-0001", extra = {}) => JSON.stringify(Object.assign({ submission_id: id,
  name: "Synthetic Tester", email: "tester@example.com", service_interest: "synthetic_test_service" }, extra));
const out = { logs };
let a = mockAdapter(); let d = deps(a);
const r1 = await fn.handleInquiry(good(), d);
out.saved = { status: r1.status, ref: r1.body.inquiry_reference };
const r2 = await fn.handleInquiry(good(), d);
out.replay = { status: r2.status, same: JSON.stringify(r1.body) === JSON.stringify(r2.body), records: a.records,
               replayHeader: r2.headers["Idempotent-Replay"] };
out.privileged = (await fn.handleInquiry(good("synthetic-0002", { pipeline_id: "x" }), d)).status;
out.empty = (await fn.handleInquiry("", d)).status;
const sleeps = [];
a = mockAdapter([new fn.UpstreamError("down", true, 503), new fn.UpstreamError("down", true, 503)]);
const rr = await fn.handleInquiry(good("synthetic-0003"), deps(a, memStore(), sleeps));
out.retry = { status: rr.status, calls: a.calls, sleeps };
a = mockAdapter([new fn.UpstreamError("token rejected", false, 502)]);
const rp = await fn.handleInquiry(good("synthetic-0004"), deps(a));
out.permission = { status: rp.status, calls: a.calls };
out.notConfigured = (await fn.handleInquiry(good("synthetic-0005"), deps(fn.createGhlAdapterFromEnv()))).status;
out.noStore = (await fn.handleInquiry(good("synthetic-0006"), deps(mockAdapter(), null))).status;
out.queuedNoDurable = (await fn.handleInquiry(good("synthetic-0007"), deps(mockAdapter(["queued"], false)))).status;
out.queuedDurable = (await fn.handleInquiry(good("synthetic-0008"), deps(mockAdapter(["queued"], true)))).status;
const dd = deps(mockAdapter()); dd.config = fn.configFromEnv();
out.unsetAllowlist = (await fn.handleInquiry(good("synthetic-0009"), dd)).status;
console.log(JSON.stringify(out));
"""


if __name__ == "__main__":
    unittest.main()

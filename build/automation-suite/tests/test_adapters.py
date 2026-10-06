import email
import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters import (mock_apify, mock_calendar, mock_crm, mock_mailer, mock_openai,  # noqa: E402
                      mock_publisher, mock_video_gen, mock_youtube)
from adapters.base import LiveCallBlocked, NotAuthorized, endpoint_is_local  # noqa: E402
from guardrails import claim_guard, pricing_guard  # noqa: E402
from scripts import render_prompts  # noqa: E402

MOCKS = [mock_openai.MockOpenAI, mock_calendar.MockCalendar, mock_crm.MockCRM, mock_mailer.MockMailer,
         mock_video_gen.MockVideoGen, mock_apify.MockApify, mock_publisher.MockPublisher, mock_youtube.MockYouTube]
LIVES = [mock_openai.LiveOpenAI, mock_calendar.LiveCalendar, mock_crm.LiveCRM, mock_mailer.LiveMailer,
         mock_video_gen.LiveVideoGen, mock_apify.LiveApify, mock_publisher.LivePublisher, mock_youtube.LiveYouTube]


class TmpOut(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def make(self, cls, **kw):
        return cls(out_dir=self.out, **kw)


class BaseTest(TmpOut):
    def test_endpoint_is_local(self):
        for ep in (None, "", "file:///x", "http://localhost:8080", "https://api.example.com", "http://127.0.0.1"):
            self.assertTrue(endpoint_is_local(ep), ep)
        for ep in ("https://api.openai.com/v1", "https://api.heygen.com"):
            self.assertFalse(endpoint_is_local(ep), ep)

    def test_every_mock_refuses_a_real_endpoint_in_dry_run(self):
        calls = {
            mock_openai.MockOpenAI: lambda a: a.transcribe("synthetic-ad-001"),
            mock_calendar.MockCalendar: lambda a: a.availability("2026-10-06"),
            mock_crm.MockCRM: lambda a: a.query("t", []),
            mock_mailer.MockMailer: lambda a: a.has_reply("a@example.com"),
            mock_video_gen.MockVideoGen: lambda a: a.create_job("heygen", "avatar", {}),
            mock_apify.MockApify: lambda a: a.run_actor("google-maps-scraper", {}),
            mock_publisher.MockPublisher: lambda a: a.notify("#x", "hi"),
            mock_youtube.MockYouTube: lambda a: a.search("q"),
        }
        for cls in MOCKS:
            with self.subTest(cls=cls.__name__):
                with self.assertRaises(LiveCallBlocked):
                    calls[cls](self.make(cls, endpoint="https://real-vendor.invalid-host.com/api"))
                calls[cls](self.make(cls))  # works offline with no endpoint

    def test_every_live_method_refuses(self):
        for cls in LIVES:
            live = cls()
            methods = [m for m, _ in inspect.getmembers(cls, inspect.isfunction) if not m.startswith("_")]
            self.assertTrue(methods, cls)
            for name in methods:
                fn = getattr(live, name)
                n_args = len(inspect.signature(fn).parameters)
                with self.subTest(cls=cls.__name__, method=name):
                    with self.assertRaises(NotAuthorized) as cm:
                        fn(*([None] * n_args))
                    self.assertIn("Human approval required", str(cm.exception))


class OpenAITest(TmpOut):
    def test_canned_completion_for_every_prompt(self):
        llm = self.make(mock_openai.MockOpenAI)
        bindings = render_prompts.fixture_bindings()
        self.assertEqual(sorted(mock_openai.CANNED), render_prompts.list_prompt_ids())
        for pid, variables in bindings.items():
            text = render_prompts.render(pid, variables)
            out = llm.complete(pid, text, variables)
            self.assertTrue(out)
            self.assertEqual(out, llm.complete(pid, text, variables))  # deterministic
            self.assertFalse(claim_guard.check(out).blocked, (pid, out))
            if pid not in ("07_youtube_analysis",):
                self.assertFalse(pricing_guard.check(out).blocked, (pid, out))

    def test_rejects_unknown_prompt_and_unresolved_text(self):
        llm = self.make(mock_openai.MockOpenAI)
        with self.assertRaises(mock_openai.UnknownPrompt):
            llm.complete("99_nope", "x", {})
        with self.assertRaises(ValueError):
            llm.complete("06_translate", "Translate {{text}}", {})

    def test_enrich_scoring_is_rule_based(self):
        hi = json.loads(mock_openai.CANNED["02_lead_enrich"](
            {"niche": "HVAC contractors", "website_text": "Emergency repair. Call to book.", "company": "X"}))
        lo = json.loads(mock_openai.CANNED["02_lead_enrich"](
            {"niche": "marketing agencies", "website_text": "We do websites.", "company": "Y"}))
        self.assertEqual(hi["fit_score"], 10)
        self.assertEqual(lo["fit_score"], 3)
        self.assertEqual(lo["decision_maker"], "unknown")

    def test_detect_language(self):
        cases = {"How do I book?": "en", "Hola, quiero una cita para el martes": "es",
                 "Bonjour, je voudrais un rendez-vous": "fr", "Hallo, ich möchte einen Termin bitte": "de",
                 "नमस्ते": "hi"}
        for text, code in cases.items():
            self.assertEqual(mock_openai.detect_language(text), code, text)

    def test_file_search_and_cross_language(self):
        llm = self.make(mock_openai.MockOpenAI)
        top = llm.file_search("How do I book an appointment?", "faqs.sample.md", 2)
        self.assertEqual(top[0].question, "How do I book or schedule an appointment?")
        self.assertGreaterEqual(top[0].score, 0.7)
        es = llm.file_search("Quiero reprogramar mi cita", "faqs.sample.md", 1)
        self.assertIn("reschedule", es[0].question.lower())
        self.assertEqual(llm.file_search("solar panels", "faqs.sample.md"), [])
        with self.assertRaises(ValueError):
            llm.file_search("x", "../../config/constants.py")

    def test_transcribe(self):
        llm = self.make(mock_openai.MockOpenAI)
        self.assertIn("rattling noise", llm.transcribe("synthetic-ad-001"))
        job = self.make(mock_video_gen.MockVideoGen).create_job("elevenlabs", "voiceover", {"text": "hello there"})
        self.assertEqual(llm.transcribe(job["job_id"]), "hello there")
        with self.assertRaises(LookupError):
            llm.transcribe("missing")


class CalendarTest(TmpOut):
    def test_availability_and_booking(self):
        cal = self.make(mock_calendar.MockCalendar)
        slots = cal.availability("2026-10-06")
        self.assertEqual(slots[0], "09:00")
        ev = cal.create_event("2026-10-06", "09:00", "pat@example.com", "Appt")
        self.assertEqual(ev["status"], "dry_run_created")
        self.assertNotIn("09:00", cal.availability("2026-10-06"))
        with self.assertRaises(mock_calendar.SlotUnavailable):
            cal.create_event("2026-10-06", "09:00", "x@example.com", "dup")
        with self.assertRaises(mock_calendar.SlotUnavailable):
            cal.create_event("2026-10-06", "03:17", "x@example.com", "invented time")
        self.assertEqual(cal.availability("2026-10-10"), [])  # Saturday
        with self.assertRaises(ValueError):
            cal.availability("not-a-date")


class CRMTest(TmpOut):
    def test_contacts_records_queries(self):
        crm = self.make(mock_crm.MockCRM)
        a = crm.upsert_contact("Pat@Example.com", {"firstname": "Pat"})
        b = crm.upsert_contact("pat@example.com", {"phone": "202-555-0111"})
        self.assertEqual(a["contact_id"], b["contact_id"])
        self.assertEqual(b["firstname"], "Pat")
        crm.upsert_record("leads", "k1", {"n": 1, "flag": True})
        crm.upsert_record("leads", "k2", {"n": 5, "flag": False})
        row = crm.upsert_record("leads", "k1", {}, increment=("count",))
        self.assertEqual(row["count"], 1)
        self.assertEqual([r["_key"] for r in crm.query("leads", [["n", "lt", 3], ["flag", "isTrue", None]])], ["k1"])
        self.assertEqual(crm.query("missing", []), [])
        with self.assertRaises(ValueError):
            crm.upsert_record("leads", "", {})
        self.assertIsNone(crm.find_email("hvac02.example.com"))
        crm.known_emails["hvac02.example.com"] = "x@hvac02.example.com"
        self.assertEqual(crm.find_email("HVAC02.example.com"), "x@hvac02.example.com")


class MailerTest(TmpOut):
    def test_writes_eml_draft(self):
        m = self.make(mock_mailer.MockMailer)
        rec = m.send("pat@example.com", "Hello", "Plain body.", "sender@example.com")
        msg = email.message_from_bytes(Path(rec["path"]).read_bytes())
        self.assertEqual(msg["To"], "pat@example.com")
        self.assertEqual(msg["X-CAJ-Dry-Run"], "true")
        self.assertIn("not sent", msg["X-CAJ-Status"])
        self.assertEqual(rec["status"], "draft_written_not_sent")

    def test_guards_suppression_cap(self):
        m = self.make(mock_mailer.MockMailer, daily_cap=2)
        with self.assertRaises(pricing_guard.PricingViolation):
            m.send("a@example.com", "Hi", "Only $197", "s@example.com")
        with self.assertRaises(claim_guard.ClaimViolation):
            m.send("a@example.com", "Hi", "We take unlimited calls", "s@example.com")
        m.suppress("b@example.com")
        with self.assertRaises(mock_mailer.Suppressed):
            m.send("B@example.com", "Hi", "x", "s@example.com")
        with self.assertRaises(ValueError):
            m.send("not-an-address", "Hi", "x", "s@example.com")
        m.send("c@example.com", "Hi", "x", "s@example.com")
        m.send("d@example.com", "Hi", "x", "s@example.com")
        with self.assertRaises(mock_mailer.CapExceeded):
            m.send("e@example.com", "Hi", "x", "s@example.com")
        self.assertEqual(len(list((self.out / "mail").glob("*.eml"))), 2)

    def test_replies(self):
        m = self.make(mock_mailer.MockMailer)
        self.assertFalse(m.has_reply("a@example.com"))
        m.record_reply("A@example.com")
        self.assertTrue(m.has_reply("a@example.com"))


class VideoTest(TmpOut):
    def test_stub_job(self):
        v = self.make(mock_video_gen.MockVideoGen)
        job = v.create_job("heygen", "avatar", {"script": "hi"})
        record = json.loads((self.out / "video_jobs" / f"{job['job_id']}.json").read_text())
        self.assertFalse(record["rendered"])
        self.assertIsNone(record["output_url"])
        self.assertEqual(v.status(job["job_id"])["status"], mock_video_gen.STATUS_STUB)
        self.assertEqual(job, v.create_job("heygen", "avatar", {"script": "hi"}))
        with self.assertRaises(ValueError):
            v.create_job("unknown", "x", {})
        with self.assertRaises(LookupError):
            v.status("nope")


class ApifyTest(TmpOut):
    def test_actors(self):
        a = self.make(mock_apify.MockApify)
        leads = a.run_actor("google-maps-scraper", {"niche": "HVAC contractors"})
        self.assertEqual(len(leads), 5)
        self.assertTrue(all(l["website"].endswith(".example.com") for l in leads))
        self.assertEqual(len(a.run_actor("google-maps-scraper", {"niche": "zzz"})), 6)
        ad = a.run_actor("tiktok-scraper", {"url": "https://example.com/ads/synthetic-001"})
        self.assertEqual(ad[0]["media_id"], "synthetic-ad-001")
        with self.assertRaises(mock_apify.ActorNotApproved):
            a.run_actor("apollo-io-scraper", {})
        with self.assertRaises(LookupError):
            a.run_actor("other-actor", {})
        with self.assertRaises(LookupError):
            a.run_actor("tiktok-scraper", {"url": "https://example.com/none"})


class PublisherTest(TmpOut):
    def test_records_without_publishing(self):
        p = self.make(mock_publisher.MockPublisher)
        rec = p.post(["tiktok", "linkedin"], "Plain post", "job-1")
        self.assertEqual(rec["status"], mock_publisher.NOT_PUBLISHED)
        stats = p.analytics(rec["post_id"])
        self.assertIsNone(stats["views"])
        self.assertIsNone(stats["likes"])
        p.notify("#ops", "note")
        p.reply("s1", "hello")
        p.transfer_call("c1", "confused")
        lines = (self.out / "publish" / "intended.jsonl").read_text().splitlines()
        self.assertEqual(len(lines), 4)
        with self.assertRaises(ValueError):
            p.post(["myspace"], "x", None)
        with self.assertRaises(pricing_guard.PricingViolation):
            p.post(["x"], "Now $49", None)
        with self.assertRaises(pricing_guard.PricingViolation):
            p.reply("s1", "Our pricing is simple")
        with self.assertRaises(claim_guard.ClaimViolation):
            p.post(["x"], "Make UGC 10x faster", None)


class YouTubeTest(TmpOut):
    def test_search(self):
        yt = self.make(mock_youtube.MockYouTube)
        items = yt.search("hvac", "viewCount", None, 3)
        self.assertEqual([i["views"] for i in items], sorted([i["views"] for i in items], reverse=True))
        self.assertEqual(len(items), 3)
        self.assertEqual(len(yt.search("hvac", published_after="2026-09-20")), 3)
        with self.assertRaises(ValueError):
            yt.search("hvac", order="rating")


if __name__ == "__main__":
    unittest.main()

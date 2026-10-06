"""fetch_raw_html / baseline_inventory never touch the network here: an opener is injected."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import baseline_inventory as B  # noqa: E402
from tools import fetch_raw_html as F  # noqa: E402
from tools import state  # noqa: E402
from tools.paths import scratch_paths  # noqa: E402

PAGE = """<!DOCTYPE html><html><head><title> Example Service Page </title>
<meta name="description" content="Desc here"><meta name="robots" content="index,follow">
<link rel="canonical" href="https://www.example.com/services/x">
<meta property="og:title" content="OG T"><meta property="og:image" content="https://www.example.com/og.png">
<script>gtag('config','G-ABC1234XYZ');</script><script src="https://cdn.example.net/app.js"></script>
<style>.a{width:100%}</style></head>
<body><nav><a href="/">Home</a><a href="/contact">Contact</a><a href="https://other.example.org/x">Ext</a>
<a href="mailto:a@example.com">m</a></nav><h1>Main <em>heading</em></h1><p>Body copy for the page.</p>
<form action="/api/inquiries" method="post"></form><iframe src="https://www.example.com/widget/booking/abc"></iframe>
</body></html>"""


class Resp:
    def __init__(self, url, body, status=200):
        self.url, self.body, self.status = url, body.encode(), status
        self.headers = {"Content-Type": "text/html; charset=utf-8"}

    def getcode(self):
        return self.status

    def read(self):
        return self.body

    def geturl(self):
        return self.url


class FakeOpener:
    """Scripted offline opener. Each script entry: HTML string, an int HTTP error code, or 'neterr'."""

    def __init__(self, script):
        self.script, self.requests, self.redirect_chain = list(script), [], []

    def open(self, request, timeout=None):
        self.requests.append(request)
        step = self.script.pop(0)
        if step == "neterr":
            raise urllib.error.URLError("offline")
        if isinstance(step, int):
            raise urllib.error.HTTPError(request.full_url, step, "err", {}, io.BytesIO(b"<h1>Nope</h1>"))
        return Resp(request.full_url, step)


class FetchTests(unittest.TestCase):
    def test_parse_extracts_fields(self):
        ev = F.fetch("https://www.example.com/services/x", opener=FakeOpener([PAGE]), sleep=lambda s: None)
        self.assertEqual(ev["status"], 200)
        self.assertEqual(ev["title"], "Example Service Page")
        self.assertEqual(ev["h1"], ["Main heading"])
        self.assertEqual(ev["canonical"], "https://www.example.com/services/x")
        self.assertEqual(ev["meta_description"], "Desc here")
        self.assertEqual(ev["og"]["og:image"], "https://www.example.com/og.png")
        self.assertEqual(ev["internal_links"], ["https://www.example.com/", "https://www.example.com/contact"])
        self.assertEqual(ev["tracking_ids"], {"google_analytics_4": ["G-ABC1234XYZ"]})
        self.assertEqual(ev["forms"], [{"action": "/api/inquiries", "method": "post"}])
        self.assertNotIn("width", ev["visible_text_sample"])

    def test_no_cookies_or_auth_headers(self):
        opener = FakeOpener([PAGE])
        F.fetch("https://www.example.com/", opener=opener)
        req = opener.requests[0]
        self.assertIsNone(req.get_header("Authorization"))
        self.assertIsNone(req.get_header("Cookie"))
        self.assertEqual(req.get_method(), "GET")

    def test_retries_capped_at_two(self):
        opener = FakeOpener(["neterr", "neterr", "neterr", PAGE])
        sleeps = []
        ev = F.fetch("https://www.example.com/", opener=opener, sleep=sleeps.append, max_retries=10)
        self.assertEqual(ev["attempts"], 3)
        self.assertIsNone(ev["status"])
        self.assertIn("URLError", ev["error"])
        self.assertEqual(len(sleeps), 2)

    def test_5xx_retried_then_success_and_404_not_retried(self):
        ev = F.fetch("https://www.example.com/", opener=FakeOpener([503, PAGE]), sleep=lambda s: None)
        self.assertEqual((ev["status"], ev["attempts"]), (200, 2))
        ev = F.fetch("https://www.example.com/missing", opener=FakeOpener([404]), sleep=lambda s: None)
        self.assertEqual((ev["status"], ev["attempts"]), (404, 1))

    def test_refusals(self):
        for url in ("file:///etc/passwd", "ftp://example.com/x", "https://user:pw@example.com/",
                    "https://www.example.com/?api_key=abc", "https://api.example.com/v1/x", "notaurl"):
            with self.subTest(url=url), self.assertRaises(F.FetchRefused):
                F.fetch(url, opener=FakeOpener([PAGE]))

    def test_default_opener_has_no_cookie_or_auth_handlers(self):
        opener = F.default_opener()
        names = {type(h).__name__ for h in opener.handlers}
        self.assertNotIn("HTTPCookieProcessor", names)
        self.assertFalse(any("Auth" in n for n in names))

    def test_cli_dry_run_and_local_file(self):
        with tempfile.TemporaryDirectory() as td:
            paths = scratch_paths(Path(td))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(F.main(["https://www.example.com/"], paths=paths), 3)
                self.assertEqual(F.main(["file:///x"], paths=paths), 2)
                html = Path(td) / "p.html"
                html.write_text(PAGE)
                self.assertEqual(F.main(["--html-file", str(html)], paths=paths), 0)
                self.assertEqual(F.main(["https://www.example.com/a"], paths=paths, opener=FakeOpener([PAGE])), 0)
            self.assertIn("DRY_RUN", out.getvalue())
            files = sorted(p.name for p in (paths.out / "baseline").glob("*.json"))
            self.assertEqual(len(files), 2)


class BaselineTests(unittest.TestCase):
    def test_blocked_without_url_list(self):
        with tempfile.TemporaryDirectory() as td:
            paths = scratch_paths(Path(td))
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(B.main([], paths=paths), B.EXIT_BLOCKED)
            self.assertIn("BLOCKED", out.getvalue())
            self.assertIn("baseline_inventory", state.blockers(paths))
            self.assertFalse((paths.out / "baseline" / "baseline_inventory.json").exists())

    def test_blocked_without_network_permission(self):
        with tempfile.TemporaryDirectory() as td:
            paths = scratch_paths(Path(td))
            urls = Path(td) / "urls.txt"
            urls.write_text("https://www.example.com/\n")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(B.main(["--urls", str(urls)], paths=paths), B.EXIT_BLOCKED)

    def test_inventory_from_injected_opener(self):
        with tempfile.TemporaryDirectory() as td:
            paths = scratch_paths(Path(td))
            urls = Path(td) / "urls.txt"
            urls.write_text("# existing site\nhttps://www.example.com/\nhttps://www.example.com/thank-you\n"
                            "https://api.example.com/x\n")
            opener = FakeOpener([PAGE, PAGE])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(B.main(["--urls", str(urls)], paths=paths, opener=opener, sleep=lambda s: None), 0)
            inv = json.loads((paths.out / "baseline" / "baseline_inventory.json").read_text())
            self.assertEqual(len(inv["routes"]), 3)
            self.assertEqual(inv["routes"][0]["calendar_embeds"], ["https://www.example.com/widget/booking/abc"])
            self.assertTrue(inv["routes"][1]["is_thank_you_page"])
            self.assertTrue(inv["routes"][2]["error"].startswith("REFUSED"))
            self.assertEqual(inv["dns_mappings"], "NEEDS_EVIDENCE")
            self.assertTrue((paths.out / "baseline" / "baseline_inventory.md").exists())


if __name__ == "__main__":
    unittest.main()

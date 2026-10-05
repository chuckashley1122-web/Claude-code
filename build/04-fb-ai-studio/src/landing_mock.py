"""Static landing-page mock -> out/landing/index.html + thank-you.html (SPEC-04 step 14).

Self-contained HTML, inline CSS, no scripts, no external loads, openable via
file:// for content review only. The form is non-functional.
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.landing_content import FORM_ID, check, content  # noqa: E402

BANNER = "STATIC CONTENT MOCK — NOT THE LIVE PAGE; does not submit anywhere."

CSS = """
*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;color:#1d2733;background:#f6f8fa;line-height:1.5}
.mock-banner{background:#b00020;color:#fff;text-align:center;font-weight:bold;padding:10px;position:sticky;top:0;z-index:9}
header{display:flex;justify-content:space-between;align-items:center;padding:12px 24px;background:#fff;border-bottom:1px solid #dde3ea}
header nav a{margin-left:16px;color:#1d2733;text-decoration:none}
.brand-small{font-size:14px;font-weight:bold}
.hero{display:grid;grid-template-columns:1.2fr 1fr;gap:32px;padding:48px 24px;max-width:1100px;margin:0 auto}
h1{font-size:40px;margin:0 0 12px}h2{margin-top:0}
.cta{display:inline-block;background:#0b6bcb;color:#fff;padding:14px 22px;border-radius:6px;text-decoration:none;font-weight:bold}
section{max-width:1100px;margin:0 auto;padding:32px 24px}
.slot{border:2px dashed #9aa7b4;padding:24px;text-align:center;color:#5b6773;background:#fff}
form{background:#fff;padding:24px;border-radius:8px;border:1px solid #dde3ea}
label{display:block;font-weight:bold;margin-top:12px}input,select{width:100%;padding:10px;margin-top:4px}
.consent{font-size:13px;color:#46525e}
footer{font-size:13px;color:#46525e;padding:24px;text-align:center;border-top:1px solid #dde3ea}
footer .footer-mark{font-size:11px}
@media (max-width:760px){.hero{grid-template-columns:1fr}h1{font-size:30px}header{justify-content:center}header nav,.header-phone{display:none}.cta{display:block;text-align:center}}
"""


def e(s) -> str:
    return html.escape(str(s), quote=True)


def _field(f: dict) -> str:
    if f["type"] == "select":
        opts = "".join(f"<option>{e(o)}</option>" for o in f["options"])
        return f'<label for="{e(f["name"])}">{e(f["label"])}</label><select id="{e(f["name"])}" name="{e(f["name"])}" required>{opts}</select>'
    if f["type"] == "checkbox":
        return (f'<label class="consent"><input type="checkbox" id="{e(f["name"])}" name="{e(f["name"])}" required> '
                f'{e(f["label"])}</label>')
    return (f'<label for="{e(f["name"])}">{e(f["label"])}</label>'
            f'<input type="{e(f["type"])}" id="{e(f["name"])}" name="{e(f["name"])}" required>')


def _page(title: str, body: str) -> str:
    return (f'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{e(title)}</title>\n'
            f'<style>{CSS}</style>\n</head>\n<body>\n<div class="mock-banner" role="note">{e(BANNER)}</div>\n'
            f'{body}\n</body>\n</html>\n')


def _cta(text: str) -> str:
    return f'<a class="cta" href="#{FORM_ID}">{e(text)}</a>'


def render_index(c: dict) -> str:
    form = c["form"]
    fields = "\n".join(_field(f) for f in form["fields"])
    faq = "\n".join(f"<h3>{e(f['q'])}</h3><p>{e(f['a'])}</p>" for f in c["faq"])
    body = f"""
<header>
  <span class="brand-small">{e(C.BUSINESS_DISPLAY_NAME)}</span>
  <nav><a href="#problem">Why</a><a href="#how">How it works</a><a href="#faq">FAQ</a></nav>
  {_cta(c['hero']['primary_cta']['text'])}
</header>
<div class="hero">
  <div>
    <h1>{e(c['hero']['headline'])}</h1>
    <p>{e(c['hero']['subhead'])}</p>
    {_cta(c['hero']['primary_cta']['text'])}
    <div class="slot">Hero image slot: {e(c['hero']['hero_image'])}</div>
  </div>
  <form id="{FORM_ID}">
    <h2>{e(c['hero']['primary_cta']['text'])}</h2>
    {fields}
    <p class="consent">{e(form['consent_disclosure'])}</p>
    <button type="button" class="submit" disabled title="Mock only - does not submit">{e(form['submit_text'])}</button>
  </form>
</div>
<section id="problem"><h2>{e(c['problem']['title'])}</h2><ul>{''.join(f'<li>{e(i)}</li>' for i in c['problem']['items'])}</ul>{_cta(c['hero']['primary_cta']['text'])}</section>
<section id="what"><h2>{e(c['what_we_do']['title'])}</h2><ul>{''.join(f'<li>{e(i)}</li>' for i in c['what_we_do']['items'])}</ul></section>
<section id="how"><h2>{e(c['how_it_works']['title'])}</h2><ol>{''.join(f'<li>{e(s)}</li>' for s in c['how_it_works']['steps'])}</ol>{_cta(c['hero']['primary_cta']['text'])}</section>
<section id="who"><h2>{e(c['who_its_for']['title'])}</h2><p>{e(c['who_its_for']['text'])}</p></section>
<section id="trust"><h2>Proof</h2><div class="slot">Reviews, ratings, testimonials and client results: NEEDS_EVIDENCE (omitted until verified)</div></section>
<section id="faq"><h2>FAQ</h2>{faq}{_cta(c['hero']['primary_cta']['text'])}</section>
<footer>
  <div>{e(c['footer']['business'])} | {e(c['footer']['contact'])}</div>
  <div>Privacy policy: {e(c['footer']['privacy_policy_url'])}</div>
  <div class="footer-mark">Logo: {e(c['footer']['logo'])}</div>
  <div>{e(c['footer']['disclaimer'])}</div>
</footer>"""
    return _page(f"{C.BUSINESS_DISPLAY_NAME} - strategy session (mock)", body)


def render_thank_you(c: dict) -> str:
    body = f"""
<section>
  <h1>Thanks, we got your details.</h1>
  <p>Chuck will reach out by text or email to set a time. If you'd rather pick a time now, book your strategy session here:</p>
  <a class="cta" id="booking-cta" href="{e(C.BOOKING_URL)}">Book your strategy session</a>
</section>
<footer><div>{e(c['footer']['business'])} | {e(c['footer']['contact'])}</div></footer>"""
    return _page(f"{C.BUSINESS_DISPLAY_NAME} - thank you (mock)", body)


def build(ctx) -> list[Path]:
    c = content(ctx)
    check(c)
    return [ctx.write_asset("out/landing/index.html", render_index(c), "landing_index_html", "src/landing_mock.py"),
            ctx.write_asset("out/landing/thank-you.html", render_thank_you(c), "landing_thank_you_html", "src/landing_mock.py")]

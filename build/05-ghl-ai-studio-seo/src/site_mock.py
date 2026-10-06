"""Static site mock -> out/site/<slug>.html, 404.html, thank-you.html.

Self-contained (inline CSS, no scripts, no trackers, no fonts, no CDNs) and
openable via file://. Every page carries the STATIC CONTENT MOCK banner and
puts title, H1, core copy, canonical and navigation links in the raw markup:
the mocks are the reference target an SSR build must match. The contact form
is non-functional (no action, type="button").
"""

from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from src import page_plan  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, emit  # noqa: E402

BANNER = "STATIC CONTENT MOCK — NOT THE LIVE SITE; does not submit anywhere."
NAV = [("/", "Home"), ("/services/lead-generation", "Lead generation"),
       ("/services/reputation-management", "Reputation management"),
       ("/services/paid-advertising", "Paid advertising"), ("/about", "About"), ("/contact", "Contact")]

CSS = """
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;font-size:16px;line-height:1.6;color:#1a1a1a;background:#fff}
.mock-banner{background:#7a1f00;color:#fff;padding:.6rem 1rem;font-weight:700;text-align:center}
header,main,footer{max-width:46rem;margin:0 auto;padding:1rem}
nav ul{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:.75rem}
a{color:#0b4f8a}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:3px solid #f2a900;outline-offset:2px}
.cta-primary{display:inline-block;background:#0b4f8a;color:#fff;padding:.75rem 1.25rem;border-radius:.4rem;text-decoration:none;font-weight:700;min-height:44px}
label{display:block;font-weight:600;margin-top:.75rem}
input,select,textarea{width:100%;font-size:1rem;padding:.5rem;border:1px solid #555;border-radius:.3rem}
button{font-size:1rem;padding:.6rem 1rem;min-height:44px;margin-top:1rem}
.note{background:#f3f3f3;padding:.75rem;border-left:4px solid #7a1f00}
footer{font-size:.9rem;color:#444;border-top:1px solid #ddd}
@media (max-width:30rem){header,main,footer{padding:.75rem}}
""".strip()


def file_for(route: str) -> str:
    return page_plan.slug_for(route) + ".html"


def _nav() -> str:
    items = "".join(f'<li><a href="{file_for(r)}" data-route="{escape(r)}">{escape(label)}</a></li>'
                    for r, label in NAV)
    return f'<nav aria-label="Main"><ul>{items}</ul></nav>'


def _head(title: str, description: str, canonical: str | None, robots: str, og_image: str = C.NEEDS_EVIDENCE) -> str:
    parts = ['<meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             f"<title>{escape(title)}</title>",
             f'<meta name="description" content="{escape(description)}">',
             f'<meta name="robots" content="{robots}">']
    if canonical:
        parts += [f'<link rel="canonical" href="{escape(canonical)}">',
                  f'<meta property="og:title" content="{escape(title)}">',
                  f'<meta property="og:description" content="{escape(description)}">',
                  f'<meta property="og:url" content="{escape(canonical)}">',
                  f'<meta property="og:image" content="{escape(og_image)}">']
    parts.append(f"<style>{CSS}</style>")
    return "<head>" + "".join(parts) + "</head>"


def _footer() -> str:
    return ("<footer><p>" + escape(C.LEGAL_ENTITY) + " &middot; " + escape(C.OWNER_NAME) + " &middot; "
            + escape(C.OWNER_PHONE) + " &middot; " + escape(C.OWNER_EMAIL) + "</p>"
            + f'<p class="logo-footer">Logo (footer only): {C.NEEDS_EVIDENCE}</p></footer>')


def _document(head: str, main: str) -> str:
    return ("<!DOCTYPE html>\n<html lang=\"en\">" + head + "<body>"
            + f'<div class="mock-banner" role="note">{escape(BANNER)}</div>'
            + "<header>" + _nav() + "</header><main>" + main + "</main>" + _footer() + "</body></html>\n")


def _cta(label: str = "Book a meeting") -> str:
    return f'<p><a class="cta-primary" href="{C.BOOKING_URL}">{escape(label)}</a></p>'


def _form() -> str:
    services = ["Lead generation (proposed)", "Reputation management (proposed)", "Paid advertising (proposed)"]
    options = '<option value="">Choose a service</option>' + "".join(
        f"<option>{escape(s)}</option>" for s in services)
    return (
        '<section aria-labelledby="form-heading"><h2 id="form-heading">Inquiry form (mock)</h2>'
        '<p class="note" id="form-note">Mock only: this form has no action and does not submit anywhere. '
        "Required: name, one contact method (email or phone) and a service.</p>"
        '<form aria-describedby="form-note">'
        '<label for="f-name">Name (required)</label><input id="f-name" name="name" maxlength="'
        f'{C.MAX_NAME_LEN}" autocomplete="name" required>'
        '<label for="f-email">Email</label><input id="f-email" name="email" type="email" autocomplete="email">'
        '<label for="f-phone">Phone</label><input id="f-phone" name="phone" type="tel" autocomplete="tel">'
        f'<label for="f-service">Service (required)</label><select id="f-service" name="service_interest" '
        f'required>{options}</select>'
        f'<label for="f-area">Service area</label><input id="f-area" name="service_area" maxlength="{C.MAX_NAME_LEN}">'
        f'<label for="f-message">Message</label><textarea id="f-message" name="message" rows="5" '
        f'maxlength="{C.MAX_MESSAGE_LEN}"></textarea>'
        '<label for="f-consent"><input id="f-consent" name="consent" type="checkbox" style="width:auto"> '
        "You may contact me about this inquiry</label>"
        '<p id="f-errors" role="alert" aria-live="polite"></p>'
        '<button type="button">Send inquiry (mock - does not submit)</button>'
        "</form></section>")


def render_page(page: dict, row: dict, meta: dict) -> str:
    body = [f"<h1>{escape(page['h1'])}</h1>", f'<p class="lead">{escape(page["lead"])}</p>',
            _cta(page["primary_cta"]["label"])]
    for sec in page["sections"]:
        body.append(f"<section><h2>{escape(sec['heading'])}</h2>")
        body += [f"<p>{escape(p)}</p>" for p in sec["paragraphs"]]
        if sec["bullets"]:
            body.append("<ul>" + "".join(f"<li>{escape(b)}</li>" for b in sec["bullets"]) + "</ul>")
        body.append("</section>")
    if row["page_type"] == "contact":
        body.append(_form())
    if page["faqs"]:
        body.append("<section><h2>Frequently asked questions</h2>")
        for faq in page["faqs"]:
            body.append(f"<h3>{escape(faq['q'])}</h3><p>{escape(faq['a'])}</p>")
        body.append("</section>")
    head = _head(row["title"], meta["meta_description"], row["canonical"], "index,follow",
                 meta["og"]["og:image"])
    return _document(head, "".join(body))


def render_withheld(row: dict) -> str:
    main = (f"<h1>{escape(row['h1'])}</h1>"
            '<p class="note">This location page is withheld. The thin-content guard refused to emit it because '
            "no verified local coverage or city-specific information exists, and a page that only swaps the city "
            "name is not useful. It is merged into a single service-area record until evidence is supplied. "
            "Do not publish this route.</p>"
            + _cta())
    head = _head(row["title"], f"Withheld location page for {row.get('city', '')}.", row["canonical"],
                 "noindex,follow")
    return _document(head, main)


def render_404(origin: str) -> str:
    main = ("<h1>Page not found</h1>"
            "<p>The page you asked for does not exist. Use the navigation above to reach the main pages, "
            "or go back to the home page.</p>"
            '<p class="note">Server requirement: unknown paths must return an HTTP 404 status with this body, '
            "not a soft 200 and not a redirect to the home page.</p>"
            f'<p><a href="{file_for("/")}">Return to the home page</a></p>')
    head = _head("Page not found | CA-J Enterprises", "The requested page was not found.", None,
                 "noindex,follow")
    return _document(head, main)


def render_thank_you(origin: str) -> str:
    canonical = (origin or C.NEEDS_EVIDENCE).rstrip("/") + "/thank-you"
    main = ("<h1>Thank you - your inquiry was saved</h1>"
            "<p>Show this page only after the server confirmed the inquiry was saved (HTTP 201) and returned a "
            "reference. If the inquiry was only received for processing, say so instead.</p>"
            "<p>To pick a time to talk now, book a meeting directly.</p>" + _cta())
    head = _head("Thank You | CA-J Enterprises", "Inquiry confirmation page.", canonical, "noindex,follow")
    return _document(head, main)


def build(paths: Paths | None = None) -> list[Path]:
    paths = paths or default_paths()
    rows = page_plan.load(paths)
    model = json.loads((paths.out / "pages" / "_content_model.json").read_text(encoding="utf-8"))
    meta = {r["route"]: r for r in json.loads((paths.out / "metadata.json").read_text(encoding="utf-8"))["records"]}
    origin = json.loads(paths.build_config.read_text(encoding="utf-8")).get("site_origin", C.NEEDS_EVIDENCE)
    site = paths.out / "site"
    written = []
    for row in rows:
        target = site / file_for(row["route"])
        if row["route"] in model["pages"] and row["indexable"]:
            html = render_page(model["pages"][row["route"]], row, meta[row["route"]])
        else:
            html = render_withheld(row)
        written.append(emit(f"mock:{row['slug']}", target, html, STATUS.DRAFT, paths, source="src/site_mock.py"))
    written.append(emit("mock:404", site / "404.html", render_404(origin), STATUS.DRAFT, paths,
                        source="src/site_mock.py"))
    written.append(emit("mock:thank-you", site / "thank-you.html", render_thank_you(origin), STATUS.DRAFT, paths,
                        source="src/site_mock.py"))
    return written


if __name__ == "__main__":
    print(f"mocks written: {len(build())}")

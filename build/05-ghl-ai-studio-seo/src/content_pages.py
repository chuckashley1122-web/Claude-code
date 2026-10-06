"""Page content model per route -> out/pages/<slug>.md (+ _content_model.json).

Three gates run here and fail loudly instead of emitting bad copy:

* Content evidence gate: a section/FAQ that depends on a claim key without a
  verified evidence source is withheld from public copy; any public string that
  still trips the no-fabricated-fact / no-price / brand guardrails raises.
* Conversion path: every page has exactly one primary action whose destination
  literal is BOOKING_URL (linked as-is, offer and price untouched).
* Thin-content guard: normalized token overlap between two page bodies above
  THIN_CONTENT_SIMILARITY_MAX raises ThinContentError. Location pages that trip
  it are not emitted; a single service-area merge record is emitted instead.
"""

from __future__ import annotations

import re
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from src import business_facts, page_plan  # noqa: E402
from tools import guardrails as G  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, emit, record_blocker  # noqa: E402

MERGED_STATUS = "MERGED_PENDING_EVIDENCE"
CTA_LABEL = "Book a meeting"
PRICING_FAQ = {
    "q": "How do I find out what this would cost for my business?",
    "a": "Pricing is discussed in a meeting, once we understand your business and what you need. "
         "Use the booking button on this page to choose a time.",
    "claims": [],
}


class ThinContentError(ValueError):
    def __init__(self, pairs: list[tuple[str, str, float]]):
        detail = ", ".join(f"{a} ~ {b} = {s:.2f}" for a, b, s in pairs)
        super().__init__(f"near-duplicate page bodies above {C.THIN_CONTENT_SIMILARITY_MAX}: {detail}")
        self.pairs = pairs


class ConversionPathError(ValueError):
    pass


def S(heading: str, paragraphs: list[str], claims: list[str] | None = None, bullets: list[str] | None = None) -> dict:
    return {"heading": heading, "paragraphs": paragraphs, "bullets": bullets or [], "claims": claims or []}


def F(q: str, a: str, claims: list[str] | None = None) -> dict:
    return {"q": q, "a": a, "claims": claims or []}


def _service_pages() -> dict[str, dict]:
    return {
        "/": {
            "lead": "CA-J Enterprises builds marketing systems for local service businesses: the pages, "
                    "follow-up and booking path that move a prospect from a search to a scheduled conversation.",
            "sections": [
                S("Why most local marketing leaks",
                  ["A prospect searches, lands on a page that does not answer their question, fills in a form "
                   "nobody watches, and calls a competitor instead. Each step is small; together they decide "
                   "whether a search becomes a booked appointment."]),
                S("Three connected parts",
                  ["The work is organised around three parts that feed one another. Each has its own page "
                   "describing the problem it solves, how the work runs and what you receive."],
                  bullets=["Lead generation: pages and inquiry flows matched to how customers search.",
                           "Reputation management: accurate listings and an honest review request routine.",
                           "Paid advertising: campaigns measured against confirmed inquiries, not clicks."]),
                S("Meeting first",
                  ["Every engagement starts with a conversation about your business, your service area and the "
                   "work you want more of. Nothing is sold from a price sheet on this site."]),
                S("Results from client work", ["Client outcomes will be shown here once approved."],
                  claims=["results", "testimonials"]),
            ],
            "faqs": [
                PRICING_FAQ,
                F("Which areas do you serve?", "Coverage details will be listed once confirmed.",
                  claims=["service_areas"]),
                F("Do I have to replace my current website?",
                  "Not necessarily. The first step is an inventory of what already works, so useful pages and "
                  "existing booking paths are kept rather than rebuilt."),
            ],
        },
        "/services/lead-generation": {
            "lead": "Lead generation for local service businesses, built around the questions your customers "
                    "type before they pick up the phone.",
            "sections": [
                S("The problem",
                  ["Most service businesses do not lack interest; they lose it between the search and the "
                   "first reply. Inquiries arrive after hours, land in an inbox nobody checks, or hit a generic "
                   "page that never mentions the job the visitor needs done."]),
                S("How the work runs",
                  ["The process is deliberately plain and each step is reviewed with you before the next "
                   "one starts."],
                  bullets=["Map where inquiries come from today and where they stall.",
                           "Group searches by service and intent so each page answers one kind of request.",
                           "Build focused landing pages with a short inquiry form that saves to your CRM.",
                           "Set up follow-up so every inquiry receives a timely, personal reply.",
                           "Review booked appointments with you and adjust pages and follow-up."]),
                S("What you receive",
                  ["A written search-intent map, the landing pages themselves, a tested inquiry form, a "
                   "follow-up sequence you approve word for word, and a simple monthly review of what "
                   "converted and what did not."]),
                S("Typical outcomes", ["Outcome figures will be added once approved."], claims=["results"]),
            ],
            "faqs": [
                F("Will this work with the CRM I already use?",
                  "That depends on the integrations your CRM actually supports. It is confirmed during the "
                  "first meeting rather than assumed."),
                F("Who writes the follow-up messages?",
                  "Drafts are prepared for you, and nothing is sent to a customer until you approve the wording."),
                PRICING_FAQ,
            ],
        },
        "/services/reputation-management": {
            "lead": "Reputation management for local businesses: accurate public listings, a steady habit of "
                    "asking real customers for feedback, and replies you would be proud to sign.",
            "sections": [
                S("The problem",
                  ["Prospects read what strangers say about you before they ever visit your site. Outdated "
                   "listings, mismatched phone numbers and unanswered feedback quietly push them toward "
                   "someone else."]),
                S("How the work runs",
                  ["Reputation work is mostly consistency, so the routine matters more than any single "
                   "campaign."],
                  bullets=["Audit your public listings for matching name, phone, hours and categories.",
                           "Set up a request routine that asks recent customers for honest feedback after "
                           "completed work.",
                           "Prepare reply guidelines for positive, mixed and critical feedback for your approval.",
                           "Check listings and new feedback on a regular schedule and flag anything urgent."]),
                S("What you receive",
                  ["A listing accuracy report, a feedback request sequence, a reply playbook in your own voice, "
                   "and a short recurring summary of new feedback and open issues."]),
                S("Current rating snapshot", ["Rating details will be added once sourced."],
                  claims=["review_rating", "review_count"]),
            ],
            "faqs": [
                F("Will you write feedback on our behalf?",
                  "No. Feedback must come from real customers. The work helps you ask at the right moment "
                  "and answer well."),
                F("Can negative feedback be removed?",
                  "Removal is not promised. Critical feedback gets a professional reply, and anything that "
                  "breaks a platform's own policy is reported through that platform's process."),
                PRICING_FAQ,
            ],
        },
        "/services/paid-advertising": {
            "lead": "Paid advertising management for local businesses, measured against confirmed inquiries "
                    "rather than clicks or impressions.",
            "sections": [
                S("The problem",
                  ["Ad platforms make it easy to spend and hard to see what the spending produced. Campaigns "
                   "often send every click to a homepage, so nobody can tell which service, area or message "
                   "actually led to a conversation."]),
                S("How the work runs",
                  ["Budget control stays with you throughout, and every change is written down."],
                  bullets=["Agree the single outcome that counts: a confirmed inquiry or booking.",
                           "Build separate campaigns per service so results are not blended together.",
                           "Point each ad at a landing page that repeats its promise and offer.",
                           "Review search terms and placements on a schedule and cut what wastes budget.",
                           "Change budgets only with your written approval."]),
                S("What you receive",
                  ["A campaign plan by service, matched landing pages, conversion tracking that counts only "
                   "confirmed submissions, and a plain-language summary at each review."]),
                S("Platforms and past campaign data", ["Platform list and campaign data pending approval."],
                  claims=["services_verified", "results"]),
            ],
            "faqs": [
                F("Who controls the ad budget?",
                  "You do. Budgets are set and changed only with your written approval."),
                F("Do you share personal details with ad platforms?",
                  "No email addresses, phone numbers or message contents are sent to analytics or ad tracking."),
                PRICING_FAQ,
            ],
        },
        "/about": {
            "lead": "CA-J Enterprises is a marketing systems business for local service companies.",
            "sections": [
                S("Who runs it", ["CA-J Enterprises is run by {owner_name}. The legal entity is {legal_entity}."],
                  claims=["owner_name", "legal_entity"]),
                S("How the work is approached",
                  ["Meetings come before proposals. Spending decisions are made in writing by the client. "
                   "New pages and forms are tested with synthetic data before real customers see them, and "
                   "nothing goes live without a recorded way to roll it back."]),
                S("Background and track record", ["Background details pending approval."],
                  claims=["years_in_business", "customers_served"]),
            ],
            "faqs": [
                F("Who will I talk to first?",
                  "Your first meeting is booked through the button on this page."),
                PRICING_FAQ,
            ],
        },
        "/contact": {
            "lead": "Send an inquiry or book a meeting with CA-J Enterprises.",
            "sections": [
                S("Direct contact", ["{owner_name} - phone {owner_phone} - email {owner_email}"],
                  claims=["owner_name", "owner_phone", "owner_email"]),
                S("Send an inquiry",
                  ["Use the inquiry form to tell us your name, the best way to reach you, the service you are "
                   "interested in and a short message. Only a name, one contact method and a service choice "
                   "are required."]),
                S("What happens after you send it",
                  ["If your inquiry is saved you will see a confirmation with a reference. If it cannot be "
                   "saved, your entries stay on the page so you can try again or book a meeting directly."]),
                S("Response times", ["Response time details pending approval."], claims=["response_time"]),
            ],
            "faqs": [
                F("Is my information shared?",
                  "Inquiry details are used to reply to you and are not sent to analytics or advertising tools."),
                PRICING_FAQ,
            ],
        },
    }


def _location_page(city: str, coverage_fact: str) -> dict:
    # Shared structure on purpose: until real city-specific evidence exists, the public body of every
    # location page is the same apart from the city name, and the thin-content guard must catch it.
    return {
        "lead": f"Marketing support for service businesses in {city}.",
        "sections": [
            S(f"Who this page is for",
              [f"Owners of service businesses in {city} looking for help with lead generation, reputation "
               "management and paid advertising."]),
            S("What working together looks like",
              ["Every engagement starts with a meeting, then an inventory of what already works, then a "
               "written plan you approve before anything changes."]),
            S(f"Local coverage in {city}", [f"Coverage details for {city} pending evidence."],
              claims=[coverage_fact, "service_areas"]),
            S(f"Local market notes for {city}", [f"City-specific notes for {city} pending evidence."],
              claims=[coverage_fact]),
        ],
        "faqs": [
            F(f"Do you work with businesses in {city}?", "Coverage pending evidence.", claims=[coverage_fact]),
            PRICING_FAQ,
        ],
    }


def page_models(rows: list[dict]) -> dict[str, dict]:
    models = _service_pages()
    for row in rows:
        if row["page_type"] == "location":
            models[row["route"]] = _location_page(row["city"], row["coverage_fact"])
    out = {}
    for row in rows:
        m = dict(models[row["route"]])
        m.update({"route": row["route"], "slug": row["slug"], "title": row["title"], "h1": row["h1"],
                  "primary_cta": {"label": CTA_LABEL, "href": C.BOOKING_URL},
                  "hero": {"opening_element": "outcome_headline",
                           "elements": ["outcome_headline", "offer_line", "primary_cta", "logo_footer_disclaimer"],
                           "logo_position": "footer", "hero_image": C.NEEDS_EVIDENCE}})
        out[row["route"]] = m
    return out


def apply_evidence_gate(model: dict, facts: dict) -> dict:
    """Split a model into public and withheld parts; fill verified placeholders."""
    values = {}

    def eligible(claims: list[str]) -> bool:
        ok = True
        for key in claims:
            if business_facts.is_public(facts, key):
                values[key] = business_facts.public_copy_value(facts, key)
            else:
                ok = False
        return ok

    public_sections, public_faqs, withheld = [], [], []
    for sec in model["sections"]:
        if eligible(sec["claims"]):
            public_sections.append({**sec, "paragraphs": [p.format(**values) for p in sec["paragraphs"]]})
        else:
            withheld.append({"kind": "section", "heading": sec["heading"],
                             "missing_claims": [k for k in sec["claims"] if not business_facts.is_public(facts, k)]})
    for faq in model["faqs"]:
        if eligible(faq["claims"]):
            public_faqs.append(faq)
        else:
            withheld.append({"kind": "faq", "heading": faq["q"],
                             "missing_claims": [k for k in faq["claims"] if not business_facts.is_public(facts, k)]})
    return {**model, "sections": public_sections, "faqs": public_faqs, "withheld": withheld}


def public_body(page: dict) -> str:
    parts = [page["lead"]]
    for sec in page["sections"]:
        parts.append(sec["heading"])
        parts.extend(sec["paragraphs"])
        parts.extend(sec["bullets"])
    for faq in page["faqs"]:
        parts.extend([faq["q"], faq["a"]])
    return "\n".join(parts)


def public_text(page: dict) -> str:
    return "\n".join([page["title"], page["h1"], public_body(page), page["primary_cta"]["label"]])


_TOKEN = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> set[str]:
    return set(_TOKEN.findall(text.lower()))


def similarity(a: str, b: str) -> float:
    """Normalized token overlap (Jaccard) between two bodies."""
    ta, tb = tokens(a), tokens(b)
    if not ta and not tb:
        return 1.0
    return len(ta & tb) / len(ta | tb)


def similarity_pairs(bodies: dict[str, str]) -> list[tuple[str, str, float]]:
    return [(a, b, round(similarity(bodies[a], bodies[b]), 4)) for a, b in combinations(sorted(bodies), 2)]


def assert_not_thin(bodies: dict[str, str], threshold: float = C.THIN_CONTENT_SIMILARITY_MAX) -> None:
    offending = [(a, b, s) for a, b, s in similarity_pairs(bodies) if s > threshold]
    if offending:
        raise ThinContentError(offending)


def assert_conversion_path(page: dict) -> None:
    ctas = [page["primary_cta"]] if isinstance(page.get("primary_cta"), dict) else page.get("primary_cta") or []
    if len(ctas) != 1:
        raise ConversionPathError(f"{page['route']}: expected exactly one primary action, got {len(ctas)}")
    if ctas[0]["href"] != C.BOOKING_URL:
        raise ConversionPathError(f"{page['route']}: primary CTA must link to {C.BOOKING_URL}")


def assert_public_copy_clean(page: dict, facts: dict) -> None:
    text = public_text(page)
    G.assert_no_fabricated_fact(text, facts)
    G.assert_no_price_in_message(text)
    G.assert_no_consumer_brand(text)
    G.assert_no_banned_phrase(text)
    G.assert_logo_not_first(page["hero"])


def render_markdown(page: dict, row: dict) -> str:
    lines = [f"<!-- DRAFT copy for {page['route']} | status {row['status']} | not eligible for publication "
             f"until the service/route is approved and claims are verified -->",
             f"# {page['h1']}", "", page["lead"], ""]
    for sec in page["sections"]:
        lines += [f"## {sec['heading']}", ""]
        for p in sec["paragraphs"]:
            lines += [p, ""]
        for b in sec["bullets"]:
            lines.append(f"- {b}")
        if sec["bullets"]:
            lines.append("")
    if page["faqs"]:
        lines += ["## Frequently asked questions", ""]
        for faq in page["faqs"]:
            lines += [f"**{faq['q']}**", "", faq["a"], ""]
    lines += [f"[{page['primary_cta']['label']}]({page['primary_cta']['href']})", ""]
    return "\n".join(lines)


def build(paths: Paths | None = None) -> dict:
    paths = paths or default_paths()
    facts = business_facts.load(paths)
    rows = page_plan.load(paths)
    by_route = {r["route"]: r for r in rows}
    pages = {route: apply_evidence_gate(m, facts) for route, m in page_models(rows).items()}

    for page in pages.values():
        assert_conversion_path(page)
        assert_public_copy_clean(page, facts)

    bodies = {route: public_body(p) for route, p in pages.items()}
    merge_record = None
    try:
        assert_not_thin(bodies)
    except ThinContentError as exc:
        merged = sorted({r for a, b, _ in exc.pairs for r in (a, b)})
        non_location = [r for r in merged if by_route[r]["page_type"] != "location"]
        if non_location:
            raise  # service/home/about pages must be genuinely distinct: refuse the whole build
        merge_record = {
            "record_type": "service-area-merge",
            "status": MERGED_STATUS,
            "merged_routes": merged,
            "similarity_pairs": [{"a": a, "b": b, "similarity": s} for a, b, s in exc.pairs],
            "threshold": C.THIN_CONTENT_SIMILARITY_MAX,
            "reason": "Location pages differ only by city name because no verified local coverage or "
                      "city-specific information exists. Refused to emit near-identical pages.",
            "evidence_needed": sorted({by_route[r]["coverage_fact"] for r in merged} | {"service_areas"}),
            "next_action": "Supply verified coverage and city-specific information, or approve one "
                           "service-area page that lists only confirmed areas.",
        }
        for route in merged:
            by_route[route]["indexable"] = False
            by_route[route]["status"] = MERGED_STATUS
            pages.pop(route)
        page_plan.write_inventory(rows, paths)
        record_blocker("location_pages", "Verified local coverage per city", "/locations/* pages",
                       merge_record["next_action"], paths)

    for route, page in pages.items():
        emit(f"page:{page['slug']}", paths.out / "pages" / f"{page['slug']}.md",
             render_markdown(page, by_route[route]), STATUS.DRAFT, paths, source="src/content_pages.py")
    if merge_record:
        emit("page:service-area-merge", paths.out / "pages" / "service-area-merge.json", merge_record,
             STATUS.BLOCKED, paths, source="src/content_pages.py")
    model = {"pages": pages, "similarity": [{"a": a, "b": b, "similarity": s}
                                            for a, b, s in similarity_pairs(bodies)],
             "merge_record": merge_record}
    emit("content_model", paths.out / "pages" / "_content_model.json", model, STATUS.DRAFT, paths,
         source="src/content_pages.py")
    return model


if __name__ == "__main__":
    result = build()
    print(f"pages emitted: {len(result['pages'])}; merge record: {bool(result['merge_record'])}")

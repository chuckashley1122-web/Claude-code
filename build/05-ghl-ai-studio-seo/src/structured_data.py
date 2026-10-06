"""JSON-LD builder -> out/structured_data/<slug>.json.

Properties are emitted only from facts that are verified with an evidence
source in config/business_facts.json. Anything unsourced is written by name
into ``_blocked_fields`` and recorded as a blocker; no plausible value is ever
substituted. ``priceRange`` is never emitted (meeting-first; locked pricing is
internal only). Keys beginning with ``_`` are review notes to strip before
pasting.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from src import business_facts, page_plan  # noqa: E402
from tools import guardrails as G  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, emit, record_blocker  # noqa: E402

NEVER_EMIT = {"priceRange"}


def _phone_e164ish(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) == 10:
        return f"+1-{digits[0:3]}-{digits[3:6]}-{digits[6:]}"
    return phone


def _value(facts, key):
    return business_facts.public_copy_value(facts, key) if business_facts.is_public(facts, key) else None


def build_organization(facts) -> tuple[dict, list[str]]:
    org: dict = {"@type": "Organization"}
    blocked: list[str] = []

    def put(prop: str, keys: list[str], make) -> None:
        vals = [_value(facts, k) for k in keys]
        if prop in NEVER_EMIT:
            blocked.append(prop)
        elif all(v is not None for v in vals):
            org[prop] = make(*vals)
        else:
            blocked.append(prop)

    put("name", ["brand_name"], lambda v: v)
    put("legalName", ["legal_entity"], lambda v: v)
    put("telephone", ["owner_phone"], _phone_e164ish)
    put("email", ["owner_email"], lambda v: v)
    put("founder", ["owner_name"], lambda v: {"@type": "Person", "name": v})
    put("url", ["site_origin"], lambda v: v)
    put("logo", ["logo_file", "site_origin"], lambda f, o: o.rstrip("/") + "/" + str(f).lstrip("/"))
    put("address", ["office_address"], lambda v: {"@type": "PostalAddress", "streetAddress": v})
    put("areaServed", ["service_areas"], lambda v: v)
    put("openingHours", ["opening_hours"], lambda v: v)
    put("aggregateRating", ["review_rating", "review_count"],
        lambda r, n: {"@type": "AggregateRating", "ratingValue": r, "reviewCount": n})
    put("review", ["testimonials"], lambda v: v)
    put("priceRange", [], lambda: None)
    return org, blocked


def build_route_document(row: dict, facts) -> dict:
    org, blocked = build_organization(facts)
    graph = [org]
    if row["page_type"] == "service":
        blocked.append("Service (service not in services_verified)")
    if business_facts.is_public(facts, "office_address") and business_facts.is_public(facts, "service_areas"):
        graph.append({"@type": "LocalBusiness", "name": org.get("name"),
                      "address": org.get("address"), "areaServed": org.get("areaServed")})
    else:
        blocked.append("LocalBusiness (needs verified address and service area)")
    if row["route"] != "/":
        if business_facts.is_public(facts, "site_origin"):
            origin = business_facts.public_copy_value(facts, "site_origin").rstrip("/")
            graph.append({"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": origin + "/"},
                {"@type": "ListItem", "position": 2, "name": row["h1"], "item": origin + row["route"]}]})
        else:
            blocked.append("BreadcrumbList (needs absolute URLs from a verified site_origin)")
    return {
        "@context": "https://schema.org",
        "@graph": graph,
        "_route": row["route"],
        "_status": "DRAFT - built only from verified facts; validate against the live URL before relying on it",
        "_blocked_fields": blocked,
    }


def build(paths: Paths | None = None) -> dict:
    paths = paths or default_paths()
    facts = business_facts.load(paths)
    docs = {}
    for row in page_plan.load(paths):
        if not row["indexable"]:
            continue
        doc = build_route_document(row, facts)
        text = str(doc["@graph"])
        G.assert_no_fabricated_fact(text, facts)
        G.assert_no_price_in_message(text)
        docs[row["slug"]] = doc
        emit(f"jsonld:{row['slug']}", paths.out / "structured_data" / f"{row['slug']}.json", doc, STATUS.DRAFT,
             paths, source="src/structured_data.py")
        for field in doc["_blocked_fields"]:
            record_blocker(f"jsonld:{field.split(' ')[0]}", f"verified source for {field}", "structured data",
                           "Supply verified fact in config/business_facts.json, then rebuild", paths)
    return docs


if __name__ == "__main__":
    build()
    print("structured data written")

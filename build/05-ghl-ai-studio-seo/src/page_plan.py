"""Route + intent inventory -> config/route_inventory.json + out/route_inventory.md.

The routes are the source's suggestions, carried as PROPOSED_NOT_APPROVED.
Canonical = site origin + route; the origin is NEEDS_EVIDENCE, so the marker is
emitted in place of a domain rather than guessing one.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, emit, record_blocker  # noqa: E402

AUDIENCE = "Owners and managers of local service businesses (PROPOSED_NOT_APPROVED audience)"

ROUTE_PLAN = {
    "/": {
        "page_type": "home", "search_intent": "navigational / commercial investigation",
        "primary_topic": "Marketing systems for local service businesses",
        "title": "Local Service Business Marketing Systems | CA-J Enterprises",
        "h1": "Marketing systems that turn local searches into booked appointments",
        "supporting_proof": ["services_verified", "results", "testimonials"],
    },
    "/services/lead-generation": {
        "page_type": "service", "search_intent": "commercial: find a lead generation partner",
        "primary_topic": "Lead generation for local service businesses",
        "title": "Lead Generation for Local Service Businesses | CA-J Enterprises",
        "h1": "Lead generation built around how your customers actually search",
        "supporting_proof": ["services_verified", "results"],
    },
    "/services/reputation-management": {
        "page_type": "service", "search_intent": "commercial: improve online reputation and review flow",
        "primary_topic": "Reputation management for local businesses",
        "title": "Reputation Management for Local Businesses | CA-J Enterprises",
        "h1": "Reputation management that keeps your public profile current and honest",
        "supporting_proof": ["services_verified", "review_rating", "review_count"],
    },
    "/services/paid-advertising": {
        "page_type": "service", "search_intent": "commercial: hire paid ad management",
        "primary_topic": "Paid advertising management for local businesses",
        "title": "Paid Advertising Management for Local Businesses | CA-J Enterprises",
        "h1": "Paid advertising managed against the outcome you care about",
        "supporting_proof": ["services_verified", "results"],
    },
    "/locations/austin": {
        "page_type": "location", "city": "Austin", "coverage_fact": "local_coverage_austin",
        "search_intent": "local: marketing help in Austin",
        "primary_topic": "Marketing support for Austin service businesses",
        "title": "Marketing for Austin Service Businesses | CA-J Enterprises",
        "h1": "Marketing support for service businesses in Austin",
        "supporting_proof": ["local_coverage_austin", "service_areas"],
    },
    "/locations/round-rock": {
        "page_type": "location", "city": "Round Rock", "coverage_fact": "local_coverage_round_rock",
        "search_intent": "local: marketing help in Round Rock",
        "primary_topic": "Marketing support for Round Rock service businesses",
        "title": "Marketing for Round Rock Service Businesses | CA-J Enterprises",
        "h1": "Marketing support for service businesses in Round Rock",
        "supporting_proof": ["local_coverage_round_rock", "service_areas"],
    },
    "/about": {
        "page_type": "about", "search_intent": "navigational: who runs CA-J Enterprises",
        "primary_topic": "About CA-J Enterprises and its founder",
        "title": "About CA-J Enterprises and Founder Chuck Ashley",
        "h1": "About CA-J Enterprises",
        "supporting_proof": ["owner_name", "legal_entity"],
    },
    "/contact": {
        "page_type": "contact", "search_intent": "navigational: contact or book a meeting",
        "primary_topic": "Contact CA-J Enterprises",
        "title": "Contact CA-J Enterprises | Send an Inquiry or Book a Meeting",
        "h1": "Contact CA-J Enterprises",
        "supporting_proof": ["owner_phone", "owner_email"],
    },
}

INTERNAL_LINKS = {
    "/": ["/services/lead-generation", "/services/reputation-management", "/services/paid-advertising",
          "/about", "/contact"],
    "/services/lead-generation": ["/", "/services/paid-advertising", "/contact"],
    "/services/reputation-management": ["/", "/services/lead-generation", "/contact"],
    "/services/paid-advertising": ["/", "/services/lead-generation", "/contact"],
    "/locations/austin": ["/", "/services/lead-generation", "/contact"],
    "/locations/round-rock": ["/", "/services/lead-generation", "/contact"],
    "/about": ["/", "/contact"],
    "/contact": ["/", "/about"],
}


def slug_for(route: str) -> str:
    return "index" if route == "/" else route.strip("/").replace("/", "-")


def canonical_for(origin: str, route: str) -> str:
    origin = (origin or C.NEEDS_EVIDENCE).rstrip("/")
    return origin + route


def build_rows(site_origin: str) -> list[dict]:
    rows = []
    for route in C.PROPOSED_ROUTES:
        plan = ROUTE_PLAN[route]
        row = {
            "route": route,
            "slug": slug_for(route),
            "page_type": plan["page_type"],
            "audience": AUDIENCE,
            "search_intent": plan["search_intent"],
            "primary_topic": plan["primary_topic"],
            "title": plan["title"],
            "h1": plan["h1"],
            "canonical": canonical_for(site_origin, route),
            "canonical_origin_status": "verified" if site_origin != C.NEEDS_EVIDENCE else C.NEEDS_EVIDENCE,
            "cta_destination": C.BOOKING_URL,
            "supporting_proof": plan["supporting_proof"],
            "internal_links": INTERNAL_LINKS[route],
            "indexable": True,
            "status": C.PROPOSED_NOT_APPROVED,
        }
        for extra in ("city", "coverage_fact"):
            if extra in plan:
                row[extra] = plan[extra]
        rows.append(row)
    return rows


def render_markdown(rows: list[dict]) -> str:
    lines = [
        "# Route and intent inventory (SPEC-05)",
        "",
        "All routes are the source's suggestions and are `PROPOSED_NOT_APPROVED`. Reusing existing "
        "URLs is preferred, but the existing route list is `NEEDS_EVIDENCE` until "
        "`tools/baseline_inventory.py` runs over a human-supplied URL list. Add only verified services.",
        "",
        "| Route | Type | Search intent | Title | H1 | Canonical | CTA | Proof needed | Internal links | Indexable | Status |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append("| {route} | {page_type} | {search_intent} | {title} | {h1} | {canonical} | {cta} | {proof} | "
                     "{links} | {idx} | {status} |".format(
                         cta=r["cta_destination"], proof=", ".join(r["supporting_proof"]),
                         links=", ".join(r["internal_links"]), idx="yes" if r["indexable"] else "no", **r))
    lines.append("")
    return "\n".join(lines)


def build(paths: Paths | None = None) -> list[dict]:
    paths = paths or default_paths()
    cfg = json.loads(paths.build_config.read_text(encoding="utf-8"))
    rows = build_rows(cfg.get("site_origin", C.NEEDS_EVIDENCE))
    write_inventory(rows, paths)
    record_blocker("site_origin", "Confirmed site origin (domain)", "canonicals, sitemap, JSON-LD url",
                   "Human confirms domain via work order 005-001 / 005-007", paths)
    record_blocker("existing_routes", "Existing live route list", "URL reuse and redirect map",
                   "Human supplies URL list and runs tools/baseline_inventory.py", paths)
    return rows


def write_inventory(rows: list[dict], paths: Paths) -> None:
    emit("route_inventory_json", paths.route_inventory, {"routes": rows}, STATUS.DRAFT, paths,
         source="src/page_plan.py")
    emit("route_inventory_md", paths.out / "route_inventory.md", render_markdown(rows), STATUS.DRAFT, paths,
         source="src/page_plan.py")


def load(paths: Paths | None = None) -> list[dict]:
    paths = paths or default_paths()
    return json.loads(paths.route_inventory.read_text(encoding="utf-8"))["routes"]


if __name__ == "__main__":
    build()
    print("route inventory written")

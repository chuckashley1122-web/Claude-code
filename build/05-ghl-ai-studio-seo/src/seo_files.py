"""Crawl-control files -> out/seo/sitemap.xml, robots.txt, indexability.md.

The sitemap lists only indexable canonical public routes; thank-you, 404 and
merged/withheld routes are excluded. Each URL carries a verified_status of
NEEDS_EVIDENCE until a human observes a real 200. Submission is a human
Search Console action (work order 005-008).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from src import page_plan  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, emit  # noqa: E402

NON_ROUTE_PAGES = [
    {"route": "/thank-you", "decision": "noindex", "reason": "post-submission page; not a search landing page"},
    {"route": "(any unknown path) -> 404", "decision": "noindex", "reason": "host must return a real HTTP 404"},
]


def sitemap_routes(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["indexable"]]


def render_sitemap(rows: list[dict]) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             "<!-- DRAFT sitemap: proposed canonical public routes only. Every URL has verified_status: "
             "NEEDS_EVIDENCE until a human observes a real HTTP 200. Submission is a human Search Console "
             "action. -->",
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for r in sitemap_routes(rows):
        lines.append(f"  <url><loc>{escape(r['canonical'])}</loc></url>"
                     f"<!-- verified_status: {C.NEEDS_EVIDENCE} -->")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def render_robots(site_origin: str) -> str:
    lines = ["# DRAFT robots.txt for review. robots.txt is crawl guidance, not privacy:",
             "# private data must sit behind authentication, and pages that must stay out of search use noindex.",
             "User-agent: *",
             "Allow: /"]
    if site_origin and site_origin != C.NEEDS_EVIDENCE:
        lines.append(f"Sitemap: {site_origin.rstrip('/')}/sitemap.xml")
    else:
        lines.append(f"# Sitemap: <site origin>/sitemap.xml  (site origin {C.NEEDS_EVIDENCE})")
    return "\n".join(lines) + "\n"


def render_indexability(rows: list[dict]) -> str:
    lines = ["# Indexability plan (SPEC-05)", "",
             "Robots blocking alone is not privacy; private data requires authentication. Pages that must not "
             "appear in search use a `noindex` robots meta tag (and are not blocked in robots.txt, so crawlers "
             "can read the noindex). Sitemap submission and URL inspection are human Search Console actions "
             "(work order 005-008). Indexing is tracked separately from ranking.", "",
             "| Route | Decision | In sitemap | Reason |", "|---|---|---|---|"]
    for r in rows:
        decision = "index" if r["indexable"] else "noindex"
        reason = "proposed public route (PROPOSED_NOT_APPROVED)" if r["indexable"] else r["status"]
        lines.append(f"| {r['route']} | {decision} | {'yes' if r['indexable'] else 'no'} | {reason} |")
    for p in NON_ROUTE_PAGES:
        lines.append(f"| {p['route']} | {p['decision']} | no | {p['reason']} |")
    lines.append("")
    return "\n".join(lines)


def build(paths: Paths | None = None) -> None:
    paths = paths or default_paths()
    rows = page_plan.load(paths)
    origin = json.loads(paths.build_config.read_text(encoding="utf-8")).get("site_origin", C.NEEDS_EVIDENCE)
    seo = paths.out / "seo"
    emit("sitemap", seo / "sitemap.xml", render_sitemap(rows), STATUS.DRAFT, paths, source="src/seo_files.py")
    emit("robots", seo / "robots.txt", render_robots(origin), STATUS.DRAFT, paths, source="src/seo_files.py")
    emit("indexability", seo / "indexability.md", render_indexability(rows), STATUS.DRAFT, paths,
         source="src/seo_files.py")


if __name__ == "__main__":
    build()
    print("seo files written")

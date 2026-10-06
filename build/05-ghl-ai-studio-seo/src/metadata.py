"""Metadata set -> out/metadata.json + out/metadata.md, validated by assert_canonical_unique.

Social preview images must be absolute URLs; none is approved, so og_image is
NEEDS_EVIDENCE (never a fabricated path). title_length_warning is a soft,
informational flag, not a hard SEO rule.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from src import page_plan  # noqa: E402
from tools import guardrails as G  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, emit, record_blocker  # noqa: E402

TITLE_SOFT_MAX = 60
DESCRIPTION_SOFT_MAX = 160

DESCRIPTIONS = {
    "/": "Marketing systems for local service businesses: pages, follow-up and a booking path that turn "
         "searches into conversations. Start with a meeting.",
    "/services/lead-generation": "Lead generation for local service businesses: intent-matched landing pages, "
                                 "inquiry forms that save to your CRM, and follow-up you approve.",
    "/services/reputation-management": "Reputation management for local businesses: accurate listings, an "
                                       "honest feedback request routine and replies in your own voice.",
    "/services/paid-advertising": "Paid advertising management for local businesses, measured against "
                                  "confirmed inquiries, with budget changes only on your written approval.",
    "/locations/austin": "Marketing support for service businesses in Austin.",
    "/locations/round-rock": "Marketing support for service businesses in Round Rock.",
    "/about": "About CA-J Enterprises, the marketing systems business run by Chuck Ashley, and how the work "
              "is approached.",
    "/contact": "Contact CA-J Enterprises: send an inquiry with one contact method, or book a meeting directly.",
}


class MetadataError(ValueError):
    pass


def _is_absolute_or_marker(url: str) -> bool:
    return url == C.NEEDS_EVIDENCE or url.startswith("https://") or url.startswith("http://")


def build_records(rows: list[dict], og_image: str = C.NEEDS_EVIDENCE) -> list[dict]:
    records = []
    for row in rows:
        if not row["indexable"]:
            continue
        desc = DESCRIPTIONS[row["route"]]
        rec = {
            "route": row["route"],
            "slug": row["slug"],
            "indexable": True,
            "title": row["title"],
            "h1": row["h1"],
            "meta_description": desc,
            "canonical": row["canonical"],
            "og": {"og:title": row["title"], "og:description": desc, "og:url": row["canonical"],
                   "og:type": "website", "og:image": og_image},
            "twitter": {"twitter:card": "summary_large_image", "twitter:title": row["title"],
                        "twitter:description": desc, "twitter:image": og_image},
            "og_creative": {"opening_element": "outcome_headline",
                            "elements": ["outcome_headline", "offer_line", "logo_footer_disclaimer"],
                            "logo_position": "footer", "og_image": og_image},
            "title_length_warning": len(row["title"]) > TITLE_SOFT_MAX,
            "description_length_warning": len(desc) > DESCRIPTION_SOFT_MAX,
        }
        for url in (rec["og"]["og:image"], rec["twitter"]["twitter:image"]):
            if not _is_absolute_or_marker(url):
                raise MetadataError(f"{row['route']}: social image must be an absolute URL, got {url!r}")
        records.append(rec)
    return records


def validate(records: list[dict]) -> None:
    G.assert_canonical_unique(records)
    for rec in records:
        G.assert_logo_not_first(rec["og_creative"])
        G.assert_no_price_in_message(rec["title"] + "\n" + rec["meta_description"])


def render_markdown(records: list[dict], excluded: list[dict]) -> str:
    lines = ["# Metadata set (SPEC-05)", "",
             "Unique title, meta description and exactly one canonical per indexable route. `og:image` is "
             "`NEEDS_EVIDENCE` until an approved absolute image URL exists. The length warning is a soft, "
             "informational flag.", "",
             "| Route | Title | Meta description | Canonical | og:image | Title length warning |",
             "|---|---|---|---|---|---|"]
    for r in records:
        lines.append(f"| {r['route']} | {r['title']} | {r['meta_description']} | {r['canonical']} | "
                     f"{r['og']['og:image']} | {'yes' if r['title_length_warning'] else 'no'} |")
    if excluded:
        lines += ["", "Excluded (not indexable):", ""]
        lines += [f"- {e['route']}: {e['reason']}" for e in excluded]
    lines.append("")
    return "\n".join(lines)


def build(paths: Paths | None = None) -> dict:
    paths = paths or default_paths()
    rows = page_plan.load(paths)
    records = build_records(rows)
    validate(records)
    excluded = [{"route": r["route"], "reason": r["status"]} for r in rows if not r["indexable"]]
    data = {"records": records, "excluded": excluded}
    emit("metadata_json", paths.out / "metadata.json", data, STATUS.DRAFT, paths, source="src/metadata.py")
    emit("metadata_md", paths.out / "metadata.md", render_markdown(records, excluded), STATUS.DRAFT, paths,
         source="src/metadata.py")
    record_blocker("og_image", "Approved absolute social preview image URL", "og:image / twitter:image",
                   "Supply an approved image hosted at the confirmed origin", paths)
    return data


if __name__ == "__main__":
    build()
    print("metadata written")

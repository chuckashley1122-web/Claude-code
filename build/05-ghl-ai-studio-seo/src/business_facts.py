"""Verified-business-facts register -> config/business_facts.json + out/business_facts.md.

Only house facts supplied by Chuck are verified. Everything else is
NEEDS_EVIDENCE with a blank evidence column. Locked pricing is recorded as
internal-only and is never eligible for public copy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, emit, record_blocker  # noqa: E402

HOUSE_SOURCE = "House fact supplied by Chuck Ashley (SPEC-05 section 6; config/constants.py {name})"
OWNER = "Chuck Ashley"


class UnsourcedClaim(ValueError):
    """A copy string referenced a claim with no verified evidence source."""


def _house(key: str, value, const_name: str, public: bool = True, internal: bool = False) -> dict:
    return {"key": key, "value": value, "evidence_source": HOUSE_SOURCE.format(name=const_name),
            "verified": True, "owner": OWNER, "next_action": "none",
            "public_copy_eligible": public and not internal, "internal_only": internal}


def _unknown(key: str, description: str, next_action: str) -> dict:
    return {"key": key, "value": C.NEEDS_EVIDENCE, "description": description, "evidence_source": "",
            "verified": False, "owner": OWNER, "next_action": next_action,
            "public_copy_eligible": False, "internal_only": False}


def fact_records() -> list[dict]:
    supply = "Supply approved material and an evidence link, then set verified=true"
    return [
        _house("owner_name", C.OWNER_NAME, "OWNER_NAME"),
        _house("owner_phone", C.OWNER_PHONE, "OWNER_PHONE"),
        _house("owner_email", C.OWNER_EMAIL, "OWNER_EMAIL"),
        _house("legal_entity", C.LEGAL_ENTITY, "LEGAL_ENTITY"),
        _house("brand_name", C.BRAND_NAME, "BRAND_NAME"),
        _house("booking_url", C.BOOKING_URL, "BOOKING_URL"),
        _house("tech_fee_monthly_usd", C.TECH_FEE_MONTHLY_USD, "TECH_FEE_MONTHLY_USD", internal=True),
        _house("setup_fee_usd", C.SETUP_FEE_USD, "SETUP_FEE_USD", internal=True),
        _house("per_booked_appointment_min_usd", C.PER_BOOKED_APPOINTMENT_MIN_USD,
               "PER_BOOKED_APPOINTMENT_MIN_USD", internal=True),
        _house("per_booked_appointment_max_usd", C.PER_BOOKED_APPOINTMENT_MAX_USD,
               "PER_BOOKED_APPOINTMENT_MAX_USD", internal=True),
        _unknown("business_name", "Approved public business name for page copy and JSON-LD", supply),
        _unknown("site_origin", "Owned/confirmed domain (scheme + host) for canonicals and sitemap",
                 "Confirm domain in work order 005-001; no purchase without approval (005-007)"),
        _unknown("services_verified", "Approved list of services actually offered", supply),
        _unknown("service_areas", "Real service areas actually covered", supply),
        _unknown("primary_location", "Primary business location", supply),
        _unknown("local_coverage_austin", "Actual local coverage and city-specific information for Austin", supply),
        _unknown("local_coverage_round_rock", "Actual local coverage and city-specific information for Round Rock",
                 supply),
        _unknown("offer_details_at_ai", "What the offer at the booking URL currently contains (do not rewrite it)",
                 "Human records the current /ai offer as-is in work order 005-001"),
        _unknown("logo_file", "Approved logo file (footer use only)", supply),
        _unknown("photos", "Approved photos with descriptive alt text", supply),
        _unknown("license_info", "Licences held", supply),
        _unknown("insurance", "Insurance held", supply),
        _unknown("guarantee", "Any guarantee offered", supply),
        _unknown("response_time", "Any response-time promise", supply),
        _unknown("testimonials", "Client testimonials with written permission", supply),
        _unknown("review_rating", "Review rating with source", supply),
        _unknown("review_count", "Review count with source", supply),
        _unknown("years_in_business", "Years in business", supply),
        _unknown("customers_served", "Count of clients served", supply),
        _unknown("results", "Client results or statistics", supply),
        _unknown("office_address", "Public office/postal address", supply),
        _unknown("opening_hours", "Published opening hours", supply),
        _unknown("privacy_policy_url", "Privacy policy URL", supply),
    ]


def facts_index(facts: dict | list) -> dict[str, dict]:
    records = facts["facts"] if isinstance(facts, dict) else facts
    return {r["key"]: r for r in records}


def public_copy_value(facts: dict | list, key: str):
    """Return a fact for public copy, or raise UnsourcedClaim (the content evidence gate)."""
    rec = facts_index(facts).get(key)
    if rec is None or not rec["verified"] or not rec["evidence_source"] or not rec["public_copy_eligible"]:
        raise UnsourcedClaim(f"claim {key!r} has no verified evidence or is not public-copy eligible")
    return rec["value"]


def is_public(facts: dict | list, key: str) -> bool:
    try:
        public_copy_value(facts, key)
        return True
    except UnsourcedClaim:
        return False


def render_markdown(records: list[dict]) -> str:
    lines = [
        "# Verified business facts and content evidence gate (SPEC-05)",
        "",
        "Every claim carries an evidence source or `NEEDS_EVIDENCE`. Only rows with "
        "`PUBLIC COPY ELIGIBILITY = YES` may appear in public copy; generators fail rather "
        "than publish an unsupported claim. Internal-only rows (locked commercial terms) are "
        "never emitted into customer-facing copy; their values live in `config/constants.py` only.",
        "",
        "| Key | Value | Evidence source | Verified | PUBLIC COPY ELIGIBILITY | Owner | Next action |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in records:
        value = "internal only (see config/constants.py)" if r["internal_only"] else str(r["value"])
        lines.append("| {k} | {v} | {e} | {ver} | {pub} | {o} | {n} |".format(
            k=r["key"], v=value, e=r["evidence_source"] or "", ver="yes" if r["verified"] else "no",
            pub="YES" if r["public_copy_eligible"] else "NO", o=r["owner"], n=r["next_action"]))
    lines += ["", "Consumer brands are kept out of this B2B register entirely.", ""]
    return "\n".join(lines)


def build(paths: Paths | None = None) -> dict:
    paths = paths or default_paths()
    records = fact_records()
    data = {"_note": "Unknown = NEEDS_EVIDENCE. Internal-only rows never appear in public copy.",
            "facts": records}
    emit("business_facts_json", paths.business_facts, data, STATUS.DRAFT, paths, source="src/business_facts.py")
    emit("business_facts_md", paths.out / "business_facts.md", render_markdown(records), STATUS.DRAFT, paths,
         source="src/business_facts.py")
    for r in records:
        if not r["verified"]:
            record_blocker(f"fact:{r['key']}", r["description"], "page copy / structured data",
                           r["next_action"], paths)
    return data


def load(paths: Paths | None = None) -> dict:
    paths = paths or default_paths()
    return json.loads(paths.business_facts.read_text(encoding="utf-8"))


if __name__ == "__main__":
    build()
    print("business facts written")

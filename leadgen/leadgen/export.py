"""Write results out in the shapes a CRM and a human each want."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import Lead

COLUMNS = [
    "tier", "score", "full_name", "first_name", "last_name", "title",
    "company", "company_domain", "industry", "employee_count", "location",
    "email", "phone", "linkedin_url", "website", "signals", "source",
    "source_ref", "notes",
]


def to_csv(leads: list[Lead], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for lead in sorted(leads, key=lambda x: -x.score):
            writer.writerow(lead.to_dict())
    return path


def to_json(leads: list[Lead], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [lead.to_dict() for lead in sorted(leads, key=lambda x: -x.score)]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def summary(leads: list[Lead]) -> str:
    tiers = {"hot": 0, "warm": 0, "cold": 0}
    for lead in leads:
        tiers[lead.tier] = tiers.get(lead.tier, 0) + 1
    reachable = sum(1 for x in leads if x.email or x.phone)
    return (
        f"{len(leads)} leads | hot {tiers['hot']} · warm {tiers['warm']} · "
        f"cold {tiers['cold']} | {reachable} with an email or phone"
    )

"""Release package -> out/release_package.md, out/asset_register.md, out/spend_items.json.

Fills the source's required final-status format; every unknown slot prints
NEEDS_EVIDENCE. Nothing is published: production status is "draft".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from src import acceptance_matrix, page_plan  # noqa: E402
from tools import secret_scan  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, blockers, emit, mark_asset, read_asset_register  # noqa: E402

NE = C.NEEDS_EVIDENCE

SPEND_ITEMS = [
    {"service": "Domain registration or transfer (only if no owned domain is confirmed)",
     "purpose": "Public origin for canonicals, sitemap and publish", "category": "domain"},
    {"service": "GoHighLevel plan change or AI Studio add-on (only if SSR/server functions/secrets require it)",
     "purpose": "Server-rendered pages, server functions and secrets vault", "category": "plan_change"},
    {"service": "GoHighLevel API access beyond the current plan (if required for the inquiry integration)",
     "purpose": "Contact upsert from the inquiry server function", "category": "subscription"},
    {"service": "Paid SEO tool (none prescribed; the zero-cost path is the design)",
     "purpose": "Not needed: local HTML checks + free Search Console", "category": "seo_tool"},
    {"service": "Ad spend (out of scope; AD_SPEND_CAP_USD = 0)",
     "purpose": "None in this build", "category": "ad_spend"},
]

CRM_FIELD_MAP = [
    ("name", "Contact name (standard field)", "contact matching rule NEEDS_EVIDENCE"),
    ("email", "Contact email (standard field)", "used for upsert if confirmed"),
    ("phone", "Contact phone (standard field)", "used for upsert if confirmed"),
    ("service_interest", "custom field id from env GHL_CUSTOM_FIELD_SERVICE_INTEREST", NE),
    ("service_area", "custom field id from env GHL_CUSTOM_FIELD_SERVICE_AREA", NE),
    ("message", "note or custom field (decision NEEDS_EVIDENCE)", NE),
    ("source_page", "custom field id from env GHL_CUSTOM_FIELD_SOURCE_PAGE", NE),
    ("submission_id", "custom field id from env GHL_CUSTOM_FIELD_SUBMISSION_ID (searchable reference)", NE),
    ("location (server)", f"env GHL_LOCATION_ID (expected {C.GHL_LOCATION_ID}, exact case)", "server config only"),
    ("pipeline/stage (server)", "env GHL_PIPELINE_ID / GHL_STAGE_ID, only if the approved flow needs an opportunity",
     NE),
]

OUTSIDE_AUTHORIZATION = [
    "Domain change or purchase (spend gate, work order 005-007)",
    "Any paid dependency: plan change, add-on, subscription, paid SEO tool (spend gate)",
    "Outbound workflow: any email/SMS/automation to real contacts (A2P/email status NEEDS_EVIDENCE)",
    "Publish of any page or version (PUBLISH_AUTHORITY = none)",
    "Migration of the existing project to a new runtime (unverified; 005-002)",
    "Any Meta object, including the frozen campaign held in config/constants.py (out of scope)",
]


def spend_items() -> dict:
    return {"total_build_spend_usd": C.TOTAL_BUILD_SPEND_USD, "ad_spend_cap_usd": C.AD_SPEND_CAP_USD,
            "items": [{**item, "cost_usd": NE, "approval_required": True, "approved": False,
                       "approval_ref": "", "authorized_amount_usd": 0} for item in SPEND_ITEMS]}


def final_status(results: list[dict], outstanding: list[str]) -> list[tuple[str, str]]:
    c = acceptance_matrix.counts(results)
    return [
        ("Project and location verified", f"{NE} (configured target location {C.GHL_LOCATION_ID}; project ID "
                                          f"{NE}; not verified in a live session)"),
        ("Draft/live URL", NE),
        ("Saved version and rollback target", NE),
        ("Completed steps", "Code-layer drafts only for source steps 6-8, 10, 13-14, 16-20 (files and local "
                            "reference implementation); no platform step completed"),
        ("Test results", f"PASS {c['PASS']} / FAIL {c['FAIL']} / BLOCKED {c['BLOCKED']}; evidence "
                         "out/tests/test_log.md and out/tests/T01.json-T14.json"),
        ("CRM persistence", f"{NE} (mock adapter only; no real CRM record exists)"),
        ("Outstanding inputs", "; ".join(outstanding)),
        ("Production status", "draft (nothing published, deployed, sent or purchased)"),
        ("Next executable action", "Human completes ui-work-orders/005-001-ghl-project-inventory-and-backup.md "
                                   "(record IDs and a reversible version before any change)"),
    ]


def render(paths: Paths, results: list[dict]) -> str:
    rows = page_plan.load(paths)
    redirect = json.loads((paths.out / "seo" / "redirect_map.json").read_text(encoding="utf-8"))
    open_blockers = blockers(paths)
    outstanding = sorted(open_blockers)
    lines = ["# Release package (SPEC-05)", "",
             "Draft-only package. Nothing was published, deployed, sent or purchased. No GHL, DNS, Search Console "
             "or Meta object was touched.", "", "## Required final status", ""]
    lines += [f"- **{k}:** {v}" for k, v in final_status(results, outstanding)]
    lines += ["", "## Draft URL, version and rollback", "",
              f"- Draft URL: {NE}", f"- Saved version ID: {NE}", f"- Rollback target: {NE}",
              "- Restore instructions: in the GHL account, restore the version recorded in work order 005-001 "
              "using the platform's supported version/restore mechanism (mechanism itself NEEDS_EVIDENCE). If no "
              "reversible version exists, do not replace the live project.", "",
              "## Route map", "", "| Route | Status | Indexable | Canonical |", "|---|---|---|---|"]
    lines += [f"| {r['route']} | {r['status']} | {'yes' if r['indexable'] else 'no'} | {r['canonical']} |"
              for r in rows]
    lines += ["", f"Redirect map: {redirect['status']} ({len(redirect['entries'])} entries); live redirect test "
              f"{redirect['live_redirect_test']}.", "", "## Redacted configuration names", "",
              "Environment variable names only (values live in the platform secrets vault / local .env, never "
              "in files):", ""]
    lines += [f"- `{n}`" for n in secret_scan.env_names(paths)]
    lines += ["", "## Page content inventory", ""]
    lines += [f"- `out/pages/{p.name}`" for p in sorted((paths.out / "pages").glob("*")) if p.is_file()]
    lines += ["", "## CRM field mapping (targets unverified)", "", "| Inquiry field | GHL target | Status |",
              "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in CRM_FIELD_MAP]
    lines += ["", "## Test matrix", "", "| Test | Name | Verdict | Evidence |", "|---|---|---|---|"]
    lines += [f"| {r['test_id']} | {r['name']} | {r['verdict']} | {r['evidence_path']} |" for r in results]
    lines += ["", "## Unresolved blockers", "", "| Item | Missing input | Next action |", "|---|---|---|"]
    lines += [f"| {k} | {v['missing_input']} | {v['next_action']} |" for k, v in sorted(open_blockers.items())]
    lines += ["", "## Actions outside execution authorization", ""]
    lines += [f"- {a}" for a in OUTSIDE_AUTHORIZATION]
    lines += ["", "## Spend items (all require explicit written approval; this build spends $0)", "",
              "| Service | Purpose | Cost | Approval |", "|---|---|---|---|"]
    lines += [f"| {i['service']} | {i['purpose']} | {i['cost_usd']} | approval required |"
              for i in spend_items()["items"]]
    lines.append("")
    return "\n".join(lines)


def render_asset_register(paths: Paths) -> str:
    reg = read_asset_register(paths)
    lines = ["# Asset register (SPEC-05)", "",
             "No asset carries `Published-by-human`; that status is reserved for a human after a real publish.", "",
             "| ID | Path | Status | Owner |", "|---|---|---|---|"]
    lines += [f"| {a['id']} | {a['path']} | {a['status']} | {a['owner']} |" for a in reg.values()]
    lines.append("")
    return "\n".join(lines)


def build(paths: Paths | None = None) -> str:
    paths = paths or default_paths()
    emit("spend_items", paths.out / "spend_items.json", spend_items(), STATUS.READY_FOR_HUMAN, paths,
         source="src/release_package.py")
    results = acceptance_matrix.load_results(paths)
    text = render(paths, results)
    emit("release_package", paths.out / "release_package.md", text, STATUS.READY_FOR_HUMAN, paths,
         source="src/release_package.py")
    mark_asset("asset_register_md", paths.out / "asset_register.md", STATUS.DRAFT, paths=paths)
    emit("asset_register_md", paths.out / "asset_register.md", render_asset_register(paths), STATUS.DRAFT, paths,
         source="src/release_package.py")
    return text


if __name__ == "__main__":
    build()
    print("release package written")

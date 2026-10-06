"""Run every guardrail across every generated file; per-file report; exit 1 on any hit.

Customer-facing files (page copy, mocks, metadata, structured data, the server
function, crawl files, prompt pack) get the price, fabricated-fact,
consumer-brand and disallowed-location checks. Every file gets the frozen
campaign, location-case, banned-phrase and public-contact checks. Structured
records get logo-not-first and canonical-uniqueness checks; spend items need an
approval reference before any approved spend; secrets come from secret_scan.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from tools import guardrails as G  # noqa: E402
from tools import secret_scan  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402

CUSTOMER_FACING_GLOBS = ["out/pages/*.md", "out/site/*.html", "out/metadata.json", "out/metadata.md",
                         "out/structured_data/*.json", "out/server_functions/*.ts", "out/seo/sitemap.xml",
                         "out/seo/robots.txt"]
PROMPT_PACK = "out/ai_studio_prompt_pack.md"
FROZEN_ALLOWED_FILES = {"config/constants.py"}


def customer_facing(paths: Paths) -> set[str]:
    rels = set()
    for pattern in CUSTOMER_FACING_GLOBS:
        rels |= {paths.rel(p) for p in paths.root.glob(pattern)}
    return rels


def _walk_creatives(obj, found: list) -> None:
    if isinstance(obj, dict):
        if "opening_element" in obj or "logo_position" in obj:
            found.append(obj)
        for v in obj.values():
            _walk_creatives(v, found)
    elif isinstance(obj, list):
        for v in obj:
            _walk_creatives(v, found)


def load_facts(paths: Paths) -> dict:
    if paths.business_facts.exists():
        return json.loads(paths.business_facts.read_text(encoding="utf-8"))
    return {"facts": []}


def scan_file(path: Path, rel: str, cf: set[str], facts: dict) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    problems: list[str] = []
    is_cf = rel in cf
    if rel in FROZEN_ALLOWED_FILES:
        checks_text = text.replace(C.FROZEN_CAMPAIGN_NAME, "").replace(C.DISALLOWED_LOCATION_ID, "")
    else:
        # CSS is not copy: drop <style> blocks so e.g. "width:100%" is not read as a claim
        checks_text = re.sub(r"(?is)<style\b.*?</style>", "", text) if path.suffix == ".html" else text
        if C.FROZEN_CAMPAIGN_NAME in text and not rel.endswith("HUMAN-DECISIONS.md"):
            problems.append("[frozen-campaign] frozen Meta campaign named outside constants.py and the "
                            "HUMAN-DECISIONS warning line")
    problems += G.check_all(checks_text, is_cf, facts)
    if rel == PROMPT_PACK:
        for check in (G.assert_no_price_in_message, G.assert_no_consumer_brand, G.assert_not_disallowed_location):
            try:
                check(text)
            except G.GuardrailViolation as exc:
                problems.append(str(exc))
    if path.suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        creatives: list = []
        _walk_creatives(data, creatives)
        for creative in creatives:
            try:
                G.assert_logo_not_first(creative)
            except G.GuardrailViolation as exc:
                problems.append(str(exc))
        if rel == "out/metadata.json" and data:
            try:
                G.assert_canonical_unique(data["records"])
            except G.GuardrailViolation as exc:
                problems.append(str(exc))
        if rel == "out/spend_items.json" and data:
            for item in data["items"]:
                if item.get("approved") or item.get("authorized_amount_usd") not in (0, None, C.NEEDS_EVIDENCE):
                    try:
                        G.assert_no_spend(item["service"], item.get("approval_ref"))
                    except G.GuardrailViolation as exc:
                        problems.append(str(exc))
    return problems


def scan(paths: Paths | None = None) -> dict[str, list[str]]:
    paths = paths or default_paths()
    cf = customer_facing(paths)
    facts = load_facts(paths)
    report: dict[str, list[str]] = {}
    for path in secret_scan.files_to_scan(paths):
        rel = paths.rel(path)
        report[rel] = scan_file(path, rel, cf, facts)
    for hit in secret_scan.scan(paths):
        report.setdefault(hit.file, []).append(f"[secret] {hit.kind}: {hit.redacted}")
    for rel in cf:
        report.setdefault(rel, [])
    return report


def main(argv: list[str] | None = None, paths: Paths | None = None) -> int:
    report = scan(paths)
    hits = 0
    for rel in sorted(report):
        problems = report[rel]
        hits += len(problems)
        print(f"{'FAIL' if problems else 'ok  '}  {rel}")
        for p in problems:
            print(f"        {p}")
    print(f"compliance_scan: {len(report)} files, {hits} hits")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

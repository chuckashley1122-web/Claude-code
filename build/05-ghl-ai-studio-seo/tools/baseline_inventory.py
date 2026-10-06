"""Baseline inventory over a human-supplied URL list -> out/baseline/baseline_inventory.{json,md}.

Records, per URL: status, title, H1, canonical, redirect chain, forms, calendar
embeds, thank-you pages and tracking IDs visible in raw HTML, plus the run
date. Published versions and DNS mappings cannot be observed from public HTML
and stay NEEDS_EVIDENCE (work order 005-001).

With no URL list it exits BLOCKED (code 3) and records the exact missing input.
It never fabricates a baseline. Network access requires --allow-network.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from tools import fetch_raw_html as F  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, emit, record_blocker  # noqa: E402

EXIT_BLOCKED = 3
CALENDAR_HINTS = ("calendar", "booking", "/widget/booking", "schedule")


def read_url_list(path: Path) -> list[str]:
    urls = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def summarize(evidence: dict) -> dict:
    url = evidence["url"]
    return {
        "url": url,
        "status": evidence.get("status"),
        "error": evidence.get("error"),
        "title": evidence.get("title"),
        "h1": evidence.get("h1", []),
        "canonical": evidence.get("canonical"),
        "redirect_chain": evidence.get("redirect_chain", []),
        "forms": evidence.get("forms", []),
        "calendar_embeds": [s for s in evidence.get("iframes", []) if any(h in s.lower() for h in CALENDAR_HINTS)],
        "is_thank_you_page": "thank" in url.lower(),
        "tracking_ids": evidence.get("tracking_ids", {}),
    }


def build_inventory(urls: list[str], opener: Any = None, sleep=None) -> dict:
    rows = []
    for url in urls:
        try:
            kwargs = {"opener": opener}
            if sleep is not None:
                kwargs["sleep"] = sleep
            rows.append(summarize(F.fetch(url, **kwargs)))
        except F.FetchRefused as exc:
            rows.append({"url": url, "status": None, "error": f"REFUSED: {exc}"})
    return {
        "run_date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "human-supplied URL list",
        "routes": rows,
        "published_versions": C.NEEDS_EVIDENCE,
        "dns_mappings": C.NEEDS_EVIDENCE,
        "note": "Raw HTML only (no JavaScript). Published versions and DNS mappings require the logged-in "
                "account and registrar (work order 005-001).",
    }


def render_markdown(inv: dict) -> str:
    lines = ["# Baseline inventory", "", f"Run date (UTC): {inv['run_date_utc']}", "",
             "| URL | Status | Title | H1 | Canonical | Redirects | Forms | Calendar embeds | Thank-you | Tracking IDs |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in inv["routes"]:
        lines.append("| {url} | {status} | {title} | {h1} | {canonical} | {redir} | {forms} | {cal} | {ty} | {trk} |".format(
            url=r["url"], status=r.get("status") or r.get("error"), title=r.get("title") or "",
            h1="; ".join(r.get("h1", [])), canonical=r.get("canonical") or "",
            redir=" -> ".join(f"{x['status']} {x['location']}" for x in r.get("redirect_chain", [])),
            forms=len(r.get("forms", [])), cal=", ".join(r.get("calendar_embeds", [])),
            ty="yes" if r.get("is_thank_you_page") else "no",
            trk=json.dumps(r.get("tracking_ids", {}))))
    lines += ["", f"Published versions: {inv['published_versions']}", f"DNS mappings: {inv['dns_mappings']}", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None, paths: Paths | None = None, opener: Any = None, sleep=None) -> int:
    ap = argparse.ArgumentParser(description="Baseline inventory over a human-supplied URL list")
    ap.add_argument("--urls", help="text file, one URL per line")
    ap.add_argument("--allow-network", action="store_true")
    args = ap.parse_args(argv)
    paths = paths or default_paths()
    if not args.urls or not Path(args.urls).exists() or not read_url_list(Path(args.urls)):
        record_blocker("baseline_inventory", "URL list of the existing live site (one URL per line)",
                       "baseline inventory, URL reuse, redirect map",
                       "Human writes the URL list and runs: tools/baseline_inventory.py --urls <file> "
                       "--allow-network", paths)
        print("BLOCKED: no URL list supplied (--urls <file>); no baseline fabricated")
        return EXIT_BLOCKED
    if not (args.allow_network or opener):
        print("BLOCKED: DRY_RUN - pass --allow-network to perform zero-cost unauthenticated GETs")
        return EXIT_BLOCKED
    inv = build_inventory(read_url_list(Path(args.urls)), opener=opener, sleep=sleep)
    emit("baseline_inventory_json", paths.out / "baseline" / "baseline_inventory.json", inv, STATUS.DRAFT, paths,
         source="tools/baseline_inventory.py")
    emit("baseline_inventory_md", paths.out / "baseline" / "baseline_inventory.md", render_markdown(inv),
         STATUS.DRAFT, paths, source="tools/baseline_inventory.py")
    print(f"baseline inventory: {len(inv['routes'])} URLs")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

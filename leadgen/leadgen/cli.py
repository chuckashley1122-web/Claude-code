"""python -m leadgen — source, enrich, score and export leads."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from . import export, score as scoring
from .enrich import detect_signals, llm_extract
from .models import Lead
from .sources import REGISTRY
from .sources.base import SourceError
from .sources.sales_navigator_csv import SalesNavigatorCSVSource

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
OUT_DIR = ROOT / "out"


def load_config(brand: str) -> dict[str, Any]:
    path = CONFIG_DIR / f"{brand}.yaml"
    if not path.exists():
        available = ", ".join(p.stem for p in CONFIG_DIR.glob("*.yaml"))
        raise SystemExit(f"no config for '{brand}'. Available: {available}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_source(name: str, args: argparse.Namespace):
    if name == "sales-nav-csv":
        if not args.csv:
            raise SystemExit("--csv is required for the sales-nav-csv source")
        return SalesNavigatorCSVSource(args.csv)
    if name == "apollo":
        return REGISTRY[name](reveal_contacts=args.reveal)
    if name == "nmls":
        return REGISTRY[name](state=args.state or "")
    return REGISTRY[name]()


def cmd_sources(args: argparse.Namespace) -> int:
    print(f"{'SOURCE':<16} {'LINKEDIN':<9} STATUS")
    for name, cls in REGISTRY.items():
        if name == "sales-nav-csv" and not args.csv:
            ok, why = False, "pass --csv <your LinkedIn/Sales Navigator export>"
        else:
            try:
                src = cls(args.csv) if name == "sales-nav-csv" else cls()
                ok, why = src.available()
            except Exception as exc:  # noqa: BLE001
                ok, why = False, str(exc)
        flag = "yes" if cls.linkedin_data else "no"
        print(f"{name:<16} {flag:<9} {'OK  ' if ok else 'NOT READY  '}{why}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.brand)
    icp = config.get("icp", {})

    source = build_source(args.source, args)
    ok, why = source.available()
    if not ok:
        print(f"source '{args.source}' is not usable: {why}", file=sys.stderr)
        return 2

    print(f"[1/4] searching {args.source} for {args.brand} (limit {args.limit}) ...")
    try:
        leads: list[Lead] = source.search(icp, limit=args.limit)
    except SourceError as exc:
        print(f"search failed: {exc}", file=sys.stderr)
        return 3
    print(f"      {len(leads)} raw records")

    leads = scoring.dedupe(leads)
    print(f"[2/4] {len(leads)} after dedupe")

    if args.enrich:
        print(f"[3/4] enriching from company websites (stealth={args.stealth}) ...")
        for i, lead in enumerate(leads, 1):
            detect_signals(lead, stealthy=args.stealth)
            if args.llm:
                llm_extract(lead)
            if i % 10 == 0 or i == len(leads):
                print(f"      {i}/{len(leads)}")
    else:
        print("[3/4] enrichment skipped (pass --enrich to crawl company sites)")

    print("[4/4] scoring ...")
    for lead in leads:
        scoring.score_lead(lead, config)

    if args.min_score:
        leads = [x for x in leads if x.score >= args.min_score]

    stem = args.out or f"{args.brand}-{args.source}"
    csv_path = export.to_csv(leads, OUT_DIR / f"{stem}.csv")
    json_path = export.to_json(leads, OUT_DIR / f"{stem}.json")

    print()
    print(export.summary(leads))
    print(f"wrote {csv_path}")
    print(f"wrote {json_path}")

    top = sorted(leads, key=lambda x: -x.score)[:5]
    if top:
        print("\ntop leads:")
        for lead in top:
            print(f"  [{lead.score:>3}] {lead.tier:<4} {lead.full_name or '(no name)'} — "
                  f"{lead.title or '?'} @ {lead.company or '?'} "
                  f"<{lead.email or lead.phone or 'no contact'}>")
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    config = load_config(args.brand)
    source = SalesNavigatorCSVSource(args.csv)
    for lead in source.search(config.get("icp", {}), limit=args.limit):
        if args.enrich:
            detect_signals(lead, stealthy=args.stealth)
        scoring.score_lead(lead, config)
        print(f"\n{lead.full_name} — {lead.title} @ {lead.company}")
        for line in scoring.explain(lead, config):
            print(f"   {line}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="leadgen", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_src = sub.add_parser("sources", help="list lead sources and whether they are configured")
    p_src.add_argument("--csv", help="path to a Sales Navigator export, to check it")
    p_src.set_defaults(func=cmd_sources)

    p_run = sub.add_parser("run", help="source -> enrich -> score -> export")
    p_run.add_argument("--brand", required=True, help="ca-jenterprises | ca-jconsulting")
    p_run.add_argument("--source", required=True, choices=list(REGISTRY))
    p_run.add_argument("--limit", type=int, default=50)
    p_run.add_argument("--csv", help="input CSV for the sales-nav-csv source")
    p_run.add_argument("--state", help="two-letter state, for the nmls source")
    p_run.add_argument("--enrich", action="store_true", help="crawl each company site for signals")
    p_run.add_argument("--llm", action="store_true", help="also run Scrapegraph-ai extraction")
    p_run.add_argument("--stealth", action="store_true", help="use a real browser when crawling")
    p_run.add_argument("--reveal", action="store_true", help="spend Apollo credits on emails/phones")
    p_run.add_argument("--min-score", type=int, default=0)
    p_run.add_argument("--out", help="output filename stem")
    p_run.set_defaults(func=cmd_run)

    p_exp = sub.add_parser("explain", help="show the score breakdown for leads in a CSV")
    p_exp.add_argument("--brand", required=True)
    p_exp.add_argument("--csv", required=True)
    p_exp.add_argument("--limit", type=int, default=10)
    p_exp.add_argument("--enrich", action="store_true")
    p_exp.add_argument("--stealth", action="store_true")
    p_exp.set_defaults(func=cmd_explain)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI entry point for the HVAC research pilot.

python scripts/run_research.py --retriever fixtures
python scripts/run_research.py --retriever filedrop --input inputs/companies.csv

--dry-run is on by default: no network and no external write. Local output files
under outputs/<run_id>/ are still written. Nothing is ever sent or synced.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from src.input_validation import validate_bytes, validate_file  # noqa: E402
from src.pipeline import fixture_demo_csv_bytes, run_pipeline  # noqa: E402
from src.retrieval import FileDropRetriever, FixtureRetriever  # noqa: E402

REFUSAL_BANNER = """\
==================================================================
REFUSED: ALLOW_NETWORK_RETRIEVAL is set, but ALLOW_LIVE=1 is not.
Network retrieval needs a human decision (work order 006-01).
This pilot has no live retriever; nothing was fetched or written.
=================================================================="""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CA-J HVAC research pilot (offline, draft outputs only)")
    p.add_argument("--input", default="inputs/companies.csv", help="input CSV (relative to the project root)")
    p.add_argument("--retriever", choices=("fixtures", "filedrop"), default="fixtures")
    p.add_argument("--out-root", default="outputs", help="run folders are created here")
    p.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True,
                   help="default on: no network, no external write")
    p.add_argument("--simulate-retrieval-failure", action="store_true",
                   help="test-only, fixtures mode: serve Fixture D (RETRIEVAL_FAILURE) for the last company")
    p.add_argument("--pages-root", default=None, help="filedrop page folder (default inputs/pages)")
    return p


def main(argv: list[str] | None = None, environ: dict | None = None) -> int:
    env = os.environ if environ is None else environ
    args = build_parser().parse_args(argv)
    root = config.project_root(env)

    allow_live = config.env_flag("ALLOW_LIVE", config.ALLOW_LIVE, env)
    if config.env_flag("ALLOW_NETWORK_RETRIEVAL", config.ALLOW_NETWORK_RETRIEVAL, env) and not allow_live:
        print(REFUSAL_BANNER)
        return 3
    dry_run = args.dry_run and config.env_flag("DRY_RUN", config.DRY_RUN, env)
    if not dry_run and not allow_live:
        print("REFUSED: dry-run is off but ALLOW_LIVE=1 was not set by a human. Nothing was run.")
        return 3
    if not dry_run:
        print("NOTE: dry-run is off, but this pilot has no network or external-write path; it runs offline anyway.")
    if args.simulate_retrieval_failure and args.retriever != "fixtures":
        print("REFUSED: --simulate-retrieval-failure is a test-only flag for --retriever fixtures.")
        return 2

    try:
        max_pages, max_retries = config.max_pages(env), config.max_retries(env)
        config.max_companies(env)
    except config.CapRaiseRefused as exc:
        print(f"REFUSED: {exc}")
        return 2

    def resolve(p: str) -> Path:
        path = Path(p)
        return path if path.is_absolute() else root / path

    input_path, out_root = resolve(args.input), resolve(args.out_root)
    fixture_mode = args.retriever == "fixtures"
    if fixture_mode:
        force = frozenset()
        if args.simulate_retrieval_failure:
            res = validate_file(input_path)
            if res.state == "INPUT_REQUIRED":
                res = validate_bytes(fixture_demo_csv_bytes())
            if res.ok:
                force = frozenset({res.companies[-1].company_id})
        retriever = FixtureRetriever(config.fixture_dir(env), force_failure_ids=force)
    else:
        retriever = FileDropRetriever(resolve(args.pages_root) if args.pages_root else root / "inputs" / "pages")

    report = run_pipeline(input_path, retriever, out_root, fixture_mode=fixture_mode,
                          use_fixture_demo_when_empty=True, max_pages=max_pages, max_retries=max_retries)
    if report.state == "INPUT_REQUIRED":
        print(report.message)
        return 0
    if report.state == "INPUT_INVALID":
        print(report.message)
        return 1
    if fixture_mode:
        print("FIXTURE RUN (fixture_mode=true): mock companies only, not prospect output.")
        if input_path.is_file() and validate_file(input_path).state == "INPUT_REQUIRED":
            print(f"INPUT_REQUIRED for the live run: {input_path} has no company rows (work order 006-02).")
    print(report.render())
    return 1 if report.validation_findings else 0


if __name__ == "__main__":
    sys.exit(main())

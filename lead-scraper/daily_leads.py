#!/usr/bin/env python3
"""Scheduled daily lead run.

Scrapes every source in config.yml, appends new leads to leads.csv, and writes
anything that went wrong to errors.log. Designed to be run unattended from
cron, so it never prompts and always exits with a meaningful status code:

    0  the run completed and nothing failed
    1  the run completed but some pages or sources failed (see errors.log)
    2  the run could not start at all (config/model/browser problem)

    python daily_leads.py
    python daily_leads.py --max-pages 5
"""

from __future__ import annotations

import argparse
import sys
import traceback
from datetime import datetime
from pathlib import Path

from lead_scraper import BASE_DIR, load_config, print_summary, run


def _resolve(path_value: str) -> Path:
    """Resolve a config path relative to the project directory."""
    path = Path(path_value)
    return path if path.is_absolute() else BASE_DIR / path


def log_error(error_log: Path, message: str, *, multiline: bool = False) -> None:
    """Append a timestamped entry to errors.log.

    Messages are flattened to a single line by default so the log stays
    greppable; tracebacks opt out via ``multiline``.
    """
    error_log.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not multiline:
        message = " ".join(message.split())
    with error_log.open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {message}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="Path to config.yml")
    parser.add_argument("--max-pages", type=int, help="Cap on result pages per source")
    parser.add_argument("--quiet", action="store_true", help="Only print the summary")
    args = parser.parse_args(argv)

    started = datetime.now()
    print(f"=== daily_leads run started {started:%Y-%m-%d %H:%M:%S} ===")

    # Config problems happen before we have a configured log path, so fall
    # back to the default location rather than losing the message.
    error_log = BASE_DIR / "errors.log"
    try:
        config = load_config(args.config)
        error_log = _resolve(config["output"].get("error_log", "errors.log"))
    except Exception as exc:
        log_error(error_log, f"FATAL: could not load config: {exc}")
        print(f"FATAL: could not load config: {exc}", file=sys.stderr)
        return 2

    try:
        result = run(
            config,
            max_pages=args.max_pages,
            verbose=not args.quiet,
        )
    except Exception as exc:
        log_error(error_log, f"FATAL: run aborted: {exc}")
        log_error(
            error_log,
            "Traceback:\n" + traceback.format_exc().rstrip(),
            multiline=True,
        )
        print(f"FATAL: run aborted: {exc}", file=sys.stderr)
        return 2

    print_summary(result)

    for message in result.errors:
        log_error(error_log, message)

    elapsed = (datetime.now() - started).total_seconds()
    print(f"=== finished in {elapsed:.1f}s ===")

    if result.errors:
        print(f"{len(result.errors)} problem(s) logged to {error_log}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Idempotent, dependency-ordered orchestrator. Logs to logs/build.log.

Runs every generator in order, then the acceptance matrix and the release
package. Re-running produces the same outputs; the decision log only gains
entries when a decision actually changes. Never publishes, deploys, sends or
purchases anything.
"""

from __future__ import annotations

import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import (acceptance_matrix, ai_studio_prompts, business_facts, content_pages,  # noqa: E402
                 estimator, inquiry_contract, inquiry_handler, metadata, page_plan, redirect_map,
                 release_package, seo_files, site_mock, structured_data, ui_work_orders)
from tools.paths import Paths, default_paths  # noqa: E402

STEPS = [
    ("business_facts", business_facts.build),
    ("page_plan", page_plan.build),
    ("content_pages", content_pages.build),
    ("metadata", metadata.build),
    ("structured_data", structured_data.build),
    ("seo_files", seo_files.build),
    ("redirect_map", redirect_map.build),
    ("site_mock", site_mock.build),
    ("ai_studio_prompts", ai_studio_prompts.build),
    ("inquiry_contract", inquiry_contract.build),
    ("inquiry_handler_ts", inquiry_handler.build),
    ("estimator", estimator.build),
    ("ui_work_orders", ui_work_orders.build),
    ("acceptance_matrix", acceptance_matrix.run),
    ("release_package", release_package.build),
]


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(paths: Paths | None = None, quiet: bool = False) -> int:
    paths = paths or default_paths()
    paths.logs.mkdir(parents=True, exist_ok=True)
    log_path = paths.logs / "build.log"
    with log_path.open("a", encoding="utf-8", newline="\n") as log:
        def say(msg: str) -> None:
            line = f"{_stamp()} {msg}"
            log.write(line + "\n")
            if not quiet:
                print(line)

        say("build_all start (draft only: nothing published, deployed, sent or purchased)")
        for name, fn in STEPS:
            try:
                fn(paths)
                say(f"OK    {name}")
            except Exception as exc:  # report and stop: later steps depend on earlier ones
                say(f"FAIL  {name}: {type(exc).__name__}: {exc}")
                log.write(traceback.format_exc())
                return 1
        say("build_all done")
    return 0


if __name__ == "__main__":
    sys.exit(run())

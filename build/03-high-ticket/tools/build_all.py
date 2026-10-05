"""Idempotent orchestrator. Runs every step in dependency order and logs to logs/build.log.

Order: validate config -> niche/economics -> offer -> CRM/calendar -> creatives/copy/form ->
integration -> workflows -> messages/pages -> sales/onboarding/delivery -> attribution fixtures
-> tests (T01-T14) -> UI checklists -> launch review -> compliance scan.

Run: python tools/build_all.py
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src import (calendar_spec, copy_pack, creative_pack, crm_schema, delivery_scope, form_spec,  # noqa: E402
                 integration_spec, launch_review, message_templates, niche_brief, offer_spec, onboarding_pack,
                 positioning, precall_page, risk_reversal, sales_guide, ui_tasks, utm_fixtures, workflow_specs)
from tools import break_even, compliance_scan, margin_model, run_tests, validate_config  # noqa: E402
from tools.state import State  # noqa: E402

GENERATORS = [niche_brief, break_even, margin_model, offer_spec, positioning, risk_reversal, crm_schema, calendar_spec,
              creative_pack, copy_pack, form_spec, integration_spec, workflow_specs, message_templates, precall_page,
              sales_guide, onboarding_pack, delivery_scope, utm_fixtures]


def generate(state: State) -> list[Path]:
    paths = []
    for mod in GENERATORS:
        produced = mod.build(state)
        paths += produced
        state.build_log(f"step {mod.__name__}: wrote {len(produced)} file(s)")
    state.save_blockers()
    return paths


def reset_generated(state: State) -> None:
    """Make the run idempotent: generated outputs are rebuilt from scratch each time.
    The decision log is append-only and is never truncated."""
    if state.out_dir.exists():
        shutil.rmtree(state.out_dir)
    state.out_dir.mkdir(parents=True)
    if state.asset_register_path.exists():
        state.asset_register_path.unlink()
    state.blockers = []


def run(root: Path = BUILD_ROOT) -> int:
    config = json.loads((Path(root) / "config" / "build_config.json").read_text(encoding="utf-8"))
    env_path = Path(root) / ".env.example"
    checks = validate_config.validate(config, C, env_path.read_text(encoding="utf-8") if env_path.exists() else None)
    state = State(root, config)
    state.build_log("build_all start (DRY_RUN, no network, no spend)")
    failed = [n for n, ok, _ in checks if not ok]
    for n, ok, d in checks:
        state.build_log(f"validate {'PASS' if ok else 'FAIL'} {n} {d}")
    if failed:
        state.build_log(f"build_all abort: config validation failed {failed}")
        print(f"build_all: config validation failed: {failed}")
        return 1
    reset_generated(state)
    generate(state)
    results = run_tests.run_all(state)
    state.build_log("step run_tests: " + ", ".join(f"{r['test_id']}={r['verdict']}" for r in results))
    ui_tasks.build(state)
    state.build_log("step ui_tasks: wrote 3 checklist(s)")
    launch_review.build(state)
    state.build_log("step launch_review: wrote 2 file(s)")
    report = compliance_scan.scan_tree(Path(root))
    compliance_scan.write_report(Path(root), report)
    hits = sum(len(v) for v in report.values())
    state.build_log(f"step compliance_scan: {len(report)} files, {hits} hits")
    fails = [r["test_id"] for r in results if r["verdict"] == "FAIL"]
    status = 0 if not hits and not fails else 1
    state.build_log(f"build_all end: exit {status}")
    print(f"build_all: {len(list((Path(root) / 'out').rglob('*')))} out entries; tests "
          f"PASS {sum(r['verdict'] == 'PASS' for r in results)} / FAIL {len(fails)} / BLOCKED {sum(r['verdict'] == 'BLOCKED' for r in results)}; "
          f"compliance hits {hits}; exit {status}")
    return status


if __name__ == "__main__":
    sys.exit(run())

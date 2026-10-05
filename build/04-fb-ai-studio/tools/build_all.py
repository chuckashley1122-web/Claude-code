"""Idempotent, dependency-ordered orchestrator for SPEC-04.

Run: python tools/build_all.py
Validates config first (aborts on any failed check), then runs every generator
in dependency order and logs to logs/build.log. Writes files only; makes no
network calls and launches nothing.
"""
from __future__ import annotations

import datetime as _dt
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import validate_config  # noqa: E402
from tools.state import BuildContext  # noqa: E402

# (module, reason it comes here)
STEPS = [
    ("src.offer", "offer first: everything else references it"),
    ("src.pipeline_spec", "workflows move opportunities between these stages"),
    ("src.message_templates", "workflow 01/02 embed these messages"),
    ("src.workflow_new_lead", "needs messages"),
    ("src.workflow_hot_lead", "needs workflow 01 name"),
    ("src.pixel_capi_spec", "workflow 03 reads capi_settings"),
    ("src.workflow_capi", "needs capi settings"),
    ("src.landing_content", "mock renders from the content spec"),
    ("src.landing_mock", "needs content spec"),
    ("src.ai_studio_prompts", "needs config + content rules"),
    ("src.ad_angles", "copy and creatives hang off angles"),
    ("src.ad_copy", "needs angles"),
    ("src.creative_specs", "needs angles"),
    ("src.campaign_spec", "needs copy + creatives + CAPI event"),
    ("tools.utm_builder", "needs the draft campaign name"),
    ("src.ui_checklists", "needs campaign config + all blockers"),
    ("src.launch_review", "packages everything; runs last"),
]


class BuildLogger:
    def __init__(self, root: Path, echo: bool = True):
        self.path = Path(root) / "logs" / "build.log"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.echo = echo

    def __call__(self, msg: str) -> None:
        line = f"{_dt.datetime.now(_dt.timezone.utc).isoformat(timespec='seconds')} {msg}"
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        if self.echo:
            print(line)


def run(root: Path = ROOT, work_orders_dir: Path | None = None, today: _dt.date | None = None,
        quiet: bool = False) -> list[Path]:
    root = Path(root)
    log = BuildLogger(root, echo=not quiet)
    log(f"build start root={root.name} DRY_RUN=True (no network, no spend, nothing launched)")
    cfg = validate_config.load_config(root)
    failed = [r for r in validate_config.run_checks(cfg=cfg) if not r[1]]
    if failed:
        for name, _, detail in failed:
            log(f"VALIDATION FAIL {name}: {detail}")
        raise SystemExit("Config validation failed; build aborted.")
    ctx = BuildContext(root, work_orders_dir=work_orders_dir, today=today)
    if ctx.state.blockers_file.exists():
        ctx.state.blockers_file.unlink()  # rebuilt from scratch each run (idempotent)
    written: list[Path] = []
    for mod_name, why in STEPS:
        mod = importlib.import_module(mod_name)
        result = mod.build(ctx)
        paths = result if isinstance(result, list) else [result]
        written += paths
        log(f"step {mod_name} ok ({why}) -> {len(paths)} file(s)")
    log(f"build done: {len(written)} files written; draft campaign {ctx.draft_campaign_name()} (not published)")
    return written


def main() -> int:
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Report SET / MISSING for every env var the suite knows about. Never prints values.

MISSING credentials are a blocker to live operation, not a build failure; this
script exits 0 in dry-run mode. It exits 2 if DRY_RUN=false without ALLOW_LIVE=1.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import (ENV_VARS, LiveModeRefused, enforce_run_mode, env_status,  # noqa: E402
                             ghl_location_mismatch, load_settings)


def report_lines(settings) -> list[str]:
    status = env_status(settings)
    width = max(len(v.name) for v in ENV_VARS)
    lines = [f"Mode: {'DRY_RUN (default, safe)' if settings.dry_run else 'LIVE requested'}"]
    for var in ENV_VARS:
        gate = "APPROVAL" if var.approval_required else "-"
        lines.append(f"{var.name:<{width}}  {status[var.name]:<7}  {gate:<8}  {var.gate}")
    missing = sum(1 for s in status.values() if s == "MISSING")
    lines.append(f"{len(status) - missing} SET, {missing} MISSING "
                 "(MISSING blocks live operation only; dry runs need none of them)")
    mismatch = ghl_location_mismatch(settings)
    if mismatch:
        lines.append(f"WARNING: {mismatch}")
    return lines


def main(argv=None) -> int:
    settings = load_settings()
    for line in report_lines(settings):
        print(line)
    try:
        enforce_run_mode(settings)
    except LiveModeRefused as exc:
        return int(exc.code)
    return 0


if __name__ == "__main__":
    sys.exit(main())

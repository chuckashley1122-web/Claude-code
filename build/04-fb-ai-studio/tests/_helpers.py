"""Shared test helpers: build into an isolated temp copy of the build root."""
from __future__ import annotations

import datetime as dt
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXED_DATE = dt.date(2026, 10, 5)
SOURCE_ITEMS = ["config", "tools", "src", "README.md", ".env.example", ".gitignore"]


class TempBuild:
    """Copies the source tree to <tmp>/repo/build/04-fb-ai-studio and builds there."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.root = base / "repo" / "build" / "04-fb-ai-studio"
        self.work_orders = base / "repo" / "ui-work-orders"
        self.root.mkdir(parents=True)
        ignore = shutil.ignore_patterns("__pycache__", "decision_log.jsonl", "asset_register.json")
        for item in SOURCE_ITEMS:
            src = ROOT / item
            if src.is_dir():
                shutil.copytree(src, self.root / item, ignore=ignore)
            elif src.exists():
                shutil.copy2(src, self.root / item)

    def build(self):
        from tools.build_all import run
        return run(self.root, work_orders_dir=self.work_orders, today=FIXED_DATE, quiet=True)

    def cleanup(self):
        self._tmp.cleanup()

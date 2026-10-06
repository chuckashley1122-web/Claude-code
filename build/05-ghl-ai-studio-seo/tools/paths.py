"""Filesystem layout for the SPEC-05 build.

Every generator takes a ``Paths`` instance so the real build writes into the
build root while tests write into a throwaway temporary directory.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

BUILD_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BUILD_ROOT.parents[1]
UI_WORK_ORDER_PREFIX = "005"


def ensure_import_path() -> None:
    """Make ``config``, ``tools`` and ``src`` importable from any entry point."""
    root = str(BUILD_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


@dataclass(frozen=True)
class Paths:
    root: Path
    ui_work_orders: Path

    @property
    def config(self) -> Path:
        return self.root / "config"

    @property
    def out(self) -> Path:
        return self.root / "out"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def decision_log(self) -> Path:
        return self.config / "decision_log.jsonl"

    @property
    def asset_register(self) -> Path:
        return self.config / "asset_register.json"

    @property
    def build_config(self) -> Path:
        return self.config / "build_config.json"

    @property
    def business_facts(self) -> Path:
        return self.config / "business_facts.json"

    @property
    def route_inventory(self) -> Path:
        return self.config / "route_inventory.json"

    @property
    def redirect_input(self) -> Path:
        """Optional human-supplied old->new URL list. Absent until a human supplies it."""
        return self.config / "redirect_input.json"

    def rel(self, path: Path) -> str:
        """Path relative to the build root (or repo root for work orders), POSIX style."""
        path = Path(path)
        for base in (self.root, self.ui_work_orders.parent):
            try:
                return path.resolve().relative_to(base.resolve()).as_posix()
            except ValueError:
                continue
        return path.as_posix()


def default_paths() -> Paths:
    return Paths(root=BUILD_ROOT, ui_work_orders=REPO_ROOT / "ui-work-orders")


def scratch_paths(tmp: Path) -> Paths:
    """A disposable copy of the static config inputs, for tests."""
    tmp = Path(tmp)
    (tmp / "config").mkdir(parents=True, exist_ok=True)
    shutil.copy2(BUILD_ROOT / "config" / "build_config.json", tmp / "config" / "build_config.json")
    shutil.copy2(BUILD_ROOT / ".env.example", tmp / ".env.example")
    return Paths(root=tmp, ui_work_orders=tmp / "ui-work-orders")

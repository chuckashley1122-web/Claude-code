"""State layer: status enum, decision-log writer, blocker recorder, asset register.

No script may write the status `Live` or `Ready for launch`; both are reserved
for a human after verified tests and explicit approval.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402


class Status(str, Enum):
    NOT_STARTED = "Not started"
    DRAFT = "Draft"
    TESTED = "Tested"
    READY_FOR_LAUNCH = "Ready for launch"
    LIVE = "Live"
    BLOCKED = "Blocked"


FORBIDDEN_SCRIPT_STATUSES = {Status.LIVE, Status.READY_FOR_LAUNCH}


class StatusForbidden(ValueError):
    """Raised when a script tries to write a status reserved for humans."""


def _coerce_status(status) -> Status:
    try:
        st = status if isinstance(status, Status) else Status(status)
    except ValueError as exc:
        raise ValueError(f"unknown status {status!r}; allowed: {[s.value for s in Status]}") from exc
    if st in FORBIDDEN_SCRIPT_STATUSES:
        raise StatusForbidden(f"status {st.value!r} may only be set by a human after verified tests and approval")
    return st


def load_config(root: Path = BUILD_ROOT) -> dict:
    return json.loads((Path(root) / "config" / "build_config.json").read_text(encoding="utf-8"))


class State:
    """All writes for one build run, bound to a build root (a temp dir in tests)."""

    def __init__(self, root: Path = BUILD_ROOT, config: dict | None = None, clock=None):
        self.root = Path(root)
        self.config_dir = self.root / "config"
        self.out_dir = self.root / "out"
        self.logs_dir = self.root / "logs"
        self.ui_dir = self.root / "ui-tasks"
        for d in (self.config_dir, self.out_dir, self.logs_dir, self.ui_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.config = config if config is not None else load_config(self.root)
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self.blockers: list[dict] = []

    # ---- paths -------------------------------------------------------------
    def rel(self, path: Path) -> str:
        return Path(path).resolve().relative_to(self.root.resolve()).as_posix()

    @property
    def decision_log_path(self) -> Path:
        return self.config_dir / "decision_log.jsonl"

    @property
    def asset_register_path(self) -> Path:
        return self.config_dir / "asset_register.json"

    @property
    def blockers_path(self) -> Path:
        return self.out_dir / "blockers.json"

    # ---- decision log ------------------------------------------------------
    def log(self, key: str, value, source: str, status) -> dict:
        st = _coerce_status(status)
        entry = {
            "timestamp": self._clock().isoformat(),
            "key": key,
            "value": value,
            "source": source,
            "status": st.value,
        }
        with self.decision_log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def build_log(self, message: str) -> None:
        with (self.logs_dir / "build.log").open("a", encoding="utf-8") as fh:
            fh.write(f"{self._clock().isoformat()} {message}\n")

    # ---- blockers ----------------------------------------------------------
    def record_blocker(self, item: str, missing_input: str, work_affected: str, next_action: str,
                       owner: str = C.OWNER_NAME, source_file: str = "") -> dict:
        blocker = {
            "item": item,
            "missing_input": missing_input,
            "work_affected": work_affected,
            "next_action": next_action,
            "owner": owner,
            "source_file": source_file,
        }
        for existing in self.blockers:
            if existing["item"] == item and existing["source_file"] == source_file:
                return existing
        self.blockers.append(blocker)
        self.log(f"blocker:{item}", missing_input, source_file or "build", Status.BLOCKED)
        return blocker

    def needs(self, item: str, source_file: str, next_action: str, missing_input: str | None = None,
              work_affected: str | None = None, owner: str = C.OWNER_NAME) -> str:
        """Register an unknown value and return the literal NEEDS_EVIDENCE."""
        self.record_blocker(item, missing_input or f"{item} is unknown ({C.NEEDS_EVIDENCE})",
                            work_affected or source_file, next_action, owner, source_file)
        return C.NEEDS_EVIDENCE

    def save_blockers(self) -> Path:
        existing = []
        if self.blockers_path.exists():
            existing = json.loads(self.blockers_path.read_text(encoding="utf-8"))
        merged = {(b["item"], b["source_file"]): b for b in existing}
        for b in self.blockers:
            merged[(b["item"], b["source_file"])] = b
        ordered = [merged[k] for k in sorted(merged)]
        self.blockers_path.write_text(json.dumps(ordered, indent=2) + "\n", encoding="utf-8")
        return self.blockers_path

    def load_blockers(self) -> list[dict]:
        self.save_blockers()
        return json.loads(self.blockers_path.read_text(encoding="utf-8"))

    # ---- asset register ----------------------------------------------------
    def load_assets(self) -> list[dict]:
        if not self.asset_register_path.exists():
            return []
        return json.loads(self.asset_register_path.read_text(encoding="utf-8"))["assets"]

    def mark_asset(self, asset_id: str, path, status, owner: str = C.OWNER_NAME) -> dict:
        st = _coerce_status(status)
        rel = path if isinstance(path, str) else self.rel(path)
        record = {"id": asset_id, "path": rel, "status": st.value, "owner": owner}
        assets = {a["id"]: a for a in self.load_assets()}
        assets[asset_id] = record
        payload = {"assets": [assets[k] for k in sorted(assets)]}
        self.asset_register_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return record

    # ---- file writers ------------------------------------------------------
    def write(self, rel_path: str, content: str, asset_id: str, status=Status.DRAFT, source: str = "build") -> Path:
        path = self.root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        self.log(f"asset:{asset_id}", self.rel(path), source, status)
        self.mark_asset(asset_id, path, status)
        return path

    def write_json(self, rel_path: str, obj, asset_id: str, status=Status.DRAFT, source: str = "build") -> Path:
        return self.write(rel_path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n", asset_id, status, source)


_DEFAULT: State | None = None


def default_state() -> State:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = State()
    return _DEFAULT


def log(key, value, source, status):
    return default_state().log(key, value, source, status)


def record_blocker(item, missing_input, work_affected, next_action):
    blocker = default_state().record_blocker(item, missing_input, work_affected, next_action)
    default_state().save_blockers()
    return blocker


def mark_asset(asset_id, path, status):
    return default_state().mark_asset(asset_id, path, status)


def run_standalone(build_fn) -> int:
    """Run one generator against the real build root (used by each src module's __main__)."""
    state = State()
    paths = build_fn(state)
    state.save_blockers()
    for p in paths:
        print(state.rel(p))
    return 0

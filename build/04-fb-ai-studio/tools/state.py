"""State layer: status enum, decision-log writer, blocker recorder, asset register.

Every generator writes through `BuildContext.write_asset`, which writes the file,
appends a decision-log line and upserts the asset register. No code path may
record the status `Live`; `Ready for launch` is refused while launch approval
is false.
"""
from __future__ import annotations

import datetime as _dt
import enum
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402


class STATUS(str, enum.Enum):
    NOT_STARTED = "Not started"
    DRAFT = "Draft"
    TESTED = "Tested"
    READY_FOR_LAUNCH = "Ready for launch"
    LIVE = "Live"
    BLOCKED = "Blocked"


class StatusNotAllowed(Exception):
    """Raised when a script tries to write a status it has no authority to set."""


def _coerce_status(status) -> STATUS:
    if isinstance(status, STATUS):
        return status
    for s in STATUS:
        if s.value == status or s.name == status:
            return s
    raise ValueError(f"Unknown status: {status!r}")


def check_status_allowed(status, approval_launch: bool | None = None) -> STATUS:
    s = _coerce_status(status)
    if approval_launch is None:
        approval_launch = C.APPROVAL_LAUNCH
    if s is STATUS.LIVE:
        raise StatusNotAllowed("No script may write the status 'Live'. Going live is a human action in Ads Manager.")
    if s is STATUS.READY_FOR_LAUNCH and not approval_launch:
        raise StatusNotAllowed("'Ready for launch' requires APPROVAL_LAUNCH = True (explicit human approval).")
    return s


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


class BuildState:
    """Decision log, blocker list and asset register rooted at a build directory."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.decision_log = self.root / "config" / "decision_log.jsonl"
        self.asset_register = self.root / "config" / "asset_register.json"
        self.blockers_file = self.root / "out" / "blockers.json"

    # -- decision log ------------------------------------------------------
    def log(self, key: str, value, source: str, status="Draft") -> dict:
        s = check_status_allowed(status)
        entry = {"timestamp": _now(), "key": key, "value": value, "source": source, "status": s.value}
        self.decision_log.parent.mkdir(parents=True, exist_ok=True)
        with self.decision_log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def read_log(self) -> list[dict]:
        if not self.decision_log.exists():
            return []
        return [json.loads(line) for line in self.decision_log.read_text(encoding="utf-8").splitlines() if line.strip()]

    # -- blockers ----------------------------------------------------------
    def load_blockers(self) -> list[dict]:
        if not self.blockers_file.exists():
            return []
        return json.loads(self.blockers_file.read_text(encoding="utf-8"))

    def record_blocker(self, item: str, missing_input: str, work_affected: str, next_action: str) -> dict:
        blocker = {"item": item, "missing_input": missing_input, "work_affected": work_affected,
                   "next_action": next_action, "status": STATUS.BLOCKED.value}
        blockers = [b for b in self.load_blockers() if b["item"] != item]
        blockers.append(blocker)
        self.blockers_file.parent.mkdir(parents=True, exist_ok=True)
        self.blockers_file.write_text(json.dumps(blockers, indent=2) + "\n", encoding="utf-8")
        self.log(f"blocker:{item}", missing_input, "record_blocker", STATUS.BLOCKED)
        return blocker

    # -- asset register ----------------------------------------------------
    def load_assets(self) -> list[dict]:
        if not self.asset_register.exists():
            return []
        return json.loads(self.asset_register.read_text(encoding="utf-8"))["assets"]

    def mark_asset(self, asset_id: str, path: str, status="Draft", owner: str = C.OWNER_NAME) -> dict:
        s = check_status_allowed(status)
        record = {"id": asset_id, "path": str(path).replace("\\", "/"), "status": s.value, "owner": owner}
        assets = [a for a in self.load_assets() if a["id"] != asset_id]
        assets.append(record)
        assets.sort(key=lambda a: a["id"])
        self.asset_register.parent.mkdir(parents=True, exist_ok=True)
        self.asset_register.write_text(json.dumps({"assets": assets}, indent=2) + "\n", encoding="utf-8")
        return record


class BuildContext:
    """Everything a generator needs: root paths, config, date and the state layer."""

    def __init__(self, root: Path, work_orders_dir: Path | None = None, today: _dt.date | None = None):
        self.root = Path(root)
        self.work_orders_dir = Path(work_orders_dir) if work_orders_dir else self.root.parents[1] / "ui-work-orders"
        self.today = today or _dt.date.today()
        self.state = BuildState(self.root)
        self.config = json.loads((self.root / "config" / "build_config.json").read_text(encoding="utf-8"))

    @property
    def out(self) -> Path:
        return self.root / "out"

    def draft_campaign_name(self) -> str:
        return C.NEW_CAMPAIGN_NAME_PATTERN.replace("{YYYYMMDD}", self.today.strftime("%Y%m%d"))

    def write_asset(self, rel_path: str, content: str, asset_id: str, source: str, status="Draft",
                    base: Path | None = None) -> Path:
        base = Path(base) if base else self.root
        path = base / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        try:
            shown = path.relative_to(self.root).as_posix()
        except ValueError:
            shown = path.as_posix()
        self.state.log(f"asset:{asset_id}", shown, source, status)
        self.state.mark_asset(asset_id, shown, status)
        return path

    def write_json(self, rel_path: str, data, asset_id: str, source: str, status="Draft") -> Path:
        return self.write_asset(rel_path, json.dumps(data, indent=2, ensure_ascii=False) + "\n", asset_id, source, status)

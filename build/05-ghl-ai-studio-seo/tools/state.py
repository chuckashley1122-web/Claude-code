"""Status enum, append-only decision log, blocker recorder and asset register.

No script may set ``Published-by-human``: that status is reserved for a human's
manual edit after a real publish. ``mark_asset`` refuses it.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from tools.paths import Paths, default_paths


class STATUS(str, Enum):
    NOT_STARTED = "Not started"
    DRAFT = "Draft"
    TESTED = "Tested"
    READY_FOR_HUMAN = "Ready for human action"
    PUBLISHED_BY_HUMAN = "Published-by-human"
    BLOCKED = "Blocked"


SCRIPT_FORBIDDEN_STATUSES = {STATUS.PUBLISHED_BY_HUMAN}


class StatusNotAllowed(ValueError):
    """Raised when a script tries to write a status implying deployment."""


def _coerce_status(status: Any) -> STATUS:
    if isinstance(status, STATUS):
        result = status
    else:
        try:
            result = STATUS(status)
        except ValueError as exc:
            raise StatusNotAllowed(f"unknown status {status!r}") from exc
    if result in SCRIPT_FORBIDDEN_STATUSES:
        raise StatusNotAllowed(
            f"{result.value!r} is reserved for a human after a real publish; no script may set it"
        )
    return result


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_decision_log(paths: Paths | None = None) -> list[dict]:
    paths = paths or default_paths()
    if not paths.decision_log.exists():
        return []
    entries = []
    for line in paths.decision_log.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def latest_by_key(paths: Paths | None = None) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for entry in read_decision_log(paths):
        latest[entry["key"]] = entry
    return latest


def log(key: str, value: Any, source: str, status: Any, paths: Paths | None = None) -> bool:
    """Append a decision. Returns False (no write) if it repeats the latest entry for the key.

    The log stays append-only; skipping exact repeats keeps re-runs idempotent.
    """
    paths = paths or default_paths()
    st = _coerce_status(status)
    prior = latest_by_key(paths).get(key)
    if prior and prior["value"] == value and prior["source"] == source and prior["status"] == st.value:
        return False
    paths.decision_log.parent.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": _now(), "key": key, "value": value, "source": source, "status": st.value}
    with paths.decision_log.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    return True


def record_blocker(item: str, missing_input: str, work_affected: str, next_action: str,
                   paths: Paths | None = None) -> bool:
    value = {"missing_input": missing_input, "work_affected": work_affected, "next_action": next_action}
    return log(f"blocker:{item}", value, "build", STATUS.BLOCKED, paths)


def blockers(paths: Paths | None = None) -> dict[str, dict]:
    return {k[len("blocker:"):]: v["value"] for k, v in latest_by_key(paths).items()
            if k.startswith("blocker:") and v["status"] == STATUS.BLOCKED.value}


def read_asset_register(paths: Paths | None = None) -> dict[str, dict]:
    paths = paths or default_paths()
    if not paths.asset_register.exists():
        return {}
    return json.loads(paths.asset_register.read_text(encoding="utf-8"))


def mark_asset(asset_id: str, path: Path | str, status: Any, owner: str = "build",
               paths: Paths | None = None) -> None:
    paths = paths or default_paths()
    st = _coerce_status(status)
    register = read_asset_register(paths)
    register[asset_id] = {"id": asset_id, "path": paths.rel(Path(path)) if Path(path).is_absolute() else str(path),
                          "status": st.value, "owner": owner}
    paths.asset_register.parent.mkdir(parents=True, exist_ok=True)
    paths.asset_register.write_text(json.dumps(dict(sorted(register.items())), indent=2) + "\n",
                                    encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> Path:
    """Write a generated file with LF endings, creating parents."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def write_json(path: Path, data: Any) -> Path:
    return write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def emit(asset_id: str, path: Path, content: str | Any, status: Any, paths: Paths,
         source: str = "build", owner: str = "build") -> Path:
    """Write one asset, log the decision and register it (the per-step contract in spec §5)."""
    if isinstance(content, str):
        write_text(path, content)
    else:
        write_json(path, content)
    rel = paths.rel(path)
    log(f"asset:{asset_id}", rel, source, status, paths)
    mark_asset(asset_id, path, status, owner, paths)
    return path

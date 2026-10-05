"""Input hash, UTC run_id, and an isolated output folder that never overwrites a prior run."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path


def utc_now_iso(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def input_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def make_run_id(raw: bytes, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return f"{now.strftime('%Y%m%dT%H%M%SZ')}-{input_hash(raw)[:8]}"


def create_run_dir(out_root: Path, run_id: str) -> tuple[str, Path]:
    """Create outputs/<run_id>/. If it exists, use -2, -3, ... Never overwrite or merge."""
    out_root = Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    candidate = run_id
    n = 1
    while True:
        target = out_root / candidate
        try:
            target.mkdir(parents=False, exist_ok=False)
            return candidate, target
        except FileExistsError:
            n += 1
            candidate = f"{run_id}-{n}"

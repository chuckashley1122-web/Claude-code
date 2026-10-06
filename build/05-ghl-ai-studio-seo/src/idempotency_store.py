"""File-backed idempotency store (stdlib sqlite3), one record per submission_id.

Schema: submission_id, first_seen_utc, state (in_flight | saved | failed | queued),
crm_reference, response_status, response_body. Retention is
IDEMPOTENCY_RETENTION_HOURS (24 h); ``purge_expired()`` removes older records.

Semantics:
* ``begin()`` atomically claims a submission_id. A repeat of a ``saved`` or
  ``queued`` submission returns the prior outcome and never creates a second lead.
* A repeat while the first attempt is still ``in_flight`` is reported as such
  (the handler answers "try again shortly"), never processed twice.
* A ``failed`` record (upstream failure) may be re-attempted with the same
  submission_id; that is the network-retry path, still one intended submission.

Contact matching and submission idempotency solve different problems: contact
matching (CRM upsert) decides whether two different submissions belong to the
same person; submission idempotency guarantees one intended submission is
processed once no matter how often the browser or network repeats it.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import threading
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402

STATES = ("in_flight", "saved", "failed", "queued")
FINAL_STATES = ("saved", "queued")


@dataclass
class Record:
    submission_id: str
    first_seen_utc: str
    state: str
    crm_reference: str | None
    response_status: int | None
    response_body: dict | None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IdempotencyStore:
    def __init__(self, db_path: Path | str, retention_hours: int = C.IDEMPOTENCY_RETENTION_HOURS,
                 clock: Callable[[], datetime] = _utcnow):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.retention = timedelta(hours=retention_hours)
        self.clock = clock
        self._lock = threading.Lock()
        with closing(self._connect()) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS submissions ("
                " submission_id TEXT PRIMARY KEY,"
                " first_seen_utc TEXT NOT NULL,"
                " state TEXT NOT NULL CHECK (state IN ('in_flight','saved','failed','queued')),"
                " crm_reference TEXT,"
                " response_status INTEGER,"
                " response_body TEXT)")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5, isolation_level=None)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row(row: sqlite3.Row | None) -> Record | None:
        if row is None:
            return None
        return Record(row["submission_id"], row["first_seen_utc"], row["state"], row["crm_reference"],
                      row["response_status"], json.loads(row["response_body"]) if row["response_body"] else None)

    def _expired(self, first_seen_utc: str) -> bool:
        return datetime.fromisoformat(first_seen_utc) < self.clock() - self.retention

    def get(self, submission_id: str) -> Record | None:
        with closing(self._connect()) as conn:
            rec = self._row(conn.execute("SELECT * FROM submissions WHERE submission_id = ?",
                                         (submission_id,)).fetchone())
        if rec and self._expired(rec.first_seen_utc):
            return None
        return rec

    def begin(self, submission_id: str) -> tuple[bool, Record]:
        """Claim submission_id. Returns (claimed, record).

        claimed=True means the caller must process the submission now. claimed=False
        means a prior outcome or an in-flight attempt exists and must be returned as-is.
        """
        now = self.clock().isoformat()
        with self._lock, closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = conn.execute("SELECT * FROM submissions WHERE submission_id = ?",
                                   (submission_id,)).fetchone()
                rec = self._row(row)
                if rec and self._expired(rec.first_seen_utc):
                    conn.execute("DELETE FROM submissions WHERE submission_id = ?", (submission_id,))
                    rec = None
                if rec is None:
                    conn.execute("INSERT INTO submissions (submission_id, first_seen_utc, state) VALUES (?, ?, ?)",
                                 (submission_id, now, "in_flight"))
                    conn.execute("COMMIT")
                    return True, Record(submission_id, now, "in_flight", None, None, None)
                if rec.state == "failed":
                    conn.execute("UPDATE submissions SET state = 'in_flight' WHERE submission_id = ?",
                                 (submission_id,))
                    conn.execute("COMMIT")
                    rec.state = "in_flight"
                    return True, rec
                conn.execute("COMMIT")
                return False, rec
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def complete(self, submission_id: str, state: str, response_status: int, response_body: dict,
                 crm_reference: str | None = None) -> Record:
        if state not in STATES or state == "in_flight":
            raise ValueError(f"invalid final state {state!r}")
        with self._lock, closing(self._connect()) as conn:
            cur = conn.execute(
                "UPDATE submissions SET state = ?, crm_reference = ?, response_status = ?, response_body = ? "
                "WHERE submission_id = ? AND state = 'in_flight'",
                (state, crm_reference, response_status, json.dumps(response_body), submission_id))
            if cur.rowcount != 1:
                raise ValueError(f"submission {submission_id!r} is not in flight")
        rec = self.get(submission_id)
        assert rec is not None
        return rec

    def purge_expired(self) -> int:
        cutoff = (self.clock() - self.retention).isoformat()
        with self._lock, closing(self._connect()) as conn:
            return conn.execute("DELETE FROM submissions WHERE first_seen_utc < ?", (cutoff,)).rowcount

    def count(self) -> int:
        with closing(self._connect()) as conn:
            return conn.execute("SELECT COUNT(*) FROM submissions").fetchone()[0]

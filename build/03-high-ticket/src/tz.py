"""US Central time without third-party tzdata.

zoneinfo needs the tzdata package on Windows, which is not stdlib. This tzinfo
implements the current US rule (DST from the second Sunday of March 02:00 to the
first Sunday of November 02:00, local time) and is checked against zoneinfo in
the tests wherever the system database exists.
"""
from __future__ import annotations

from datetime import datetime, timedelta, tzinfo

CST = timedelta(hours=-6)
CDT = timedelta(hours=-5)
TZ_NAME = "America/Chicago"


def _nth_sunday(year: int, month: int, n: int) -> datetime:
    d = datetime(year, month, 1)
    d += timedelta(days=(6 - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


class USCentral(tzinfo):
    def _dst_bounds_utc(self, year: int):
        start_local = _nth_sunday(year, 3, 2).replace(hour=2)
        end_local = _nth_sunday(year, 11, 1).replace(hour=2)
        return start_local - CST, end_local - CDT  # naive UTC instants

    def _is_dst_local(self, dt: datetime) -> bool:
        naive = dt.replace(tzinfo=None)
        start = _nth_sunday(naive.year, 3, 2).replace(hour=2)
        end = _nth_sunday(naive.year, 11, 1).replace(hour=2)
        if start <= naive < end:
            # ambiguous hour at the end of DST resolves via fold (PEP 495)
            if end - timedelta(hours=1) <= naive < end and getattr(dt, "fold", 0) == 1:
                return False
            return True
        return False

    def utcoffset(self, dt):
        return CDT if self._is_dst_local(dt) else CST

    def dst(self, dt):
        return timedelta(hours=1) if self._is_dst_local(dt) else timedelta(0)

    def tzname(self, dt):
        return "CDT" if self._is_dst_local(dt) else "CST"

    def fromutc(self, dt):
        naive = dt.replace(tzinfo=None)
        start_utc, end_utc = self._dst_bounds_utc(naive.year)
        if start_utc <= naive < end_utc:
            local = naive + CDT
            fold = 0
        else:
            local = naive + CST
            # first hour after DST ends repeats; mark the second pass with fold=1
            fold = 1 if end_utc <= naive < end_utc + timedelta(hours=1) else 0
        return local.replace(tzinfo=self, fold=fold)

    def __repr__(self):
        return TZ_NAME


CENTRAL = USCentral()


def fmt_local(dt: datetime) -> str:
    local = dt.astimezone(CENTRAL)
    return local.strftime("%A %B %d, %Y at %I:%M %p ") + f"{local.tzname()} ({TZ_NAME})"

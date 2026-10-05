"""Sales calendar spec (playbook steps 16-18) -> out/calendar_spec.md

Also provides the availability calculation used by the offline funnel
simulator, so the spec and the tested behavior share one source of truth.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src.tz import CENTRAL, TZ_NAME  # noqa: E402

SRC = "out/calendar_spec.md"
CALENDAR_NAME = "HVAC Growth Strategy Session"
SOURCE_CALENDAR_NAME = "Real Estate Strategy Session"
DURATION_MIN = 45
HORIZON_DAYS = 3
MIN_NOTICE_HOURS = 2
BUFFER_MIN = 15


def available_slots(now: datetime, working_hours, busy: list[tuple[datetime, datetime]], step_min: int = 15) -> list[datetime]:
    """Bookable start times inside the horizon.

    working_hours: {weekday int: (time start, time end)} in Central time, or
    NEEDS_EVIDENCE / None when unknown (returns no slots; caller must create an owner task).
    """
    if not working_hours or working_hours == C.NEEDS_EVIDENCE:
        return []
    now_local = now.astimezone(CENTRAL)
    earliest = now_local + timedelta(hours=MIN_NOTICE_HOURS)
    latest = now_local + timedelta(days=HORIZON_DAYS)
    slots = []
    day = now_local.date()
    while datetime.combine(day, time(0), CENTRAL) <= latest:
        hours = working_hours.get(day.weekday())
        if hours:
            t = datetime.combine(day, hours[0], CENTRAL)
            end_of_day = datetime.combine(day, hours[1], CENTRAL)
            while t + timedelta(minutes=DURATION_MIN) <= end_of_day:
                end = t + timedelta(minutes=DURATION_MIN)
                if earliest <= t <= latest and not any(
                        t < b_end + timedelta(minutes=BUFFER_MIN) and end + timedelta(minutes=BUFFER_MIN) > b_start
                        for b_start, b_end in busy):
                    slots.append(t)
                t += timedelta(minutes=step_min)
        day += timedelta(days=1)
    return slots


def can_book(now: datetime, start: datetime, working_hours, busy) -> bool:
    return start.astimezone(CENTRAL) in [s for s in available_slots(now, working_hours, busy)]


def render(config: dict) -> str:
    rows = [
        ("Name", CALENDAR_NAME, f"Source replay name: {SOURCE_CALENDAR_NAME}"),
        ("Type", "Personal booking calendar for the salesperson", ""),
        ("Duration", f"{DURATION_MIN} minutes", ""),
        ("Timezone", TZ_NAME, f"{C.NEEDS_EVIDENCE}: confirm account and owner timezone settings"),
        ("Working hours", C.NEEDS_EVIDENCE, "Enter the owner's actual hours"),
        ("Max booking horizon", f"{HORIZON_DAYS} days", ""),
        ("Minimum notice", f"{MIN_NOTICE_HOURS} hours", "Only if it fits the owner schedule"),
        ("Buffers", f"{BUFFER_MIN} minutes before/after", "Only if it fits the owner schedule"),
        ("Conflict calendar + Google Meet", C.NEEDS_EVIDENCE, "Connect owner calendar; confirm meeting link generation"),
        ("Booking fields", "Name, email, phone with communication disclosures", "Business details can follow"),
        ("Cancel / reschedule", "Enabled", ""),
        ("Public calendar URL", C.NEEDS_EVIDENCE, "Record after creation; test on desktop and phone"),
        ("Calendar ID", config.get("sales_calendar_id", C.NEEDS_EVIDENCE), "Record after creation"),
    ]
    lines = ["# Calendar specification", "", f"Target location `{C.GHL_LOCATION_ID}`. Status: Draft spec for a human to create.", "",
             "| Setting | Value | Note |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    lines += ["", "## No-slot rule", "",
              "If no slots exist inside the horizon, create an owner task immediately and stop sending booking links to that lead. "
              "Never run an empty-calendar loop.", "",
              "## Unidentified control", "",
              "The transcript's \"keep this off\" remark at 25:01 refers to an unidentified control. Do not guess which one; record the labels actually used.", "",
              "## Completion check", "",
              "A test appointment appears once in the correct owner calendar, blocks that time, has a usable meeting link, "
              "and cannot be booked outside the three-day window.", ""]
    return "\n".join(lines)


def build(state) -> list[Path]:
    state.needs("calendar working hours", SRC, "Enter owner's actual working hours in the calendar availability")
    state.needs("timezone confirmation", SRC, "Confirm America/Chicago in GHL account and owner settings")
    state.needs("public calendar URL", SRC, "Create calendar, record URL, test-book on desktop and phone")
    state.needs("sales_calendar_id", SRC, "Record calendar ID after a human creates the calendar")
    state.needs("conflict calendar and meeting link", SRC, "Connect owner calendar and Google Meet if available")
    return [state.write(SRC, render(state.config), "CALENDAR-SPEC", source="src/calendar_spec.py")]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

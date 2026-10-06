"""Calendar interface: in-memory free/busy and create-event (Google Calendar stand-in)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from adapters.base import LiveAdapter, MockAdapter, stable_id


class SlotUnavailable(ValueError):
    """Raised when asked to book a time that availability did not offer."""


class CalendarClient(Protocol):
    def availability(self, day: str) -> list[str]: ...
    def create_event(self, day: str, time: str, attendee_email: str, summary: str) -> dict: ...


DEFAULT_SLOTS = ("09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00")


@dataclass
class MockCalendar(MockAdapter):
    service: str = "google_calendar"
    slots: tuple[str, ...] = DEFAULT_SLOTS
    busy: dict[str, set] = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)

    def mark_busy(self, day: str, time: str) -> None:
        self.busy.setdefault(day, set()).add(time)

    def availability(self, day: str) -> list[str]:
        self._guard("availability", day=day)
        d = date.fromisoformat(day)  # validates the date; raises on garbage
        if d.weekday() >= 5:
            return []
        taken = self.busy.get(day, set())
        return [s for s in self.slots if s not in taken]

    def create_event(self, day: str, time: str, attendee_email: str, summary: str) -> dict:
        self._guard("create_event", day=day, time=time)
        # "Never invent times": only a slot that availability currently offers can be booked.
        if time not in self.availability(day):
            raise SlotUnavailable(f"{day} {time} is not an available slot")
        event = {"event_id": stable_id("evt", day, time, attendee_email), "day": day, "time": time,
                 "attendee": attendee_email, "summary": summary, "status": "dry_run_created"}
        self.mark_busy(day, time)
        self.events.append(event)
        return event


class LiveCalendar(LiveAdapter):
    service = "google_calendar"
    credential_env = ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN")

    def availability(self, day: str) -> list[str]:
        self._refuse("availability")

    def create_event(self, day: str, time: str, attendee_email: str, summary: str) -> dict:
        self._refuse("create_event")

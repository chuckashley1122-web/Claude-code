"""Workflow logic specs (playbook steps 31-36) -> out/workflows/01-intake.md .. 04-outcome.md

Documents only; nothing is built or published. TIMING is the single source
for the waits used by src/funnel_sim.py, so the tested behavior and the spec
cannot drift apart.
"""
from __future__ import annotations

from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src.common import prefix  # noqa: E402

TIMING = {
    "call_task_due_minutes": 5,
    "unbooked_reminder_hours": 2,
    "unbooked_email_days": 1,
    "unbooked_manual_review_days": 3,
    "appointment_reminders_hours_before": [24, 2],
}
RECHECKS = ["active relevant appointment", "reply received", "opt-out on the channel", "qualification status", "opportunity status"]


def workflows(config: dict) -> list[dict]:
    p = prefix(config)
    t = TIMING
    return [
        {"file": "01-intake.md", "name": f"{p}-01-Intake",
         "trigger": "Facebook Lead Form Submitted, filtered to the specific Page and form (IDs " + C.NEEDS_EVIDENCE + ")",
         "filters": ["Page = the verified Page", "Form = the qualification form"],
         "actions": ["Store lead received time", "Tag source", "Assign owner", "Evaluate qualification (decision_maker_answer)",
                     "Yes → stage Qualified unbooked unless a current relevant appointment exists (then Booked) → enroll in 02-Unbooked",
                     "No → stage Disqualified; no booking nurture", "Notify the owner once"],
         "waits": [], "stop": ["Duplicate Meta lead ID (replay) → no action"]},
        {"file": "02-unbooked.md", "name": f"{p}-02-Unbooked",
         "trigger": "Qualified lead with no active relevant appointment",
         "filters": ["qualification_status = Qualified", "no active appointment", "not already enrolled"],
         "actions": ["Immediately send the permitted booking acknowledgment",
                     f"Immediately create an owner call task due within {t['call_task_due_minutes']} minutes during staffed hours "
                     "(created at once, never after a 5-minute wait); after hours, due at the start of the next staffed window",
                     f"+{t['unbooked_reminder_hours']}h: one permitted reminder if still unbooked and no reply",
                     f"+{t['unbooked_email_days']}d: one email follow-up",
                     f"+{t['unbooked_manual_review_days']}d: manual review task, then end"],
         "waits": [f"{t['unbooked_reminder_hours']} hours", f"{t['unbooked_email_days']} day", f"{t['unbooked_manual_review_days']} days"],
         "stop": ["Booking → remove immediately", "Reply → pause automation, route to owner",
                  "Opt-out → nothing further on that channel", "Before every action re-check: " + ", ".join(RECHECKS)]},
        {"file": "03-booked.md", "name": f"{p}-03-Booked",
         "trigger": "New booking event on the HVAC Growth Strategy Session calendar",
         "filters": ["Calendar = sales calendar (ID " + C.NEEDS_EVIDENCE + ")"],
         "actions": ["Save appointment ID and time", "Move to Booked", "Stop Workflow 02",
                     "Send meeting details + confirmation request (timezone shown)",
                     "Schedule reminders at −24h and −2h; skip any window already passed",
                     "Clear confirmation reply → Confirmed + send pre-call page once; ambiguous reply → owner task",
                     "Never auto-cancel an unconfirmed appointment",
                     "Cancel → stop that appointment's reminders + offer reschedule route",
                     "Reschedule → clear old waits; schedule reminders against the new appointment time"],
         "waits": ["until appointment −24h", "until appointment −2h"], "stop": ["Cancel", "Opt-out on that channel"]},
        {"file": "04-outcome.md", "name": f"{p}-04-Outcome",
         "trigger": "Appointment end time passed",
         "filters": ["Real attendance outcome recorded by salesperson or reliable meeting record"],
         "actions": ["Attended → next-action task (never auto-Won)",
                     "No-show → one permitted reschedule message + follow-up task", "Lost → stop sales nurture",
                     "Verbal yes → Won pending payment only",
                     "Paid → stop acquisition messaging; start onboarding only after processor payment verification"],
         "waits": [], "stop": ["Lost", "Paid (acquisition messaging)"]},
    ]


def render(wf: dict) -> str:
    sec = lambda title, items: [f"## {title}", ""] + ([f"- {i}" for i in items] or ["- none"]) + [""]  # noqa: E731
    lines = [f"# Workflow {wf['name']}", "",
             f"Status: Draft spec. Location `{C.GHL_LOCATION_ID}`. **Stays unpublished during assembly.** Not built by this script.", "",
             "## Trigger", "", wf["trigger"], ""]
    lines += sec("Filters", wf["filters"]) + sec("Actions and branches", wf["actions"]) + sec("Waits", wf["waits"]) + sec("Stop conditions", wf["stop"])
    lines += ["All sends require valid channel permission and a working sender; opted-out channels are suppressed. "
              "Verify with a test clone using short waits, then inspect production timing.", ""]
    return "\n".join(lines)


def build(state) -> list[Path]:
    state.needs("staffed hours", "out/workflows/02-unbooked.md", "Define staffed hours for the 5-minute call task window")
    state.needs("sales_calendar_id", "out/workflows/03-booked.md", "Record the calendar ID for the booking trigger filter")
    state.needs("form and page IDs for intake filter", "out/workflows/01-intake.md", "Record after the human creates the Meta form")
    return [state.write(f"out/workflows/{wf['file']}", render(wf), f"WORKFLOW-{wf['file'][:2]}", source="src/workflow_specs.py")
            for wf in workflows(state.config)]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

"""Offline, deterministic simulator of the four workflows, payments, routing,
form-sync reconciliation and rollback, run against the LocalCRM/LocalAds
connectors. run_tests.py uses it for the logic half of T01-T14; the live half
of every case needs a human in GHL/Meta and is reported BLOCKED.
"""
from __future__ import annotations

import itertools
import json
import shutil
from datetime import datetime, time, timedelta
from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src import calendar_spec as CAL  # noqa: E402
from src import form_spec as FORM  # noqa: E402
from src import message_templates as MSG  # noqa: E402
from src.common import OFFER_VERSION  # noqa: E402
from src.connectors import LocalCRM  # noqa: E402
from src.tz import CENTRAL, fmt_local  # noqa: E402
from src.workflow_specs import TIMING  # noqa: E402

CONFIRM_WORDS = {"yes", "confirm", "confirmed", "see you then", "i'll be there", "i will be there"}
OPT_OUT_WORDS = {"stop", "unsubscribe", "stopall", "cancel texts"}


class FunnelEngine:
    def __init__(self, crm: LocalCRM | None = None, working_hours=None, staffed_hours=None,
                 page_id: str = "TEST-PAGE", form_id: str = "TEST-FORM", offer: str = OFFER_VERSION):
        self.crm = crm or LocalCRM()
        self.working_hours = working_hours
        self.staffed_hours = staffed_hours
        self.page_id, self.form_id, self.offer = page_id, form_id, offer
        self.queue: list[dict] = []
        self.appointments: dict[str, dict] = {}
        self.unbooked_active: dict[str, bool] = {}
        self.onboarding: dict[str, int] = {}
        self.processed_payments: dict[str, dict] = {}
        self.no_slot_task_open = False
        self.trace: list[dict] = []
        self._ids = itertools.count(1)

    # ------------------------------------------------------------------ helpers
    def _log(self, at, kind, **detail):
        self.trace.append({"at": at.isoformat() if isinstance(at, datetime) else str(at), "kind": kind, **detail})

    def _opp(self, contact_id):
        return self.crm.open_opportunity(contact_id, self.offer)

    def _active_appt(self, contact_id):
        for a in self.appointments.values():
            if a["contact_id"] == contact_id and a["status"] == "active":
                return a
        return None

    def _permitted(self, contact_id, channel):
        return channel not in self.crm.get_contact(contact_id)["opted_out"]

    def _values(self, contact_id, appt=None):
        c = self.crm.get_contact(contact_id)
        when = fmt_local(appt["start"]) if appt else ""
        return {"FIRST NAME": (c["name"].split() or ["there"])[0], "CALENDAR LINK": C.BOOKING_URL,
                "DATE AND TIME WITH TIMEZONE": when, "DATE/TIME/TIMEZONE": when,
                "MEETING LINK": f"https://meet.example.com/{appt['id'] if appt else 'none'}",
                "RESCHEDULE LINK": f"https://example.com/reschedule/{appt['id'] if appt else 'none'}",
                "PRE-CALL LINK": "https://example.com/precall"}

    def _send(self, contact_id, template_id, at, appt=None) -> bool:
        channel = MSG.TEMPLATES[template_id]["channel"]
        if not self._permitted(contact_id, channel):
            self._log(at, "send_suppressed_opt_out", contact=contact_id, template=template_id, channel=channel)
            return False
        body = MSG.render_message(template_id, self._values(contact_id, appt))
        self.crm.send_message(contact_id, channel, template_id, body, at)
        self._log(at, "send", contact=contact_id, template=template_id, channel=channel)
        return True

    def _schedule(self, due, workflow, action, contact_id, appt_id=None, gen=None):
        self.queue.append({"id": next(self._ids), "due": due, "workflow": workflow, "action": action,
                           "contact_id": contact_id, "appt_id": appt_id, "gen": gen, "cancelled": False})

    def _cancel(self, contact_id=None, workflow=None, appt_id=None):
        for q in self.queue:
            if q["cancelled"]:
                continue
            if contact_id and q["contact_id"] != contact_id:
                continue
            if workflow and q["workflow"] != workflow:
                continue
            if appt_id and q["appt_id"] != appt_id:
                continue
            q["cancelled"] = True

    def is_staffed(self, at: datetime) -> bool:
        if not self.staffed_hours:
            return False
        local = at.astimezone(CENTRAL)
        hours = self.staffed_hours.get(local.weekday())
        return bool(hours) and hours[0] <= local.time() < hours[1]

    def next_staffed_start(self, at: datetime) -> datetime | None:
        if not self.staffed_hours:
            return None
        local = at.astimezone(CENTRAL)
        for d in range(0, 8):
            day = local.date() + timedelta(days=d)
            hours = self.staffed_hours.get(day.weekday())
            if hours:
                start = datetime.combine(day, hours[0], CENTRAL)
                if start > local:
                    return start
        return None

    def slots(self, now):
        busy = [(a["start"], a["start"] + timedelta(minutes=CAL.DURATION_MIN))
                for a in self.appointments.values() if a["status"] == "active"]
        return CAL.available_slots(now, self.working_hours, busy)

    # ------------------------------------------------------------------ workflow 01 intake
    def submit_lead(self, lead: dict, now: datetime):
        if lead.get("page_id") != self.page_id or lead.get("form_id") != self.form_id:
            self._log(now, "intake_filtered_out", page=lead.get("page_id"), form=lead.get("form_id"))
            return None
        lead_id = lead.get("leadgen_id")
        existing = self.crm.find_contact_by_lead_id(lead_id) if lead_id else None
        if existing:
            self._log(now, "intake_replay_ignored", contact=existing, lead_id=lead_id)
            return existing
        cid = self.crm.find_contact(lead.get("email"), lead.get("phone"))
        if cid:
            self._log(now, "intake_contact_updated", contact=cid)
        else:
            cid = self.crm.create_contact(lead)
            self._log(now, "intake_contact_created", contact=cid)
        q = FORM.evaluate(lead.get("decision_maker_question"))
        self.crm.update_contact(cid, {
            "lead_id": lead_id, "tag": "source:meta-lead-form",
            "attribution": {"campaign_id": lead.get("campaign_id", C.NEEDS_EVIDENCE), "ad_id": lead.get("ad_id", C.NEEDS_EVIDENCE),
                            "form_id": lead.get("form_id"), "lead_id": lead_id, "at": now.isoformat()},
            "custom": {"decision_maker_answer": lead.get("decision_maker_question"), "qualification_status": q["qualification_status"],
                       "lead_received_time": now.isoformat(), "form_id": lead.get("form_id"), "meta_lead_id": lead_id,
                       "offer_version": self.offer},
            "owner": C.OWNER_NAME,
        })
        opp = self._opp(cid)
        if not q["qualified"]:
            self.crm.update_contact(cid, {"tag": q["tag"]})
            if opp:
                self.crm.set_stage(opp["id"], "Disqualified")
            else:
                self.crm.create_opportunity(cid, self.offer, "Disqualified")
            self.unbooked_active[cid] = False
            self._cancel(contact_id=cid, workflow="02")
            self._notify_owner_once(cid, now, "Disqualified lead received")
            return cid
        appt = self._active_appt(cid)
        stage = "Booked" if appt else "Qualified unbooked"
        if opp is None:
            self.crm.create_opportunity(cid, self.offer, stage)
        elif opp["stage"] in ("New lead", "Qualified unbooked"):
            self.crm.set_stage(opp["id"], stage)
        self._notify_owner_once(cid, now, "Qualified lead received")
        if not appt:
            self.enroll_unbooked(cid, now)
        return cid

    def _notify_owner_once(self, cid, now, title):
        c = self.crm.get_contact(cid)
        if not c["owner_notified"]:
            self.crm.update_contact(cid, {"owner_notified": True})
            self.crm.create_task(cid, f"Owner notification: {title}", now, now)
            self._log(now, "owner_notified", contact=cid)

    # ------------------------------------------------------------------ workflow 02 unbooked
    def enroll_unbooked(self, cid, now):
        if self.unbooked_active.get(cid):
            self._log(now, "unbooked_already_enrolled", contact=cid)
            return
        self.unbooked_active[cid] = True
        if self.slots(now):
            self._send(cid, "booking_ack", now)
        else:
            self._no_slot_recovery(cid, now)
        if self.is_staffed(now):
            due = now + timedelta(minutes=TIMING["call_task_due_minutes"])
        else:
            nxt = self.next_staffed_start(now)
            due = (nxt + timedelta(minutes=TIMING["call_task_due_minutes"])) if nxt else None
        self.crm.create_task(cid, "Call new qualified lead", now, due)  # created immediately, never after a wait
        if not self.crm.get_contact(cid)["custom"].get("first_response_time"):
            self.crm.update_contact(cid, {"custom": {"first_response_time": now.isoformat()}})
        self._schedule(now + timedelta(hours=TIMING["unbooked_reminder_hours"]), "02", "unbooked_reminder", cid)
        self._schedule(now + timedelta(days=TIMING["unbooked_email_days"]), "02", "unbooked_followup", cid)
        self._schedule(now + timedelta(days=TIMING["unbooked_manual_review_days"]), "02", "manual_review", cid)

    def _no_slot_recovery(self, cid, now):
        self._log(now, "no_slots_available", contact=cid)
        if not self.no_slot_task_open:
            self.no_slot_task_open = True
            self.crm.create_task(None, "No calendar slots: add availability (booking links suppressed)", now, now)

    def _unbooked_still_valid(self, cid) -> bool:
        c = self.crm.get_contact(cid)
        opp = self._opp(cid)
        return (self.unbooked_active.get(cid, False) and not self._active_appt(cid) and not c["replied"]
                and c["custom"].get("qualification_status") == "Qualified"
                and opp is not None and opp["stage"] == "Qualified unbooked")

    # ------------------------------------------------------------------ workflow 03 booked
    def book(self, cid, start: datetime, now: datetime) -> str | None:
        if not CAL.can_book(now, start, self.working_hours,
                            [(a["start"], a["start"] + timedelta(minutes=CAL.DURATION_MIN)) for a in self.appointments.values() if a["status"] == "active"]):
            self._log(now, "booking_rejected_outside_availability", contact=cid, start=start.isoformat())
            return None
        aid = f"appt-{next(self._ids):04d}"
        self.appointments[aid] = {"id": aid, "contact_id": cid, "start": start, "status": "active", "gen": 1,
                                  "confirmed": False, "precall_sent": False, "no_show_sent": False}
        self.crm.update_contact(cid, {"custom": {"appointment_id": aid, "appointment_confirmation": "Unconfirmed"}})
        opp = self._opp(cid)
        if opp:
            self.crm.set_stage(opp["id"], "Booked")
        else:
            self.crm.create_opportunity(cid, self.offer, "Booked")
        self.unbooked_active[cid] = False
        self._cancel(contact_id=cid, workflow="02")  # stop workflow 02
        self._send(cid, "confirmation", now, self.appointments[aid])
        self._schedule_reminders(aid, now)
        self._log(now, "booked", contact=cid, appt=aid)
        return aid

    def _schedule_reminders(self, aid, now):
        a = self.appointments[aid]
        for h in TIMING["appointment_reminders_hours_before"]:
            due = a["start"] - timedelta(hours=h)
            if due > now:
                self._schedule(due, "03", f"reminder_{h}h", a["contact_id"], aid, a["gen"])
            else:
                self._log(now, "reminder_window_passed_skipped", appt=aid, hours_before=h)

    def reschedule(self, aid, new_start, now):
        a = self.appointments[aid]
        self._cancel(appt_id=aid)
        a["start"], a["gen"] = new_start, a["gen"] + 1
        self._send(a["contact_id"], "confirmation", now, a)
        self._schedule_reminders(aid, now)
        self._log(now, "rescheduled", appt=aid)

    def cancel(self, aid, now):
        a = self.appointments[aid]
        a["status"] = "cancelled"
        self._cancel(appt_id=aid)
        self.crm.create_task(a["contact_id"], "Appointment cancelled: offer reschedule route", now, now)
        opp = self._opp(a["contact_id"])
        if opp:
            self.crm.set_stage(opp["id"], "Qualified unbooked")
        self._log(now, "cancelled", appt=aid)

    def reply(self, cid, text, now, channel="sms"):
        norm = text.strip().lower()
        if norm in OPT_OUT_WORDS:
            return self.opt_out(cid, channel, now)
        self.crm.update_contact(cid, {"replied": True})
        if self.unbooked_active.get(cid):
            self.unbooked_active[cid] = False
            self._cancel(contact_id=cid, workflow="02")
        appt = self._active_appt(cid)
        if appt and norm.rstrip("!.") in CONFIRM_WORDS:
            appt["confirmed"] = True
            self.crm.update_contact(cid, {"custom": {"appointment_confirmation": "Confirmed"}})
            opp = self._opp(cid)
            if opp:
                self.crm.set_stage(opp["id"], "Confirmed")
            if not appt["precall_sent"]:
                appt["precall_sent"] = True
                self._log(now, "precall_asset_sent", appt=appt["id"])
        else:
            if appt:
                self.crm.update_contact(cid, {"custom": {"appointment_confirmation": "Ambiguous"}})
            self.crm.create_task(cid, "Reply received: owner to respond", now, now)
        self._log(now, "reply", contact=cid)

    def opt_out(self, cid, channel, now):
        c = self.crm.get_contact(cid)
        if channel not in c["opted_out"]:
            c["opted_out"].append(channel)
        self._log(now, "opt_out", contact=cid, channel=channel)

    # ------------------------------------------------------------------ clock
    def tick(self, now: datetime):
        due = sorted((q for q in self.queue if not q["cancelled"] and q["due"] <= now), key=lambda q: (q["due"], q["id"]))
        for q in due:
            q["cancelled"] = True  # consumed
            self._run(q, q["due"])

    def _run(self, q, at):
        cid = q["contact_id"]
        if q["workflow"] == "02":
            if not self._unbooked_still_valid(cid):
                self._log(at, "unbooked_action_skipped_recheck", contact=cid, action=q["action"])
                return
            if q["action"] == "manual_review":
                self.crm.create_task(cid, "Manual review: unbooked after 3 days", at, at)
                self.unbooked_active[cid] = False
                self._log(at, "unbooked_sequence_ended", contact=cid)
                return
            if not self.slots(at):
                self._no_slot_recovery(cid, at)
                return
            self._send(cid, q["action"], at)
        elif q["workflow"] == "03":
            a = self.appointments.get(q["appt_id"])
            if not a or a["status"] != "active" or a["gen"] != q["gen"]:
                self._log(at, "stale_reminder_skipped", appt=q["appt_id"])
                return
            self._send(cid, "reminder_sms", at, a)

    # ------------------------------------------------------------------ workflow 04 outcome + payment
    def record_outcome(self, aid, outcome, now):
        a = self.appointments[aid]
        cid = a["contact_id"]
        opp = self._opp(cid)
        if outcome == "attended":
            a["status"] = "attended"
            if opp:
                self.crm.set_stage(opp["id"], "Attended")
            self.crm.create_task(cid, "Next action after strategy session", now, now + timedelta(days=1))
        elif outcome == "no_show":
            a["status"] = "no_show"
            if not a["no_show_sent"]:
                a["no_show_sent"] = True
                self._send(cid, "no_show", now, a)
            self.crm.create_task(cid, "No-show follow-up", now, now + timedelta(days=1))
        elif outcome == "lost":
            if opp:
                self.crm.set_stage(opp["id"], "Lost")
            self.unbooked_active[cid] = False
            self._cancel(contact_id=cid)
        else:
            raise ValueError(f"unknown outcome {outcome!r}; a real attendance outcome is required")
        self._log(now, "outcome", appt=aid, outcome=outcome)

    def verbal_yes(self, cid, deal_amount, now):
        opp = self._opp(cid)
        self.crm.set_stage(opp["id"], "Won pending payment")
        self.crm.update_contact(cid, {"custom": {"deal_amount": deal_amount}})
        self._log(now, "won_pending_payment", contact=cid)

    def payment_event(self, event: dict, now) -> str:
        cid, ref = event["contact_id"], event.get("reference")
        if event.get("status") != "succeeded":
            self._log(now, "payment_not_succeeded", contact=cid, status=event.get("status"))
            return "ignored_not_succeeded"
        if not ref:
            return "ignored_no_reference"
        if ref in self.processed_payments:
            self._log(now, "payment_duplicate_ignored", reference=ref)
            return "duplicate"
        opp = self._opp(cid)
        expected = self.crm.get_contact(cid)["custom"].get("deal_amount")
        if opp is None or opp["stage"] not in ("Won pending payment",):
            self.crm.create_task(cid, "Payment received without a pending won deal: verify", now, now)
            return "unexpected_stage"
        if expected is None or event.get("amount") != expected:
            self.crm.create_task(cid, "Payment amount mismatch: verify with processor", now, now)
            return "amount_mismatch"
        self.processed_payments[ref] = event
        self.crm.set_stage(opp["id"], "Paid onboarding")
        self.crm.update_contact(cid, {"custom": {"payment_reference": ref}})
        self._cancel(contact_id=cid)  # stop acquisition messaging
        if self.onboarding.get(cid, 0) == 0:
            self.onboarding[cid] = 1
            self.crm.create_task(cid, "Book 45-minute onboarding; send welcome page", now, now + timedelta(days=1))
        self._log(now, "paid_onboarding", contact=cid, reference=ref)
        return "paid"


# ---------------------------------------------------------------------- T09 form sync reconciliation
def reconcile_test_leads(submitted: list[dict], crm: LocalCRM) -> list[str]:
    """Return lead IDs that were submitted on the form but never reached the CRM."""
    return [l["leadgen_id"] for l in submitted if crm.find_contact_by_lead_id(l["leadgen_id"]) is None]


def launch_gate(missing_leads: list[str], tests_blocked: list[str]) -> dict:
    reasons = []
    if missing_leads:
        reasons.append(f"form sync lost test leads {missing_leads}")
    if tests_blocked:
        reasons.append(f"tests not verified live: {tests_blocked}")
    if C.LAUNCH_AUTHORITY == "none":
        reasons.append("LAUNCH_AUTHORITY is none")
    return {"launch_allowed": not reasons, "reasons": reasons}


# ---------------------------------------------------------------------- T13 client routing
class RoutingNotVerified(ValueError):
    pass


def validate_routing(cfg: dict) -> dict:
    if cfg.get("mode") not in ("calendar", "live_transfer"):
        raise RoutingNotVerified("routing mode must be calendar or live_transfer")
    unverified = [r["name"] for r in cfg.get("recipients", []) if not r.get("verified")]
    if not cfg.get("recipients") or unverified:
        raise RoutingNotVerified(f"recipients missing or unverified: {unverified}")
    fb = cfg.get("fallback") or {}
    if not fb.get("tested"):
        raise RoutingNotVerified("missed-call fallback is not documented and tested; do not promise live transfers")
    return cfg


def route_call(cfg: dict, scenario: str, at: datetime) -> dict:
    validate_routing(cfg)
    local = at.astimezone(CENTRAL)
    hours = cfg["operating_hours"].get(local.weekday())
    open_now = bool(hours) and hours[0] <= local.time() < hours[1]
    if not open_now or scenario == "after_hours":
        return {"destination": cfg["fallback"]["type"], "reason": "after hours"}
    if scenario == "answered":
        return {"destination": cfg["recipients"][0]["name"], "reason": "answered"}
    if scenario in ("busy", "unanswered"):
        return {"destination": cfg["fallback"]["type"], "reason": f"{scenario} after {cfg['timeout_seconds']}s"}
    raise ValueError(f"unknown scenario {scenario}")


# ---------------------------------------------------------------------- T14 rollback
class WorkflowRegistry:
    def __init__(self, names):
        self.state = {n: "unpublished" for n in names}

    def stop(self, name):
        self.state[name] = "stopped"


def snapshot_config(config_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    dst = backup_dir / (config_path.name + ".bak")
    shutil.copy2(config_path, dst)
    return dst


def rollback(ads, campaign_id, registry: WorkflowRegistry, affected: list[str], config_path: Path, backup: Path) -> dict:
    ads.pause_campaign(campaign_id)
    for n in affected:
        registry.stop(n)
    shutil.copy2(backup, config_path)
    return {"campaign_status": ads.get_campaign(campaign_id)["status"],
            "workflows": {n: registry.state[n] for n in affected},
            "config_restored": json.loads(config_path.read_text(encoding="utf-8")) == json.loads(backup.read_text(encoding="utf-8"))}


# Assumed fixture hours used only by the simulator (the real hours are NEEDS_EVIDENCE).
FIXTURE_HOURS = {d: (time(9, 0), time(17, 0)) for d in range(0, 5)}

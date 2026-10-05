"""CRM schema spec (playbook steps 14-15) -> out/ghl_pipeline_spec.md, out/ghl_custom_fields.json, out/ghl_pipeline_spec.json

Specifications for a human to type into GHL. Nothing is created by this script.
"""
from __future__ import annotations

from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src.common import md_table, prefix  # noqa: E402

STAGES = ["New lead", "Qualified unbooked", "Booked", "Confirmed", "Attended", "Proposal sent",
          "Won pending payment", "Paid onboarding", "Active client", "Lost", "Disqualified"]
STAGE_ENTRY = {
    "New lead": "Lead form received; qualification not yet evaluated",
    "Qualified unbooked": "Decision-maker answer = Yes and no active relevant appointment",
    "Booked": "Calendar booking event saved with appointment ID and time",
    "Confirmed": "Reply clearly confirms the active appointment",
    "Attended": "Real attendance outcome recorded by the salesperson or a reliable meeting record",
    "Proposal sent": "Written scope sent after the call",
    "Won pending payment": "Verbal or written yes; payment NOT yet confirmed by the processor",
    "Paid onboarding": "Processor confirms payment; amount and reference stored",
    "Active client": "Agreement, payment and required onboarding inputs all present",
    "Lost": "Prospect declined or went silent after the manual review task; sales nurture stops",
    "Disqualified": "Decision-maker answer = No; no booking nurture",
}

CUSTOM_FIELDS = [
    ("niche", "Niche", "TEXT"), ("business_name", "Business name", "TEXT"), ("website", "Website", "TEXT"),
    ("service_area", "Service area", "TEXT"), ("decision_maker_answer", "Decision maker answer", "SINGLE_OPTIONS:Yes|No"),
    ("offer_version", "Offer version", "TEXT"), ("campaign_id", "Campaign ID", "TEXT"), ("ad_id", "Ad ID", "TEXT"),
    ("form_id", "Form ID", "TEXT"), ("meta_lead_id", "Meta lead ID", "TEXT"), ("lead_received_time", "Lead received time", "DATE_TIME"),
    ("first_response_time", "First response time", "DATE_TIME"),
    ("qualification_status", "Qualification status", "SINGLE_OPTIONS:Pending|Qualified|Disqualified"),
    ("appointment_id", "Appointment ID", "TEXT"),
    ("appointment_confirmation", "Appointment confirmation", "SINGLE_OPTIONS:Unconfirmed|Confirmed|Ambiguous"),
    ("deal_amount", "Deal amount", "MONETARY"), ("payment_reference", "Payment reference", "TEXT"),
    ("loss_reason", "Loss reason", "TEXT"), ("consent_source", "Consent source", "TEXT"),
    ("consent_wording_version", "Consent wording version", "TEXT"), ("consent_timestamp", "Consent timestamp", "DATE_TIME"),
]
NATIVE_FIELDS = ["first_name", "last_name", "email", "phone"]


def field_records() -> list[dict]:
    out = []
    for key, label, ftype in CUSTOM_FIELDS:
        rec = {"key": key, "label": label, "type": ftype.split(":")[0], "location_id": C.GHL_LOCATION_ID}
        if ":" in ftype:
            rec["options"] = ftype.split(":", 1)[1].split("|")
        out.append(rec)
    return out


def pipeline_spec(config: dict) -> dict:
    return {
        "location_id": C.GHL_LOCATION_ID,
        "existing_pipeline_reference_only": {"name": C.GHL_PIPELINE_NAME, "id": C.GHL_PIPELINE_ID,
                                             "stages": list(C.GHL_PIPELINE_STAGES), "action": "do not modify"},
        "new_pipeline": {"name": f"{prefix(config)}-Sales", "stages": [{"name": s, "entry_rule": STAGE_ENTRY[s]} for s in STAGES],
                         "status": "Draft (to be created by a human)"},
    }


def render(config: dict) -> str:
    spec = pipeline_spec(config)
    lines = ["# GHL pipeline specification", "",
             f"Target location: `{C.GHL_LOCATION_ID}` (exact case). Status: Draft spec; a human creates these objects.", "",
             "## Existing object (reference only, do not modify)", "",
             f"Pipeline `{C.GHL_PIPELINE_NAME}` = `{C.GHL_PIPELINE_ID}`; stages: " + ", ".join(C.GHL_PIPELINE_STAGES) + ".",
             "This existing pipeline stays as is; the high-ticket acquisition flow gets its own separate pipeline.", "",
             f"## New acquisition pipeline `{spec['new_pipeline']['name']}`", ""]
    lines += md_table(["#", "Stage", "Entry rule"], [[i + 1, s["name"], s["entry_rule"]] for i, s in enumerate(spec["new_pipeline"]["stages"])])
    lines += ["", "Rules:", "",
              "- Appointment status is the source for scheduling stages; verified processor payment status is the only source for `Paid onboarding`.",
              "- A verbal yes moves to `Won pending payment` only.",
              "- Track service delivery separately from prospecting.",
              "- Phone and email stay in native contact fields. No secrets in contact notes.", "",
              "## Custom fields", "", "See `ghl_custom_fields.json` (" + str(len(CUSTOM_FIELDS)) + " fields).", ""]
    lines += md_table(["Key", "Label", "Type"], [[k, l, t] for k, l, t in CUSTOM_FIELDS])
    lines.append("")
    return "\n".join(lines)


def build(state) -> list[Path]:
    return [
        state.write("out/ghl_pipeline_spec.md", render(state.config), "GHL-PIPELINE-SPEC", source="src/crm_schema.py"),
        state.write_json("out/ghl_pipeline_spec.json", pipeline_spec(state.config), "GHL-PIPELINE-JSON", source="src/crm_schema.py"),
        state.write_json("out/ghl_custom_fields.json", {"location_id": C.GHL_LOCATION_ID, "native_fields": NATIVE_FIELDS,
                                                         "custom_fields": field_records(),
                                                         "rule": "No secrets in contact notes"},
                         "GHL-CUSTOM-FIELDS", source="src/crm_schema.py"),
    ]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

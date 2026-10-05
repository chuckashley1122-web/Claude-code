"""Workflow 01 spec -> out/workflows/01-new-lead-automation.md (SPEC-04 step 9).

A reviewable spec table plus an embedded machine-readable JSON block (used by
run_tests.py T04). It is not a built workflow.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.common import A2P_CAVEAT, DRAFT_NOTICE, MERGE_TOKEN_FLAG, NE, cfg_value, md_table  # noqa: E402
from src.message_templates import SMS_STEPS, full_sms  # noqa: E402

WORKFLOW_NAME = "New Lead Automation"
SPEC_BLOCK = "workflow-spec"


def steps(ctx) -> list[dict]:
    pre_check = {"type": "if_else", "config": "Contact replied OR opted out / DND on SMS -> End workflow",
                 "note": "Re-checked before every send"}
    out = [
        {"type": "create_update_opportunity",
         "config": f"Pipeline={C.NEW_PIPELINE_NAME}; Stage=New Lead; Status=Open; Name={{{{contact.full_name}}}}",
         "note": "Opportunity name token is an unconfirmed placeholder"},
        {"type": "add_tag", "config": "Tag=Facebook Ads", "note": "Source suggests 'Facebook Landing Page' or 'Facebook Ads'"},
        {"type": "internal_notification",
         "config": f"SMS to {C.OWNER_PHONE} if A2P verified ({NE}); else email to {C.OWNER_EMAIL}",
         "note": "Copy: out/messages/internal_alerts.md#alert_new_lead"},
    ]
    for s in SMS_STEPS:
        out.append({"type": "wait", "config": s["wait_before"], "note": f"Before {s['id']}"})
        out.append(dict(pre_check))
        out.append({"type": "send_sms", "config": f"{s['id']} (Day {s['day']})", "message_id": s["id"],
                    "day": s["day"], "note": full_sms(s)})
    out.append({"type": "wait", "config": "1 day", "note": "After the final follow-up"})
    out.append(dict(pre_check))
    out.append({"type": "create_update_opportunity", "config": f"Pipeline={C.NEW_PIPELINE_NAME}; Stage=Lost",
                "note": "No reply after the full sequence"})
    for i, st in enumerate(out, start=1):
        st["order"] = i
    return out


def spec(ctx) -> dict:
    return {
        "workflow": WORKFLOW_NAME, "status": "Draft", "published_by_build": False,
        "trigger": {"type": "AI Studio Form Submitted",
                    "filters": {"ai_studio_project": cfg_value(ctx, "ghl_project_name"),
                                "ai_studio_form": cfg_value(ctx, "ghl_form_name")}},
        "location_id": C.GHL_LOCATION_ID,
        "steps": steps(ctx),
        "stop_conditions": ["Contact replies (Workflow 02 removes them from this workflow)",
                            "Contact opts out / DND", "Sequence completes -> Lost"],
    }


def render(ctx) -> str:
    sp = spec(ctx)
    rows = [[s["order"], s["type"], s["config"], s["note"]] for s in sp["steps"]]
    sends = [s for s in sp["steps"] if s["type"] == "send_sms"]
    return "\n".join([
        f"# Workflow 01 - {WORKFLOW_NAME} (spec, not a built workflow)", "", DRAFT_NOTICE, "", MERGE_TOKEN_FLAG, "",
        "## Trigger",
        md_table(["Field", "Value"], [["Trigger", sp["trigger"]["type"]],
                                       ["Filter: AI Studio Project", sp["trigger"]["filters"]["ai_studio_project"]],
                                       ["Filter: AI Studio Form", sp["trigger"]["filters"]["ai_studio_form"]],
                                       ["Location", C.GHL_LOCATION_ID]]), "",
        "## Actions (in order)", md_table(["#", "Action", "Configuration", "Notes / copy"], rows), "",
        f"Total follow-ups to the contact: **{len(sends)}** (Day " + ", Day ".join(str(s["day"]) for s in sends) + ").", "",
        "## Rules",
        "- Copy rule from the source: say **'website'**, never 'landing page'.",
        "- Re-check reply / opt-out before every send (the If/Else rows above).",
        f"- {A2P_CAVEAT}",
        "- Stop conditions: " + "; ".join(sp["stop_conditions"]) + ".", "",
        f"```json {SPEC_BLOCK}", json.dumps(sp, indent=2), "```", "",
    ])


def build(ctx) -> Path:
    for key in ("ghl_project_name", "ghl_form_name"):
        if cfg_value(ctx, key) == NE:
            ctx.state.record_blocker(key, f"Exact AI Studio {key.split('_')[1]} name", "Workflow 01 and 03 trigger filters",
                                     "Read the name from AI Studio after the page is generated; set it in build_config.json")
    return ctx.write_asset("out/workflows/01-new-lead-automation.md", render(ctx), "workflow_01", "src/workflow_new_lead.py")

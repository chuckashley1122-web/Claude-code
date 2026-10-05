"""Workflow 02 spec -> out/workflows/02-hot-lead-replied.md (SPEC-04 step 10)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.common import A2P_CAVEAT, DRAFT_NOTICE, MERGE_TOKEN_FLAG, NE, md_table  # noqa: E402
from src.workflow_new_lead import SPEC_BLOCK, WORKFLOW_NAME as WF01  # noqa: E402

WORKFLOW_NAME = "Hot Lead - Replied"


def spec() -> dict:
    return {
        "workflow": WORKFLOW_NAME, "status": "Draft", "published_by_build": False,
        "trigger": {"type": "Customer Replied", "filters": {"replied_to_workflow": WF01}},
        "location_id": C.GHL_LOCATION_ID,
        "steps": [
            {"order": 1, "type": "remove_from_workflow", "config": f"Workflow={WF01}",
             "note": "Runs FIRST so no further automated follow-up is sent after a reply"},
            {"order": 2, "type": "internal_notification",
             "config": f"SMS to {C.OWNER_PHONE} if A2P verified ({NE}); else email to {C.OWNER_EMAIL}",
             "note": "Includes the reply body: out/messages/internal_alerts.md#alert_hot_lead"},
            {"order": 3, "type": "create_update_opportunity",
             "config": f"Pipeline={C.NEW_PIPELINE_NAME}; Stage=Hot Lead / Responded", "note": "Owner takes over by hand"},
        ],
    }


def render() -> str:
    sp = spec()
    return "\n".join([
        f"# Workflow 02 - {WORKFLOW_NAME} (spec, not a built workflow)", "", DRAFT_NOTICE, "", MERGE_TOKEN_FLAG, "",
        "## Trigger",
        md_table(["Field", "Value"], [["Trigger", "Customer Replied"], ["Filter: replied to workflow", WF01],
                                       ["Location", C.GHL_LOCATION_ID]]), "",
        "## Actions (in order)",
        md_table(["#", "Action", "Configuration", "Notes"], [[s["order"], s["type"], s["config"], s["note"]] for s in sp["steps"]]), "",
        "## Caveats",
        f"- {A2P_CAVEAT}",
        "- Email-fallback path: if SMS is unavailable, the owner alert goes by email with the same content.",
        "- `{{message.body}}` is an unconfirmed placeholder for the reply text; insert it with the field picker.", "",
        f"```json {SPEC_BLOCK}", json.dumps(sp, indent=2), "```", "",
    ])


def build(ctx) -> Path:
    return ctx.write_asset("out/workflows/02-hot-lead-replied.md", render(), "workflow_02", "src/workflow_hot_lead.py")

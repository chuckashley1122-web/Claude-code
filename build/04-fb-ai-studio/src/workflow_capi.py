"""Workflow 03 spec -> out/workflows/03-landing-page-capi-lead.md (SPEC-04 step 11).

Values come from capi_settings() in pixel_capi_spec.py so the workflow and
capi_settings.json can never drift (checked by T06).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.common import DRAFT_NOTICE, cfg_value, md_table  # noqa: E402
from src.pixel_capi_spec import capi_settings  # noqa: E402
from src.workflow_new_lead import SPEC_BLOCK  # noqa: E402

WORKFLOW_NAME = "Landing Page CAPI - Lead"


def spec(ctx) -> dict:
    s = capi_settings()
    return {
        "workflow": WORKFLOW_NAME, "status": "Draft", "published_by_build": False,
        "trigger": {"type": "AI Studio Form Submitted",
                    "filters": {"ai_studio_project": cfg_value(ctx, "ghl_project_name"),
                                "ai_studio_form": cfg_value(ctx, "ghl_form_name")}},
        "location_id": C.GHL_LOCATION_ID,
        "action": {"type": "Meta Conversion API", "event_type": s["event_type"], "event_to_send": s["event_to_send"],
                   "ltv": s["ltv"], "currency": s["currency"], "test_code": s["test_code"],
                   "custom_mapping": s["custom_mapping"], "access_token_env": s["access_token_env"],
                   "pixel_id_env": s["pixel_id_env"], "dataset_id_env": s["dataset_id_env"]},
    }


def render(ctx) -> str:
    sp = spec(ctx)
    a = sp["action"]
    return "\n".join([
        f"# Workflow 03 - {WORKFLOW_NAME} (spec, not a built workflow)", "", DRAFT_NOTICE, "",
        "## Trigger",
        md_table(["Field", "Value"], [["Trigger", sp["trigger"]["type"]],
                                       ["Filter: AI Studio Project", sp["trigger"]["filters"]["ai_studio_project"]],
                                       ["Filter: AI Studio Form", sp["trigger"]["filters"]["ai_studio_form"]]]), "",
        "## Action: Meta Conversion API",
        md_table(["Field", "Value"], [
            ["Event Type", a["event_type"] + " (the event happens on the funnel/page)"],
            ["Access Token", f"from env var `{a['access_token_env']}` - paste in the GHL UI only, never in a file"],
            ["Dataset / Pixel ID", f"from env var `{a['pixel_id_env']}` / `{a['dataset_id_env']}`"],
            ["Event to Send", a["event_to_send"]],
            ["Lifetime Value", a["ltv"] + " (configurable; the source's example figure is not a CA-J value)"],
            ["Currency", a["currency"]],
            ["Test Code", "(leave empty)"],
            ["Custom Mapping", a["custom_mapping"] + " (AI Studio contacts are native GHL contacts)"],
        ]), "",
        "## Expected behaviour (not a bug)",
        "- A submission **without Facebook parameters** (direct visit) is not marked a Facebook lead and **does not "
        "fire a conversion**. That is correct and prevents false conversions.",
        "- CAPI fails outright if the subdomain is not connected or the form is not natively connected to GHL.",
        "- Only a human reading the workflow's Execution Logs can confirm CAPI works. This build does not claim it does.", "",
        f"```json {SPEC_BLOCK}", json.dumps(sp, indent=2), "```", "",
    ])


def build(ctx) -> Path:
    return ctx.write_asset("out/workflows/03-landing-page-capi-lead.md", render(ctx), "workflow_03", "src/workflow_capi.py")

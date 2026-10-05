"""Pipeline spec -> out/pipeline_spec.md + out/pipeline.json (SPEC-04 step 8)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.common import DRAFT_NOTICE, md_table  # noqa: E402

STAGES = [
    {"order": 1, "name": "New Lead",
     "reason": "Every landing-page form submission starts here so nothing is lost.",
     "entry": "Workflow 01 creates/updates the opportunity on AI Studio Form Submitted.",
     "exit": "Contact replies (-> Hot Lead / Responded) or the sequence ends with no reply (-> Lost)."},
    {"order": 2, "name": "Hot Lead / Responded",
     "reason": "A reply means a real conversation; the owner takes over by hand.",
     "entry": "Workflow 02 moves the opportunity on Customer Replied to a Workflow 01 message.",
     "exit": "Owner marks Closed (won) after a booked appointment / signed agreement, or Lost."},
    {"order": 3, "name": "Closed (won)",
     "reason": "Records a won deal so the campaign can be judged on outcomes, not clicks.",
     "entry": "Owner moves it manually after the strategy session results in a signed agreement.",
     "exit": "Terminal stage."},
    {"order": 4, "name": "Lost",
     "reason": "Keeps the active stages clean; no-reply leads stop receiving automated messages.",
     "entry": "Workflow 01 moves it 1 day after the final follow-up with no reply, or the owner moves it.",
     "exit": "Terminal stage (owner may reopen by hand)."},
]


def pipeline_doc() -> dict:
    assert [s["name"] for s in STAGES] == C.NEW_PIPELINE_STAGES
    return {
        "status": "Draft",
        "location_id": C.GHL_LOCATION_ID,
        "new_pipeline": {"name": C.NEW_PIPELINE_NAME, "stages": STAGES, "created_by_build": False},
        "existing_pipeline_do_not_overwrite": {"name": C.GHL_PIPELINE_NAME, "id": C.GHL_PIPELINE_ID,
                                               "stages": C.GHL_PIPELINE_STAGES},
        "custom_fields": [
            {"name": "Service Needed", "type": "single line / dropdown", "source": "landing-page form",
             "note": "Field key is NEEDS_EVIDENCE until created; insert via field picker"},
            {"name": "Lead Source Detail", "type": "single line", "source": "attribution (utm_campaign / utm_content)",
             "note": "Only if GHL attribution does not already expose it; NEEDS_EVIDENCE"},
        ],
    }


def render_md(doc: dict) -> str:
    rows = [[s["order"], s["name"], s["reason"], s["entry"], s["exit"]] for s in STAGES]
    return "\n".join([
        f"# Pipeline spec: {C.NEW_PIPELINE_NAME}", "", DRAFT_NOTICE, "",
        f"- Target GHL location: `{C.GHL_LOCATION_ID}` (exact case).",
        f"- **Do not overwrite** the existing pipeline `{C.GHL_PIPELINE_NAME}` = `{C.GHL_PIPELINE_ID}` "
        f"(stages: {', '.join(C.GHL_PIPELINE_STAGES)}). `{C.NEW_PIPELINE_NAME}` is a separate new pipeline.",
        "- Created by a human in GHL > Opportunities > Pipelines (see `ui-tasks/GHL-CHECKLIST.md`).", "",
        "## Stages", md_table(["#", "Stage", "Why it exists", "Entry condition", "Exit condition"], rows), "",
        "## Custom fields",
        md_table(["Field", "Type", "Source", "Note"],
                 [[f["name"], f["type"], f["source"], f["note"]] for f in doc["custom_fields"]]), "",
    ])


def build(ctx) -> list[Path]:
    doc = pipeline_doc()
    return [ctx.write_asset("out/pipeline_spec.md", render_md(doc), "pipeline_spec", "src/pipeline_spec.py"),
            ctx.write_json("out/pipeline.json", doc, "pipeline_json", "src/pipeline_spec.py")]

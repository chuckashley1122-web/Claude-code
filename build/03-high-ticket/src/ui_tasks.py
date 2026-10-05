"""Human UI checklists -> ui-tasks/GHL-BUILD-CHECKLIST.md, META-BUILD-CHECKLIST.md, HUMAN-DECISIONS.md

Every item: exact object, field, value, target location and a verify-by line.
No item is ever marked done, Live or Ready for launch by this script.
"""
from __future__ import annotations

from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src import calendar_spec as CAL  # noqa: E402
from src import crm_schema as CRM  # noqa: E402
from src import form_spec as FORM  # noqa: E402
from src import workflow_specs as WF  # noqa: E402
from src.common import prefix  # noqa: E402

APPROVAL = "REQUIRES EXPLICIT HUMAN APPROVAL"
LOC = C.GHL_LOCATION_ID


def item(obj, field, value, verify, spend=False, title=None):
    return {"title": title or f"{obj}: {field}", "object": obj, "field": field, "value": value, "location": LOC,
            "verify_by": verify, "spend": spend, "status": "Not started"}


def ghl_items(config: dict) -> list[dict]:
    p = prefix(config)
    items = [
        item("Sub-account", "Location ID", LOC, f"Browser URL contains /location/{LOC}/ in exact case; record the displayed business name"),
        item("Source playbook location reference", "Location ID",
             "Do NOT use the source playbook's location ID (it is DISALLOWED_LOCATION_ID in config/constants.py)",
             "No object, note or workflow references that ID"),
        item("Existing objects inventory", "Calendars, pipelines, forms, workflows, payment products, connected Pages",
             "Record each object name + ID; duplicate before materially changing any live asset",
             "Inventory saved to config/decision_log.jsonl by the operator"),
        item("Existing pipeline", "Name / ID", f"{C.GHL_PIPELINE_NAME} = {C.GHL_PIPELINE_ID} (do not modify)",
             "Pipeline unchanged after the build"),
        item("Existing offer", "$27 HVAC Review System funnel", "Do not replace or merge with this high-ticket offer",
             "Funnel and its workflows unchanged"),
        item("Pipeline", "Name", f"{p}-Sales", "Pipeline appears under Opportunities with exact name"),
    ]
    for i, s in enumerate(CRM.STAGES, 1):
        items.append(item(f"Pipeline {p}-Sales", f"Stage {i}", s, f"Stage {i} reads exactly '{s}'"))
    for key, label, ftype in CRM.CUSTOM_FIELDS:
        items.append(item("Custom field (contact)", label, f"key={key}; type={ftype}", f"Field '{label}' exists with type {ftype.split(':')[0]}"))
    cal_rows = [("Name", CAL.CALENDAR_NAME), ("Duration", f"{CAL.DURATION_MIN} minutes"), ("Timezone", "America/Chicago (confirm account setting)"),
                ("Working hours", C.NEEDS_EVIDENCE), ("Max booking horizon", f"{CAL.HORIZON_DAYS} days"),
                ("Minimum notice", f"{CAL.MIN_NOTICE_HOURS} hours"), ("Buffers", f"{CAL.BUFFER_MIN} minutes"),
                ("Meeting link", "Google Meet if available"), ("Booking fields", "Name, email, phone + communication disclosures")]
    for field, value in cal_rows:
        items.append(item("Calendar", field, value, "Test booking on desktop and phone shows the expected setting"))
    items += [
        item("Settings > Integrations > Facebook", "Page and lead form access", "The verified Page and the qualification form",
             "Integration lists the Page and form"),
        item("Settings > Integrations > Facebook", "Import mode", "New leads only", "No historical leads imported"),
        item("Facebook lead field mapping", "Decision-maker question", "custom field decision_maker_answer",
             "Test lead shows the answer in that field"),
    ]
    for wf in WF.workflows(config):
        items.append(item("Workflow", "Name / publish state", f"{wf['name']} - UNPUBLISHED during assembly",
                          f"Workflow saved as draft; logic matches out/workflows/{wf['file']}"))
    items += [
        item("Message templates", "Placeholders", "Replace every [TOKEN] using the account field picker",
             "Test preview shows correct name, date, timezone, links and sender"),
        item("Pre-call page", "Visibility", "Private/unlisted draft from out/precall_page/index.html", "Opens without login; no invented outcomes"),
        item("Welcome page + intake form", "Fields", "From out/welcome_page/index.html and out/intake_form.json", "No password fields"),
        item("Payment product", "Create checkout/invoice item", f"Locked CA-J terms; test mode first; no automatic subscription - {APPROVAL}",
             "Test-mode checkout shows correct amount, buyer, description and renewal behavior", spend=True),
        item("Test contacts", "Run T01-T14", "Designated test contacts only (example.com emails, 555-01xx numbers)",
             "Results recorded in out/tests/ evidence and test log"),
    ]
    return items


def meta_items(config: dict) -> list[dict]:
    p = prefix(config)
    return [
        item("Meta Business portfolio", "Page and ad account", f"Page ID {config.get('facebook_page_id')}, ad account {config.get('ad_account_id')}",
             "Both IDs recorded with evidence in config"),
        item("Ad account", "Payment method", f"Do not add or change - {APPROVAL}", "No new payment method", spend=True),
        item("Instant Form", "Type", "More volume", "Form preview"),
        item("Instant Form", "Question", FORM.QUESTION, "Preview shows exact question; Yes/No options"),
        item("Instant Form", "Qualified ending", f"{FORM.QUALIFIED_ENDING['headline']} / {FORM.QUALIFIED_ENDING['body']} / "
             f"button '{FORM.QUALIFIED_ENDING['button']}' -> {C.BOOKING_URL}", "Preview on mobile"),
        item("Instant Form", "Privacy policy URL", f"{config.get('privacy_policy_url')} (never guessed)", "URL opens the published policy"),
        item("Campaign (NEW draft)", "Name", f"{p}-Leads-<YYYYMMDD of draft creation>", "Name is new; it is not the frozen campaign"),
        item("Campaign (NEW draft)", "Objective / destination", "Leads; Instant Forms; lead volume optimization", "Campaign summary"),
        item("Campaign (NEW draft)", "Status", "PAUSED (never published by this build)", "Status column shows Paused/Draft"),
        item("Campaign (NEW draft)", "Daily budget", f"NOT SET. AD_SPEND_CAP_USD = 0 - {APPROVAL}", "No budget saved without written approval", spend=True),
        item("Campaign (NEW draft)", "Special Ad Category", "Determine from the actual campaign and current platform prompts", "Recorded in decision log"),
        item("Ad set 1", "Audience / geography", f"Service area {config.get('service_area')}; HVAC owners and decision makers (not homeowners)", "Audience summary"),
        *[item(f"Ad {a}", "Image + copy", f"out/creatives/{a}.json + out/copy/{a}.md; same Instant Form attached",
               "Preview: image, primary text, headline, CTA, Page identity, destination, mobile rendering") for a in ("A01", "A02", "A03", "A04", "A05")],
        item("Ad images", "Generate 5 x (1080x1350 + 1080x1080)", f"Use each image_prompt; any paid image tool - {APPROVAL}",
             "Spelling, brand, legibility, margins, crop preview", spend=True),
        item("Pixel / Dataset / CAPI", "Create or connect", f"{C.NEEDS_EVIDENCE} whether needed for lead ads; any token stays in .env only",
             "No token in any committed file"),
        item("Whop", "Campaign interface", "Do not purchase a tool to reproduce the video interface", "No new subscription", spend=True),
    ]


def render_items(title: str, header: list[str], items: list[dict], code: str) -> str:
    lines = [f"# {title}", ""] + header + [""]
    for i, it in enumerate(items, 1):
        lines += [f"### {code}-{i:02d} {it['title']}", "", f"- Object: {it['object']}", f"- Field: {it['field']}",
                  f"- Value: {it['value']}", f"- Target location: `{it['location']}`", f"- Verify by: {it['verify_by']}"]
        if it["spend"]:
            lines.append(f"- Spend: {APPROVAL}")
        lines += [f"- Status: {it['status']}", ""]
    return "\n".join(lines)


def human_decisions(config: dict, blockers: list[dict]) -> str:
    lines = ["# Human decisions and approval gates", "",
             "Every NEEDS_EVIDENCE value and every approval gate, with the next action and owner. Nothing here is approved by the build.", "",
             "## Config values that are NEEDS_EVIDENCE", "", "| Config key | Next action | Owner |", "|---|---|---|"]
    for k, v in config.items():
        if v == C.NEEDS_EVIDENCE:
            lines.append(f"| {k} | Supply a verified value with evidence; record it in config/decision_log.jsonl | {C.OWNER_NAME} |")
    lines += ["", "## Approval gates", "", "| Gate | Current | Next action | Owner |", "|---|---|---|---|",
              f"| Ad spend | AD_SPEND_CAP_USD = 0, APPROVAL_AD_SPEND = false | {APPROVAL}: written daily amount, test cap and end date | {C.OWNER_NAME} |",
              f"| Launch | LAUNCH_AUTHORITY = none, APPROVAL_LAUNCH = false | {APPROVAL} after tests pass live | {C.OWNER_NAME} |",
              f"| Payment product | not created | {APPROVAL}; choose processor; test mode first | {C.OWNER_NAME} |",
              f"| Image tool / any purchase | none | {APPROVAL} | {C.OWNER_NAME} |",
              f"| SMS sending | messaging eligibility NEEDS_EVIDENCE | Confirm A2P/consent basis; {APPROVAL} for any messaging fees | {C.OWNER_NAME} |",
              f"| Stale location ID in source playbook | rejected (DISALLOWED_LOCATION_ID) | Confirm the only build location is `{LOC}` | {C.OWNER_NAME} |",
              "", "## Recorded blockers", "", "| Item | Missing input | Work affected | Next action | Owner | Source |", "|---|---|---|---|---|---|"]
    for b in blockers:
        lines.append(f"| {b['item']} | {b['missing_input']} | {b['work_affected']} | {b['next_action']} | {b['owner']} | {b['source_file']} |")
    lines.append("")
    return "\n".join(lines)


def build(state) -> list[Path]:
    cfg = state.config
    ghl = render_items("GHL build checklist", [f"Target location for every item: `{LOC}` (exact case). Every workflow stays unpublished. "
                                               "Mark items done only in your own tracker after verifying."], ghl_items(cfg), "GHL")
    meta = render_items("Meta build checklist", [
        f"**The live campaign `{C.FROZEN_CAMPAIGN_NAME}` is FROZEN — do not edit, pause, or duplicate it; build any new campaign "
        "as a separate NEW draft, because editing resets Meta's learning phase.**", "",
        f"Every spend line is marked `{APPROVAL}`. Nothing is launched by this build."], meta_items(cfg), "META")
    paths = [state.write("ui-tasks/GHL-BUILD-CHECKLIST.md", ghl, "UI-GHL-CHECKLIST", status="Not started", source="src/ui_tasks.py"),
             state.write("ui-tasks/META-BUILD-CHECKLIST.md", meta, "UI-META-CHECKLIST", status="Not started", source="src/ui_tasks.py")]
    paths.append(state.write("ui-tasks/HUMAN-DECISIONS.md", human_decisions(cfg, state.load_blockers()), "UI-HUMAN-DECISIONS",
                             status="Not started", source="src/ui_tasks.py"))
    return paths


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

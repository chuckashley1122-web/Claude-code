"""Close and onboarding pack (playbook steps 44-49)
-> out/close_pack.md, out/welcome_page/index.html, out/intake_form.json
"""
from __future__ import annotations

import re
from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src.common import esc, html_page, ul  # noqa: E402
from src.offer_spec import fee_lines  # noqa: E402
from tools import guardrails as G  # noqa: E402

ONBOARDING_MINUTES = 45
RENEWAL_TASK_DAYS_BEFORE_END = 30
INTAKE_FIELDS = [
    ("legal_business_name", "Legal business name", "text"), ("website", "Website", "url"), ("service_area", "Service area", "text"),
    ("services", "Services offered", "textarea"), ("target_customer", "Target customer", "textarea"),
    ("current_offers", "Current offers", "textarea"), ("brand_assets", "Brand assets (upload or link)", "file_or_url"),
    ("point_of_contact", "Point of contact", "text"), ("reporting_contact", "Reporting contact", "text"),
    ("operating_hours", "Operating hours", "text"), ("calendar_owner", "Calendar owner", "text"),
    ("routing_needs", "Routing needs (calendar, live transfer, fallback)", "textarea"), ("budget", "Media budget", "text"),
    ("proof_assets", "Proof assets you can verify", "textarea"),
]
FORBIDDEN_INTAKE_WORDS = ["password", "passcode", "login credentials", "pin"]


def intake_form() -> dict:
    fields = [{"key": k, "label": l, "type": t, "required": k in ("legal_business_name", "point_of_contact")} for k, l, t in INTAKE_FIELDS]
    for f in fields:
        low = (f["key"] + " " + f["label"]).lower()
        if any(re.search(r"\b" + re.escape(w) + r"\b", low) for w in FORBIDDEN_INTAKE_WORDS):
            raise G.GuardrailViolation(f"intake field {f['key']} asks for credentials; use platform invitations")
    return {"name": "CAJ-HT-HVAC Client Intake", "estimated_minutes": "10-15", "fields": fields,
            "access_rule": "Use platform invitations for access. Never ask for passwords in a form.", "status": "Draft"}


def close_pack(config: dict) -> str:
    lines = ["# Close and onboarding pack (internal)", "",
             "Status: Draft. Internal call material: pricing is presented on the call only.", "",
             "## Price presentation (locked CA-J terms only)", ""]
    lines += [f"- {f}" for f in fee_lines()]
    lines += [f"- Currency: USD", f"- Payment timing: {C.NEEDS_EVIDENCE}", f"- Service dates / term: {config.get('service_term', C.NEEDS_EVIDENCE)}",
              "- Included costs: the agreed scope in out/offer_spec.md", "- Separate costs: client media spend paid to the ad platform",
              f"- Cancellation: {C.NEEDS_EVIDENCE}", "- Guarantee: none (see out/risk_reversal.md)",
              "- Renewal: no automatic charge; terms agreed in writing", "",
              "## Acceptance and payment (plan only)", "",
              "1. Prepare a written scope/agreement and a matching invoice or checkout item.",
              "2. **Payment-product creation is human-only and requires explicit approval.** No automatic subscription.",
              "3. In test mode verify amount, buyer, description and renewal behavior before sending.",
              "4. Verbal yes → `Won pending payment`. Processor-confirmed payment → `Paid onboarding`; store amount and reference.", "",
              "## Onboarding", "",
              f"- Book the next practical onboarding slot; reserve {ONBOARDING_MINUTES} minutes.",
              "- Send the welcome page and ask for the 10-15 minute intake before the meeting; verify receipt.",
              "- Confirm the sold scope against the intake; assign an owner and date for access, tracking, scripts, recording, editing, approval, routing and launch testing.",
              "- Activate delivery only when agreement, payment and required inputs support it.", "",
              "## Renewal", "",
              f"Create an internal renewal discussion task {RENEWAL_TASK_DAYS_BEFORE_END} days before the actual term ends. "
              "Never create a new charge without agreed terms.", ""]
    return "\n".join(lines)


def welcome_page() -> str:
    checklist = ["Complete the intake form (10-15 minutes)", "Send platform invitations for ad account, Page and calendar access",
                 "Gather brand assets", "Confirm who answers new inquiries and when"]
    intake = ul([l for _, l, _ in INTAKE_FIELDS])
    access = ("<p>We request access through each platform's own invitation feature. We will never ask for a password.</p>")
    for t in checklist:
        G.assert_prospect_copy(t)
    sections = [
        ("Welcome video", f"<div class=\"slot\">Welcome video slot: {C.NEEDS_EVIDENCE}</div>"),
        ("Preparation checklist", ul(checklist)),
        ("Intake form", f"<p>Intake form link: {C.NEEDS_EVIDENCE}. It asks for:</p>{intake}"),
        ("Access instructions", access),
        ("Book your onboarding session", f"<p>{ONBOARDING_MINUTES} minutes reserved. Onboarding booking link: {C.NEEDS_EVIDENCE}</p>"),
        ("Contact", f"<p>{esc(C.OWNER_NAME)}, {esc(C.OWNER_PHONE)}, {esc(C.OWNER_EMAIL)}</p>"),
    ]
    return html_page("Welcome to CA-J Enterprises", sections, "DRAFT for content review. Not published.")


def build(state) -> list[Path]:
    for item, action in [("payment timing", "Decide in writing"), ("cancellation terms", "Decide in writing"),
                         ("payment_processor", "Choose processor; create test-mode product only after explicit approval"),
                         ("welcome video", "Record and host; replace the slot"),
                         ("intake form link", "Build the intake form in GHL from intake_form.json"),
                         ("onboarding booking link", "Create a 45-minute onboarding calendar")]:
        state.needs(item, "out/close_pack.md", action)
    for item, action in [("welcome video", "Record and host; replace the slot"),
                         ("intake form link", "Build the intake form in GHL from intake_form.json"),
                         ("onboarding booking link", "Create a 45-minute onboarding calendar")]:
        state.needs(item, "out/welcome_page/index.html", action)
    return [state.write("out/close_pack.md", close_pack(state.config), "CLOSE-PACK", source="src/onboarding_pack.py"),
            state.write("out/welcome_page/index.html", welcome_page(), "WELCOME-PAGE", source="src/onboarding_pack.py"),
            state.write_json("out/intake_form.json", intake_form(), "INTAKE-FORM", source="src/onboarding_pack.py")]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

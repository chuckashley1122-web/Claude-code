"""Qualification form spec (playbook steps 25-26) -> out/form_spec.md + out/qualification_logic.json

evaluate() is the executable form of the logic JSON; the funnel simulator uses it.
"""
from __future__ import annotations

from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from tools import guardrails as G  # noqa: E402

SRC = "out/form_spec.md"
QUESTION = "Do you own or make marketing decisions for an HVAC company?"
SOURCE_QUESTION = "Are you a licensed real estate agent?"
QUALIFIED_ENDING = {
    "headline": "One last step — book your strategy session.",
    "body": "Choose a time to review your goals, service area and marketing needs.",
    "button": "Book a time",
    "url": C.BOOKING_URL,
}
DISQUALIFIED_ENDING = {
    "headline": "Thanks for your interest.",
    "body": "These strategy sessions are for HVAC owners and marketing decision makers.",
}
DISQUALIFIED_TAG = "caj-ht-hvac-disqualified"


def logic(config: dict, territory_policy_documented: bool = False) -> dict:
    data = {
        "form_type": "More volume",
        "question": {"text": QUESTION, "custom_field": "decision_maker_answer", "options": ["Yes", "No"]},
        "routes": {"Yes": {"action": "continue", "ending": "qualified", "qualification_status": "Qualified"},
                   "No": {"action": "disqualify", "ending": "disqualified", "qualification_status": "Disqualified"}},
        "collect": ["full_name", "email", "phone"],
        "fallback_if_conditional_endings_unavailable": {
            "flag_no_responses_in_ghl": True, "tag": DISQUALIFIED_TAG, "custom_field": "decision_maker_answer",
            "suppress_sales_booking_sequence": True,
        },
        "qualified_ending": QUALIFIED_ENDING,
        "disqualified_ending": DISQUALIFIED_ENDING,
        "privacy_policy_url": config.get("privacy_policy_url", C.NEEDS_EVIDENCE),
        "conditional_endings_available": C.NEEDS_EVIDENCE,
    }
    if territory_policy_documented:
        data["territory_claim"] = "One company per area (documented territory policy)"
    return data


def evaluate(answer) -> dict:
    """Route one answer. Anything other than an explicit Yes is not qualified."""
    norm = str(answer).strip().lower() if answer is not None else ""
    if norm == "yes":
        return {"qualified": True, "qualification_status": "Qualified", "ending": "qualified", "suppress_booking": False}
    return {"qualified": False, "qualification_status": "Disqualified", "ending": "disqualified",
            "suppress_booking": True, "tag": DISQUALIFIED_TAG}


def check_copy(data: dict) -> None:
    for text in [data["question"]["text"], *QUALIFIED_ENDING.values(), *DISQUALIFIED_ENDING.values()]:
        G.assert_meeting_first(text)
        G.assert_prospect_copy(text)


def render(data: dict) -> str:
    lines = ["# Lead form specification", "", "Status: Draft. A human builds this form in Meta (see ui-tasks/META-BUILD-CHECKLIST.md).", "",
             f"- Form type: {data['form_type']}", f"- Single qualification question: \"{QUESTION}\" (source replay: \"{SOURCE_QUESTION}\")",
             "- Yes: continue to the qualified ending", "- No: disqualification ending", "- Collect: name, email, phone",
             f"- Privacy policy URL: {data['privacy_policy_url']} (never guessed)",
             f"- Conditional endings available in the account: {data['conditional_endings_available']}", "",
             "## If conditional endings are unavailable", "",
             f"Flag No responses in GHL (tag `{DISQUALIFIED_TAG}`, field `decision_maker_answer`) and suppress the sales booking sequence.", "",
             "## Qualified ending", "", f"- Headline: {QUALIFIED_ENDING['headline']}", f"- Body: {QUALIFIED_ENDING['body']}",
             f"- Button: {QUALIFIED_ENDING['button']} → {QUALIFIED_ENDING['url']}", "",
             "## Disqualified ending", "", f"- Headline: {DISQUALIFIED_ENDING['headline']}", f"- Body: {DISQUALIFIED_ENDING['body']}", ""]
    if "territory_claim" not in data:
        lines += ["The one-company-per-area claim is omitted: no documented territory policy exists (" + C.NEEDS_EVIDENCE + ").", ""]
    return "\n".join(lines)


def build(state) -> list[Path]:
    data = logic(state.config)
    check_copy(data)
    if data["privacy_policy_url"] == C.NEEDS_EVIDENCE:
        state.needs("privacy_policy_url", SRC, "Supply the real published privacy policy URL")
        state.needs("privacy_policy_url", "out/qualification_logic.json", "Supply the real published privacy policy URL")
    state.needs("conditional endings availability", "out/qualification_logic.json", "Check in Meta form builder; if absent use the GHL flag fallback")
    state.needs("conditional endings availability", SRC, "Check in Meta form builder; if absent use the GHL flag fallback")
    state.needs("territory policy", SRC, "Only document if a real one-company-per-area policy exists; otherwise keep omitted")
    return [state.write(SRC, render(data), "FORM-SPEC", source="src/form_spec.py"),
            state.write_json("out/qualification_logic.json", data, "QUALIFICATION-LOGIC", source="src/form_spec.py")]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

"""Facebook -> GHL integration and field mapping (playbook steps 28-30)
-> out/ghl_facebook_integration.md + out/field_map.json

The duplicate-handling rules here are implemented in src/funnel_sim.py and
tested by T04.
"""
from __future__ import annotations

from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402

SRC = "out/ghl_facebook_integration.md"
FIELD_MAP = [
    {"source": "full_name", "target": "native:name", "kind": "native"},
    {"source": "email", "target": "native:email", "kind": "native"},
    {"source": "phone", "target": "native:phone", "kind": "native"},
    {"source": "decision_maker_question", "target": "custom:decision_maker_answer", "kind": "custom"},
    {"source": "form_id", "target": "custom:form_id", "kind": "metadata"},
    {"source": "leadgen_id", "target": "custom:meta_lead_id", "kind": "metadata"},
    {"source": "campaign_id", "target": "custom:campaign_id", "kind": "attribution"},
    {"source": "ad_id", "target": "custom:ad_id", "kind": "attribution"},
    {"source": "created_time", "target": "custom:lead_received_time", "kind": "metadata"},
]
DUPLICATE_RULES = [
    "Key inbound events on Meta lead ID when present; a repeated lead ID is a replay and changes nothing.",
    "Match an existing contact on native email or phone (native matching settings) and update it rather than create another.",
    "Reuse the open opportunity for the same contact and offer; never open a second one.",
    "A repeat lead updates attribution history without enrolling the contact twice in the same unbooked sequence.",
    "Never collapse distinct people on name alone.",
]


def field_map() -> dict:
    return {
        "location_id": C.GHL_LOCATION_ID,
        "mappings": [dict(m, availability=C.NEEDS_EVIDENCE if m["kind"] in ("attribution", "metadata") else "standard") for m in FIELD_MAP],
        "duplicate_handling": DUPLICATE_RULES,
        "import_mode": "new leads only during setup",
        "unavailable_field_rule": "Record the limitation and use a documented lookup or reporting reconciliation; never invent attribution.",
    }


def render() -> str:
    steps = [
        f"Open Settings → Integrations in location `{C.GHL_LOCATION_ID}` (exact case).",
        "Inspect the Facebook connection. Confirm access to the intended Page and its lead forms.",
        "Connect or refresh only through the authorized account flow if necessary.",
        "Prefer **new leads only** during setup so a historical import does not trigger follow-up on old contacts.",
        "Map fields as in `field_map.json`; record which attribution fields the integration actually exposes.",
        "Submit test leads (Yes, Yes+book, No, repeat) and verify each route (tests T01-T04, T09).",
    ]
    lines = ["# GHL Facebook lead integration (human steps)", "", "Status: Draft spec. A human performs every step below.", ""]
    lines += [f"{i}. {s}" for i, s in enumerate(steps, 1)]
    lines += ["", "## Field map", "", "| Form field | GHL target | Kind |", "|---|---|---|"]
    lines += [f"| {m['source']} | {m['target']} | {m['kind']} |" for m in FIELD_MAP]
    lines += ["", "Name, email and phone go to native fields; the decision-maker question goes to its dedicated custom field. "
              "Preserve form ID and source metadata; save campaign and ad attribution where available "
              f"(availability {C.NEEDS_EVIDENCE}).", "", "## Duplicate handling", ""]
    lines += [f"- {r}" for r in DUPLICATE_RULES]
    lines += ["", "**A calendar link alone does not deliver every unbooked form submission into the CRM.** "
              "The native lead sync is required; an integration failure blocks paid launch until corrected.", ""]
    return "\n".join(lines)


def build(state) -> list[Path]:
    state.needs("facebook_page_id", SRC, "Confirm the intended Page in GHL Integrations; record its ID with evidence")
    state.needs("attribution field availability", SRC, "Inspect integration mapping UI; record available fields")
    state.needs("attribution field availability", "out/field_map.json", "Inspect integration mapping UI; record which metadata/attribution fields exist")
    state.needs("duplicate-match settings", SRC, "Inspect GHL contact matching settings; record them")
    return [state.write(SRC, render(), "GHL-FB-INTEGRATION", source="src/integration_spec.py"),
            state.write_json("out/field_map.json", field_map(), "FIELD-MAP", source="src/integration_spec.py")]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

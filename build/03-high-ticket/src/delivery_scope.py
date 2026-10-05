"""Delivery scope (playbook steps 50-55) -> out/delivery_scope.md"""
from __future__ import annotations

from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402

SRC = "out/delivery_scope.md"
NE = C.NEEDS_EVIDENCE
MINIMUM_SCOPE = {
    "Separate client environment": ["Authorized client account or subaccount; record ownership of ad accounts, Pages, calendar, phone numbers, reporting and customer data",
                                    "Client inquiries kept separate from CA-J agency prospects",
                                    "Copy only tested workflow structure; replace all identity, routing, offer and disclosure fields"],
    "Customer acquisition campaign plan": [f"Channel and job focus from the signed scope: {NE}",
                                           "Audience, geography, offer, scripts, destination, conversion event, budget and reporting documented per account",
                                           "Channel setup stays incomplete until an account-specific plan and a conversion test exist"],
    "Qualification and appointment setting": ["Qualified customer inquiry = correct service area + relevant service need + usable contact details + scope criteria",
                                              "Duplicates and invalid inquiries recorded separately",
                                              f"Follow-up method (human / workflow / AI assisted): {NE}"],
    "Routing": ["Calendar: connect client calendar; verify availability and booking ownership",
                "Live transfer: approved telephony, dedicated destination, verified recipients, operating hours, ring behavior, timeout, missed-call fallback",
                "Test answered, busy, unanswered and after-hours calls; document and test the fallback before promising it"],
    "AI behavior (only if included)": [f"Provider: {NE}; knowledge source: {NE}", "Allowed answers, handoff conditions, communication permissions, usage cost, transcript retention: " + NE,
                                       "Must not invent pricing, book unavailable slots, or diagnose HVAC faults",
                                       "Automated outbound calling stays disabled until channel configuration and permission basis are verified"],
    "Client reporting": ["Spend, unique inquiries, qualified inquiries, booked and held appointments, completed sales, verified contribution where available",
                         "Weekly reconciliation of lead outcomes with the client", "Fix operational failures before expanding spend"],
}
UNRESOLVED = [
    "The source sells fulfillment but never shows its construction.",
    "The video contains no complete YouTube or AI-agent tutorial.",
    "The word \"AI\" in a title does not establish a calling architecture, provider or model.",
    "Live-transfer capability and multi-person ringing are unverified.",
    "Client media budget, channel and job focus are unknown until a scope is signed.",
]


def render() -> str:
    lines = ["# Delivery scope", "", "Status: Draft. Build addition (playbook section 13).", "", "## Minimum client delivery scope", ""]
    for title, items in MINIMUM_SCOPE.items():
        lines += [f"### {title}", ""] + [f"- {i}" for i in items] + [""]
    lines += ["## Unresolved work (recorded explicitly)", ""] + [f"- {u}" for u in UNRESOLVED] + [""]
    return "\n".join(lines)


def build(state) -> list[Path]:
    state.needs("client acquisition channel and job focus", SRC, "Set from the signed client scope")
    state.needs("follow-up method (human/workflow/AI)", SRC, "Decide per client scope")
    state.needs("AI provider and behavior spec", SRC, "Only if AI is sold: choose provider and define behavior; requires approval for usage cost")
    return [state.write(SRC, render(), "DELIVERY-SCOPE", source="src/delivery_scope.py")]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

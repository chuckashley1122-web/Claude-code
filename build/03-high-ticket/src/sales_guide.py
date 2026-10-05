"""Sales call guide (playbook steps 39-43) -> out/sales_call_guide.md"""
from __future__ import annotations

from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402

SRC = "out/sales_call_guide.md"
PRICING_RULE = ("No price is quoted in any email, chat, or AI agent reply — pricing is presented on the call only. "
                f"Pricing questions outside the call route to {C.BOOKING_URL}.")

STEPS = [
    ("1. Open and diagnose", [
        "Ask: \"What would make this conversation useful for you?\"",
        "Ask who handles marketing, what produces leads today, what has been tried, what takes too much time, and who owns the decision.",
        "Summarize the problem in the prospect's own words. Do not assume every prospect wants the same outcome."]),
    ("2. Quantify the desired outcome", [
        "Current inquiry, appointment and sale volume.", "Average contribution per sale (revenue minus variable delivery cost).",
        "Current acquisition spend.", "Team capacity: which job types and service areas have profitable capacity.",
        "Extra monthly sales needed.",
        "If the prospect cannot supply numbers, assign a dated follow-up instead of inventing ROI. Use out/economics/client_break_even.md."]),
    ("3. Explain the service concretely", [
        "Walk through: attraction → qualification → follow-up → calendar (or live transfer only if tested) → client sales process → reporting.",
        "Say who creates scripts, who records video, who edits, who answers leads, and how outcomes are tracked.",
        "Distinguish the Meta campaign that brought this prospect to CA-J from the channel proposed to reach the prospect's own customers."]),
    ("4. Validate lead routing", [
        "Destinations, who answers during operating hours, ring timeout, and the missed-call fallback.",
        "Record names and destinations only after verification.",
        "Never promise working live transfers before the chosen system is tested; multi-person ringing may be unsupported."]),
    ("5. Discuss timing and fit", [
        "Quote only the timeline the actual delivery team can support (" + C.NEEDS_EVIDENCE + " until capacity review).",
        "The source's 2-3 week launch and ~90-day horizon are instructor expectations, not CA-J commitments.",
        "Ask: \"Does this address the problem you described? What would you need to see to feel comfortable moving forward?\""]),
    ("6. If there is a fit", [
        "Present pricing using out/close_pack.md (locked CA-J terms only).",
        "A verbal yes moves the opportunity to Won pending payment only."]),
]


def render() -> str:
    lines = ["# Sales call guide", "", "Status: Draft. Source: playbook steps 39-43 (reconstructed call structure; the transcript enters mid-conversation).", "",
             f"**Rule: {PRICING_RULE}**", ""]
    for title, items in STEPS:
        lines += [f"## {title}", ""] + [f"- {i}" for i in items] + [""]
    lines += ["## Call record must contain", "",
              "Business goals, baseline economics, capacity, decision maker, routing needs, objections, agreed scope and a dated next action. "
              "No prospect is marked Won solely because a call occurred.", ""]
    return "\n".join(lines)


def build(state) -> list[Path]:
    state.needs("delivery timeline", SRC, "Quote only after the delivery team's capacity review")
    return [state.write(SRC, render(), "SALES-CALL-GUIDE", source="src/sales_guide.py")]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

"""Positioning (playbook step 12) -> out/positioning.md"""
from __future__ import annotations

from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from tools import guardrails as G  # noqa: E402

SRC = "out/positioning.md"
POSITIONING = (
    "CA-J Enterprises helps HVAC businesses build a managed system for generating inquiries, following up and booking "
    "estimates. We handle the agreed marketing and automation work while your team handles calls, estimates and sales. "
    "Book a strategy session to review fit, capacity and budget."
)
FORBIDDEN_CLAIM_WORDS = ["roi", "guarantee", "exclusive", "only one", "limited spots", "spots left"]


def check_positioning(text: str) -> str:
    G.assert_prospect_copy(text)
    low = text.lower()
    hits = [w for w in FORBIDDEN_CLAIM_WORDS if w in low]
    if hits:
        raise G.GuardrailViolation(f"positioning contains ROI/scarcity/exclusivity/guarantee wording: {hits}")
    return text


def render() -> str:
    check_positioning(POSITIONING)
    return "\n".join([
        "# Positioning", "",
        "Status: Draft. **Proposed copy, not a performance guarantee.** Source: playbook step 12 (CA-J adaptation).", "",
        "> " + POSITIONING, "",
        "Rules: no ROI figure, no scarcity, no exclusivity, no guarantee. Pricing is never stated; the booking destination is the plain booking URL.", "",
    ])


def build(state) -> list[Path]:
    return [state.write(SRC, render(), "POSITIONING", source="src/positioning.py")]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

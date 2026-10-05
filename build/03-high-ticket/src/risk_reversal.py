"""Risk reversal (playbook step 13) -> out/risk_reversal.md

Default: NO numerical guarantee. A guarantee can only be drafted when every
required term is supplied.
"""
from __future__ import annotations

from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src.common import proof_block  # noqa: E402

SRC = "out/risk_reversal.md"
DEFAULT_POLICY = "No numerical guarantee."
REQUIRED_GUARANTEE_TERMS = [
    "eligible_revenue_or_contribution_definition", "included_costs", "attribution_method", "duration",
    "evidence_standard", "client_obligations", "exclusions", "claim_window", "exact_remedy",
]


class IncompleteGuarantee(ValueError):
    pass


def validate_guarantee(terms: dict, fee_prepaid: bool) -> dict:
    """Return the terms if complete; raise listing every missing term otherwise."""
    required = list(REQUIRED_GUARANTEE_TERMS) + (["refund_or_credit_mechanism"] if fee_prepaid else [])
    missing = [k for k in required if not terms.get(k) or terms.get(k) == C.NEEDS_EVIDENCE]
    if missing:
        raise IncompleteGuarantee(f"guarantee cannot be offered; missing: {missing}")
    return terms


def render() -> str:
    lines = ["# Risk reversal", "", f"**Default policy: {DEFAULT_POLICY}** Status: Draft.", "",
             "No guarantee language may appear in ads, forms, messages or the call unless a human chooses one and every term below is defined in writing.", ""]
    lines += proof_block(["- The source uses a \"2x ROI\" framing with no enforceable calculation and no remedy. It ships with neither, so it is not reused.",
                          "- \"Pay per deal\" and \"five listings in six months\" create different obligations and are not CA-J terms."])
    lines += ["", "## Template if a human later chooses a guarantee", "",
              "All of the following are required (the build refuses an incomplete guarantee):", ""]
    lines += [f"- {k}: {C.NEEDS_EVIDENCE}" for k in REQUIRED_GUARANTEE_TERMS]
    lines += [f"- refund_or_credit_mechanism (required whenever the fee is prepaid): {C.NEEDS_EVIDENCE}", ""]
    return "\n".join(lines)


def build(state) -> list[Path]:
    state.needs("guarantee decision", SRC, "Keep default (no numerical guarantee) or define every template term in writing")
    return [state.write(SRC, render(), "RISK-REVERSAL", source="src/risk_reversal.py")]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

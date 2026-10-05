"""Client break-even planning formulas (playbook step 09) -> out/economics/client_break_even.md

Formulas (exact):
  monthly_acquisition_cost = monthly_service_fee + media_spend + separately_charged_tools
  required_sales  = ceil(acquisition_cost / contribution_per_sale)
  required_held   = ceil(required_sales / close_rate)
  required_leads  = ceil(required_held / lead_to_held_rate)
Contribution = revenue - variable delivery cost. Revenue or commission is never profit.
Exact rational arithmetic is used so 4 / 0.4 is 10, not 10.000000000000002.
"""
from __future__ import annotations

from fractions import Fraction
from math import ceil
from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402


class InputUnknown(ValueError):
    """An input is NEEDS_EVIDENCE or otherwise not a number."""


def _num(name: str, value) -> Fraction:
    if value == C.NEEDS_EVIDENCE or value is None or isinstance(value, bool):
        raise InputUnknown(f"{name} is {C.NEEDS_EVIDENCE}")
    try:
        return Fraction(str(value))
    except (ValueError, TypeError) as exc:
        raise InputUnknown(f"{name}={value!r} is not a number") from exc


def _rate(name: str, value) -> Fraction:
    r = _num(name, value)
    if not (0 < r <= 1):
        raise ValueError(f"{name} must be in (0, 1], got {value}")
    return r


def contribution(revenue, variable_delivery_cost) -> Fraction:
    return _num("revenue", revenue) - _num("variable_delivery_cost", variable_delivery_cost)


def monthly_acquisition_cost(monthly_service_fee, media_spend, separately_charged_tools) -> Fraction:
    return (_num("monthly_service_fee", monthly_service_fee) + _num("media_spend", media_spend)
            + _num("separately_charged_tools", separately_charged_tools))


def required_sales(acquisition_cost, contribution_per_sale) -> int:
    cps = _num("contribution_per_sale", contribution_per_sale)
    if cps <= 0:
        raise ValueError("contribution_per_sale must be positive; a sale that loses money cannot break even")
    return ceil(_num("acquisition_cost", acquisition_cost) / cps)


def required_held(required_sales_n, close_rate) -> int:
    return ceil(_num("required_sales", required_sales_n) / _rate("close_rate", close_rate))


def required_leads(required_held_n, lead_to_held_rate) -> int:
    return ceil(_num("required_held", required_held_n) / _rate("lead_to_held_rate", lead_to_held_rate))


def plan(monthly_service_fee, media_spend, separately_charged_tools, contribution_per_sale,
         close_rate, lead_to_held_rate) -> dict:
    cost = monthly_acquisition_cost(monthly_service_fee, media_spend, separately_charged_tools)
    sales = required_sales(cost, contribution_per_sale)
    held = required_held(sales, close_rate)
    leads = required_leads(held, lead_to_held_rate)
    return {"monthly_acquisition_cost": cost, "required_sales": sales, "required_held": held, "required_leads": leads}


def try_plan(**inputs) -> dict:
    """Like plan() but returns a not-computable record instead of guessing."""
    try:
        return {"computable": True, **plan(**inputs)}
    except InputUnknown as exc:
        return {"computable": False, "reason": str(exc)}


# Source illustration (playbook step 09). Every value is an assumption, not a CA-J result.
ILLUSTRATION = {
    "monthly_service_fee": 1300,
    "media_spend": 1500,
    "separately_charged_tools": 0,
    "contribution_per_sale": 3000,
    "close_rate": "0.25",
    "lead_to_held_rate": "0.40",
}

LABEL = "assumption — not a CA-J result"


def _usd(x) -> str:
    return f"${int(x):,}" if Fraction(x).denominator == 1 else f"${float(x):,.2f}"


def render() -> str:
    p = plan(**ILLUSTRATION)
    caj = try_plan(monthly_service_fee=C.NEEDS_EVIDENCE, media_spend=C.NEEDS_EVIDENCE, separately_charged_tools=C.NEEDS_EVIDENCE,
                   contribution_per_sale=C.NEEDS_EVIDENCE, close_rate=C.NEEDS_EVIDENCE, lead_to_held_rate=C.NEEDS_EVIDENCE)
    lines = [
        "# Client break-even (planning worksheet)",
        "",
        "Status: Draft. Source: playbook step 09 (build addition). Nothing here is a CA-J result.",
        "",
        "## Formulas (exact)",
        "",
        "```",
        "monthly_acquisition_cost = monthly_service_fee + media_spend + separately_charged_tools",
        "required_sales = ceil(acquisition_cost / contribution_per_sale)",
        "required_held = ceil(required_sales / close_rate)",
        "required_leads = ceil(required_held / lead_to_held_rate)",
        "```",
        "",
        "Contribution = revenue − variable delivery cost. Never treat commission or revenue as profit.",
        "For real estate, use the client's actual commission split and transaction costs.",
        "",
        "## Source illustration",
        "",
        "| Input | Value | Label |",
        "|---|---|---|",
        f"| monthly_service_fee | {_usd(ILLUSTRATION['monthly_service_fee'])} | {LABEL} (monthly equivalent of the source example package) |",
        f"| media_spend | {_usd(ILLUSTRATION['media_spend'])} | {LABEL} |",
        f"| separately_charged_tools | {_usd(ILLUSTRATION['separately_charged_tools'])} | {LABEL} |",
        f"| contribution_per_sale | {_usd(ILLUSTRATION['contribution_per_sale'])} | {LABEL} |",
        f"| close_rate (held appointment to sale) | 25% | {LABEL} |",
        f"| lead_to_held_rate | 40% | {LABEL} |",
        "",
        "| Output | Value | Label |",
        "|---|---|---|",
        f"| monthly_acquisition_cost | {_usd(p['monthly_acquisition_cost'])} | computed from assumptions — not a CA-J result |",
        f"| required_sales | {p['required_sales']} | computed from assumptions |",
        f"| required_held | {p['required_held']} | computed from assumptions |",
        f"| required_leads | {p['required_leads']} | computed from assumptions |",
        "",
        "## CA-J client worksheet (to fill on the strategy call)",
        "",
        "Service fee for a CA-J client = TECH_FEE_MONTHLY_USD + (per-booked-appointment fee × booked appointments),",
        "using the locked CA-J terms in `config/constants.py` (setup fee waived). Media spend, tools, contribution per sale,",
        "close rate and lead-to-held rate are client-specific.",
        "",
        "Result with current inputs: " + ("computable" if caj["computable"] else "not computable — " + caj["reason"]) + ".",
        f"Every client input is {C.NEEDS_EVIDENCE} until the prospect supplies it; assign a follow-up instead of inventing ROI.",
        "",
    ]
    return "\n".join(lines)


def build(state) -> list[Path]:
    path = state.write("out/economics/client_break_even.md", render(), "ECON-BREAK-EVEN", source="tools/break_even.py")
    for key in ("client media_spend", "client contribution_per_sale", "client close_rate", "client lead_to_held_rate"):
        state.needs(key, "out/economics/client_break_even.md", "Collect on the strategy call (sales_call_guide step 2)",
                    owner=C.OWNER_NAME)
    return [path]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

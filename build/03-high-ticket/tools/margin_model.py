"""Agency margin on any stated package term (playbook step 10) -> out/economics/agency_margin.md

margin = package revenue
         - (fulfillment labor + appointment setting + editing + software + payment fees + refund exposure)
         - CA-J's own acquisition cost
If any input is NEEDS_EVIDENCE the model says so instead of guessing.
Unlimited-scope delivery with unknown delivery cost is refused outright.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402

COST_KEYS = ["fulfillment_labor", "appointment_setting", "editing", "software", "payment_fees", "refund_exposure"]
CANNOT_MODEL = "margin cannot be modeled with current inputs"


class UnlimitedScopeRefused(ValueError):
    """Unlimited-scope delivery cannot be priced when delivery cost is unknown."""


def _unknown(v) -> bool:
    return v == C.NEEDS_EVIDENCE or v is None


def caj_package_revenue(months, booked_appointments, per_booked_appointment_usd):
    """Revenue for the locked CA-J terms over a term. Returns NEEDS_EVIDENCE if any input is unknown."""
    if any(_unknown(v) for v in (months, booked_appointments, per_booked_appointment_usd)):
        return C.NEEDS_EVIDENCE
    per = Fraction(str(per_booked_appointment_usd))
    if not (C.PER_BOOKED_APPOINTMENT_MIN_USD <= per <= C.PER_BOOKED_APPOINTMENT_MAX_USD):
        raise ValueError("per-booked-appointment fee outside the locked CA-J range")
    return (Fraction(C.TECH_FEE_MONTHLY_USD) * Fraction(str(months)) + Fraction(C.SETUP_FEE_USD)
            + per * Fraction(str(booked_appointments)))


def model_margin(term: dict) -> dict:
    costs = term.get("costs", {})
    if term.get("scope") == "unlimited" and any(_unknown(costs.get(k)) for k in COST_KEYS):
        raise UnlimitedScopeRefused(f"{term.get('name')}: refuse to model unlimited-scope delivery with unknown delivery cost")
    inputs = {"revenue": term.get("revenue"), "agency_acquisition_cost": term.get("agency_acquisition_cost")}
    inputs.update({k: costs.get(k) for k in COST_KEYS})
    unknown = [k for k, v in inputs.items() if _unknown(v)]
    if unknown:
        return {"name": term.get("name"), "modelable": False, "message": CANNOT_MODEL, "unknown_inputs": unknown}
    rev = Fraction(str(inputs["revenue"]))
    delivery = sum((Fraction(str(costs[k])) for k in COST_KEYS), Fraction(0))
    margin = rev - delivery - Fraction(str(inputs["agency_acquisition_cost"]))
    return {
        "name": term.get("name"),
        "modelable": True,
        "revenue": rev,
        "delivery_cost": delivery,
        "margin": margin,
        "margin_pct": (margin / rev * 100) if rev else None,
    }


def candidate_terms(config: dict) -> list[dict]:
    unknown_costs = {k: C.NEEDS_EVIDENCE for k in COST_KEYS}
    term_months = config.get("service_term", C.NEEDS_EVIDENCE)
    return [
        {
            "name": "CA-J locked terms (tech fee + per booked appointment, setup waived)",
            "revenue": caj_package_revenue(term_months, C.NEEDS_EVIDENCE, C.PER_BOOKED_APPOINTMENT_MIN_USD),
            "scope": "defined",
            "costs": dict(unknown_costs),
            "agency_acquisition_cost": C.NEEDS_EVIDENCE,
        },
    ]


def render(config: dict) -> str:
    lines = [
        "# Agency margin model",
        "",
        "Status: Draft. Source: playbook step 10 (build addition).",
        "",
        "Margin = package revenue − (fulfillment labor + appointment setting + editing + software + payment fees",
        "+ refund exposure) − CA-J's own acquisition cost. Unlimited-scope delivery is not modeled while delivery cost is unknown.",
        "",
    ]
    for term in candidate_terms(config):
        res = model_margin(term)
        lines += [f"## {term['name']}", ""]
        lines.append("Revenue basis: TECH_FEE_MONTHLY_USD × term months + SETUP_FEE_USD (waived) + per-booked-appointment fee "
                     "× booked appointments (locked CA-J terms in `config/constants.py`).")
        lines.append("")
        if res["modelable"]:
            lines.append(f"Margin: {float(res['margin']):,.2f} (assumption-based)")
        else:
            lines.append(f"**Result: {res['message']}.**")
            lines.append("")
            lines.append("Unknown inputs (each is " + C.NEEDS_EVIDENCE + "): " + ", ".join(res["unknown_inputs"]))
        lines.append("")
    lines += [
        "## Source example package",
        "",
        "<!-- DO-NOT-USE-AS-PROOF:START -->",
        "Do not use as proof. The source's six-month prepaid example ($7,800, source example, unverified) is an instructor price,",
        "not a CA-J price. Its delivery costs were never shown, so its margin also cannot be modeled with current inputs.",
        "<!-- DO-NOT-USE-AS-PROOF:END -->",
        "",
        "The niche brief is complete only after both client economics and agency margin are modeled with real inputs.",
        "",
    ]
    return "\n".join(lines)


def build(state) -> list[Path]:
    path = state.write("out/economics/agency_margin.md", render(state.config), "ECON-AGENCY-MARGIN", source="tools/margin_model.py")
    for key in COST_KEYS + ["agency_acquisition_cost", "booked appointments per term"]:
        state.needs(f"margin input: {key}", "out/economics/agency_margin.md",
                    "Estimate from actual fulfillment plan and vendor quotes; record evidence in decision log")
    if state.config.get("service_term") == C.NEEDS_EVIDENCE:
        state.needs("service_term", "out/economics/agency_margin.md", "Decide the CA-J service term in writing")
    return [path]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

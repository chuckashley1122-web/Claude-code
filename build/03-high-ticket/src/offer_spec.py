"""Offer specification (playbook step 11) -> out/offer_spec.md

The fee comes only from the locked CA-J terms in config/constants.py.
This is an INTERNAL document; prices here are presented on the call only.
"""
from __future__ import annotations

from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src.common import OFFER_VERSION, md_table, proof_block  # noqa: E402

SRC = "out/offer_spec.md"
NE = C.NEEDS_EVIDENCE


def fee_lines() -> list[str]:
    return [
        f"${C.TECH_FEE_MONTHLY_USD}/mo tech fee (locked CA-J term)",
        f"Setup fee waived, ${C.SETUP_FEE_USD} (locked CA-J term)",
        f"${C.PER_BOOKED_APPOINTMENT_MIN_USD} to ${C.PER_BOOKED_APPOINTMENT_MAX_USD} per booked appointment (locked CA-J term)",
    ]


def offer(config: dict) -> dict:
    return {
        "offer_version": OFFER_VERSION,
        "buyer": "HVAC owners or marketing decision makers who can handle additional replacement or installation estimates",
        "desired_outcome": "A managed system for generating inquiries, following up and booking estimates",
        "actual_service": "Managed HVAC lead generation and follow-up; scope to be costed",
        "included_channels": NE,
        "deliverable_quantity": NE,
        "implementation_dependencies": "Client access via platform invitations, client calendar owner, verified routing, approved media budget",
        "service_term": config.get("service_term", NE),
        "fee": fee_lines(),
        "separate_media_budget": "Separate client media budget, paid by the client; not agency prospecting spend. Amount " + NE,
        "client_responsibilities": "Supply assets, cover calls, attend estimates, report outcomes",
        "reporting": "Spend, unique and qualified inquiries, booked and held appointments, completed sales, verified contribution; weekly reconciliation",
        "cancellation": NE,
        "renewal": "No automatic charge; internal renewal discussion task 30 days before term end; terms " + NE,
        "remedy": "No numerical guarantee (see out/risk_reversal.md)",
    }


def render(o: dict) -> str:
    lines = ["# Offer specification (internal)", "",
             f"Offer version: `{o['offer_version']}`. Status: Draft. Internal document: pricing is presented on the call only, "
             f"never in email, chat or AI replies (pricing intent routes to {C.BOOKING_URL}).", ""]
    rows = []
    for key in ["buyer", "desired_outcome", "actual_service", "included_channels", "deliverable_quantity",
                "implementation_dependencies", "service_term", "separate_media_budget", "client_responsibilities",
                "reporting", "cancellation", "renewal", "remedy"]:
        rows.append([key, o[key]])
    lines += md_table(["Field", "Value"], rows)
    lines += ["", "## Fee (locked CA-J terms)", ""] + [f"- {f}" for f in o["fee"]]
    lines += ["", "## Source example vs CA-J adaptation", ""]
    lines += proof_block(md_table(["Term", "Source example (unverified)", "CA-J adaptation"], [
        ["Service", "YouTube seller leads, editing, appointment setting, software (source example)",
         "Managed HVAC lead generation and follow-up; scope " + NE],
        ["Fee", "$2,000 monthly or $7,800 for six months (source example, unverified instructor price)",
         "Locked CA-J terms: tech fee monthly, setup waived, per booked appointment (see Fee above)"],
        ["Media", "About $50 daily for client YouTube ads (source example, unverified)",
         "Separate client media budget; amount " + NE],
        ["Launch", "Usually 2-3 weeks; depends on client videos (source example)", "Delivery estimate after access and capacity review: " + NE],
        ["Renewal", "No automatic charge after six months (source example)", "Actual agreed renewal terms: " + NE],
        ["Client work", "Record videos, answer calls, attend appointments (source example)", "Supply assets, cover calls, attend estimates, report outcomes"],
    ]))
    lines += ["", "Every headline, form, call guide, payment description and agreement must carry this same commercial promise.", ""]
    return "\n".join(lines)


def build(state) -> list[Path]:
    o = offer(state.config)
    for key in ("included_channels", "deliverable_quantity", "cancellation"):
        state.needs(f"offer: {key}", SRC, "Decide in writing before converting the offer into public copy")
    state.needs("offer: renewal terms", SRC, "Decide renewal terms in writing")
    state.needs("offer: client media budget", SRC, "Agree per client on the strategy call")
    state.needs("offer: launch timeline", SRC, "Quote only what the delivery team can support after capacity review")
    return [state.write(SRC, render(o), "OFFER-SPEC", source="src/offer_spec.py")]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

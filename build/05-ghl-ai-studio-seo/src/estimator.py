"""OPTIONAL phase-2 estimator -> out/estimator/ only. Disabled by default.

With ESTIMATOR_ENABLED = False (the shipped setting) only out/estimator/BLOCKED.md
is written, naming the missing inputs. When a human explicitly enables it, the
output is a clearly labelled SYNTHETIC demonstration: the values below are not
prices, not CA-J terms and not the source's illustrative formula as commercial
rules. A contractor estimator belongs to a separate client project.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, emit, record_blocker  # noqa: E402

MISSING_INPUTS = [
    "service unit", "allowed quantity range", "material rate", "labour assumptions", "travel rule",
    "minimum charge", "tax treatment", "exclusions", "rounding rule", "binding-vs-indicative status",
    "pricing_version", "at least three approved worked examples",
]

SYNTHETIC_DEMO_RULES = {
    "label": "SYNTHETIC DEMONSTRATION - NOT A PRICE - NOT FOR CUSTOMERS",
    "pricing_version": "synthetic-demo-0",
    "currency": "XXX",  # ISO 4217 code reserved for "no currency": deliberately not a real currency
    "binding": False,
    "services": {
        "demo_service": {"unit": "unit", "min_qty": "1", "max_qty": "1000",
                         "material_per_unit": "1.00", "labour_per_unit": "1.00", "equipment_flat": "1.00",
                         "travel_flat": "1.00", "minimum_charge": "10.00", "tax_rate": "0.10",
                         "exclusions": ["synthetic demo only"]},
    },
    "rounding": "ROUND_HALF_UP to 0.01 once, on the final total after tax",
}


class EstimateRejected(ValueError):
    pass


class EstimatorDisabled(RuntimeError):
    pass


@dataclass
class Estimate:
    service: str
    quantity: str
    subtotal: str
    total: str
    currency: str
    pricing_version: str
    label: str
    binding: bool
    exclusions: list


def _decimal(value, name: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise EstimateRejected(f"{name} must be numeric")
    if isinstance(value, float) and not math.isfinite(value):
        raise EstimateRejected(f"{name} must be finite")
    try:
        d = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise EstimateRejected(f"{name} must be numeric") from exc
    if not d.is_finite():
        raise EstimateRejected(f"{name} must be finite")
    return d


def compute_estimate(request: dict, rules: dict) -> Estimate:
    """Validate and recompute server-side. Any browser-supplied total is ignored."""
    service = request.get("service")
    if service not in rules["services"]:
        raise EstimateRejected("unsupported service")
    rule = rules["services"][service]
    if request.get("unit", rule["unit"]) != rule["unit"]:
        raise EstimateRejected("ambiguous or unsupported unit")
    qty = _decimal(request.get("quantity"), "quantity")
    if qty < 0:
        raise EstimateRejected("quantity must not be negative")
    if qty < Decimal(rule["min_qty"]) or qty > Decimal(rule["max_qty"]):
        raise EstimateRejected("quantity outside the allowed range")
    subtotal = (qty * (Decimal(rule["material_per_unit"]) + Decimal(rule["labour_per_unit"]))
                + Decimal(rule["equipment_flat"]) + Decimal(rule["travel_flat"]))
    subtotal = max(subtotal, Decimal(rule["minimum_charge"]))
    total = (subtotal * (Decimal(1) + Decimal(rule["tax_rate"]))).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return Estimate(service, str(qty), str(subtotal), str(total), rules["currency"], rules["pricing_version"],
                    rules["label"], rules["binding"], rule["exclusions"])


def blocked_markdown() -> str:
    lines = ["# Estimator: BLOCKED (optional phase 2)", "",
             "`ESTIMATOR_ENABLED = False`. No approved pricing rules exist. The source's illustrative formula "
             "is not commercial rule data, and CA-J's own commercial terms are internal and never quoted by a "
             "calculator or any customer-facing output (meeting-first). A contractor estimator belongs to a "
             "separate client project.", "", "Missing inputs:", ""]
    lines += [f"- {item}" for item in MISSING_INPUTS]
    lines.append("")
    return "\n".join(lines)


def build(paths: Paths | None = None, enabled: bool = C.ESTIMATOR_ENABLED) -> Path:
    paths = paths or default_paths()
    est_dir = paths.out / "estimator"
    if not enabled:
        record_blocker("estimator", "; ".join(MISSING_INPUTS), "optional estimator (T14)",
                       "Business supplies versioned pricing rules and three worked examples", paths)
        return emit("estimator_blocked", est_dir / "BLOCKED.md", blocked_markdown(), STATUS.BLOCKED, paths,
                    source="src/estimator.py")
    demo = compute_estimate({"service": "demo_service", "quantity": "12", "browser_total": "0.01"},
                            SYNTHETIC_DEMO_RULES)
    return emit("estimator_demo", est_dir / "SYNTHETIC_DEMO.json",
                {"label": SYNTHETIC_DEMO_RULES["label"], "rules": SYNTHETIC_DEMO_RULES, "example": demo.__dict__},
                STATUS.DRAFT, paths, source="src/estimator.py")


if __name__ == "__main__":
    print(build())

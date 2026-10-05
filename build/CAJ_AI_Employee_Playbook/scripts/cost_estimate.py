"""Monthly contribution model for one active AI-employee client (internal only).

contribution = revenue - platform allocation - AI usage - telephony
               - payment fees - support labour

Revenue comes from guardrails/locked_pricing.json (the locked CA&J terms:
monthly tech fee, setup waived, per-booked-appointment range) and the
booked-appointment count in rates.yaml. Costs come from the human-maintained
rates.yaml. Output is internal; it is never rendered into outbound copy.

Usage (from the build root):
    python3 scripts/cost_estimate.py [--rates rates.yaml] [--pricing guardrails/locked_pricing.json]

Exit codes:
    0  contribution non-negative and every rate verified
    1  contribution negative (low end of the per-appointment range)
    2  refused: unlimited usage advertised, or the rates file is malformed
    3  at least one rate (or the appointment count) is still verified: false
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import mini_yaml  # noqa: E402

REQUIRED_CATEGORIES = ("platform_allocation", "ai_usage", "telephony", "payment_fees", "support_labour")
BASES = ("fixed_monthly", "per_unit", "percent_of_revenue")


class RatesError(ValueError):
    pass


@dataclass
class Estimate:
    revenue_low: float
    revenue_high: float
    costs_low: dict[str, float]
    costs_high: dict[str, float]
    unverified: list[str]

    @property
    def contribution_low(self) -> float:
        return self.revenue_low - sum(self.costs_low.values())

    @property
    def contribution_high(self) -> float:
        return self.revenue_high - sum(self.costs_high.values())


def _num(row: dict, key: str, default=None) -> float:
    value = row.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RatesError(f"rate {row.get('name', '?')!r}: {key} must be a number, got {value!r}")
    if value < 0:
        raise RatesError(f"rate {row.get('name', '?')!r}: {key} must not be negative")
    return float(value)


def check_no_unlimited(rates: dict) -> None:
    """Refuse any configuration that implies unlimited usage."""
    def walk(v):
        if isinstance(v, str) and "unlimited" in v.lower():
            raise RatesError("refused: 'unlimited' usage may not be modelled or advertised; set an allowance")
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        if isinstance(v, list):
            for x in v:
                walk(x)
    walk(rates)


def estimate(pricing: dict, rates: dict) -> Estimate:
    check_no_unlimited(rates)
    rows = rates.get("rates")
    if not isinstance(rows, list) or not rows:
        raise RatesError("rates.yaml needs a non-empty 'rates' list")
    appts = rates.get("booked_appointments_per_month", 0)
    if isinstance(appts, bool) or not isinstance(appts, int) or appts < 0:
        raise RatesError("booked_appointments_per_month must be a non-negative integer")

    base = float(pricing["TECH_FEE_MONTHLY_USD"])
    revenue_low = base + appts * float(pricing["PER_BOOKED_APPOINTMENT_MIN_USD"])
    revenue_high = base + appts * float(pricing["PER_BOOKED_APPOINTMENT_MAX_USD"])

    unverified: list[str] = []
    if rates.get("booked_appointments_verified") is not True:
        unverified.append("booked_appointments_per_month")
    costs_low = {c: 0.0 for c in REQUIRED_CATEGORIES}
    costs_high = {c: 0.0 for c in REQUIRED_CATEGORIES}
    seen = set()
    for row in rows:
        name = row.get("name") or "?"
        cat, basis = row.get("category"), row.get("basis")
        if cat not in REQUIRED_CATEGORIES:
            raise RatesError(f"rate {name!r}: category must be one of {REQUIRED_CATEGORIES}")
        if basis not in BASES:
            raise RatesError(f"rate {name!r}: basis must be one of {BASES}")
        amount = _num(row, "amount")
        if basis == "percent_of_revenue":
            if amount > 100:
                raise RatesError(f"rate {name!r}: percentage above 100")
            low, high = revenue_low * amount / 100, revenue_high * amount / 100
        else:
            qty = _num(row, "quantity_per_month")
            low = high = amount * qty
        costs_low[cat] += low
        costs_high[cat] += high
        seen.add(cat)
        if row.get("verified") is not True:
            unverified.append(name)
    missing = [c for c in REQUIRED_CATEGORIES if c not in seen]
    if missing:
        raise RatesError(f"rates.yaml is missing cost categories: {', '.join(missing)}")
    return Estimate(revenue_low, revenue_high, costs_low, costs_high, unverified)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Internal contribution model (never for outbound copy).")
    ap.add_argument("--rates", type=Path, default=ROOT / "rates.yaml")
    ap.add_argument("--pricing", type=Path, default=ROOT / "guardrails" / "locked_pricing.json")
    args = ap.parse_args(argv)

    pricing = json.loads(args.pricing.read_text(encoding="utf-8"))
    try:
        rates = mini_yaml.loads(args.rates.read_text(encoding="utf-8"))
        est = estimate(pricing, rates)
    except (RatesError, mini_yaml.MiniYamlError) as exc:
        print(f"REFUSED: {exc}")
        return 2

    print("INTERNAL ONLY - never quote these figures in outbound copy (MEETING-FIRST).")
    print(f"{'line':<22} {'low':>12} {'high':>12}")
    print(f"{'revenue':<22} {est.revenue_low:>12.2f} {est.revenue_high:>12.2f}")
    for cat in REQUIRED_CATEGORIES:
        print(f"{'- ' + cat:<22} {est.costs_low[cat]:>12.2f} {est.costs_high[cat]:>12.2f}")
    print(f"{'contribution':<22} {est.contribution_low:>12.2f} {est.contribution_high:>12.2f}")

    code = 0
    if est.contribution_low < 0:
        print("FAIL: contribution is negative at the low end of the per-appointment range.")
        code = 1
    if est.unverified:
        print(f"UNVERIFIED: {len(est.unverified)} input(s) not human-verified: {', '.join(est.unverified)}")
        print("The contribution figure above is NOT reliable until every rate is verified.")
        code = code or 3
    if code == 0:
        print("OK: all rates verified and contribution non-negative.")
    return code


if __name__ == "__main__":
    sys.exit(main())

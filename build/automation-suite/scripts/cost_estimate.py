"""Monthly worst-case spend from config/pricing.yaml, compared with SPEND_CAP_USD.

Each vendor row contributes ``unit_cost * worst_case_monthly_units``. A row with
either value null is NEEDS_EVIDENCE: its cost is unknown, so the worst case is
UNBOUNDED. Rows marked ``verified: false`` are reported as unverified even when
a human has filled in numbers.

Exit 1 when the worst case exceeds SPEND_CAP_USD (including UNBOUNDED). Nothing
is purchased; the output is for human sign-off only.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants, yaml_lite  # noqa: E402

REQUIRED_FIELDS = ("id", "unit", "unit_cost", "worst_case_monthly_units", "verified", "source")


class PricingTableError(ValueError):
    pass


@dataclass(frozen=True)
class Line:
    vendor: str
    monthly: Optional[float]
    verified: bool
    reason: str


@dataclass(frozen=True)
class Estimate:
    lines: list[Line]
    known_subtotal: float
    unknown_count: int
    cap: float

    @property
    def unbounded(self) -> bool:
        return self.unknown_count > 0

    @property
    def exceeds_cap(self) -> bool:
        return self.unbounded or self.known_subtotal > self.cap


def _number(value, field_name: str, vendor: str) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise PricingTableError(f"{vendor}: {field_name} must be null or a non-negative number")
    return float(value)


def estimate(table: dict, cap: float = constants.SPEND_CAP_USD) -> Estimate:
    vendors = table.get("vendors")
    if not isinstance(vendors, list) or not vendors:
        raise PricingTableError("pricing table needs a non-empty 'vendors' list")
    lines, subtotal, unknown, seen = [], 0.0, 0, set()
    for row in vendors:
        missing = [f for f in REQUIRED_FIELDS if f not in row]
        if missing:
            raise PricingTableError(f"row {row.get('id')!r} missing {missing}")
        vid = row["id"]
        if vid in seen:
            raise PricingTableError(f"duplicate vendor {vid!r}")
        seen.add(vid)
        if not isinstance(row["verified"], bool):
            raise PricingTableError(f"{vid}: verified must be true/false")
        unit_cost = _number(row["unit_cost"], "unit_cost", vid)
        units = _number(row["worst_case_monthly_units"], "worst_case_monthly_units", vid)
        if unit_cost is None or units is None:
            unknown += 1
            lines.append(Line(vid, None, row["verified"], "NEEDS_EVIDENCE (no unit cost / volume recorded)"))
            continue
        monthly = round(unit_cost * units, 2)
        subtotal += monthly
        lines.append(Line(vid, monthly, row["verified"], "verified" if row["verified"] else "UNVERIFIED figure"))
    return Estimate(lines, round(subtotal, 2), unknown, float(cap))


def render(est: Estimate) -> list[str]:
    out = ["vendor            monthly worst case   status"]
    for line in est.lines:
        amount = f"${line.monthly:,.2f}" if line.monthly is not None else "UNKNOWN"
        out.append(f"{line.vendor:<17} {amount:<20} {line.reason}")
    worst = (f"UNBOUNDED (known subtotal ${est.known_subtotal:,.2f} + {est.unknown_count} vendor(s) NEEDS_EVIDENCE)"
             if est.unbounded else f"${est.known_subtotal:,.2f}")
    out.append(f"Monthly worst case: {worst}")
    out.append(f"SPEND_CAP_USD = {est.cap:.2f}")
    if est.exceeds_cap:
        out.append("RESULT: exceeds SPEND_CAP_USD. No spend is authorized; human approval required "
                   "(docs/COST-AND-APPROVALS.md).")
    else:
        out.append("RESULT: within SPEND_CAP_USD.")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pricing", type=Path, default=ROOT / "config" / "pricing.yaml")
    args = ap.parse_args(argv)
    try:
        est = estimate(yaml_lite.load(args.pricing))
    except (PricingTableError, yaml_lite.YamlLiteError, OSError) as exc:
        print(f"FAIL: {exc}")
        return 2
    for line in render(est):
        print(line)
    return 1 if est.exceeds_cap else 0


if __name__ == "__main__":
    sys.exit(main())

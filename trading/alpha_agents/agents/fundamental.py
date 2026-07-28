"""Valuation and business-quality analyst.

Scores a company on three axes — valuation, growth, quality — and combines
them. The axes are kept separate rather than collapsed into one number so a
cheap-but-deteriorating business and an expensive-but-compounding one do not
look identical.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..models import AnalystView, Evidence, ResearchBundle, Stance
from .base import BaseAnalyst

# Rough cross-sector reference points. They are anchors for a relative score,
# not thresholds anyone should defend as fair value for a specific name.
BENCHMARKS: dict[str, float] = {
    "pe": 20.0,
    "ps": 3.0,
    "ev_ebitda": 14.0,
    "revenue_growth": 0.08,
    "gross_margin": 0.40,
    "net_margin": 0.10,
    "debt_to_equity": 1.0,
    "fcf_yield": 0.04,
    "roe": 0.15,
}


class FundamentalAnalyst(BaseAnalyst):
    name = "fundamental"
    role_description = "an equity research analyst"
    focus = "valuation multiples, growth durability and balance-sheet quality"

    def gather(self, bundle: ResearchBundle) -> dict[str, Any]:
        if bundle.fundamentals is None:
            return {"available": False}

        m = dict(bundle.fundamentals.metrics)
        valuation = _valuation_score(m)
        growth = _growth_score(m)
        quality = _quality_score(m)

        return {
            "available": True,
            "as_of": bundle.fundamentals.as_of.isoformat(),
            "metrics": m,
            "valuation_score": valuation,
            "growth_score": growth,
            "quality_score": quality,
            "composite": round(valuation * 0.4 + growth * 0.3 + quality * 0.3, 3),
        }

    def decide(self, signals: Mapping[str, Any], bundle: ResearchBundle) -> AnalystView:
        if not signals.get("available"):
            return AnalystView(
                analyst=self.name,
                symbol=bundle.symbol,
                stance=Stance.HOLD,
                confidence=0.0,
                rationale="No fundamental data available for this symbol.",
                horizon_days=self.horizon_days,
            )

        metrics: Mapping[str, float] = signals["metrics"]
        composite = float(signals["composite"])
        evidence: list[Evidence] = []

        for key in ("pe", "ps", "revenue_growth", "gross_margin", "debt_to_equity", "fcf_yield"):
            if key in metrics:
                evidence.append(
                    Evidence(key, f"{key} = {_fmt_metric(key, metrics[key])}", metrics[key])
                )

        evidence.append(
            Evidence(
                "sub_scores",
                f"valuation {signals['valuation_score']:+.2f}, "
                f"growth {signals['growth_score']:+.2f}, "
                f"quality {signals['quality_score']:+.2f}",
            )
        )

        if abs(composite) < 0.25:
            stance, confidence = Stance.HOLD, 0.2 + abs(composite) * 0.4
        else:
            stance = Stance.BUY if composite > 0 else Stance.SELL
            confidence = 0.4 + min(abs(composite), 1.5) * 0.25

        # A leveraged balance sheet caps how much conviction the rest earns.
        dte = metrics.get("debt_to_equity")
        if dte is not None and dte > 2.5 and stance is Stance.BUY:
            confidence *= 0.75
            evidence.append(
                Evidence("leverage_warning", f"debt/equity {dte:.1f} caps conviction", dte)
            )

        return AnalystView(
            analyst=self.name,
            symbol=bundle.symbol,
            stance=stance,
            confidence=round(min(confidence, 1.0), 3),
            rationale=(
                f"Composite fundamental score {composite:+.2f} "
                f"(valuation {signals['valuation_score']:+.2f}, "
                f"growth {signals['growth_score']:+.2f}, "
                f"quality {signals['quality_score']:+.2f}). "
                f"Reads as {stance.value.upper()} on the business, "
                "before any price consideration."
            ),
            evidence=tuple(evidence),
            horizon_days=self.horizon_days,
        )


def _valuation_score(m: Mapping[str, float]) -> float:
    """Positive means cheap relative to the reference multiple."""
    score, weight = 0.0, 0.0
    for key in ("pe", "ps", "ev_ebitda"):
        value = m.get(key)
        if value is None or value <= 0:
            continue
        bench = BENCHMARKS[key]
        score += _bounded((bench - value) / bench, 1.0)
        weight += 1
    fcf = m.get("fcf_yield")
    if fcf is not None:
        score += _bounded((fcf - BENCHMARKS["fcf_yield"]) / BENCHMARKS["fcf_yield"], 1.0)
        weight += 1
    return round(score / weight, 3) if weight else 0.0


def _growth_score(m: Mapping[str, float]) -> float:
    growth = m.get("revenue_growth")
    if growth is None:
        return 0.0
    return round(_bounded((growth - BENCHMARKS["revenue_growth"]) / 0.15, 1.5), 3)


def _quality_score(m: Mapping[str, float]) -> float:
    score, weight = 0.0, 0.0
    for key in ("gross_margin", "net_margin", "roe"):
        value = m.get(key)
        if value is None:
            continue
        bench = BENCHMARKS[key]
        score += _bounded((value - bench) / bench, 1.0)
        weight += 1
    dte = m.get("debt_to_equity")
    if dte is not None:
        # Leverage above the benchmark subtracts; below it adds, but modestly.
        score += _bounded((BENCHMARKS["debt_to_equity"] - dte) / 2.0, 0.75)
        weight += 1
    return round(score / weight, 3) if weight else 0.0


def _bounded(value: float, limit: float) -> float:
    return max(-limit, min(limit, value))


def _fmt_metric(key: str, value: float) -> str:
    if key in {"revenue_growth", "gross_margin", "net_margin", "fcf_yield", "roe"}:
        return f"{value:.1%}"
    return f"{value:.2f}"

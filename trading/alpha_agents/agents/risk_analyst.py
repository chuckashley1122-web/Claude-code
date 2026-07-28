"""The dissenting seat on the committee.

This analyst does not look for reasons to trade. Its job is to state, in
numbers, how the position could hurt — and to raise flags that the moderator
must weigh explicitly. A committee of three bulls reaches consensus quickly and
is wrong together; this seat exists to make that harder.

Its stance is HOLD by default and only turns SELL when the risk picture is bad
enough to argue against holding the name at all. It is not a directional view.
"""

from __future__ import annotations

from typing import Any, Mapping

from .. import indicators as ind
from ..models import AnalystView, Evidence, ResearchBundle, Stance
from .base import BaseAnalyst, last_defined

FLAG_PREFIX = "flag:"
"""Evidence labelled with this prefix is promoted to a verdict-level risk flag."""


class RiskAnalyst(BaseAnalyst):
    name = "risk"
    role_description = "a risk officer"
    focus = (
        "downside: realised volatility, drawdown, gap risk, liquidity and how "
        "wrong this position could go"
    )

    def __init__(self, *args: Any, vol_ceiling: float = 0.60, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.vol_ceiling = vol_ceiling

    def gather(self, bundle: ResearchBundle) -> dict[str, Any]:
        closes = list(bundle.prices.closes)
        if len(closes) < 30:
            return {"bars": len(closes), "insufficient_history": True}

        vol = last_defined(ind.realized_volatility(closes, 20))
        vol60 = last_defined(ind.realized_volatility(closes, 60))
        atr14 = last_defined(ind.atr(bundle.prices, 14))
        price = closes[-1]
        returns = _returns(closes)

        return {
            "bars": len(closes),
            "price": price,
            "annualized_vol_20d": vol,
            "annualized_vol_60d": vol60,
            "vol_ratio_20_over_60": (vol / vol60) if vol and vol60 else None,
            "atr_pct_of_price": (atr14 / price) if atr14 and price else None,
            "max_drawdown": ind.max_drawdown(closes),
            "worst_1d_return": min(returns) if returns else None,
            "best_1d_return": max(returns) if returns else None,
            "gap_days_over_5pct": sum(1 for r in returns[-60:] if abs(r) > 0.05),
            "downside_days_pct": (
                sum(1 for r in returns[-60:] if r < 0) / min(60, len(returns))
                if returns
                else None
            ),
            "avg_volume_20d": _mean(list(bundle.prices.volumes)[-20:]),
        }

    def decide(self, signals: Mapping[str, Any], bundle: ResearchBundle) -> AnalystView:
        if signals.get("insufficient_history"):
            return AnalystView(
                analyst=self.name,
                symbol=bundle.symbol,
                stance=Stance.HOLD,
                confidence=0.4,
                rationale=(
                    f"Only {signals.get('bars', 0)} bars — too little history to "
                    "characterise the downside. Treat any position as unsized."
                ),
                evidence=(Evidence(f"{FLAG_PREFIX}thin_history", "insufficient price history"),),
                horizon_days=self.horizon_days,
            )

        evidence: list[Evidence] = []
        severity = 0.0

        vol = signals.get("annualized_vol_20d")
        if vol is not None:
            evidence.append(Evidence("realized_vol", f"20-day annualised {vol:.0%}", vol))
            if vol > self.vol_ceiling:
                severity += 1.0
                evidence.append(
                    Evidence(
                        f"{FLAG_PREFIX}high_volatility",
                        f"realised vol {vol:.0%} above the {self.vol_ceiling:.0%} ceiling",
                        vol,
                    )
                )

        ratio = signals.get("vol_ratio_20_over_60")
        if ratio is not None and ratio > 1.5:
            severity += 0.6
            evidence.append(
                Evidence(
                    f"{FLAG_PREFIX}vol_expanding",
                    f"short-term vol is {ratio:.1f}x the 60-day — regime is shifting",
                    ratio,
                )
            )

        dd = signals.get("max_drawdown")
        if dd is not None:
            evidence.append(Evidence("max_drawdown", f"historic peak-to-trough {dd:.0%}", dd))
            if dd > 0.40:
                severity += 0.7
                evidence.append(
                    Evidence(
                        f"{FLAG_PREFIX}deep_drawdown_history",
                        f"has drawn down {dd:.0%} before; size for that, not for the average",
                        dd,
                    )
                )

        gaps = signals.get("gap_days_over_5pct", 0)
        if gaps and gaps >= 5:
            severity += 0.5
            evidence.append(
                Evidence(
                    f"{FLAG_PREFIX}gap_prone",
                    f"{gaps} moves over 5% in the last 60 sessions — stops will slip",
                    float(gaps),
                )
            )

        worst = signals.get("worst_1d_return")
        if worst is not None and worst < -0.12:
            severity += 0.4
            evidence.append(
                Evidence(
                    f"{FLAG_PREFIX}tail_risk",
                    f"worst single session {worst:.1%}",
                    worst,
                )
            )

        # Only an extreme risk picture argues outright against the position.
        if severity >= 2.0:
            stance = Stance.SELL
            confidence = min(0.45 + (severity - 2.0) * 0.15, 0.85)
            summary = "Risk is severe enough to argue against holding this name."
        else:
            stance = Stance.HOLD
            confidence = min(0.3 + severity * 0.15, 0.7)
            summary = (
                "Risk is tolerable at a reduced size."
                if severity > 0
                else "Nothing unusual in the risk profile."
            )

        return AnalystView(
            analyst=self.name,
            symbol=bundle.symbol,
            stance=stance,
            confidence=round(confidence, 3),
            rationale=(
                f"Risk severity {severity:.1f} across "
                f"{sum(1 for e in evidence if e.label.startswith(FLAG_PREFIX))} flags. "
                f"{summary}"
            ),
            evidence=tuple(evidence),
            horizon_days=self.horizon_days,
        )


def _returns(closes: list[float]) -> list[float]:
    return [
        (closes[i] - closes[i - 1]) / closes[i - 1]
        for i in range(1, len(closes))
        if closes[i - 1] > 0
    ]


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None

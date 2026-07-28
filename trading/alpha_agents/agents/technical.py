"""Price-and-volume analyst: trend, momentum, mean reversion, volatility."""

from __future__ import annotations

from typing import Any, Mapping

from .. import indicators as ind
from ..models import AnalystView, Evidence, ResearchBundle, Stance
from .base import BaseAnalyst, last_defined

MIN_BARS = 60
"""Below this there is not enough history for the slow averages to mean anything."""


class TechnicalAnalyst(BaseAnalyst):
    name = "technical"
    role_description = "a technical analyst"
    focus = (
        "price action, trend structure, momentum, mean reversion and realised "
        "volatility"
    )

    def gather(self, bundle: ResearchBundle) -> dict[str, Any]:
        closes = list(bundle.prices.closes)
        if len(closes) < MIN_BARS:
            return {"bars": len(closes), "insufficient_history": True}

        price = closes[-1]
        sma20 = last_defined(ind.sma(closes, 20))
        sma50 = last_defined(ind.sma(closes, 50))
        sma200 = last_defined(ind.sma(closes, 200)) if len(closes) >= 200 else None
        rsi14 = last_defined(ind.rsi(closes, 14))
        macd_line, signal_line, hist = ind.macd(closes)
        upper, mid, lower = ind.bollinger(closes, 20, 2.0)
        atr14 = last_defined(ind.atr(bundle.prices, 14))
        vol = last_defined(ind.realized_volatility(closes, 20))
        mom20 = last_defined(ind.momentum(closes, 20))
        mom60 = last_defined(ind.momentum(closes, 60))

        band_position = None
        band_up, band_low = last_defined(upper), last_defined(lower)
        if band_up is not None and band_low is not None and band_up > band_low:
            band_position = (price - band_low) / (band_up - band_low)

        return {
            "bars": len(closes),
            "price": price,
            "sma20": sma20,
            "sma50": sma50,
            "sma200": sma200,
            "price_vs_sma50_pct": _pct(price, sma50),
            "sma20_vs_sma50_pct": _pct(sma20, sma50),
            "rsi14": rsi14,
            "macd_hist": last_defined(hist),
            "macd_line": last_defined(macd_line),
            "bollinger_position": band_position,
            "atr14": atr14,
            "atr_pct_of_price": (atr14 / price) if atr14 and price else None,
            "annualized_vol": vol,
            "momentum_20d": mom20,
            "momentum_60d": mom60,
            "drawdown_from_high": _drawdown_from_high(closes),
        }

    def decide(self, signals: Mapping[str, Any], bundle: ResearchBundle) -> AnalystView:
        if signals.get("insufficient_history"):
            return AnalystView(
                analyst=self.name,
                symbol=bundle.symbol,
                stance=Stance.HOLD,
                confidence=0.0,
                rationale=(
                    f"Only {signals.get('bars', 0)} bars of history; "
                    f"need {MIN_BARS} before the trend signals are meaningful."
                ),
                horizon_days=self.horizon_days,
            )

        score = 0.0
        evidence: list[Evidence] = []

        # Trend: price above a rising 50-day is the backbone of the read.
        p_vs_50 = signals.get("price_vs_sma50_pct")
        if p_vs_50 is not None:
            score += _bounded(p_vs_50 * 8, 1.5)
            evidence.append(
                Evidence("price_vs_sma50", f"{p_vs_50:+.1%} vs 50-day average", p_vs_50)
            )

        s20_vs_50 = signals.get("sma20_vs_sma50_pct")
        if s20_vs_50 is not None:
            score += _bounded(s20_vs_50 * 10, 1.0)
            evidence.append(
                Evidence("ma_structure", f"20-day is {s20_vs_50:+.1%} vs 50-day", s20_vs_50)
            )

        # Momentum confirmation.
        mom60 = signals.get("momentum_60d")
        if mom60 is not None:
            score += _bounded(mom60 * 4, 1.0)
            evidence.append(Evidence("momentum_60d", f"{mom60:+.1%} over 60 bars", mom60))

        # MACD histogram: agreement adds a little, it is not a primary signal.
        hist = signals.get("macd_hist")
        if hist is not None and signals.get("price"):
            normalised = hist / signals["price"]
            score += _bounded(normalised * 200, 0.7)
            evidence.append(Evidence("macd_hist", f"histogram {hist:+.3f}", hist))

        # RSI as a fade, not a trigger: extremes argue against chasing.
        rsi = signals.get("rsi14")
        if rsi is not None:
            if rsi > 75:
                score -= 0.8
                evidence.append(Evidence("rsi14", f"overbought at {rsi:.0f}", rsi))
            elif rsi < 25:
                score += 0.8
                evidence.append(Evidence("rsi14", f"oversold at {rsi:.0f}", rsi))
            else:
                evidence.append(Evidence("rsi14", f"neutral at {rsi:.0f}", rsi))

        stance, confidence = _score_to_view(score)

        # High realised volatility means the same score is worth less.
        vol = signals.get("annualized_vol")
        if vol and vol > 0.60:
            confidence *= 0.7
            evidence.append(
                Evidence("volatility", f"elevated realised vol {vol:.0%}, view discounted", vol)
            )

        return AnalystView(
            analyst=self.name,
            symbol=bundle.symbol,
            stance=stance,
            confidence=round(min(confidence, 1.0), 3),
            rationale=_rationale(stance, score, signals),
            evidence=tuple(evidence),
            horizon_days=self.horizon_days,
        )


def _rationale(stance: Stance, score: float, signals: Mapping[str, Any]) -> str:
    parts = [f"Composite trend/momentum score {score:+.2f}."]
    p_vs_50 = signals.get("price_vs_sma50_pct")
    if p_vs_50 is not None:
        side = "above" if p_vs_50 >= 0 else "below"
        parts.append(f"Price sits {abs(p_vs_50):.1%} {side} its 50-day average.")
    rsi = signals.get("rsi14")
    if rsi is not None:
        parts.append(f"RSI {rsi:.0f}.")
    dd = signals.get("drawdown_from_high")
    if dd:
        parts.append(f"{dd:.1%} below the trailing high.")
    parts.append(f"Reads as {stance.value.upper()} on price action alone.")
    return " ".join(parts)


def _pct(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return (a - b) / b


def _bounded(value: float, limit: float) -> float:
    return max(-limit, min(limit, value))


def _score_to_view(score: float) -> tuple[Stance, float]:
    """Map a signed composite score onto a stance plus calibrated confidence.

    The dead zone around zero is intentional: a weak score is genuinely a hold,
    and forcing it into a direction is how a strategy trades noise.
    """
    magnitude = abs(score)
    if magnitude < 0.5:
        return Stance.HOLD, min(0.35, 0.15 + magnitude * 0.3)
    stance = Stance.BUY if score > 0 else Stance.SELL
    confidence = 0.45 + min(magnitude - 0.5, 2.5) * 0.16
    return stance, confidence


def _drawdown_from_high(closes: list[float]) -> float | None:
    if not closes:
        return None
    peak = max(closes)
    if peak <= 0:
        return None
    return (peak - closes[-1]) / peak

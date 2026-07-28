"""Builders for price series with a known, deliberate shape.

The synthetic provider is random-walk by design, which is right for end-to-end
runs but useless for asserting that an analyst reacts to a trend: you cannot
test "detects an uptrend" against data that may not contain one. These helpers
produce series whose shape is stipulated, so a failing assertion means the
analyst is wrong rather than the data being unlucky.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta

from trading.alpha_agents.models import (
    Bar,
    Fundamentals,
    NewsItem,
    PriceSeries,
    ResearchBundle,
)

START = date(2024, 1, 1)


def _bar(day: date, close: float, prev_close: float) -> Bar:
    """A candle around ``close`` that satisfies the Bar invariants."""
    open_ = prev_close
    high = max(open_, close) * 1.005
    low = min(open_, close) * 0.995
    return Bar(ts=day, open=open_, high=high, low=low, close=close, volume=1_000_000)


def series_from_closes(symbol: str, closes: list[float]) -> PriceSeries:
    bars: list[Bar] = []
    day = START
    prev = closes[0]
    for close in closes:
        while day.weekday() >= 5:
            day += timedelta(days=1)
        bars.append(_bar(day, close, prev))
        prev = close
        day += timedelta(days=1)
    return PriceSeries(symbol, tuple(bars))


def uptrend(symbol: str = "UP", n: int = 260, daily: float = 0.004) -> PriceSeries:
    """Steady compounding advance — unambiguously bullish price action."""
    return series_from_closes(symbol, [100.0 * (1 + daily) ** i for i in range(n)])


def downtrend(symbol: str = "DOWN", n: int = 260, daily: float = 0.004) -> PriceSeries:
    return series_from_closes(symbol, [100.0 * (1 - daily) ** i for i in range(n)])


def flat(symbol: str = "FLAT", n: int = 260, level: float = 100.0) -> PriceSeries:
    """Perfectly flat. Every indicator's degenerate case at once."""
    return series_from_closes(symbol, [level] * n)


def choppy(symbol: str = "CHOP", n: int = 260, amplitude: float = 0.25) -> PriceSeries:
    """Violent oscillation: high realised volatility, no net direction."""
    return series_from_closes(
        symbol, [100.0 * (1 + amplitude * math.sin(i / 3.0)) for i in range(n)]
    )


def fundamentals(symbol: str = "TEST", **metrics: float) -> Fundamentals:
    base = {
        "pe": 20.0,
        "ps": 3.0,
        "revenue_growth": 0.08,
        "gross_margin": 0.40,
        "net_margin": 0.10,
        "debt_to_equity": 1.0,
        "fcf_yield": 0.04,
        "roe": 0.15,
    }
    base.update(metrics)
    return Fundamentals(symbol=symbol, as_of=START, metrics=base)


def news(*headlines: str, symbol: str = "TEST") -> tuple[NewsItem, ...]:
    return tuple(
        NewsItem(
            ts=datetime(2024, 1, 1) + timedelta(hours=i),
            headline=h,
            summary="",
            source="test",
        )
        for i, h in enumerate(headlines)
    )


def bundle(
    prices: PriceSeries,
    *,
    symbol: str | None = None,
    funda: Fundamentals | None = None,
    items: tuple[NewsItem, ...] = (),
) -> ResearchBundle:
    sym = symbol or prices.symbol
    return ResearchBundle(
        symbol=sym,
        as_of=prices.last.ts if len(prices) else START,
        prices=prices,
        fundamentals=funda,
        news=items,
    )

"""Technical indicators over plain sequences of floats.

Pure functions, no state, standard library only: these run inside the backtest
loop, where a hidden rolling buffer would be a look-ahead hazard and a heavy
numeric dependency would be a deployment one.

Every series-returning function hands back a list the *same length* as its
input, with ``None`` in the leading positions where the indicator is not yet
defined. Shortening the output would force every caller to re-derive the offset
before zipping results against bars — the exact bug that silently misaligns a
signal with the price it was computed from.
"""

from __future__ import annotations

import math
from typing import Sequence

from .models import PriceSeries


def _require_period(period: int, *, name: str = "period", minimum: int = 1) -> None:
    """Reject nonsense windows up front: a bad period corrupts every later bar."""
    if period < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {period}")


def _mean(values: Sequence[float]) -> float:
    return math.fsum(values) / len(values)


def _stdev(values: Sequence[float], *, sample: bool) -> float:
    """Standard deviation, population or sample.

    Bollinger bands are conventionally population; risk statistics estimate an
    unknown distribution and so use the sample (n-1) form.
    """
    n = len(values)
    divisor = n - 1 if sample else n
    if divisor <= 0:
        return 0.0
    mu = _mean(values)
    return math.sqrt(math.fsum((v - mu) ** 2 for v in values) / divisor)


def sma(values: Sequence[float], period: int) -> list[float | None]:
    """Simple moving average."""
    _require_period(period)
    vals = list(values)
    out: list[float | None] = [None] * len(vals)
    for i in range(period - 1, len(vals)):
        out[i] = _mean(vals[i - period + 1 : i + 1])
    return out


def ema(values: Sequence[float], period: int) -> list[float | None]:
    """Exponential moving average, seeded with the SMA of the first window.

    Seeding from the SMA (rather than the first value) is what makes the result
    reproducible across differing history lengths — a live run and a backtest
    that start on different dates converge to the same number.
    """
    _require_period(period)
    vals = list(values)
    out: list[float | None] = [None] * len(vals)
    if len(vals) < period:
        return out
    k = 2.0 / (period + 1)
    level = _mean(vals[:period])
    out[period - 1] = level
    for i in range(period, len(vals)):
        level = (vals[i] - level) * k + level
        out[i] = level
    return out


def _rsi_value(avg_gain: float, avg_loss: float) -> float:
    """RSI from its two smoothed averages, with the zero-loss case pinned.

    A window with no losses has an infinite relative strength; convention caps
    it at 100. A window with neither gains nor losses (a flat series) has no
    direction at all, so it sits at the neutral midpoint instead of pretending
    to be maximally overbought.
    """
    if avg_loss == 0.0:
        return 100.0 if avg_gain > 0.0 else 50.0
    return 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)


def rsi(values: Sequence[float], period: int = 14) -> list[float | None]:
    """Relative strength index using Wilder's smoothing."""
    _require_period(period)
    vals = list(values)
    n = len(vals)
    out: list[float | None] = [None] * n
    if n <= period:
        return out

    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, n):
        change = vals[i] - vals[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    avg_gain = _mean(gains[:period])
    avg_loss = _mean(losses[:period])
    out[period] = _rsi_value(avg_gain, avg_loss)
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        out[i] = _rsi_value(avg_gain, avg_loss)
    return out


def macd(
    values: Sequence[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    """MACD line, signal line and histogram.

    The signal EMA is seeded from the first *defined* MACD value, not from the
    ``None`` padding, which is why it is computed on the compacted line and then
    written back at the original offsets.
    """
    _require_period(fast, name="fast")
    _require_period(slow, name="slow")
    _require_period(signal, name="signal")
    if fast >= slow:
        raise ValueError(f"fast period {fast} must be shorter than slow period {slow}")

    vals = list(values)
    n = len(vals)
    fast_ema = ema(vals, fast)
    slow_ema = ema(vals, slow)

    line: list[float | None] = [None] * n
    for i in range(n):
        f, s = fast_ema[i], slow_ema[i]
        if f is not None and s is not None:
            line[i] = f - s

    defined = [v for v in line if v is not None]
    offset = n - len(defined)
    signal_line: list[float | None] = [None] * n
    for i, v in enumerate(ema(defined, signal)):
        signal_line[offset + i] = v

    histogram: list[float | None] = [None] * n
    for i in range(n):
        m, s = line[i], signal_line[i]
        if m is not None and s is not None:
            histogram[i] = m - s
    return line, signal_line, histogram


def bollinger(
    values: Sequence[float],
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    """Bollinger bands as ``(upper, mid, lower)``; population standard deviation."""
    _require_period(period)
    if num_std < 0:
        raise ValueError(f"num_std must be >= 0, got {num_std}")

    vals = list(values)
    n = len(vals)
    mid = sma(vals, period)
    upper: list[float | None] = [None] * n
    lower: list[float | None] = [None] * n
    for i in range(period - 1, n):
        window = vals[i - period + 1 : i + 1]
        centre = mid[i]
        assert centre is not None  # sma is defined wherever the window is full
        spread = num_std * _stdev(window, sample=False)
        upper[i] = centre + spread
        lower[i] = centre - spread
    return upper, mid, lower


def true_range(series: PriceSeries) -> list[float | None]:
    """Per-bar true range.

    The first bar has no prior close, so it is ``None`` rather than a bare
    high-low: substituting the smaller quantity would bias the first ATR low.
    """
    bars = series.bars
    out: list[float | None] = [None] * len(bars)
    for i in range(1, len(bars)):
        bar = bars[i]
        prev_close = bars[i - 1].close
        out[i] = max(
            bar.high - bar.low,
            abs(bar.high - prev_close),
            abs(bar.low - prev_close),
        )
    return out


def atr(series: PriceSeries, period: int = 14) -> list[float | None]:
    """Average true range, Wilder-smoothed over :func:`true_range`."""
    _require_period(period)
    ranges = true_range(series)
    n = len(ranges)
    out: list[float | None] = [None] * n
    if n < period + 1:  # bar 0 contributes no range, so we need one extra bar
        return out

    seed = [r for r in ranges[1 : period + 1] if r is not None]
    level = _mean(seed)
    out[period] = level
    for i in range(period + 1, n):
        current = ranges[i]
        assert current is not None  # only index 0 is undefined
        level = (level * (period - 1) + current) / period
        out[i] = level
    return out


def realized_volatility(
    values: Sequence[float],
    period: int = 20,
    annualize: bool = True,
    periods_per_year: int = 252,
) -> list[float | None]:
    """Rolling standard deviation of log returns, optionally annualised.

    Sample (n-1) deviation, because this estimates an unknown return
    distribution rather than describing a fixed window — hence ``period >= 2``.
    Non-positive prices have no log return, so windows touching them stay
    ``None`` instead of raising.
    """
    _require_period(period, minimum=2)
    _require_period(periods_per_year, name="periods_per_year")

    vals = list(values)
    n = len(vals)
    out: list[float | None] = [None] * n
    if n <= period:
        return out

    log_returns: list[float | None] = [None] * n
    for i in range(1, n):
        prev, current = vals[i - 1], vals[i]
        if prev > 0 and current > 0:
            log_returns[i] = math.log(current / prev)

    scale = math.sqrt(periods_per_year) if annualize else 1.0
    for i in range(period, n):
        window = log_returns[i - period + 1 : i + 1]
        if any(r is None for r in window):
            continue
        out[i] = _stdev([r for r in window if r is not None], sample=True) * scale
    return out


def max_drawdown(values: Sequence[float]) -> float:
    """Worst peak-to-trough decline, as a positive fraction (0.2 == -20%)."""
    vals = list(values)
    if len(vals) < 2:
        return 0.0
    peak = vals[0]
    worst = 0.0
    for v in vals:
        if v > peak:
            peak = v
        if peak > 0:  # a non-positive peak makes the fraction meaningless
            worst = max(worst, (peak - v) / peak)
    return worst


def sharpe(
    returns: Sequence[float],
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """Annualised Sharpe ratio. ``risk_free_rate`` is an annual rate.

    Returns 0.0 rather than raising when the ratio is undefined (fewer than two
    observations, or no dispersion) so that callers can rank strategies without
    special-casing degenerate ones.
    """
    _require_period(periods_per_year, name="periods_per_year")
    rets = list(returns)
    if len(rets) < 2:
        return 0.0
    per_period_rf = risk_free_rate / periods_per_year
    excess = [r - per_period_rf for r in rets]
    deviation = _stdev(excess, sample=True)
    if deviation == 0.0:
        return 0.0
    return _mean(excess) / deviation * math.sqrt(periods_per_year)


def momentum(values: Sequence[float], period: int) -> list[float | None]:
    """Fractional return over the trailing ``period`` bars."""
    _require_period(period)
    vals = list(values)
    out: list[float | None] = [None] * len(vals)
    for i in range(period, len(vals)):
        base = vals[i - period]
        if base == 0:  # undefined rather than infinite
            continue
        out[i] = (vals[i] - base) / base
    return out

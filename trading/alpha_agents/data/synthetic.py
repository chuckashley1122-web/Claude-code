"""Offline, deterministic market data.

This is the default provider on purpose. Every demo, test and CI run needs
price history that is identical on every machine and does not depend on a
vendor being reachable — so the series here is generated from a hash of the
symbol rather than fetched.

Two properties matter more than realism:

* **Determinism.** ``SyntheticProvider("X").prices("AAPL", a, b)`` returns the
  same bars today, tomorrow and on a colleague's laptop.
* **Window independence.** The walk always starts at a fixed epoch, so the bar
  for a given date is the same whether the caller asked for one month or ten
  years of history. Without that, a backtest that re-requests data with a
  different start would silently see a different world.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from ..models import Bar, Fundamentals, NewsItem, PriceSeries

_EPOCH = date(2010, 1, 1)
"""Anchor for every walk. Fixed so results never depend on the requested window."""

_PRICE_ANCHOR = date(2024, 1, 1)
"""Date the per-symbol price level is calibrated to.

The walk starts at the epoch, so a name with strong drift would be worth a
five-figure share price by now and one with negative drift would grind into the
floor. Discounting the starting price back from this anchor keeps quotes in a
believable range across the window anyone actually backtests.
"""

_TRADING_DAYS = 252
"""Trading days per year, used to scale annual drift/vol down to one bar."""

_MIN_PRICE = 1.0
"""Floor on the walk. A real issuer would reverse-split long before this, and it
keeps prices strictly positive so ``Bar`` never sees a non-positive level."""

_HEADLINES = (
    "{symbol} beats quarterly estimates as margins expand",
    "{symbol} guides below consensus on softer demand",
    "Analysts raise price target on {symbol} after channel checks",
    "{symbol} announces buyback and dividend increase",
    "Supply chain costs weigh on {symbol} outlook",
    "{symbol} unveils new product line at annual event",
    "Regulator opens inquiry touching {symbol}'s core market",
    "{symbol} names new chief financial officer",
    "Insiders trim holdings in {symbol}, filings show",
    "{symbol} expands into adjacent market with tuck-in acquisition",
)

_SOURCES = ("Reuters", "Bloomberg", "Dow Jones", "AP", "Barron's")


def _stable_hash(text: str) -> int:
    """A hash that survives process restarts.

    ``hash()`` is salted per interpreter run, which would make "deterministic"
    true only within a single process. SHA-256 is not.
    """
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def _rng(*parts: object) -> random.Random:
    """A generator seeded off the joined parts, independent of every other stream."""
    return random.Random("|".join(str(p) for p in parts))


def _last_quarter_end(when: date) -> date:
    """The most recent quarter end strictly before ``when``'s quarter.

    Fundamentals only move when someone files, and nobody has filed for the
    quarter still in progress. Pinning to the previous quarter end keeps the
    metrics stable through a quarter *and* keeps them point-in-time honest.
    """
    quarter_first_month = ((when.month - 1) // 3) * 3 + 1
    return date(when.year, quarter_first_month, 1) - timedelta(days=1)


@dataclass
class _Walk:
    """Resumable state of one symbol's random walk.

    Mutable and private: it is a memo, not part of the value model.
    """

    rng: random.Random
    bars: list[Bar]
    close: float
    cursor: date


class SyntheticProvider:
    """Generates reproducible OHLCV history, fundamentals and news.

    ``seed`` shifts the whole universe to a different draw, which is useful for
    checking that a strategy is not overfit to one particular fake world.

    History begins at :data:`_EPOCH` and runs Monday to Friday with no holiday
    calendar — a request before the epoch simply returns fewer bars.
    """

    name = "synthetic"
    # The generator derives fundamentals from the quarter preceding
    # ``as_of``, so they are genuinely sliceable through history.
    point_in_time_fundamentals = True

    def __init__(self, seed: int = 1729, annual_volume: float = 5_000_000.0) -> None:
        self.seed = seed
        self.annual_volume = annual_volume
        # Bars generated so far per symbol, plus the live walk state, so that a
        # backtest calling prices() once per day does not regenerate from the
        # epoch every time. Keyed by symbol; always a prefix of the same walk.
        self._walks: dict[str, _Walk] = {}

    # -- MarketDataProvider ------------------------------------------------

    def prices(self, symbol: str, start: date, end: date) -> PriceSeries:
        """Daily bars for ``symbol`` in ``[start, end]``, weekdays only."""
        if start > end:
            raise ValueError(f"{symbol}: start {start} is after end {end}")
        bars = tuple(b for b in self._bars_through(symbol, end) if start <= b.ts <= end)
        return PriceSeries(symbol, bars)

    def fundamentals(self, symbol: str, as_of: date) -> Fundamentals | None:
        """Plausible metrics, fixed for the last quarter that could have been filed."""
        as_of_quarter = _last_quarter_end(as_of)
        rng = _rng(symbol, self.seed, "fundamentals", as_of_quarter.isoformat())

        # One "quality" factor drives the rest, so the numbers hang together:
        # a high-quality name gets fat margins *and* a rich multiple rather
        # than an incoherent mix that no analyst would ever see.
        quality = rng.random()
        gross_margin = 0.25 + 0.50 * quality + rng.uniform(-0.04, 0.04)
        net_margin = gross_margin * (0.15 + 0.35 * quality) + rng.uniform(-0.01, 0.01)
        revenue_growth = -0.05 + 0.35 * quality + rng.uniform(-0.05, 0.05)
        metrics = {
            "pe": round(9.0 + 40.0 * quality + rng.uniform(-3.0, 3.0), 2),
            "ps": round(0.8 + 11.0 * quality**1.5 + rng.uniform(-0.3, 0.3), 2),
            "revenue_growth": round(revenue_growth, 4),
            "gross_margin": round(gross_margin, 4),
            "net_margin": round(max(net_margin, -0.10), 4),
            "debt_to_equity": round(rng.uniform(0.0, 2.2) * (1.3 - quality), 3),
            "fcf_yield": round(0.01 + 0.06 * (1.0 - quality) + rng.uniform(-0.005, 0.005), 4),
            "roe": round(0.03 + 0.32 * quality + rng.uniform(-0.02, 0.02), 4),
        }
        return Fundamentals(symbol=symbol, as_of=as_of_quarter, metrics=metrics)

    def news(self, symbol: str, as_of: date, lookback_days: int = 7) -> tuple[NewsItem, ...]:
        """A handful of headlines inside ``(as_of - lookback_days, as_of]``.

        Newest first, which is the order a human would scan them in.
        """
        if lookback_days <= 0:
            return ()
        rng = _rng(symbol, self.seed, "news", as_of.isoformat(), lookback_days)
        window_start = as_of - timedelta(days=lookback_days - 1)

        count = rng.randint(2, 4)
        templates = rng.sample(_HEADLINES, count)
        items: list[NewsItem] = []
        for template in templates:
            offset = rng.randrange(lookback_days)
            day = window_start + timedelta(days=offset)
            published = time(hour=rng.randrange(6, 20), minute=rng.randrange(60))
            stamp = datetime.combine(day, published)
            source = rng.choice(_SOURCES)
            items.append(
                NewsItem(
                    ts=stamp,
                    headline=template.format(symbol=symbol),
                    summary=f"Synthetic coverage of {symbol} generated for offline runs.",
                    source=source,
                )
            )
        items.sort(key=lambda item: item.ts, reverse=True)
        return tuple(items)

    # -- walk generation ---------------------------------------------------

    def _params(self, symbol: str) -> tuple[float, float, float, float]:
        """Starting price, annual drift, annual vol and average volume.

        Derived from a stable hash of the symbol so two providers with the same
        seed agree without sharing any state.
        """
        rng = _rng(_stable_hash(symbol.upper()), self.seed, "params")
        anchor_price = 15.0 + rng.random() ** 2 * 385.0
        drift = rng.uniform(-0.06, 0.22)
        volatility = rng.uniform(0.14, 0.55)
        volume = self.annual_volume * rng.uniform(0.2, 3.0)

        years = (_PRICE_ANCHOR - _EPOCH).days / 365.25
        start_price = max(round(anchor_price * math.exp(-drift * years), 2), _MIN_PRICE)
        return start_price, drift, volatility, volume

    def _bars_through(self, symbol: str, end: date) -> list[Bar]:
        """All bars from the epoch through ``end``, extending the cached walk.

        The walk state carries the *unrounded* close: resuming from the rounded
        bar would make an extended walk diverge from one generated in a single
        pass, and window independence would quietly stop holding.
        """
        start_price, drift, volatility, volume = self._params(symbol)
        walk = self._walks.get(symbol)
        if walk is None:
            walk = _Walk(
                rng=_rng(_stable_hash(symbol.upper()), self.seed, "walk"),
                bars=[],
                close=start_price,
                cursor=_EPOCH,
            )
            self._walks[symbol] = walk

        step_drift = drift / _TRADING_DAYS
        step_vol = volatility / math.sqrt(_TRADING_DAYS)

        while walk.cursor <= end:
            if walk.cursor.weekday() < 5:  # Mon-Fri only; no synthetic holidays.
                bar, walk.close = self._make_bar(
                    walk.rng, walk.cursor, walk.close, step_drift, step_vol, volume
                )
                walk.bars.append(bar)
            walk.cursor += timedelta(days=1)

        return walk.bars

    @staticmethod
    def _make_bar(
        rng: random.Random,
        when: date,
        prev_close: float,
        step_drift: float,
        step_vol: float,
        avg_volume: float,
    ) -> tuple[Bar, float]:
        """One geometric-random-walk step, returned as a bar plus its close.

        High and low are built *from* the open/close pair rather than drawn
        independently — ``Bar`` rejects a candle whose body escapes its range,
        and rounding to cents is applied before the final clamp so the
        invariant holds on the values actually stored.
        """
        # Overnight gap, then the intraday move. Splitting them is what gives
        # the series realistic open != previous close behaviour.
        open_price = prev_close * math.exp(rng.gauss(0.0, step_vol * 0.4))
        shock = rng.gauss(0.0, 1.0)
        close_price = open_price * math.exp(step_drift - 0.5 * step_vol**2 + step_vol * shock)

        open_price = max(open_price, _MIN_PRICE)
        close_price = max(close_price, _MIN_PRICE)

        body_high = max(open_price, close_price)
        body_low = min(open_price, close_price)
        high = body_high * (1.0 + abs(rng.gauss(0.0, step_vol * 0.5)))
        low = body_low * (1.0 - abs(rng.gauss(0.0, step_vol * 0.5)))

        o, c = round(open_price, 2), round(close_price, 2)
        h, low_ = round(high, 2), round(low, 2)
        h = max(h, o, c)
        low_ = max(min(low_, o, c), 0.01)

        # Volume rises with the size of the move — quiet days are thin days.
        volume = round(avg_volume * math.exp(rng.gauss(0.0, 0.35)) * (1.0 + abs(shock) * 0.4))

        return Bar(ts=when, open=o, high=h, low=low_, close=c, volume=float(volume)), close_price

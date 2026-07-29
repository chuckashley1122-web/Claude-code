"""The backtester must refuse a provider that cannot serve historical fundamentals.

`yfinance` exposes only *current* fundamentals: asking it about 2019 returns
today's numbers. Scoring a 2019 decision with them is look-ahead of the most
flattering kind — the fundamental analyst would "know" which companies went on
to compound. The provider docstring warned about it; a warning in a docstring
does not stop a backtest, so this is enforced in code and pinned here.
"""

from __future__ import annotations

import unittest
from datetime import date, timedelta

from trading.alpha_agents.agents import default_committee
from trading.alpha_agents.backtest import Backtester
from trading.alpha_agents.config import Settings
from trading.alpha_agents.data import SyntheticProvider
from trading.alpha_agents.data.cache import CachingProvider
from trading.alpha_agents.execution import PaperBroker
from trading.alpha_agents.models import Fundamentals, NewsItem, PriceSeries
from trading.alpha_agents.pipeline import TradingPipeline
from trading.alpha_agents.portfolio import Portfolio


class StaleFundamentalsProvider:
    """Stands in for yfinance: prices are historical, fundamentals are not."""

    name = "stale"
    point_in_time_fundamentals = False

    def __init__(self) -> None:
        self._inner = SyntheticProvider()

    def prices(self, symbol: str, start: date, end: date) -> PriceSeries:
        return self._inner.prices(symbol, start, end)

    def fundamentals(self, symbol: str, as_of: date) -> Fundamentals | None:
        return self._inner.fundamentals(symbol, date(2026, 1, 1))  # always "today"

    def news(self, symbol: str, as_of: date, lookback_days: int = 7) -> tuple[NewsItem, ...]:
        return self._inner.news(symbol, as_of, lookback_days)


def pipeline_with(provider, analysts=None) -> TradingPipeline:
    settings = Settings(universe=("AAA",))
    return TradingPipeline(
        settings=settings,
        provider=provider,
        broker=PaperBroker(
            portfolio=Portfolio(cash=settings.starting_cash), costs=settings.costs
        ),
        analysts=analysts if analysts is not None else default_committee(),
    )


class TestLookaheadGuard(unittest.TestCase):
    def test_leaky_provider_is_refused(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            Backtester(pipeline_with(StaleFundamentalsProvider()))
        message = str(ctx.exception)
        self.assertIn("stale", message)
        self.assertIn("allow_lookahead_fundamentals", message)

    def test_refusal_can_be_overridden_explicitly(self) -> None:
        """The escape hatch exists so the choice is visible in a diff."""
        tester = Backtester(
            pipeline_with(StaleFundamentalsProvider()),
            allow_lookahead_fundamentals=True,
        )
        self.assertTrue(tester.allow_lookahead_fundamentals)

    def test_dropping_the_fundamental_analyst_also_clears_it(self) -> None:
        """The leak only matters if something reads fundamentals."""
        committee = default_committee(names=("technical", "sentiment", "risk"))
        tester = Backtester(
            pipeline_with(StaleFundamentalsProvider(), analysts=committee)
        )
        self.assertIsNotNone(tester)

    def test_point_in_time_provider_is_accepted(self) -> None:
        tester = Backtester(pipeline_with(SyntheticProvider()))
        self.assertIsNotNone(tester)

    def test_synthetic_provider_declares_itself_honest(self) -> None:
        self.assertTrue(SyntheticProvider().point_in_time_fundamentals)

    def test_caching_cannot_launder_a_leaky_provider(self) -> None:
        """Wrapping a leaky provider in a cache must not clear the flag —
        otherwise the guard is one decorator away from being defeated."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            wrapped = CachingProvider(StaleFundamentalsProvider(), cache_dir=tmp)
            self.assertFalse(wrapped.point_in_time_fundamentals)
            with self.assertRaises(ValueError):
                Backtester(pipeline_with(wrapped))

    def test_caching_preserves_an_honest_provider(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            wrapped = CachingProvider(SyntheticProvider(), cache_dir=tmp)
            self.assertTrue(wrapped.point_in_time_fundamentals)


class BoundedProvider:
    """A feed that stops at ``last_bar`` — the live edge a real vendor has."""

    name = "bounded"
    point_in_time_fundamentals = True

    def __init__(self, last_bar: date) -> None:
        self.last_bar = last_bar
        self._inner = SyntheticProvider()

    def prices(self, symbol: str, start: date, end: date) -> PriceSeries:
        capped = min(end, self.last_bar)
        if capped < start:
            return PriceSeries(symbol, ())
        return self._inner.prices(symbol, start, capped)

    def fundamentals(self, symbol: str, as_of: date) -> Fundamentals | None:
        return self._inner.fundamentals(symbol, min(as_of, self.last_bar))

    def news(self, symbol: str, as_of: date, lookback_days: int = 7) -> tuple[NewsItem, ...]:
        return self._inner.news(symbol, min(as_of, self.last_bar), lookback_days)


class TestFillTiming(unittest.TestCase):
    """A verdict formed from a bar's close may not fill at that same close.

    Filling at the close the decision depended on hands the strategy a price it
    could not have traded. On a gapping name that is a systematic free edge and
    the most common way a backtest flatters a strategy that does not work.
    """

    AS_OF = date(2025, 6, 16)

    def _pipeline(self):
        from trading.alpha_agents.models import Stance, Verdict

        settings = Settings(universe=("AAA",))
        pipe = TradingPipeline(
            settings=settings,
            provider=SyntheticProvider(),
            broker=PaperBroker(
                portfolio=Portfolio(cash=settings.starting_cash), costs=settings.costs
            ),
        )
        pipe.research = lambda symbol, as_of: Verdict(  # type: ignore[assignment]
            symbol=symbol, stance=Stance.BUY, confidence=0.99, rationale="forced"
        )
        return pipe

    def test_fill_price_is_the_next_sessions_open(self) -> None:
        provider = SyntheticProvider()
        pipe = self._pipeline()

        todays_close = provider.prices(
            "AAA", self.AS_OF - timedelta(days=10), self.AS_OF
        ).up_to(self.AS_OF).last.close
        next_open = pipe._fill_price("AAA", self.AS_OF)

        self.assertIsNotNone(next_open)
        self.assertNotAlmostEqual(
            next_open, todays_close, places=6,
            msg="fill price must not be the close the decision was made on",
        )

        forward = provider.prices("AAA", self.AS_OF, self.AS_OF + timedelta(days=10))
        expected = next(b.open for b in forward.bars if b.ts > self.AS_OF)
        self.assertAlmostEqual(next_open, expected, places=9)

    def test_executed_fill_uses_the_next_open_not_todays_close(self) -> None:
        pipe = self._pipeline()
        todays_close = pipe._marks(self.AS_OF)["AAA"]
        next_open = pipe._fill_price("AAA", self.AS_OF)

        pipe.scan(self.AS_OF, execute=True)
        fills = pipe.broker.fills
        self.assertTrue(fills, "expected the forced BUY to fill")

        # Slippage is applied on top, so compare against the un-slipped basis:
        # the fill must sit nearer the next open than to today's close.
        traded = fills[0].price
        self.assertLess(
            abs(traded - next_open),
            abs(traded - todays_close),
            f"filled at {traded}, closer to today's close {todays_close} "
            f"than to the next open {next_open}",
        )

    def test_at_the_live_edge_the_order_is_queued_not_filled(self) -> None:
        """With no next bar, tomorrow's open genuinely does not exist. Saying
        'queued' is honest; filling anyway would be inventing a price.

        Needs a provider that actually ends. The synthetic generator will
        happily produce a bar for any date requested, so it has no live edge —
        which is itself worth knowing: only a real vendor feed reaches one.
        """
        pipe = self._pipeline()
        far_future = date(2035, 1, 3)
        pipe.provider = BoundedProvider(last_bar=far_future)

        self.assertIsNone(pipe._fill_price("AAA", far_future))

        result = pipe.scan(far_future, execute=True)
        actionable = [d for d in result.decisions if d.order is not None]
        self.assertTrue(actionable, "expected an order to be proposed")
        self.assertFalse(any(d.executed for d in actionable))
        self.assertTrue(
            all("queued" in (d.rejection or "") for d in actionable),
            [d.rejection for d in actionable],
        )
        self.assertEqual(pipe.broker.portfolio.positions, {})


class TestYFinanceDeclaresItself(unittest.TestCase):
    def test_yfinance_provider_declares_stale_fundamentals(self) -> None:
        """Importable without the optional dependency; only the flag is read."""
        from trading.alpha_agents.data.yfinance_provider import YFinanceProvider

        self.assertFalse(YFinanceProvider.point_in_time_fundamentals)


if __name__ == "__main__":
    unittest.main()

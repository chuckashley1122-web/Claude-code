"""The backtester must refuse a provider that cannot serve historical fundamentals.

`yfinance` exposes only *current* fundamentals: asking it about 2019 returns
today's numbers. Scoring a 2019 decision with them is look-ahead of the most
flattering kind — the fundamental analyst would "know" which companies went on
to compound. The provider docstring warned about it; a warning in a docstring
does not stop a backtest, so this is enforced in code and pinned here.
"""

from __future__ import annotations

import unittest
from datetime import date

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


class TestYFinanceDeclaresItself(unittest.TestCase):
    def test_yfinance_provider_declares_stale_fundamentals(self) -> None:
        """Importable without the optional dependency; only the flag is read."""
        from trading.alpha_agents.data.yfinance_provider import YFinanceProvider

        self.assertFalse(YFinanceProvider.point_in_time_fundamentals)


if __name__ == "__main__":
    unittest.main()

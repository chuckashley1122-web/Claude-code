"""Tests for the market data layer.

The bar the synthetic provider has to clear is higher than "it runs": every
downstream test and demo trusts it to produce the *same* history everywhere,
so determinism and the ``Bar`` invariants are asserted directly rather than
assumed.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest import mock

from trading.alpha_agents.data import (
    CachingProvider,
    SyntheticProvider,
    YFinanceProvider,
    get_provider,
)
from trading.alpha_agents.data.yfinance_provider import _require_yfinance
from trading.alpha_agents.interfaces import MarketDataProvider
from trading.alpha_agents.models import Fundamentals, NewsItem, PriceSeries

START = date(2023, 1, 1)
END = date(2023, 12, 31)


class SyntheticDeterminismTests(unittest.TestCase):
    def test_same_symbol_and_seed_gives_identical_bars(self) -> None:
        first = SyntheticProvider(seed=42).prices("AAPL", START, END)
        second = SyntheticProvider(seed=42).prices("AAPL", START, END)
        self.assertEqual(first, second)
        self.assertGreater(len(first), 200)

    def test_repeated_calls_on_one_instance_agree(self) -> None:
        provider = SyntheticProvider()
        self.assertEqual(provider.prices("MSFT", START, END), provider.prices("MSFT", START, END))

    def test_different_symbols_differ(self) -> None:
        provider = SyntheticProvider()
        self.assertNotEqual(
            provider.prices("AAPL", START, END).closes,
            provider.prices("MSFT", START, END).closes,
        )

    def test_different_seeds_differ(self) -> None:
        self.assertNotEqual(
            SyntheticProvider(seed=1).prices("AAPL", START, END).closes,
            SyntheticProvider(seed=2).prices("AAPL", START, END).closes,
        )

    def test_bars_do_not_depend_on_the_requested_window(self) -> None:
        """A narrower request must return the same bars, not a fresh walk.

        Otherwise a backtest that re-fetches with a different start silently
        trades a different history than the one it was tuned on.
        """
        wide = SyntheticProvider().prices("NVDA", START, END)
        narrow = SyntheticProvider().prices("NVDA", date(2023, 6, 1), date(2023, 6, 30))
        overlap = [b for b in wide.bars if date(2023, 6, 1) <= b.ts <= date(2023, 6, 30)]
        self.assertEqual(tuple(overlap), narrow.bars)
        self.assertTrue(overlap)


class SyntheticBarTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = SyntheticProvider()
        self.series = self.provider.prices("AAPL", START, END)

    def test_bars_satisfy_the_ohlc_invariants(self) -> None:
        for bar in self.series.bars:
            with self.subTest(ts=bar.ts):
                self.assertLessEqual(bar.low, bar.high)
                self.assertLessEqual(bar.low, bar.open)
                self.assertLessEqual(bar.open, bar.high)
                self.assertLessEqual(bar.low, bar.close)
                self.assertLessEqual(bar.close, bar.high)

    def test_prices_stay_positive_and_volume_non_negative(self) -> None:
        for bar in self.series.bars:
            with self.subTest(ts=bar.ts):
                self.assertGreater(bar.low, 0.0)
                self.assertGreaterEqual(bar.volume, 0.0)

    def test_bars_are_ordered_and_unique(self) -> None:
        stamps = [b.ts for b in self.series.bars]
        self.assertEqual(stamps, sorted(stamps))
        self.assertEqual(len(stamps), len(set(stamps)))

    def test_date_range_is_honoured(self) -> None:
        self.assertTrue(all(START <= b.ts <= END for b in self.series.bars))
        self.assertGreaterEqual(self.series.bars[0].ts, START)
        self.assertLessEqual(self.series.last.ts, END)

    def test_no_weekend_bars(self) -> None:
        self.assertFalse([b.ts for b in self.series.bars if b.ts.weekday() >= 5])

    def test_weekend_only_range_is_empty(self) -> None:
        saturday = date(2023, 6, 3)
        series = self.provider.prices("AAPL", saturday, saturday + timedelta(days=1))
        self.assertEqual(len(series), 0)

    def test_start_after_end_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.provider.prices("AAPL", END, START)

    def test_up_to_slices_without_look_ahead(self) -> None:
        cutoff = date(2023, 6, 30)
        sliced = self.series.up_to(cutoff)
        self.assertTrue(all(b.ts <= cutoff for b in sliced.bars))
        self.assertEqual(sliced.bars, tuple(b for b in self.series.bars if b.ts <= cutoff))
        self.assertLess(len(sliced), len(self.series))
        self.assertEqual(sliced.last.ts, date(2023, 6, 30))
        # The prefix must be untouched, not regenerated.
        self.assertEqual(sliced.bars, self.series.bars[: len(sliced)])

    def test_up_to_before_history_is_empty(self) -> None:
        self.assertEqual(len(self.series.up_to(date(2022, 1, 1))), 0)


class SyntheticFundamentalsAndNewsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = SyntheticProvider()
        self.as_of = date(2023, 6, 30)

    def test_fundamentals_expose_the_expected_keys(self) -> None:
        fundamentals = self.provider.fundamentals("AAPL", self.as_of)
        assert fundamentals is not None
        self.assertIsInstance(fundamentals, Fundamentals)
        self.assertEqual(fundamentals.symbol, "AAPL")
        self.assertEqual(
            set(fundamentals.metrics),
            {
                "pe",
                "ps",
                "revenue_growth",
                "gross_margin",
                "net_margin",
                "debt_to_equity",
                "fcf_yield",
                "roe",
            },
        )
        self.assertTrue(all(isinstance(v, float) for v in fundamentals.metrics.values()))
        self.assertGreater(fundamentals.metrics["pe"], 0.0)
        self.assertLess(fundamentals.metrics["gross_margin"], 1.0)

    def test_fundamentals_are_deterministic_and_point_in_time(self) -> None:
        first = self.provider.fundamentals("AAPL", self.as_of)
        second = SyntheticProvider().fundamentals("AAPL", self.as_of)
        self.assertEqual(first, second)
        assert first is not None
        self.assertLessEqual(first.as_of, self.as_of)

    def test_fundamentals_are_stable_within_a_quarter(self) -> None:
        may = self.provider.fundamentals("AAPL", date(2023, 5, 2))
        june = self.provider.fundamentals("AAPL", date(2023, 6, 20))
        self.assertEqual(may, june)

    def test_news_is_deterministic_and_inside_the_window(self) -> None:
        items = self.provider.news("AAPL", self.as_of, lookback_days=7)
        self.assertEqual(items, SyntheticProvider().news("AAPL", self.as_of, lookback_days=7))
        self.assertTrue(items)
        self.assertLessEqual(len(items), 4)
        for item in items:
            with self.subTest(headline=item.headline):
                self.assertIsInstance(item, NewsItem)
                self.assertIn("AAPL", item.headline)
                self.assertLessEqual(item.ts.date(), self.as_of)
                self.assertGreaterEqual(item.ts.date(), self.as_of - timedelta(days=6))

    def test_news_is_newest_first(self) -> None:
        stamps = [item.ts for item in self.provider.news("AAPL", self.as_of)]
        self.assertEqual(stamps, sorted(stamps, reverse=True))

    def test_news_with_no_lookback_is_empty(self) -> None:
        self.assertEqual(self.provider.news("AAPL", self.as_of, lookback_days=0), ())


class GetProviderTests(unittest.TestCase):
    def test_returns_the_synthetic_provider(self) -> None:
        provider = get_provider("synthetic")
        self.assertIsInstance(provider, SyntheticProvider)
        self.assertEqual(provider.name, "synthetic")

    def test_forwards_keyword_arguments(self) -> None:
        provider = get_provider("synthetic", seed=99)
        self.assertIsInstance(provider, SyntheticProvider)
        self.assertEqual(provider.seed, 99)

    def test_returns_the_yfinance_provider_without_importing_it(self) -> None:
        with mock.patch.dict(sys.modules, {"yfinance": None}):
            provider = get_provider("yfinance")
        self.assertIsInstance(provider, YFinanceProvider)
        self.assertEqual(provider.name, "yfinance")

    def test_name_is_normalised(self) -> None:
        self.assertIsInstance(get_provider("  SYNTHETIC "), SyntheticProvider)

    def test_unknown_name_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as caught:
            get_provider("bloomberg")
        message = str(caught.exception)
        self.assertIn("bloomberg", message)
        self.assertIn("synthetic", message)

    def test_providers_satisfy_the_protocol(self) -> None:
        self.assertIsInstance(get_provider("synthetic"), MarketDataProvider)


class _CountingProvider:
    """A provider that records how often it was actually asked to do work."""

    name = "counting"

    def __init__(self) -> None:
        self.inner = SyntheticProvider(seed=7)
        self.calls: dict[str, int] = {"prices": 0, "fundamentals": 0, "news": 0}

    def prices(self, symbol: str, start: date, end: date) -> PriceSeries:
        self.calls["prices"] += 1
        return self.inner.prices(symbol, start, end)

    def fundamentals(self, symbol: str, as_of: date) -> Fundamentals | None:
        self.calls["fundamentals"] += 1
        return None if symbol == "UNKNOWN" else self.inner.fundamentals(symbol, as_of)

    def news(self, symbol: str, as_of: date, lookback_days: int = 7) -> tuple[NewsItem, ...]:
        self.calls["news"] += 1
        return self.inner.news(symbol, as_of, lookback_days)


class CachingProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tempdir.cleanup)
        self.cache_dir = Path(self._tempdir.name)
        self.inner = _CountingProvider()
        self.provider = CachingProvider(self.inner, cache_dir=self.cache_dir)

    def test_name_reports_the_wrapped_provider(self) -> None:
        self.assertEqual(self.provider.name, "cached:counting")

    def test_price_series_round_trips_through_disk(self) -> None:
        first = self.provider.prices("AAPL", START, END)
        second = self.provider.prices("AAPL", START, END)
        self.assertEqual(first, second)
        self.assertEqual(self.inner.calls["prices"], 1)
        self.assertEqual(first.bars, second.bars)
        self.assertIsInstance(second.bars[0].ts, date)

    def test_a_fresh_wrapper_reads_the_file_written_by_the_first(self) -> None:
        """The point of the cache: it survives the process that filled it."""
        expected = self.provider.prices("AAPL", START, END)
        other_inner = _CountingProvider()
        reloaded = CachingProvider(other_inner, cache_dir=self.cache_dir)
        self.assertEqual(reloaded.prices("AAPL", START, END), expected)
        self.assertEqual(other_inner.calls["prices"], 0)

    def test_a_cache_file_is_written(self) -> None:
        self.provider.prices("AAPL", START, END)
        files = list(self.cache_dir.rglob("*.json"))
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].name.startswith("prices-"))

    def test_different_arguments_are_different_entries(self) -> None:
        self.provider.prices("AAPL", START, END)
        self.provider.prices("AAPL", START, date(2023, 6, 30))
        self.provider.prices("MSFT", START, END)
        self.assertEqual(self.inner.calls["prices"], 3)
        self.assertEqual(len(list(self.cache_dir.rglob("*.json"))), 3)

    def test_fundamentals_round_trip(self) -> None:
        as_of = date(2023, 6, 30)
        first = self.provider.fundamentals("AAPL", as_of)
        second = self.provider.fundamentals("AAPL", as_of)
        self.assertEqual(first, second)
        self.assertEqual(first, self.inner.inner.fundamentals("AAPL", as_of))
        self.assertEqual(self.inner.calls["fundamentals"], 1)

    def test_a_missing_result_is_cached_too(self) -> None:
        """``None`` is an answer; refetching it every time defeats the cache."""
        as_of = date(2023, 6, 30)
        self.assertIsNone(self.provider.fundamentals("UNKNOWN", as_of))
        self.assertIsNone(self.provider.fundamentals("UNKNOWN", as_of))
        self.assertEqual(self.inner.calls["fundamentals"], 1)

    def test_news_round_trips_with_datetimes(self) -> None:
        as_of = date(2023, 6, 30)
        first = self.provider.news("AAPL", as_of, lookback_days=7)
        second = self.provider.news("AAPL", as_of, lookback_days=7)
        self.assertEqual(first, second)
        self.assertTrue(first)
        self.assertIsInstance(second[0].ts, datetime)
        self.assertEqual(self.inner.calls["news"], 1)

    def test_clear_forces_a_refetch(self) -> None:
        self.provider.prices("AAPL", START, END)
        self.assertEqual(self.provider.clear(), 1)
        self.assertEqual(list(self.cache_dir.rglob("*.json")), [])
        self.provider.prices("AAPL", START, END)
        self.assertEqual(self.inner.calls["prices"], 2)

    def test_clear_on_an_empty_cache_is_harmless(self) -> None:
        self.assertEqual(CachingProvider(self.inner, cache_dir=self.cache_dir / "nope").clear(), 0)

    def test_a_corrupt_entry_is_treated_as_a_miss(self) -> None:
        self.provider.prices("AAPL", START, END)
        for path in self.cache_dir.rglob("*.json"):
            path.write_text("{not json", encoding="utf-8")
        expected = self.inner.inner.prices("AAPL", START, END)
        self.assertEqual(self.provider.prices("AAPL", START, END), expected)
        self.assertEqual(self.inner.calls["prices"], 2)

    def test_the_wrapper_satisfies_the_protocol(self) -> None:
        self.assertIsInstance(self.provider, MarketDataProvider)


class YFinanceProviderTests(unittest.TestCase):
    """yfinance is optional, so the failure mode is the behaviour under test."""

    def test_importing_the_package_does_not_import_yfinance(self) -> None:
        self.assertNotIn("yfinance", sys.modules)

    def test_constructing_the_provider_needs_nothing_installed(self) -> None:
        with mock.patch.dict(sys.modules, {"yfinance": None}):
            provider = YFinanceProvider()
        self.assertEqual(provider.name, "yfinance")

    def test_methods_raise_a_helpful_import_error(self) -> None:
        provider = YFinanceProvider()
        calls = {
            "prices": lambda: provider.prices("AAPL", START, END),
            "fundamentals": lambda: provider.fundamentals("AAPL", END),
            "news": lambda: provider.news("AAPL", END),
        }
        for method, call in calls.items():
            with self.subTest(method=method):
                # Blocking the import makes this deterministic whether or not
                # yfinance happens to be installed on the machine running it.
                with mock.patch.dict(sys.modules, {"yfinance": None}):
                    with self.assertRaises(ImportError) as caught:
                        call()
                self.assertIn("pip install yfinance", str(caught.exception))

    def test_the_import_helper_names_the_package(self) -> None:
        with mock.patch.dict(sys.modules, {"yfinance": None}):
            with self.assertRaises(ImportError) as caught:
                _require_yfinance()
        self.assertIn("yfinance", str(caught.exception))

    def test_it_satisfies_the_protocol(self) -> None:
        self.assertIsInstance(YFinanceProvider(), MarketDataProvider)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

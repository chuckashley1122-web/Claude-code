"""Tests for :mod:`trading.alpha_agents.indicators`.

Expected values are hand-computed from the indicator definitions rather than
copied from another library, so a silent formula change (Wilder vs simple
smoothing, sample vs population deviation) fails loudly here.
"""

from __future__ import annotations

import math
import unittest
from datetime import date, timedelta

from trading.alpha_agents.indicators import (
    atr,
    bollinger,
    ema,
    macd,
    max_drawdown,
    momentum,
    realized_volatility,
    rsi,
    sharpe,
    sma,
    true_range,
)
from trading.alpha_agents.models import Bar, PriceSeries

START = date(2024, 1, 1)


def make_series(rows: list[tuple[float, float, float]], symbol: str = "TEST") -> PriceSeries:
    """Build a series from ``(high, low, close)`` rows; open is pinned to close."""
    bars = tuple(
        Bar(ts=START + timedelta(days=i), open=close, high=high, low=low, close=close, volume=1000.0)
        for i, (high, low, close) in enumerate(rows)
    )
    return PriceSeries(symbol, bars)


def flat_series(price: float, count: int) -> PriceSeries:
    return make_series([(price, price, price)] * count)


class TestSMA(unittest.TestCase):
    def test_known_values(self) -> None:
        result = sma([1.0, 2.0, 3.0, 4.0, 5.0], 3)
        self.assertEqual(result[:2], [None, None])
        for got, want in zip(result[2:], [2.0, 3.0, 4.0]):
            self.assertAlmostEqual(got, want)

    def test_input_shorter_than_period_is_all_none(self) -> None:
        self.assertEqual(sma([1.0, 2.0], 5), [None] * 2)

    def test_flat_series_returns_the_level(self) -> None:
        result = sma([7.0] * 5, 3)
        self.assertEqual(result[:2], [None, None])
        for value in result[2:]:
            self.assertAlmostEqual(value, 7.0)


class TestEMA(unittest.TestCase):
    def test_seeded_with_sma_then_smoothed(self) -> None:
        # period 3 -> k = 0.5; seed = mean(1, 2, 3) = 2.
        result = ema([1.0, 2.0, 3.0, 4.0, 5.0], 3)
        self.assertEqual(result[:2], [None, None])
        for got, want in zip(result[2:], [2.0, 3.0, 4.0]):
            self.assertAlmostEqual(got, want)

    def test_input_shorter_than_period_is_all_none(self) -> None:
        self.assertEqual(ema([1.0, 2.0, 3.0], 4), [None] * 3)

    def test_flat_series_never_drifts(self) -> None:
        for value in ema([3.5] * 6, 2)[1:]:
            self.assertAlmostEqual(value, 3.5)


class TestRSI(unittest.TestCase):
    def test_known_values_with_wilder_smoothing(self) -> None:
        # changes: +1, -0.5, +1, -0.5, +1 with period 3 (period 2 could not tell
        # Wilder's smoothing apart from a plain two-point average).
        result = rsi([10.0, 11.0, 10.5, 11.5, 11.0, 12.0], period=3)
        self.assertEqual(result[:3], [None, None, None])
        self.assertAlmostEqual(result[3], 80.0)  # gain 2/3 / loss 1/6 -> RS 4
        self.assertAlmostEqual(result[4], 100.0 - 100.0 / 2.6)  # gain 4/9 / loss 5/18
        self.assertAlmostEqual(result[5], 100.0 - 100.0 / 4.4)  # gain 17/27 / loss 5/27

    def test_uninterrupted_gains_pin_to_100(self) -> None:
        result = rsi([1.0, 2.0, 3.0, 4.0], period=2)
        self.assertAlmostEqual(result[-1], 100.0)

    def test_flat_series_is_neutral(self) -> None:
        for value in rsi([5.0] * 8, period=3)[3:]:
            self.assertAlmostEqual(value, 50.0)

    def test_needs_one_bar_more_than_period(self) -> None:
        self.assertEqual(rsi([1.0, 2.0, 3.0], period=3), [None] * 3)
        self.assertIsNotNone(rsi([1.0, 2.0, 3.0, 4.0], period=3)[3])


class TestMACD(unittest.TestCase):
    def test_known_values(self) -> None:
        line, signal, histogram = macd([1.0, 2.0, 4.0, 8.0, 16.0], fast=2, slow=3, signal=2)
        self.assertEqual(line[:2], [None, None])
        for got, want in zip(line[2:], [5 / 6, 11 / 9, 239 / 108]):
            self.assertAlmostEqual(got, want)
        self.assertEqual(signal[:3], [None, None, None])
        for got, want in zip(signal[3:], [37 / 36, 589 / 324]):
            self.assertAlmostEqual(got, want)
        self.assertEqual(histogram[:3], [None, None, None])
        for got, want in zip(histogram[3:], [7 / 36, 32 / 81]):
            self.assertAlmostEqual(got, want)

    def test_input_shorter_than_slow_period_is_all_none(self) -> None:
        line, signal, histogram = macd([1.0, 2.0, 3.0], fast=2, slow=5, signal=2)
        self.assertEqual(line, [None] * 3)
        self.assertEqual(signal, [None] * 3)
        self.assertEqual(histogram, [None] * 3)

    def test_flat_series_collapses_to_zero(self) -> None:
        line, signal, histogram = macd([12.0] * 12, fast=2, slow=4, signal=3)
        for value in line[3:]:
            self.assertAlmostEqual(value, 0.0)
        for value in histogram[5:]:
            self.assertAlmostEqual(value, 0.0)
        self.assertIsNotNone(signal[-1])

    def test_fast_must_be_shorter_than_slow(self) -> None:
        with self.assertRaises(ValueError):
            macd([1.0, 2.0, 3.0], fast=10, slow=10)


class TestBollinger(unittest.TestCase):
    def test_known_values_population_stddev(self) -> None:
        # Classic worked example: mean 5, population stddev 2.
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        upper, mid, lower = bollinger(values, period=8, num_std=2.0)
        self.assertEqual(mid[:7], [None] * 7)
        self.assertAlmostEqual(mid[-1], 5.0)
        self.assertAlmostEqual(upper[-1], 9.0)
        self.assertAlmostEqual(lower[-1], 1.0)

    def test_bands_are_symmetric_about_the_average(self) -> None:
        upper, mid, lower = bollinger([1.0, 2.0, 3.0], period=3, num_std=2.0)
        spread = 2.0 * math.sqrt(2.0 / 3.0)
        self.assertAlmostEqual(mid[-1], 2.0)
        self.assertAlmostEqual(upper[-1], 2.0 + spread)
        self.assertAlmostEqual(lower[-1], 2.0 - spread)

    def test_input_shorter_than_period_is_all_none(self) -> None:
        upper, mid, lower = bollinger([1.0, 2.0], period=20)
        self.assertEqual((upper, mid, lower), ([None] * 2, [None] * 2, [None] * 2))

    def test_flat_series_collapses_the_bands(self) -> None:
        upper, mid, lower = bollinger([4.0] * 5, period=3)
        for i in range(2, 5):
            self.assertAlmostEqual(upper[i], 4.0)
            self.assertAlmostEqual(mid[i], 4.0)
            self.assertAlmostEqual(lower[i], 4.0)

    def test_negative_num_std_rejected(self) -> None:
        with self.assertRaises(ValueError):
            bollinger([1.0, 2.0, 3.0], period=2, num_std=-1.0)


class TestTrueRangeAndATR(unittest.TestCase):
    def setUp(self) -> None:
        # (high, low, close); ranges are 1.5, 1.5, 3.0, 1.5 after the first bar.
        self.series = make_series(
            [
                (10.0, 9.0, 9.5),
                (11.0, 10.0, 10.5),
                (10.5, 9.0, 9.2),
                (12.0, 9.0, 11.0),
                (11.5, 10.0, 10.2),
            ]
        )

    def test_true_range_known_values(self) -> None:
        result = true_range(self.series)
        self.assertIsNone(result[0])  # no prior close to gap against
        for got, want in zip(result[1:], [1.5, 1.5, 3.0, 1.5]):
            self.assertAlmostEqual(got, want)

    def test_true_range_of_empty_series(self) -> None:
        self.assertEqual(true_range(PriceSeries("TEST", ())), [])

    def test_atr_known_values_with_wilder_smoothing(self) -> None:
        result = atr(self.series, period=3)
        self.assertEqual(result[:3], [None, None, None])
        self.assertAlmostEqual(result[3], 2.0)  # mean of the first three ranges
        self.assertAlmostEqual(result[4], (2.0 * 2 + 1.5) / 3)

    def test_atr_needs_period_plus_one_bars(self) -> None:
        self.assertEqual(atr(self.series.window(3), period=3), [None] * 3)

    def test_atr_of_flat_bars_is_zero(self) -> None:
        result = atr(flat_series(5.0, 6), period=3)
        for value in result[3:]:
            self.assertAlmostEqual(value, 0.0)


class TestRealizedVolatility(unittest.TestCase):
    def setUp(self) -> None:
        # Log returns of exactly 0.1, 0.2, 0.3 -> sample stddev 0.1.
        self.values = [1.0, math.exp(0.1), math.exp(0.3), math.exp(0.6)]

    def test_known_annualised_value(self) -> None:
        result = realized_volatility(self.values, period=3)
        self.assertEqual(result[:3], [None, None, None])
        self.assertAlmostEqual(result[3], 0.1 * math.sqrt(252))

    def test_unannualised_value(self) -> None:
        result = realized_volatility(self.values, period=3, annualize=False)
        self.assertAlmostEqual(result[3], 0.1)

    def test_input_shorter_than_period_is_all_none(self) -> None:
        self.assertEqual(realized_volatility([1.0, 2.0, 3.0], period=3), [None] * 3)

    def test_flat_series_has_zero_volatility(self) -> None:
        for value in realized_volatility([20.0] * 6, period=3)[3:]:
            self.assertAlmostEqual(value, 0.0)

    def test_period_below_two_rejected(self) -> None:
        with self.assertRaises(ValueError):
            realized_volatility([1.0, 2.0, 3.0], period=1)


class TestMaxDrawdown(unittest.TestCase):
    def test_worst_peak_to_trough(self) -> None:
        self.assertAlmostEqual(max_drawdown([100.0, 120.0, 60.0, 80.0]), 0.5)

    def test_keeps_the_worst_not_the_latest(self) -> None:
        self.assertAlmostEqual(max_drawdown([100.0, 50.0, 100.0, 90.0]), 0.5)

    def test_monotonic_and_flat_series_have_no_drawdown(self) -> None:
        self.assertAlmostEqual(max_drawdown([1.0, 2.0, 3.0]), 0.0)
        self.assertAlmostEqual(max_drawdown([5.0] * 4), 0.0)

    def test_empty_and_single_input(self) -> None:
        self.assertAlmostEqual(max_drawdown([]), 0.0)
        self.assertAlmostEqual(max_drawdown([42.0]), 0.0)


class TestSharpe(unittest.TestCase):
    def test_known_value(self) -> None:
        # mean 0.02, sample stddev 0.01 -> 2 * sqrt(252).
        self.assertAlmostEqual(sharpe([0.01, 0.02, 0.03]), 2.0 * math.sqrt(252))

    def test_risk_free_rate_is_annual_and_lowers_the_ratio(self) -> None:
        result = sharpe([0.01, 0.02, 0.03], risk_free_rate=0.0252)
        self.assertAlmostEqual(result, 1.99 * math.sqrt(252))

    def test_zero_dispersion_returns_zero(self) -> None:
        self.assertAlmostEqual(sharpe([0.01] * 5), 0.0)

    def test_too_short_input_returns_zero(self) -> None:
        self.assertAlmostEqual(sharpe([]), 0.0)
        self.assertAlmostEqual(sharpe([0.05]), 0.0)


class TestMomentum(unittest.TestCase):
    def test_known_values(self) -> None:
        result = momentum([1.0, 2.0, 3.0, 4.0], 2)
        self.assertEqual(result[:2], [None, None])
        self.assertAlmostEqual(result[2], 2.0)
        self.assertAlmostEqual(result[3], 1.0)

    def test_zero_base_is_undefined_not_an_error(self) -> None:
        self.assertEqual(momentum([0.0, 1.0, 2.0], 1), [None, None, 1.0])

    def test_short_and_flat_inputs(self) -> None:
        self.assertEqual(momentum([1.0, 2.0], 5), [None, None])
        for value in momentum([9.0] * 4, 2)[2:]:
            self.assertAlmostEqual(value, 0.0)


class TestIndexAlignment(unittest.TestCase):
    """Every series function must return one entry per input bar."""

    def setUp(self) -> None:
        self.closes = [100.0 + (i % 7) - (i % 3) for i in range(40)]
        self.series = make_series([(c + 1.0, c - 1.0, c) for c in self.closes])

    def test_single_series_outputs_match_input_length(self) -> None:
        cases = {
            "sma": lambda: sma(self.closes, 10),
            "ema": lambda: ema(self.closes, 10),
            "rsi": lambda: rsi(self.closes),
            "realized_volatility": lambda: realized_volatility(self.closes),
            "momentum": lambda: momentum(self.closes, 5),
            "true_range": lambda: true_range(self.series),
            "atr": lambda: atr(self.series),
        }
        for name, call in cases.items():
            with self.subTest(function=name):
                self.assertEqual(len(call()), len(self.closes))

    def test_tuple_returning_outputs_match_input_length(self) -> None:
        cases = {
            "macd": lambda: macd(self.closes),
            "bollinger": lambda: bollinger(self.closes),
        }
        for name, call in cases.items():
            with self.subTest(function=name):
                for part in call():
                    self.assertEqual(len(part), len(self.closes))

    def test_short_inputs_still_align(self) -> None:
        short = self.closes[:3]
        self.assertEqual(len(sma(short, 20)), 3)
        self.assertEqual(len(rsi(short)), 3)
        self.assertEqual(len(atr(self.series.window(2))), 2)


class TestParameterValidation(unittest.TestCase):
    def test_non_positive_periods_are_rejected(self) -> None:
        values = [1.0, 2.0, 3.0, 4.0]
        series = make_series([(2.0, 1.0, 1.5)] * 4)
        cases = {
            "sma": lambda p: sma(values, p),
            "ema": lambda p: ema(values, p),
            "rsi": lambda p: rsi(values, p),
            "macd_fast": lambda p: macd(values, fast=p),
            "macd_signal": lambda p: macd(values, signal=p),
            "bollinger": lambda p: bollinger(values, p),
            "atr": lambda p: atr(series, p),
            "momentum": lambda p: momentum(values, p),
            "realized_volatility": lambda p: realized_volatility(values, p),
        }
        for name, call in cases.items():
            for bad in (0, -3):
                with self.subTest(function=name, period=bad):
                    with self.assertRaises(ValueError):
                        call(bad)

    def test_non_positive_annualisation_factor_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            sharpe([0.01, 0.02], periods_per_year=0)
        with self.assertRaises(ValueError):
            realized_volatility([1.0, 2.0, 3.0], period=2, periods_per_year=0)


if __name__ == "__main__":
    unittest.main()

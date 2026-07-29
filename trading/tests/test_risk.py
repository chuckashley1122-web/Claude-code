"""Tests for volatility-targeted sizing and the pre-trade veto.

The kill-switch tests matter most: they assert the switch *stays* tripped after
equity recovers, which is the behaviour that separates a bad day from a blown
account.
"""

from __future__ import annotations

import unittest
from datetime import date

from trading.alpha_agents.config import RiskLimits
from trading.alpha_agents.models import Order, Position, Stance
from trading.alpha_agents.portfolio import Portfolio
from trading.alpha_agents.risk import RiskManager, size_position

DAY1 = date(2025, 1, 6)
DAY2 = date(2025, 1, 7)
DAY3 = date(2025, 1, 8)


class TestSizePosition(unittest.TestCase):
    def setUp(self) -> None:
        # A roomy position cap so the volatility term is visible before the
        # clamp bites; the default 10% cap dominates at realistic vols.
        self.limits = RiskLimits(
            max_position_pct=0.50, max_gross_exposure=0.80, vol_target_annual=0.15
        )

    def test_lower_vol_earns_a_bigger_position(self) -> None:
        quiet = size_position(100_000.0, 100.0, 1.0, 0.30, self.limits)
        loud = size_position(100_000.0, 100.0, 1.0, 0.60, self.limits)
        # 100,000 * (0.15/0.30) = 50,000 notional -> 500 shares at 100.
        self.assertAlmostEqual(quiet, 500.0)
        # 100,000 * (0.15/0.60) = 25,000 notional -> 250 shares.
        self.assertAlmostEqual(loud, 250.0)
        self.assertGreater(quiet, loud)

    def test_sizing_is_monotonically_decreasing_in_vol(self) -> None:
        sizes = [
            size_position(100_000.0, 100.0, 1.0, vol, self.limits)
            for vol in (0.30, 0.40, 0.50, 0.60, 0.90)
        ]
        self.assertEqual(sizes, sorted(sizes, reverse=True))

    def test_position_cap_clamps_very_quiet_names(self) -> None:
        # 100,000 * (0.15/0.05) = 300,000 -> clamped to 50% of 100,000.
        shares = size_position(100_000.0, 100.0, 1.0, 0.05, self.limits)
        self.assertAlmostEqual(shares, 500.0)
        self.assertLessEqual(shares * 100.0, self.limits.max_position_pct * 100_000.0 + 1e-9)

    def test_default_limits_never_breach_the_cap(self) -> None:
        limits = RiskLimits()
        for vol in (0.01, 0.10, 0.15, 0.35, 1.20):
            for confidence in (0.25, 0.60, 1.0):
                notional = size_position(100_000.0, 100.0, confidence, vol, limits) * 100.0
                self.assertLessEqual(notional, limits.max_position_pct * 100_000.0 + 1e-9)

    def test_confidence_scales_the_target(self) -> None:
        full = size_position(100_000.0, 100.0, 1.0, 0.60, self.limits)
        half = size_position(100_000.0, 100.0, 0.5, 0.60, self.limits)
        self.assertAlmostEqual(half, full / 2)
        self.assertAlmostEqual(half, 125.0)

    def test_confidence_is_clamped_to_the_unit_interval(self) -> None:
        self.assertAlmostEqual(
            size_position(100_000.0, 100.0, 1.5, 0.60, self.limits),
            size_position(100_000.0, 100.0, 1.0, 0.60, self.limits),
        )
        self.assertAlmostEqual(size_position(100_000.0, 100.0, 0.0, 0.60, self.limits), 0.0)
        self.assertAlmostEqual(size_position(100_000.0, 100.0, -1.0, 0.60, self.limits), 0.0)

    def test_zero_and_negative_vol_fall_back_to_the_cap(self) -> None:
        # No usable risk estimate: take the largest size policy would allow,
        # never an infinite one.
        self.assertAlmostEqual(size_position(100_000.0, 100.0, 1.0, 0.0, self.limits), 500.0)
        self.assertAlmostEqual(size_position(100_000.0, 100.0, 1.0, -0.2, self.limits), 500.0)
        # Confidence still scales the fallback.
        self.assertAlmostEqual(size_position(100_000.0, 100.0, 0.5, 0.0, self.limits), 250.0)

    def test_degenerate_equity_or_price_sizes_nothing(self) -> None:
        self.assertAlmostEqual(size_position(0.0, 100.0, 1.0, 0.20, self.limits), 0.0)
        self.assertAlmostEqual(size_position(-500.0, 100.0, 1.0, 0.20, self.limits), 0.0)
        self.assertAlmostEqual(size_position(100_000.0, 0.0, 1.0, 0.20, self.limits), 0.0)
        self.assertAlmostEqual(size_position(100_000.0, -10.0, 1.0, 0.20, self.limits), 0.0)

    def test_fractional_shares_are_returned_unrounded(self) -> None:
        # 100,000 * (0.15/0.45) = 33,333.33 / 300 = 111.11 shares.
        shares = size_position(100_000.0, 300.0, 1.0, 0.45, self.limits)
        self.assertAlmostEqual(shares, (100_000.0 / 3) / 300.0)
        self.assertNotEqual(shares, int(shares))


class TestRiskManagerChecks(unittest.TestCase):
    def setUp(self) -> None:
        self.limits = RiskLimits()
        self.manager = RiskManager(self.limits)
        self.portfolio = Portfolio(cash=100_000.0)
        self.marks = {"AAPL": 100.0}
        self.manager.mark(DAY1, self.portfolio.equity(self.marks))

    def test_ordinary_buy_is_allowed(self) -> None:
        allowed, reason = self.manager.check(
            Order("AAPL", Stance.BUY, 50), self.portfolio, self.marks, self.limits
        )
        self.assertTrue(allowed)
        self.assertEqual(reason, "ok")

    def test_missing_mark_is_rejected(self) -> None:
        allowed, reason = self.manager.check(
            Order("NVDA", Stance.BUY, 10), self.portfolio, {}, self.limits
        )
        self.assertFalse(allowed)
        self.assertIn("no usable mark price", reason)

    def test_position_cap_rejection(self) -> None:
        # 150 * 100 = 15,000 = 15% of equity, above the 10% cap.
        allowed, reason = self.manager.check(
            Order("AAPL", Stance.BUY, 150), self.portfolio, self.marks, self.limits
        )
        self.assertFalse(allowed)
        self.assertIn("position cap", reason)
        self.assertIn("15.00%", reason)

    def test_position_cap_counts_what_is_already_held(self) -> None:
        portfolio = Portfolio(
            cash=92_000.0, positions={"AAPL": Position("AAPL", 80, 100.0)}
        )
        # 8,000 held + 3,000 new = 11% of 100,000.
        allowed, reason = self.manager.check(
            Order("AAPL", Stance.BUY, 30), portfolio, self.marks, self.limits
        )
        self.assertFalse(allowed)
        self.assertIn("position cap", reason)
        # Topping up by 10 shares (9% total) is fine.
        allowed, _ = self.manager.check(
            Order("AAPL", Stance.BUY, 10), portfolio, self.marks, self.limits
        )
        self.assertTrue(allowed)

    def test_an_order_exactly_at_the_cap_is_allowed(self) -> None:
        allowed, _ = self.manager.check(
            Order("AAPL", Stance.BUY, 100), self.portfolio, self.marks, self.limits
        )
        self.assertTrue(allowed)

    def test_gross_exposure_rejection(self) -> None:
        # Eight positions worth 9,750 each = 78,000 invested, 22,000 cash.
        positions = {
            f"SYM{i}": Position(f"SYM{i}", 97.5, 100.0) for i in range(8)
        }
        marks = {symbol: 100.0 for symbol in positions} | {"AAPL": 100.0}
        portfolio = Portfolio(cash=22_000.0, positions=positions)
        self.assertAlmostEqual(portfolio.equity(marks), 100_000.0)

        # 5,000 more is only 5% in the name, but 83% gross.
        allowed, reason = self.manager.check(
            Order("AAPL", Stance.BUY, 50), portfolio, marks, self.limits
        )
        self.assertFalse(allowed)
        self.assertIn("gross exposure cap", reason)
        self.assertIn("83.00%", reason)

    def test_insufficient_cash_rejection(self) -> None:
        portfolio = Portfolio(cash=1_000.0, positions={"AAPL": Position("AAPL", 990, 100.0)})
        marks = {"AAPL": 100.0}
        allowed, reason = self.manager.check(
            Order("AAPL", Stance.BUY, 50), portfolio, marks, self.limits
        )
        self.assertFalse(allowed)
        self.assertIn("insufficient cash", reason)
        # The requirement quoted includes a costs allowance, so it exceeds the
        # bare $5,000 notional — the broker would charge slippage and
        # commission on top, and approving an order it will then refuse burns a
        # new-position slot for a position that never opens.
        self.assertIn("including costs", reason)
        self.assertIn("$5,025.00", reason)
        self.assertIn("have $1,000.00", reason)

    def test_daily_new_position_limit_rejection(self) -> None:
        for i in range(self.limits.max_new_positions_per_day):
            allowed, reason = self.manager.check(
                Order(f"SYM{i}", Stance.BUY, 50),
                self.portfolio,
                {f"SYM{i}": 100.0},
                self.limits,
            )
            self.assertTrue(allowed, reason)
        self.assertEqual(self.manager.new_positions_today, 3)

        allowed, reason = self.manager.check(
            Order("EXTRA", Stance.BUY, 50), self.portfolio, {"EXTRA": 100.0}, self.limits
        )
        self.assertFalse(allowed)
        self.assertIn("daily new-position limit", reason)

    def test_adding_to_an_existing_position_does_not_consume_a_slot(self) -> None:
        portfolio = Portfolio(cash=99_000.0, positions={"AAPL": Position("AAPL", 10, 100.0)})
        for _ in range(5):
            allowed, reason = self.manager.check(
                Order("AAPL", Stance.BUY, 10), portfolio, self.marks, self.limits
            )
            self.assertTrue(allowed, reason)
        self.assertEqual(self.manager.new_positions_today, 0)

    def test_new_day_resets_the_position_counter(self) -> None:
        for i in range(3):
            self.manager.check(
                Order(f"SYM{i}", Stance.BUY, 50),
                self.portfolio,
                {f"SYM{i}": 100.0},
                self.limits,
            )
        self.assertEqual(self.manager.new_positions_today, 3)
        # Marking a new bar on a new date rolls the day automatically.
        self.manager.mark(DAY2, 100_000.0)
        self.assertEqual(self.manager.new_positions_today, 0)
        allowed, _ = self.manager.check(
            Order("EXTRA", Stance.BUY, 50), self.portfolio, {"EXTRA": 100.0}, self.limits
        )
        self.assertTrue(allowed)

    def test_sells_bypass_the_exposure_caps(self) -> None:
        # 90% of equity in one name — far past every buy-side cap, but exiting
        # it must never be blocked.
        portfolio = Portfolio(cash=10_000.0, positions={"AAPL": Position("AAPL", 900, 100.0)})
        allowed, reason = self.manager.check(
            Order("AAPL", Stance.SELL, 900), portfolio, self.marks, self.limits
        )
        self.assertTrue(allowed, reason)

    def test_selling_more_than_held_is_rejected(self) -> None:
        # Equity held at the day's opening 100,000 so the kill switch stays out
        # of it and the shares-on-hand rule is what fires.
        portfolio = Portfolio(cash=90_000.0, positions={"AAPL": Position("AAPL", 100, 100.0)})
        allowed, reason = self.manager.check(
            Order("AAPL", Stance.SELL, 101), portfolio, self.marks, self.limits
        )
        self.assertFalse(allowed)
        self.assertIn("only 100 held", reason)

    def test_no_equity_left_is_rejected(self) -> None:
        manager = RiskManager(RiskLimits())
        broke = Portfolio(cash=0.0)
        allowed, reason = manager.check(
            Order("AAPL", Stance.BUY, 1), broke, self.marks, RiskLimits()
        )
        self.assertFalse(allowed)
        self.assertIn("no equity", reason)

    def test_limits_default_to_the_managers_own(self) -> None:
        allowed, reason = self.manager.check(
            Order("AAPL", Stance.BUY, 150), self.portfolio, self.marks
        )
        self.assertFalse(allowed)
        self.assertIn("position cap", reason)


class TestKillSwitch(unittest.TestCase):
    def setUp(self) -> None:
        self.limits = RiskLimits()  # 3% daily loss, 20% drawdown
        self.manager = RiskManager(self.limits)
        self.manager.mark(DAY1, 100_000.0)

    def test_quiet_days_do_not_trip(self) -> None:
        tripped, reason = self.manager.kill_switch_tripped(98_000.0)
        self.assertFalse(tripped)
        self.assertEqual(reason, "")

    def test_daily_loss_limit_trips(self) -> None:
        tripped, reason = self.manager.kill_switch_tripped(96_500.0)  # -3.5%
        self.assertTrue(tripped)
        self.assertIn("daily loss limit", reason)

    def test_exactly_at_the_daily_limit_trips(self) -> None:
        tripped, _ = self.manager.kill_switch_tripped(97_000.0)  # exactly -3%
        self.assertTrue(tripped)

    def test_drawdown_limit_trips(self) -> None:
        # Generous daily limit so the drawdown rule is what fires.
        manager = RiskManager(RiskLimits(max_daily_loss_pct=0.90, max_drawdown_pct=0.20))
        manager.mark(DAY1, 100_000.0)
        manager.mark(DAY2, 95_000.0)  # new day: open resets, peak stays 100,000
        self.assertAlmostEqual(manager.peak_equity or 0.0, 100_000.0)
        tripped, reason = manager.kill_switch_tripped(79_000.0)  # -21% from peak
        self.assertTrue(tripped)
        self.assertIn("max drawdown", reason)

    def test_peak_tracks_upward_only(self) -> None:
        self.manager.mark(DAY2, 120_000.0)
        self.manager.mark(DAY3, 110_000.0)
        self.assertAlmostEqual(self.manager.peak_equity or 0.0, 120_000.0)

    def test_switch_stays_tripped_after_equity_recovers(self) -> None:
        tripped, reason = self.manager.kill_switch_tripped(96_000.0)
        self.assertTrue(tripped)
        first_reason = reason

        # Equity fully recovers — the switch must not silently release.
        for equity in (100_000.0, 105_000.0, 250_000.0):
            still, why = self.manager.kill_switch_tripped(equity)
            self.assertTrue(still, f"switch released at equity {equity}")
            self.assertEqual(why, first_reason)
        self.assertTrue(self.manager.tripped)

    def test_a_new_day_does_not_clear_the_switch(self) -> None:
        self.manager.kill_switch_tripped(96_000.0)
        self.manager.new_day(DAY2, 100_000.0)
        self.assertEqual(self.manager.new_positions_today, 0)
        tripped, _ = self.manager.kill_switch_tripped(100_000.0)
        self.assertTrue(tripped)
        self.manager.mark(DAY3, 100_000.0)
        self.assertTrue(self.manager.kill_switch_tripped(100_000.0)[0])

    def test_reset_clears_the_switch(self) -> None:
        self.manager.kill_switch_tripped(96_000.0)
        self.assertTrue(self.manager.tripped)
        self.manager.reset()
        self.assertFalse(self.manager.tripped)
        self.assertEqual(self.manager.trip_reason, "")
        tripped, _ = self.manager.kill_switch_tripped(100_000.0)
        self.assertFalse(tripped)

    def test_reset_without_rebaselining_re_trips_on_the_same_loss(self) -> None:
        self.manager.kill_switch_tripped(96_000.0)
        self.manager.reset()
        # Day-open is still 100,000, so 96,000 is still a 4% loss.
        self.assertTrue(self.manager.kill_switch_tripped(96_000.0)[0])

    def test_reset_with_equity_rebaselines(self) -> None:
        self.manager.kill_switch_tripped(96_000.0)
        self.manager.reset(equity=96_000.0)
        self.assertAlmostEqual(self.manager.day_open_equity or 0.0, 96_000.0)
        self.assertAlmostEqual(self.manager.peak_equity or 0.0, 96_000.0)
        self.assertFalse(self.manager.kill_switch_tripped(96_000.0)[0])

    def test_check_rejects_buys_once_tripped(self) -> None:
        portfolio = Portfolio(cash=100_000.0)
        marks = {"AAPL": 100.0}
        self.manager.kill_switch_tripped(96_000.0)

        allowed, reason = self.manager.check(
            Order("AAPL", Stance.BUY, 10), portfolio, marks, self.limits
        )
        self.assertFalse(allowed)
        self.assertIn("kill switch tripped", reason)
        self.assertIn("daily loss limit", reason)

    def test_tripped_switch_still_permits_exits(self) -> None:
        """The switch stops the book adding risk; it must not trap it.

        Blocking exits would mean the control that fires on a bad day also
        prevents de-risking on that day, which is how a limit breach becomes a
        much larger loss.
        """
        marks = {"AAPL": 100.0}
        self.manager.kill_switch_tripped(96_000.0)
        self.assertTrue(self.manager.tripped)

        held = Portfolio(cash=0.0, positions={"AAPL": Position("AAPL", 10, 100.0)})
        allowed, reason = self.manager.check(
            Order("AAPL", Stance.SELL, 10), held, marks, self.limits
        )
        self.assertTrue(allowed, f"exit should survive a trip, got: {reason}")

        # The switch stays tripped — permitting the exit must not clear it.
        self.assertTrue(self.manager.tripped)
        allowed, _ = self.manager.check(
            Order("AAPL", Stance.BUY, 1), Portfolio(cash=100_000.0), marks, self.limits
        )
        self.assertFalse(allowed)

    def test_check_trips_the_switch_from_the_current_equity(self) -> None:
        # Book is down 5% since the open; the first order of the bar should
        # both trip the switch and be refused.
        portfolio = Portfolio(cash=95_000.0)
        allowed, reason = self.manager.check(
            Order("AAPL", Stance.BUY, 10), portfolio, {"AAPL": 100.0}, self.limits
        )
        self.assertFalse(allowed)
        self.assertIn("kill switch tripped", reason)
        self.assertTrue(self.manager.tripped)

    def test_no_baseline_means_no_trip(self) -> None:
        fresh = RiskManager(self.limits)
        self.assertFalse(fresh.kill_switch_tripped(1.0)[0])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

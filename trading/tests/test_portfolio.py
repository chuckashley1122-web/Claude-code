"""Tests for the portfolio accounting and the paper broker that drives it.

The numbers in here are hand-computed and written out longhand on purpose: an
accounting bug that a test reproduces from the same code it is testing is worse
than no test at all.
"""

from __future__ import annotations

import unittest
from datetime import date

from trading.alpha_agents.config import CostModel
from trading.alpha_agents.execution import PaperBroker
from trading.alpha_agents.models import Fill, Order, Position, Stance
from trading.alpha_agents.portfolio import Portfolio

DAY = date(2025, 1, 6)


def buy(symbol: str, quantity: float, price: float, commission: float = 0.0) -> Fill:
    return Fill(symbol, Stance.BUY, quantity, price, DAY, commission=commission)


def sell(symbol: str, quantity: float, price: float, commission: float = 0.0) -> Fill:
    return Fill(symbol, Stance.SELL, quantity, price, DAY, commission=commission)


class TestPortfolioAccounting(unittest.TestCase):
    def setUp(self) -> None:
        self.portfolio = Portfolio(cash=100_000.0)

    def test_single_buy_sets_cash_and_basis(self) -> None:
        self.portfolio.apply(buy("AAPL", 100, 50.0, commission=1.0))

        # 100 * 50 = 5,000 notional, plus 1.00 commission.
        self.assertAlmostEqual(self.portfolio.cash, 94_999.0)
        position = self.portfolio.positions["AAPL"]
        self.assertAlmostEqual(position.quantity, 100.0)
        self.assertAlmostEqual(position.avg_price, 50.0)
        # Commission is an immediate, certain loss.
        self.assertAlmostEqual(self.portfolio.realized_pnl, -1.0)

    def test_buy_buy_then_partial_sell_is_exact(self) -> None:
        self.portfolio.apply(buy("AAPL", 100, 50.0, commission=1.0))
        self.portfolio.apply(buy("AAPL", 50, 60.0, commission=1.0))

        # Weighted average: (100*50 + 50*60) / 150 = 8,000 / 150 = 53.3333...
        position = self.portfolio.positions["AAPL"]
        self.assertAlmostEqual(position.quantity, 150.0)
        self.assertAlmostEqual(position.avg_price, 8_000.0 / 150.0)
        # 100,000 - 5,000 - 1 - 3,000 - 1
        self.assertAlmostEqual(self.portfolio.cash, 91_998.0)
        self.assertAlmostEqual(self.portfolio.realized_pnl, -2.0)

        self.portfolio.apply(sell("AAPL", 60, 70.0, commission=1.0))

        # Realised: (70 - 53.3333...) * 60 = 4,200 - 3,200 = 1,000 gross,
        # less 3.00 of cumulative commission = 997.00.
        self.assertAlmostEqual(self.portfolio.realized_pnl, 997.0)
        # Cash: 91,998 + 4,200 - 1
        self.assertAlmostEqual(self.portfolio.cash, 96_197.0)
        # A sale does not move the average cost of what is left.
        position = self.portfolio.positions["AAPL"]
        self.assertAlmostEqual(position.quantity, 90.0)
        self.assertAlmostEqual(position.avg_price, 8_000.0 / 150.0)

    def test_equity_identity_holds_after_round_trip(self) -> None:
        self.portfolio.apply(buy("AAPL", 100, 50.0, commission=1.0))
        self.portfolio.apply(buy("AAPL", 50, 60.0, commission=1.0))
        self.portfolio.apply(sell("AAPL", 60, 70.0, commission=1.0))
        marks = {"AAPL": 70.0}

        # 96,197 cash + 90 shares * 70
        self.assertAlmostEqual(self.portfolio.equity(marks), 102_497.0)
        self.assertAlmostEqual(
            self.portfolio.equity(marks),
            self.portfolio.initial_cash
            + self.portfolio.realized_pnl
            + self.portfolio.unrealized_pnl(marks),
        )

    def test_full_sell_closes_position_and_realises_loss(self) -> None:
        self.portfolio.apply(buy("MSFT", 10, 100.0, commission=1.0))
        self.portfolio.apply(sell("MSFT", 10, 90.0, commission=1.0))

        self.assertNotIn("MSFT", self.portfolio.positions)
        # (90 - 100) * 10 = -100 gross, less 2.00 of commission.
        self.assertAlmostEqual(self.portfolio.realized_pnl, -102.0)
        self.assertAlmostEqual(self.portfolio.cash, 100_000.0 - 1_000.0 - 1.0 + 900.0 - 1.0)

    def test_over_selling_raises(self) -> None:
        self.portfolio.apply(buy("AAPL", 10, 50.0))
        with self.assertRaises(ValueError) as ctx:
            self.portfolio.apply(sell("AAPL", 11, 50.0))
        self.assertIn("only 10", str(ctx.exception))
        # The failed sell left the book alone.
        self.assertAlmostEqual(self.portfolio.positions["AAPL"].quantity, 10.0)

    def test_selling_an_unheld_symbol_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.portfolio.apply(sell("NVDA", 1, 100.0))

    def test_dust_residual_closes_the_position(self) -> None:
        self.portfolio.apply(buy("AAPL", 1.0, 100.0))
        # Leaves 1e-10 shares behind — below DUST, so the position should go.
        self.portfolio.apply(sell("AAPL", 1.0 - 1e-10, 100.0))
        self.assertNotIn("AAPL", self.portfolio.positions)

    def test_dust_overshoot_is_tolerated_not_raised(self) -> None:
        self.portfolio.apply(buy("AAPL", 1.0, 100.0))
        self.portfolio.apply(sell("AAPL", 1.0 + 1e-12, 100.0))
        self.assertNotIn("AAPL", self.portfolio.positions)

    def test_repeated_fractional_trades_do_not_leave_dust(self) -> None:
        self.portfolio.apply(buy("AAPL", 0.1, 100.0))
        self.portfolio.apply(buy("AAPL", 0.2, 100.0))
        self.portfolio.apply(sell("AAPL", 0.3, 100.0))
        self.assertEqual(self.portfolio.positions, {})

    def test_material_residual_survives(self) -> None:
        self.portfolio.apply(buy("AAPL", 1.0, 100.0))
        self.portfolio.apply(sell("AAPL", 0.999, 100.0))
        self.assertAlmostEqual(self.portfolio.positions["AAPL"].quantity, 0.001)

    def test_rejects_degenerate_fills(self) -> None:
        with self.assertRaises(ValueError):
            self.portfolio.apply(Fill("AAPL", Stance.HOLD, 1, 10.0, DAY))
        with self.assertRaises(ValueError):
            self.portfolio.apply(Fill("AAPL", Stance.BUY, 0, 10.0, DAY))
        with self.assertRaises(ValueError):
            self.portfolio.apply(Fill("AAPL", Stance.BUY, 1, -10.0, DAY))


class TestPortfolioValuation(unittest.TestCase):
    def setUp(self) -> None:
        self.portfolio = Portfolio(
            cash=50_000.0,
            positions={
                "AAPL": Position("AAPL", 100, 50.0),
                "MSFT": Position("MSFT", 200, 25.0),
            },
        )

    def test_equity_and_weights(self) -> None:
        marks = {"AAPL": 60.0, "MSFT": 30.0}
        # 50,000 cash + 6,000 + 6,000
        self.assertAlmostEqual(self.portfolio.equity(marks), 62_000.0)
        self.assertAlmostEqual(self.portfolio.position_weight("AAPL", marks), 6_000 / 62_000)
        self.assertAlmostEqual(self.portfolio.position_weight("NVDA", marks), 0.0)

    def test_missing_mark_falls_back_to_average_cost(self) -> None:
        # No MSFT mark: valued at its 25.00 basis rather than dropped to zero.
        self.assertAlmostEqual(self.portfolio.equity({"AAPL": 60.0}), 50_000 + 6_000 + 5_000)

    def test_weight_is_zero_when_equity_is_zero(self) -> None:
        broke = Portfolio(cash=0.0, positions={"AAPL": Position("AAPL", 100, 50.0)})
        self.assertAlmostEqual(broke.position_weight("AAPL", {"AAPL": 0.0}), 0.0)

    def test_snapshot_is_sorted_and_complete(self) -> None:
        marks = {"AAPL": 60.0, "MSFT": 30.0}
        snapshot = self.portfolio.snapshot(DAY, marks)
        self.assertEqual(snapshot.ts, DAY)
        self.assertAlmostEqual(snapshot.cash, 50_000.0)
        self.assertAlmostEqual(snapshot.equity, 62_000.0)
        self.assertEqual([p.symbol for p in snapshot.positions], ["AAPL", "MSFT"])
        self.assertAlmostEqual(snapshot.exposure, 12_000 / 62_000)

    def test_negative_starting_cash_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Portfolio(cash=-1.0)


class TestPaperBroker(unittest.TestCase):
    def setUp(self) -> None:
        self.portfolio = Portfolio(cash=100_000.0)
        # 100 bps = 1% slippage keeps the arithmetic legible.
        self.costs = CostModel(
            commission_per_share=0.01, commission_minimum=1.00, slippage_bps=100.0
        )
        self.broker = PaperBroker(self.portfolio, self.costs)

    def test_identity(self) -> None:
        self.assertEqual(self.broker.name, "paper")
        self.assertFalse(self.broker.is_live)

    def test_buy_slippage_is_adverse(self) -> None:
        fill = self.broker.submit(Order("AAPL", Stance.BUY, 100), DAY, 100.0)
        assert fill is not None
        # 1% above the reference: 101.00.
        self.assertAlmostEqual(fill.price, 101.0)
        self.assertAlmostEqual(fill.slippage, 100.0)  # 1.00/share * 100 shares
        self.assertAlmostEqual(self.portfolio.positions["AAPL"].avg_price, 101.0)

    def test_sell_slippage_is_adverse(self) -> None:
        self.broker.submit(Order("AAPL", Stance.BUY, 100), DAY, 100.0)
        fill = self.broker.submit(Order("AAPL", Stance.SELL, 100), DAY, 100.0)
        assert fill is not None
        # 1% below the reference: 99.00.
        self.assertAlmostEqual(fill.price, 99.0)
        self.assertAlmostEqual(fill.slippage, 100.0)

    def test_round_trip_at_a_flat_price_loses_money(self) -> None:
        self.broker.submit(Order("AAPL", Stance.BUY, 100), DAY, 100.0)
        self.broker.submit(Order("AAPL", Stance.SELL, 100), DAY, 100.0)
        # Bought at 101, sold at 99: -200 gross, less 2.00 of commission.
        self.assertAlmostEqual(self.portfolio.realized_pnl, -202.0)
        self.assertAlmostEqual(self.portfolio.cash, 100_000.0 - 202.0)
        self.assertEqual(len(self.broker.fills), 2)

    def test_commission_uses_per_share_when_above_minimum(self) -> None:
        fill = self.broker.submit(Order("AAPL", Stance.BUY, 500), DAY, 10.0)
        assert fill is not None
        # 500 * 0.01 = 5.00 > 1.00 minimum.
        self.assertAlmostEqual(fill.commission, 5.0)

    def test_commission_respects_the_minimum(self) -> None:
        fill = self.broker.submit(Order("AAPL", Stance.BUY, 10), DAY, 10.0)
        assert fill is not None
        # 10 * 0.01 = 0.10, floored at the 1.00 minimum.
        self.assertAlmostEqual(fill.commission, 1.0)

    def test_insufficient_cash_returns_none_and_leaves_book_untouched(self) -> None:
        before_cash = self.portfolio.cash
        fill = self.broker.submit(Order("AAPL", Stance.BUY, 10_000), DAY, 100.0)
        self.assertIsNone(fill)
        self.assertAlmostEqual(self.portfolio.cash, before_cash)
        self.assertEqual(self.portfolio.positions, {})
        self.assertEqual(self.broker.fills, [])
        assert self.broker.last_rejection is not None
        self.assertIn("insufficient cash", self.broker.last_rejection)

    def test_selling_unheld_shares_returns_none(self) -> None:
        fill = self.broker.submit(Order("AAPL", Stance.SELL, 10), DAY, 100.0)
        self.assertIsNone(fill)
        self.assertAlmostEqual(self.portfolio.cash, 100_000.0)
        assert self.broker.last_rejection is not None
        self.assertIn("only 0 held", self.broker.last_rejection)

    def test_oversized_sell_returns_none_and_keeps_position(self) -> None:
        self.broker.submit(Order("AAPL", Stance.BUY, 10), DAY, 100.0)
        cash_after_buy = self.portfolio.cash
        fill = self.broker.submit(Order("AAPL", Stance.SELL, 11), DAY, 100.0)
        self.assertIsNone(fill)
        self.assertAlmostEqual(self.portfolio.cash, cash_after_buy)
        self.assertAlmostEqual(self.portfolio.positions["AAPL"].quantity, 10.0)
        self.assertEqual(len(self.broker.fills), 1)

    def test_commission_is_included_in_the_affordability_check(self) -> None:
        broker = PaperBroker(Portfolio(cash=101.0), self.costs)
        # 1 share fills at 101.00 and carries a 1.00 minimum commission: 102.00.
        self.assertIsNone(broker.submit(Order("AAPL", Stance.BUY, 1), DAY, 100.0))
        assert broker.last_rejection is not None
        self.assertIn("102.00", broker.last_rejection)

    def test_invalid_reference_price_returns_none(self) -> None:
        self.assertIsNone(self.broker.submit(Order("AAPL", Stance.BUY, 1), DAY, 0.0))
        assert self.broker.last_rejection is not None
        self.assertIn("invalid reference price", self.broker.last_rejection)

    def test_unmarketable_limit_is_not_filled(self) -> None:
        # Fills at 101.00, above the 100.50 limit.
        order = Order("AAPL", Stance.BUY, 10, limit_price=100.50)
        self.assertIsNone(self.broker.submit(order, DAY, 100.0))
        assert self.broker.last_rejection is not None
        self.assertIn("limit not marketable", self.broker.last_rejection)

    def test_marketable_limit_fills(self) -> None:
        order = Order("AAPL", Stance.BUY, 10, limit_price=101.0)
        fill = self.broker.submit(order, DAY, 100.0)
        assert fill is not None
        self.assertAlmostEqual(fill.price, 101.0)

    def test_last_rejection_clears_after_a_good_fill(self) -> None:
        self.broker.submit(Order("AAPL", Stance.BUY, 10_000), DAY, 100.0)
        self.assertIsNotNone(self.broker.last_rejection)
        self.broker.submit(Order("AAPL", Stance.BUY, 10), DAY, 100.0)
        self.assertIsNone(self.broker.last_rejection)

    def test_snapshot_delegates_to_the_portfolio(self) -> None:
        self.broker.submit(Order("AAPL", Stance.BUY, 100), DAY, 100.0)
        snapshot = self.broker.snapshot(DAY, {"AAPL": 110.0})
        self.assertEqual(snapshot.ts, DAY)
        self.assertEqual([p.symbol for p in snapshot.positions], ["AAPL"])
        self.assertAlmostEqual(snapshot.equity, self.portfolio.equity({"AAPL": 110.0}))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

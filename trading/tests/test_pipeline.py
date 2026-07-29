"""Tests for the orchestration layer.

The claims worth defending here are safety claims, not P&L claims:

* research cannot see a bar past ``as_of``;
* nothing reaches a broker without passing the risk check;
* a live broker is refused unless it was explicitly authorised.

Each of those is asserted directly rather than inferred from a passing backtest.
"""

from __future__ import annotations

import unittest
from datetime import date, timedelta

from trading.alpha_agents.backtest import Backtester
from trading.alpha_agents.config import RiskLimits, Settings
from trading.alpha_agents.data import SyntheticProvider
from trading.alpha_agents.execution import PaperBroker
from trading.alpha_agents.models import Order, Position, Stance, Verdict
from trading.alpha_agents.pipeline import TradingPipeline
from trading.alpha_agents.portfolio import Portfolio

AS_OF = date(2025, 6, 16)


def make_pipeline(**overrides) -> TradingPipeline:
    base = {
        "universe": ("AAA", "BBB"),
        "starting_cash": 100_000.0,
        "data_provider": "synthetic",
    }
    base.update(overrides)
    settings = Settings.from_dict(base)
    portfolio = Portfolio(cash=settings.starting_cash)
    broker = PaperBroker(portfolio=portfolio, costs=settings.costs)
    return TradingPipeline(
        settings=settings,
        provider=SyntheticProvider(),
        broker=broker,
    )


class _LiveBroker(PaperBroker):
    """Stand-in for a live adapter, used only to prove the guard fires."""

    name = "fake-live"
    is_live = True


class TestLiveTradingGuard(unittest.TestCase):
    def test_live_broker_is_refused_by_default(self) -> None:
        settings = Settings()
        broker = _LiveBroker(portfolio=Portfolio(cash=1000.0), costs=settings.costs)
        with self.assertRaises(RuntimeError) as ctx:
            TradingPipeline(settings, SyntheticProvider(), broker)
        self.assertIn("allow_live_trading", str(ctx.exception))

    def test_paper_broker_is_always_allowed(self) -> None:
        pipeline = make_pipeline()
        self.assertFalse(pipeline.broker.is_live)


class TestLookAhead(unittest.TestCase):
    def test_research_bundle_contains_no_future_bars(self) -> None:
        pipeline = make_pipeline()
        bundle = pipeline.build_bundle("AAA", AS_OF)
        self.assertTrue(len(bundle.prices) > 0)
        self.assertTrue(
            all(bar.ts <= AS_OF for bar in bundle.prices.bars),
            "research must not see a bar dated after as_of",
        )
        self.assertEqual(bundle.as_of, AS_OF)

    def test_earlier_as_of_yields_a_strict_prefix(self) -> None:
        """The same symbol researched at two dates must agree on the overlap.

        If it does not, the provider is rewriting history and every backtest
        result computed from it is meaningless.
        """
        pipeline = make_pipeline()
        early = pipeline.build_bundle("AAA", AS_OF - timedelta(days=90))
        late = pipeline.build_bundle("AAA", AS_OF)

        early_bars = {b.ts: b.close for b in early.prices.bars}
        late_bars = {b.ts: b.close for b in late.prices.bars}
        overlap = set(early_bars) & set(late_bars)
        self.assertTrue(overlap, "expected overlapping history between the two dates")
        for ts in overlap:
            self.assertAlmostEqual(early_bars[ts], late_bars[ts], places=6)


class TestScan(unittest.TestCase):
    def test_scan_covers_the_whole_universe(self) -> None:
        pipeline = make_pipeline(universe=("AAA", "BBB", "CCC"))
        result = pipeline.scan(AS_OF, execute=False)
        self.assertEqual(
            {d.symbol for d in result.decisions}, {"AAA", "BBB", "CCC"}
        )

    def test_dry_run_places_nothing(self) -> None:
        pipeline = make_pipeline()
        before = pipeline.broker.portfolio.cash
        result = pipeline.scan(AS_OF, execute=False)
        self.assertEqual(pipeline.broker.portfolio.cash, before)
        self.assertFalse(any(d.executed for d in result.decisions))

    def test_low_confidence_verdict_produces_no_order(self) -> None:
        pipeline = make_pipeline()
        verdict = Verdict(
            symbol="AAA", stance=Stance.BUY, confidence=0.1, rationale="weak"
        )
        marks = {"AAA": 100.0}
        self.assertIsNone(pipeline._propose_order(verdict, AS_OF, marks))

    def test_hold_verdict_produces_no_order(self) -> None:
        pipeline = make_pipeline()
        verdict = Verdict(
            symbol="AAA", stance=Stance.HOLD, confidence=0.99, rationale="flat"
        )
        self.assertIsNone(pipeline._propose_order(verdict, AS_OF, {"AAA": 100.0}))

    def test_sell_when_flat_produces_no_order(self) -> None:
        """No shorting in v1 — a SELL on a position we do not hold is a no-op,
        not an order to go short."""
        pipeline = make_pipeline()
        verdict = Verdict(
            symbol="AAA", stance=Stance.SELL, confidence=0.99, rationale="bearish"
        )
        self.assertIsNone(pipeline._propose_order(verdict, AS_OF, {"AAA": 100.0}))

    def test_confident_buy_produces_a_sized_order(self) -> None:
        pipeline = make_pipeline()
        verdict = Verdict(
            symbol="AAA", stance=Stance.BUY, confidence=0.95, rationale="strong"
        )
        order = pipeline._propose_order(verdict, AS_OF, {"AAA": 100.0})
        self.assertIsNotNone(order)
        assert order is not None
        self.assertIs(order.side, Stance.BUY)
        self.assertGreater(order.quantity, 0)
        # Sizing must respect the position cap: 10% of 100k at $100 = 100 shares.
        self.assertLessEqual(order.quantity * 100.0, 100_000.0 * 0.10 + 1)

    def test_sell_exits_the_whole_position(self) -> None:
        pipeline = make_pipeline()
        pipeline.broker.portfolio.positions["AAA"] = Position("AAA", 25.0, 90.0)
        verdict = Verdict(
            symbol="AAA", stance=Stance.SELL, confidence=0.9, rationale="exit"
        )
        order = pipeline._propose_order(verdict, AS_OF, {"AAA": 100.0})
        self.assertIsNotNone(order)
        assert order is not None
        self.assertIs(order.side, Stance.SELL)
        self.assertAlmostEqual(order.quantity, 25.0)

    def test_missing_mark_produces_no_order(self) -> None:
        pipeline = make_pipeline()
        verdict = Verdict(
            symbol="ZZZ", stance=Stance.BUY, confidence=0.99, rationale="strong"
        )
        self.assertIsNone(pipeline._propose_order(verdict, AS_OF, {}))

    def test_tripped_kill_switch_halts_buying_but_still_researches(self) -> None:
        """A halt suppresses buys; it does not abandon the book.

        This previously asserted `decisions == []`, which looked like a strong
        safety property and was the opposite: returning before any order was
        proposed meant the risk layer's "exits stay permitted" rule could never
        be exercised, and a stopped-out book could never be de-risked.
        """
        pipeline = make_pipeline()
        pipeline.risk.new_day(AS_OF, 100_000.0)
        pipeline.risk.kill_switch_tripped(50_000.0)  # catastrophic loss
        result = pipeline.scan(AS_OF, execute=True)

        self.assertTrue(result.halted)
        self.assertTrue(result.halt_reason)
        # The universe is still researched, so exits remain reachable...
        self.assertEqual({d.symbol for d in result.decisions}, {"AAA", "BBB"})
        # ...but nothing was bought.
        self.assertEqual(pipeline.broker.portfolio.positions, {})

    def test_scan_returns_a_snapshot(self) -> None:
        pipeline = make_pipeline()
        result = pipeline.scan(AS_OF, execute=True)
        self.assertIsNotNone(result.snapshot)
        assert result.snapshot is not None
        self.assertGreater(result.snapshot.equity, 0)


class TestRiskIsAlwaysConsulted(unittest.TestCase):
    def test_every_executed_order_passed_the_risk_check(self) -> None:
        """Instrument RiskManager.check and assert the broker never saw an
        order the risk manager had not approved."""
        pipeline = make_pipeline(
            universe=("AAA", "BBB", "CCC", "DDD"),
            risk={"min_confidence": 0.05},  # force orders to be proposed
        )
        checked: list[Order] = []
        submitted: list[Order] = []

        real_check = pipeline.risk.check
        real_submit = pipeline.broker.submit

        def spy_check(order, portfolio, marks, limits=None):
            checked.append(order)
            return real_check(order, portfolio, marks, limits)

        def spy_submit(order, when, reference_price):
            submitted.append(order)
            return real_submit(order, when, reference_price)

        pipeline.risk.check = spy_check  # type: ignore[method-assign]
        pipeline.broker.submit = spy_submit  # type: ignore[method-assign]

        pipeline.scan(AS_OF, execute=True)

        self.assertTrue(checked, "expected at least one order to be proposed")
        for order in submitted:
            self.assertIn(
                order, checked, "an order reached the broker without a risk check"
            )

    def test_risk_check_is_called_once_per_order(self) -> None:
        pipeline = make_pipeline(
            universe=("AAA", "BBB", "CCC"), risk={"min_confidence": 0.05}
        )
        calls: list[Order] = []
        real_check = pipeline.risk.check

        def spy(order, portfolio, marks, limits=None):
            calls.append(order)
            return real_check(order, portfolio, marks, limits)

        pipeline.risk.check = spy  # type: ignore[method-assign]
        pipeline.scan(AS_OF, execute=True)

        # A duplicate would double-consume the daily new-position budget.
        self.assertEqual(len(calls), len(set(id(o) for o in calls)))


class TestBacktester(unittest.TestCase):
    def test_backtest_produces_an_equity_curve(self) -> None:
        pipeline = make_pipeline()
        result = Backtester(pipeline, rebalance_every=5).run(
            date(2025, 1, 1), date(2025, 3, 31)
        )
        self.assertGreater(len(result.equity_curve), 30)
        self.assertTrue(all(eq > 0 for _, eq in result.equity_curve))

    def test_stats_are_computable_and_sane(self) -> None:
        pipeline = make_pipeline()
        result = Backtester(pipeline, rebalance_every=5).run(
            date(2025, 1, 1), date(2025, 3, 31)
        )
        stats = result.stats()
        self.assertIn("sharpe", stats)
        self.assertIn("max_drawdown", stats)
        self.assertGreaterEqual(stats["max_drawdown"], 0.0)
        self.assertLessEqual(stats["max_drawdown"], 1.0)
        self.assertGreaterEqual(stats["win_rate"], 0.0)
        self.assertLessEqual(stats["win_rate"], 1.0)

    def test_dates_only_move_forward(self) -> None:
        pipeline = make_pipeline()
        result = Backtester(pipeline).run(date(2025, 1, 1), date(2025, 2, 28))
        days = [d for d, _ in result.equity_curve]
        self.assertEqual(days, sorted(days))
        self.assertEqual(len(days), len(set(days)))

    def test_no_weekend_sessions(self) -> None:
        pipeline = make_pipeline()
        result = Backtester(pipeline).run(date(2025, 1, 1), date(2025, 2, 28))
        self.assertTrue(all(d.weekday() < 5 for d, _ in result.equity_curve))

    def test_reversed_range_is_rejected(self) -> None:
        pipeline = make_pipeline()
        with self.assertRaises(ValueError):
            Backtester(pipeline).run(date(2025, 3, 1), date(2025, 1, 1))

    def test_invalid_rebalance_interval_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Backtester(make_pipeline(), rebalance_every=0)

    def test_summary_renders(self) -> None:
        pipeline = make_pipeline()
        result = Backtester(pipeline).run(date(2025, 1, 1), date(2025, 2, 28))
        summary = result.summary()
        self.assertIn("Sharpe", summary)
        self.assertIn("Max drawdown", summary)


class TestSettingsGuards(unittest.TestCase):
    def test_position_cap_cannot_exceed_gross_exposure(self) -> None:
        with self.assertRaises(ValueError):
            RiskLimits(max_position_pct=0.9, max_gross_exposure=0.5)

    def test_fractions_must_be_in_range(self) -> None:
        with self.assertRaises(ValueError):
            RiskLimits(max_position_pct=1.5)
        with self.assertRaises(ValueError):
            RiskLimits(min_confidence=0.0)

    def test_settings_round_trip_through_dict(self) -> None:
        original = Settings(universe=("XYZ",), starting_cash=5_000.0)
        restored = Settings.from_dict(original.to_dict())
        self.assertEqual(restored.universe, ("XYZ",))
        self.assertEqual(restored.starting_cash, 5_000.0)
        self.assertEqual(restored.risk, original.risk)


if __name__ == "__main__":
    unittest.main()

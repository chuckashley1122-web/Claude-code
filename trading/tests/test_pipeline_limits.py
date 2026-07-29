"""Limits driven through `scan()`, not through the risk manager in isolation.

Every limit here already had a unit test that passed. They passed because they
called `RiskManager` directly, against a baseline set on the previous line. The
pipeline reached those same limits differently and defeated two of them, so the
green suite was asserting behaviour the product could not actually reach.

These tests drive the limits the way the product does.
"""

from __future__ import annotations

import unittest
from datetime import date, timedelta

from trading.alpha_agents.config import Settings
from trading.alpha_agents.data import SyntheticProvider
from trading.alpha_agents.execution import PaperBroker
from trading.alpha_agents.models import Position, Stance, Verdict
from trading.alpha_agents.pipeline import TradingPipeline
from trading.alpha_agents.portfolio import Portfolio

DAY1 = date(2025, 6, 16)
DAY2 = date(2025, 6, 17)


class FixedVerdictPipeline(TradingPipeline):
    """Pins research output so the tests exercise limits, not the committee."""

    forced: Verdict | None = None

    def research(self, symbol: str, as_of: date) -> Verdict:
        if self.forced is not None:
            return Verdict(
                symbol=symbol,
                stance=self.forced.stance,
                confidence=self.forced.confidence,
                rationale=self.forced.rationale,
            )
        return super().research(symbol, as_of)


def build(universe=("AAA", "BBB", "CCC", "DDD", "EEE"), **risk) -> FixedVerdictPipeline:
    settings = Settings.from_dict(
        {"universe": list(universe), "starting_cash": 100_000.0, "risk": risk or {}}
    )
    portfolio = Portfolio(cash=settings.starting_cash)
    return FixedVerdictPipeline(
        settings=settings,
        provider=SyntheticProvider(),
        broker=PaperBroker(portfolio=portfolio, costs=settings.costs),
    )


class TestDailyLossLimitReachesThePipeline(unittest.TestCase):
    def test_daily_loss_limit_halts_a_later_scan(self) -> None:
        """The bug this pins: `scan` used to re-baseline the day's opening
        equity to current equity before evaluating the limit, so the daily loss
        term was always exactly zero and the 3% stop could never fire."""
        pipeline = build()
        pipeline.risk.mark(DAY1, 100_000.0)

        # Day two opens 5% down — past the 3% daily limit.
        pipeline.broker.portfolio.cash = 95_000.0
        result = pipeline.scan(DAY2, execute=True)

        self.assertTrue(result.halted, "a 5% daily loss must halt new buying")
        self.assertIn("daily loss", result.halt_reason.lower())

    def test_a_small_daily_loss_does_not_halt(self) -> None:
        pipeline = build()
        pipeline.risk.mark(DAY1, 100_000.0)
        pipeline.broker.portfolio.cash = 99_000.0  # -1%, inside the limit
        result = pipeline.scan(DAY2, execute=True)
        self.assertFalse(result.halted)

    def test_the_day_baseline_survives_repeated_same_day_scans(self) -> None:
        pipeline = build()
        pipeline.risk.mark(DAY1, 100_000.0)
        opening = pipeline.risk.day_open_equity
        pipeline.scan(DAY1, execute=False)
        pipeline.scan(DAY1, execute=False)
        self.assertEqual(pipeline.risk.day_open_equity, opening)


class TestDailyNewPositionBudget(unittest.TestCase):
    def test_rerunning_a_scan_does_not_refill_the_budget(self) -> None:
        """Re-running a scan on the same date used to hand back a fresh budget
        of three new positions on every invocation."""
        pipeline = build(universe=tuple(f"S{i}" for i in range(8)))
        pipeline.forced = Verdict("X", Stance.BUY, 0.99, "forced")

        for _ in range(4):
            pipeline.scan(DAY1, execute=True)

        opened = len(pipeline.broker.portfolio.positions)
        cap = pipeline.settings.risk.max_new_positions_per_day
        self.assertLessEqual(
            opened, cap, f"opened {opened} positions against a daily cap of {cap}"
        )


class TestHaltStillPermitsExits(unittest.TestCase):
    def test_a_tripped_switch_does_not_strand_the_book(self) -> None:
        """The risk layer permits exits while tripped. The pipeline used to
        return before proposing any order, so the contract was unreachable and
        a stopped-out book could never be de-risked."""
        pipeline = build(universe=("AAA",))
        pipeline.broker.portfolio.cash = 0.0
        pipeline.broker.portfolio.positions["AAA"] = Position("AAA", 100.0, 100.0)

        pipeline.risk.mark(DAY1, 100_000.0)
        pipeline.risk.kill_switch_tripped(50_000.0)  # latch it
        pipeline.forced = Verdict("AAA", Stance.SELL, 0.99, "get out")

        result = pipeline.scan(DAY2, execute=True)

        self.assertTrue(result.halted)
        self.assertNotIn(
            "AAA",
            pipeline.broker.portfolio.positions,
            "an exit must still be reachable while the switch is tripped",
        )

    def test_a_tripped_switch_still_blocks_buys(self) -> None:
        pipeline = build(universe=("AAA", "BBB"))
        pipeline.risk.mark(DAY1, 100_000.0)
        pipeline.risk.kill_switch_tripped(50_000.0)
        pipeline.forced = Verdict("X", Stance.BUY, 0.99, "forced")

        result = pipeline.scan(DAY2, execute=True)

        self.assertTrue(result.halted)
        self.assertEqual(pipeline.broker.portfolio.positions, {})
        self.assertFalse(any(d.executed for d in result.decisions))


class TestUnmarkedPositions(unittest.TestCase):
    def test_an_unmarked_holding_suppresses_new_buying(self) -> None:
        """A position with no mark is valued at cost, so equity is unreliable
        and the drawdown limit is blind. Do not add risk on top of a number we
        cannot trust."""
        pipeline = build(universe=("AAA",))
        pipeline.broker.portfolio.positions["GHOST"] = Position("GHOST", 10.0, 100.0)
        pipeline.forced = Verdict("AAA", Stance.BUY, 0.99, "forced")

        original_marks = pipeline._marks

        def marks_without_ghost(as_of):
            marks = original_marks(as_of)
            marks.pop("GHOST", None)
            return marks

        pipeline._marks = marks_without_ghost  # type: ignore[method-assign]
        result = pipeline.scan(DAY1, execute=True)

        self.assertIn("GHOST", result.unmarked_positions)
        self.assertNotIn("AAA", pipeline.broker.portfolio.positions)


class TestVolatilityTargetingActuallyBinds(unittest.TestCase):
    def test_a_high_vol_name_is_sized_smaller_than_the_cap(self) -> None:
        """With the previous default vol target the position cap dominated at
        every realistic volatility, so the vol term never did any work and a
        60%-vol name got the same size as a 12%-vol name."""
        from trading.alpha_agents.risk import size_position

        limits = Settings().risk
        calm = size_position(
            equity=100_000.0, price=100.0, confidence=0.8, annual_vol=0.15, limits=limits
        )
        wild = size_position(
            equity=100_000.0, price=100.0, confidence=0.8, annual_vol=0.80, limits=limits
        )
        self.assertLess(wild, calm, "a high-vol name must be sized smaller")
        cap_shares = limits.max_position_pct * 100_000.0 / 100.0
        self.assertLessEqual(calm, cap_shares + 1e-9)


if __name__ == "__main__":
    unittest.main()

"""Walk-forward backtest and performance statistics.

The engine steps forward one trading day at a time and hands the pipeline only
``as_of``. Every provider call is sliced with ``PriceSeries.up_to(as_of)``, so
a strategy physically cannot read a bar it would not have had. That property is
the only thing separating a backtest from a plausible-looking fiction, and it is
enforced structurally rather than by convention.

Costs are charged through the broker's cost model, so results here already
include commission and slippage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Sequence

from . import indicators as ind
from .models import AccountSnapshot
from .pipeline import Decision, ScanResult, TradingPipeline


@dataclass
class BacktestResult:
    start: date
    end: date
    equity_curve: list[tuple[date, float]] = field(default_factory=list)
    snapshots: list[AccountSnapshot] = field(default_factory=list)
    decisions: list[tuple[date, Decision]] = field(default_factory=list)
    halted_days: list[tuple[date, str]] = field(default_factory=list)

    @property
    def equities(self) -> list[float]:
        return [e for _, e in self.equity_curve]

    @property
    def daily_returns(self) -> list[float]:
        eq = self.equities
        return [
            (eq[i] - eq[i - 1]) / eq[i - 1]
            for i in range(1, len(eq))
            if eq[i - 1] > 0
        ]

    def stats(self) -> dict[str, float | int]:
        eq = self.equities
        if len(eq) < 2:
            return {"days": len(eq), "total_return": 0.0}

        returns = self.daily_returns
        start_eq, end_eq = eq[0], eq[-1]
        total_return = (end_eq - start_eq) / start_eq if start_eq else 0.0
        years = max(len(eq) / 252.0, 1e-9)

        # CAGR is undefined if the account is wiped out; report -100% instead of
        # raising on a fractional power of a negative number.
        if end_eq <= 0 or start_eq <= 0:
            cagr = -1.0
        else:
            cagr = (end_eq / start_eq) ** (1 / years) - 1

        wins = sum(1 for r in returns if r > 0)
        gains = sum(r for r in returns if r > 0)
        losses = -sum(r for r in returns if r < 0)

        return {
            "days": len(eq),
            "start_equity": round(start_eq, 2),
            "end_equity": round(end_eq, 2),
            "total_return": round(total_return, 4),
            "cagr": round(cagr, 4),
            "sharpe": round(ind.sharpe(returns), 3),
            "max_drawdown": round(ind.max_drawdown(eq), 4),
            "volatility_annual": round(_annualized_vol(returns), 4),
            "win_rate": round(wins / len(returns), 4) if returns else 0.0,
            "profit_factor": round(gains / losses, 3) if losses > 0 else 0.0,
            "trades": sum(1 for _, d in self.decisions if d.executed),
            "halted_days": len(self.halted_days),
        }

    def summary(self) -> str:
        s = self.stats()
        if s.get("days", 0) < 2:
            return "Backtest produced too few observations to summarise."
        return "\n".join(
            [
                f"Period          {self.start} -> {self.end} ({s['days']} sessions)",
                f"Equity          {s['start_equity']:,.2f} -> {s['end_equity']:,.2f}",
                f"Total return    {s['total_return']:+.2%}",
                f"CAGR            {s['cagr']:+.2%}",
                f"Sharpe          {s['sharpe']:.2f}",
                f"Max drawdown    {s['max_drawdown']:.2%}",
                f"Annual vol      {s['volatility_annual']:.2%}",
                f"Win rate        {s['win_rate']:.1%}",
                f"Profit factor   {s['profit_factor']:.2f}",
                f"Trades          {s['trades']}",
                f"Halted days     {s['halted_days']}",
            ]
        )


class Backtester:
    """Steps a :class:`TradingPipeline` through history one session at a time."""

    def __init__(self, pipeline: TradingPipeline, rebalance_every: int = 5) -> None:
        """``rebalance_every`` throttles research to every Nth session.

        Running a four-analyst LLM committee on every symbol every day is both
        slow and expensive, and daily rebalancing rarely improves a
        multi-week-horizon strategy. Non-research days still mark the book.
        """
        if rebalance_every < 1:
            raise ValueError("rebalance_every must be at least 1")
        self.pipeline = pipeline
        self.rebalance_every = rebalance_every

    def run(self, start: date, end: date) -> BacktestResult:
        if end < start:
            raise ValueError(f"end {end} precedes start {start}")

        result = BacktestResult(start=start, end=end)
        sessions = _trading_days(start, end)

        for index, day in enumerate(sessions):
            marks = self.pipeline._marks(day)
            if not marks:
                continue

            if index % self.rebalance_every == 0:
                scan: ScanResult = self.pipeline.scan(day, execute=True)
                if scan.halted:
                    result.halted_days.append((day, scan.halt_reason))
                result.decisions.extend((day, d) for d in scan.decisions)
                snapshot = scan.snapshot
            else:
                snapshot = self.pipeline.broker.snapshot(day, marks)
                self.pipeline.risk.mark(day, snapshot.equity)

            if snapshot is not None:
                result.snapshots.append(snapshot)
                result.equity_curve.append((day, snapshot.equity))

        return result


def _trading_days(start: date, end: date) -> list[date]:
    """Weekdays in the range.

    Exchange holidays are not modelled; on a synthetic-data backtest that is
    immaterial, and against a real provider those days simply return no bar and
    are skipped by the caller.
    """
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def _annualized_vol(returns: Sequence[float], periods_per_year: int = 252) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return (variance ** 0.5) * (periods_per_year ** 0.5)

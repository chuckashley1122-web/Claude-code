"""End-to-end orchestration: data in, sized orders out.

The order of operations here is the whole safety argument, so it is worth
stating plainly. Research produces a verdict. The verdict is *proposed* as an
order. The risk manager then gets an independent veto on that order, using the
live portfolio state rather than anything the analysts said. Only what survives
both stages reaches a broker.

Nothing in the analyst layer can size a position or bypass a limit, because it
never sees the portfolio.
"""

from __future__ import annotations

import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Sequence

from . import indicators as ind
from .agents import BaseAnalyst, default_committee
from .config import Settings
from .debate import DebateModerator
from .interfaces import Broker, LanguageModel, MarketDataProvider
from .models import (
    AccountSnapshot,
    AnalystView,
    Order,
    ResearchBundle,
    Stance,
    Verdict,
)
from .portfolio import Portfolio
from .risk import RiskManager, size_position


@dataclass
class Decision:
    """One symbol's full audit trail for one day."""

    verdict: Verdict
    order: Order | None = None
    executed: bool = False
    rejection: str | None = None

    @property
    def symbol(self) -> str:
        return self.verdict.symbol


@dataclass
class ScanResult:
    as_of: date
    decisions: list[Decision] = field(default_factory=list)
    snapshot: AccountSnapshot | None = None
    halted: bool = False
    halt_reason: str = ""
    unmarked_positions: tuple[str, ...] = ()
    """Held symbols with no usable mark, so equity is valued at cost for them."""

    @property
    def actionable(self) -> list[Decision]:
        return [d for d in self.decisions if d.order is not None]

    @property
    def executed(self) -> list[Decision]:
        return [d for d in self.decisions if d.executed]


class TradingPipeline:
    """Wires the committee, the risk manager and a broker together."""

    def __init__(
        self,
        settings: Settings,
        provider: MarketDataProvider,
        broker: Broker,
        analysts: Sequence[BaseAnalyst] | None = None,
        moderator: DebateModerator | None = None,
        llm: LanguageModel | None = None,
        max_workers: int = 4,
    ) -> None:
        if broker.is_live and not settings.allow_live_trading:
            raise RuntimeError(
                "Refusing to run against a live broker: Settings.allow_live_trading "
                "is False. This system has not been validated for live execution."
            )
        self.settings = settings
        self.provider = provider
        self.broker = broker
        self.analysts = list(analysts) if analysts is not None else default_committee(llm)
        self.moderator = moderator or DebateModerator(llm=llm)
        self.risk = RiskManager(settings.risk)
        self.max_workers = max_workers

    # --- research -------------------------------------------------------

    def build_bundle(self, symbol: str, as_of: date) -> ResearchBundle:
        start = as_of - timedelta(days=int(self.settings.lookback_days * 1.6))
        prices = self.provider.prices(symbol, start, as_of)
        return ResearchBundle(
            symbol=symbol,
            as_of=as_of,
            # Belt and braces: even a provider that leaks future bars cannot
            # get them past this slice.
            prices=prices.up_to(as_of),
            fundamentals=self.provider.fundamentals(symbol, as_of),
            news=self.provider.news(symbol, as_of),
        )

    def research(self, symbol: str, as_of: date) -> Verdict:
        bundle = self.build_bundle(symbol, as_of)
        views = self._run_analysts(bundle)
        return self.moderator.resolve(symbol, views)

    def _run_analysts(self, bundle: ResearchBundle) -> list[AnalystView]:
        """Analysts are independent by construction, so run them concurrently.

        With LLM-backed analysts this is the difference between four sequential
        round trips per symbol and one.
        """
        if len(self.analysts) == 1 or self.max_workers <= 1:
            return [a.analyze(bundle) for a in self.analysts]
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            return list(pool.map(lambda a: a.analyze(bundle), self.analysts))

    # --- execution ------------------------------------------------------

    def scan(self, as_of: date, execute: bool = True) -> ScanResult:
        """Research the universe, then size, check and optionally place orders."""
        result = ScanResult(as_of=as_of)

        marks = self._marks(as_of)
        equity = self._portfolio.equity(marks)

        # mark(), not new_day(). new_day() re-baselines the day's opening equity
        # unconditionally, so calling it here set day_open == current equity on
        # every scan: the daily-loss term computed (E - E)/E == 0 and the 3%
        # limit could never fire, while every re-run on the same date also
        # handed back a fresh new-position budget. mark() rolls the day only
        # when the date actually changes.
        self.risk.mark(as_of, equity)

        tripped, reason = self.risk.kill_switch_tripped(equity)
        if tripped:
            result.halted = True
            result.halt_reason = reason

        # Equity is only as trustworthy as the marks behind it. Portfolio values
        # an unmarked holding at cost, so a delisted or provider-dropped name
        # would sit at its entry price indefinitely and hide the loss from the
        # drawdown limit. Do not add risk on top of a number we cannot trust.
        result.unmarked_positions = tuple(
            sorted(set(self._portfolio.positions) - set(marks))
        )

        # Both conditions suppress buys only. Exits stay reachable by design:
        # halting everything strands the book in the very positions that tripped
        # the switch, which is the failure the risk layer explicitly guards
        # against — and the guard is worthless if the pipeline never proposes
        # the exit for it to approve.
        buys_suppressed = tripped or bool(result.unmarked_positions)

        verdicts = sorted(
            (self.research(sym, as_of) for sym in self.settings.universe),
            key=lambda v: v.confidence,
            reverse=True,
        )

        for verdict in verdicts:
            decision = Decision(verdict=verdict)
            result.decisions.append(decision)

            order = self._propose_order(verdict, as_of, marks)
            if order is None:
                continue
            decision.order = order

            if buys_suppressed and order.side is not Stance.SELL:
                decision.rejection = (
                    f"buying suppressed: {reason}"
                    if tripped
                    else f"buying suppressed: unmarked holdings "
                    f"{', '.join(result.unmarked_positions)} make equity unreliable"
                )
                continue

            allowed, why = self.risk.check(order, self._portfolio, marks, self.settings.risk)
            if not allowed:
                decision.rejection = why
                continue

            if not execute:
                decision.rejection = "dry run — not submitted"
                continue

            # Execute at the next session's open, never at the close the
            # decision was made on. `marks` stays the close because valuing the
            # book and filling an order are different questions.
            fill_price = self._fill_price(order.symbol, as_of)
            if fill_price is None:
                decision.rejection = (
                    "queued: fills at the next session's open, which does not exist yet"
                )
                continue

            fill = self.broker.submit(order, as_of, fill_price)
            if fill is None:
                decision.rejection = getattr(self.broker, "last_rejection", "broker declined")
                continue

            # RiskManager.check already consumed the new-position slot for this
            # order, so there is nothing to record here — re-marking is enough.
            decision.executed = True
            marks = self._marks(as_of)

        equity = self._portfolio.equity(marks)
        self.risk.mark(as_of, equity)
        result.snapshot = self.broker.snapshot(as_of, marks)
        return result

    def _propose_order(
        self, verdict: Verdict, as_of: date, marks: dict[str, float]
    ) -> Order | None:
        if not verdict.is_actionable:
            return None
        if verdict.confidence < self.settings.risk.min_confidence:
            return None

        price = marks.get(verdict.symbol)
        if not price or price <= 0:
            return None

        held = self._portfolio.positions.get(verdict.symbol)

        if verdict.stance is Stance.SELL:
            # No shorting in v1: a SELL is an exit, and is a no-op if flat.
            if held is None or held.quantity <= 0:
                return None
            return Order(
                symbol=verdict.symbol,
                side=Stance.SELL,
                quantity=held.quantity,
                reason=verdict.rationale,
            )

        equity = self._portfolio.equity(marks)
        annual_vol = self._annual_vol(verdict.symbol, as_of)
        target_shares = size_position(
            equity=equity,
            price=price,
            confidence=verdict.confidence,
            annual_vol=annual_vol,
            limits=self.settings.risk,
        )
        existing = held.quantity if held else 0.0
        delta = math.floor(target_shares - existing)
        if delta <= 0:
            return None
        return Order(
            symbol=verdict.symbol,
            side=Stance.BUY,
            quantity=float(delta),
            reason=verdict.rationale,
        )

    # --- helpers --------------------------------------------------------

    @property
    def _portfolio(self) -> Portfolio:
        portfolio = getattr(self.broker, "portfolio", None)
        if portfolio is None:
            raise AttributeError(
                f"Broker {self.broker.name!r} exposes no portfolio; the pipeline "
                "needs one to size positions against."
            )
        return portfolio

    def _fill_price(self, symbol: str, as_of: date) -> float | None:
        """The next session's open — the earliest price this order could fill at.

        A verdict formed from ``as_of``'s bar is only known once that bar has
        closed, so filling at that same close assumes a price the decision
        itself depended on. Over a universe of gapping names that is a
        systematic free edge, and it is the single most common way a backtest
        flatters a strategy that does not work.

        Returns ``None`` at the live edge, where tomorrow's open genuinely does
        not exist yet. That is not a failure — it is the honest statement that
        the order is queued, not filled.
        """
        series = self.provider.prices(symbol, as_of, as_of + timedelta(days=10))
        for bar in series.bars:
            if bar.ts > as_of:
                return bar.open
        return None

    def _marks(self, as_of: date) -> dict[str, float]:
        symbols = set(self.settings.universe) | set(self._portfolio.positions)
        marks: dict[str, float] = {}
        for symbol in symbols:
            series = self.provider.prices(
                symbol, as_of - timedelta(days=14), as_of
            ).up_to(as_of)
            if len(series):
                marks[symbol] = series.last.close
        return marks

    def _annual_vol(self, symbol: str, as_of: date) -> float:
        series = self.provider.prices(
            symbol, as_of - timedelta(days=180), as_of
        ).up_to(as_of)
        closes = list(series.closes)
        vols = ind.realized_volatility(closes, 20) if len(closes) > 21 else []
        for v in reversed(vols):
            if v:
                return v
        # Unknown volatility must not read as "safe" — assume a busy name.
        return 0.35

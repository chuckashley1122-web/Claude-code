"""Position sizing and the pre-trade veto.

Everything upstream of here produces opinions; this module is what turns an
opinion into a bounded amount of money at risk, and what refuses to trade at
all when the account is bleeding. Two rules shape the design:

* **Size by volatility, not by conviction alone.** A 60%-vol name and a 12%-vol
  name at the same confidence are not the same bet. Sizing to a volatility
  target makes them comparable before the hard percentage caps are applied.
* **The kill switch is sticky.** Once a loss limit is breached it stays
  breached until a human calls :meth:`RiskManager.reset`. A switch that
  un-trips as soon as the mark ticks back up is how a bad day becomes a blown
  account.

Every rejection carries a human-readable reason: the pipeline reads these back
to the user, so "rejected" alone is never good enough.
"""

from __future__ import annotations

from datetime import date

from .config import RiskLimits
from .models import Order, Stance
from .portfolio import Portfolio

EPSILON: float = 1e-9
"""Float tolerance for cap comparisons.

An order sized to be *exactly* at the cap must not be rejected because the
division landed 1e-16 over the line.
"""

COST_ALLOWANCE: float = 0.005
"""Headroom reserved for slippage and commission in the cash check.

The risk layer does not hold the broker's ``CostModel``, so it reserves a flat
50bps rather than pretending execution is free. Comfortably covers the default
5bps slippage plus commission at any realistic order size.
"""


def size_position(
    equity: float,
    price: float,
    confidence: float,
    annual_vol: float,
    limits: RiskLimits,
) -> float:
    """Shares to trade, sized to a volatility target and capped by policy.

    The target notional is ``equity * (vol_target_annual / annual_vol)``: a
    quiet name earns more capital because the same dollar exposure carries less
    risk. That is then scaled by ``confidence`` (a half-conviction view gets
    half the money) and clamped to ``max_position_pct * equity`` so no single
    idea can dominate the book no matter how calm or compelling it looks.

    ``annual_vol <= 0`` means we have no usable risk estimate — a flat or
    degenerate price history. Rather than dividing by zero and asking for an
    infinite position, we fall back to the max-position cap, which is the
    largest amount policy would ever allow anyway.

    Returns a possibly fractional share count; callers that need whole shares
    floor it themselves (flooring here would silently zero out small accounts).
    """
    if equity <= 0 or price <= 0:
        return 0.0

    confidence = min(max(confidence, 0.0), 1.0)
    if confidence == 0.0:
        return 0.0

    cap_notional = limits.max_position_pct * equity
    if annual_vol <= 0:
        base_notional = cap_notional
    else:
        base_notional = equity * (limits.vol_target_annual / annual_vol)

    target_notional = min(base_notional * confidence, cap_notional)
    return target_notional / price


class RiskManager:
    """Stateful guardian: daily counters, the equity peak, and the kill switch.

    One instance lives for the length of a run. It must be told about the
    passage of time — call :meth:`mark` once per bar with the current equity —
    because both loss limits are measured against state (day-open equity, the
    running peak) that nothing else tracks.
    """

    def __init__(self, limits: RiskLimits) -> None:
        self.limits = limits
        self._day: date | None = None
        self._day_open_equity: float | None = None
        self._peak_equity: float | None = None
        self._new_positions_today: int = 0
        self._last_equity: float | None = None
        self._tripped: bool = False
        self._trip_reason: str = ""

    # ------------------------------------------------------------------
    # read-only state
    # ------------------------------------------------------------------
    @property
    def day(self) -> date | None:
        return self._day

    @property
    def day_open_equity(self) -> float | None:
        return self._day_open_equity

    @property
    def peak_equity(self) -> float | None:
        return self._peak_equity

    @property
    def new_positions_today(self) -> int:
        return self._new_positions_today

    @property
    def tripped(self) -> bool:
        """Whether the kill switch is currently latched."""
        return self._tripped

    @property
    def trip_reason(self) -> str:
        return self._trip_reason

    # ------------------------------------------------------------------
    # bookkeeping
    # ------------------------------------------------------------------
    def mark(self, when: date, equity: float) -> None:
        """Record equity for ``when``. Call once per bar, before sizing.

        Rolls the day over automatically when ``when`` differs from the last
        marked date, so callers cannot forget to reset the daily counters, and
        keeps the running peak that the drawdown limit measures against.
        """
        if self._day is None or when != self._day:
            # Roll into the new day using the *previous* day's closing equity as
            # the baseline, not the equity being marked now. Baselining to the
            # current mark makes the daily move measure (E - E)/E == 0 in any
            # system that marks once per session — which is every daily-bar
            # backtest — so the daily loss limit would silently never fire.
            self.new_day(
                when, self._last_equity if self._last_equity is not None else equity
            )
        if self._peak_equity is None or equity > self._peak_equity:
            self._peak_equity = equity
        self._last_equity = equity

    def new_day(self, when: date, equity: float) -> None:
        """Start a new trading day: reset per-day counters and the open mark.

        Note what is *not* reset: the kill switch. A fresh day gives the daily
        loss limit a new baseline, but a latched switch stays latched until
        :meth:`reset` is called deliberately.
        """
        self._day = when
        self._day_open_equity = equity
        self._new_positions_today = 0
        if self._peak_equity is None or equity > self._peak_equity:
            self._peak_equity = equity

    def reset(self, equity: float | None = None) -> None:
        """Un-latch the kill switch. This is the deliberate human override.

        Pass ``equity`` to also re-baseline the day-open mark and the peak;
        without it the same breach is likely to re-trip on the next check,
        which is usually the honest outcome.
        """
        self._tripped = False
        self._trip_reason = ""
        if equity is not None:
            self._day_open_equity = equity
            self._peak_equity = equity

    # ------------------------------------------------------------------
    # limits
    # ------------------------------------------------------------------
    def kill_switch_tripped(self, equity: float) -> tuple[bool, str]:
        """``(tripped, reason)`` for the current ``equity``.

        Trips on either the daily loss limit (versus the day's opening equity)
        or the max drawdown (versus the all-time equity peak). Once tripped it
        stays tripped for the rest of the run regardless of what equity does
        next — only :meth:`reset` clears it.
        """
        if self._tripped:
            return True, self._trip_reason

        if self._day_open_equity is not None and self._day_open_equity > 0:
            loss = (self._day_open_equity - equity) / self._day_open_equity
            if loss >= self.limits.max_daily_loss_pct - EPSILON:
                return self._trip(
                    f"daily loss limit: down {loss:.2%} from the open "
                    f"(${self._day_open_equity:,.2f} to ${equity:,.2f}), "
                    f"limit {self.limits.max_daily_loss_pct:.2%}"
                )

        if self._peak_equity is not None and self._peak_equity > 0:
            drawdown = (self._peak_equity - equity) / self._peak_equity
            if drawdown >= self.limits.max_drawdown_pct - EPSILON:
                return self._trip(
                    f"max drawdown: {drawdown:.2%} below the peak of "
                    f"${self._peak_equity:,.2f} (now ${equity:,.2f}), "
                    f"limit {self.limits.max_drawdown_pct:.2%}"
                )

        return False, ""

    def _trip(self, reason: str) -> tuple[bool, str]:
        self._tripped = True
        self._trip_reason = reason
        return True, reason

    def check(
        self,
        order: Order,
        portfolio: Portfolio,
        marks: dict[str, float],
        limits: RiskLimits | None = None,
    ) -> tuple[bool, str]:
        """``(allowed, reason)`` for ``order`` against the current book.

        Sells are only checked for the kill switch and for having the shares:
        reducing a position always lowers risk, and blocking an exit on an
        exposure cap is precisely the wrong behaviour.

        A tripped kill switch blocks *buys only*. Exits stay open deliberately:
        the switch exists to stop the book taking on more risk, and a control
        that also traps you in the losing positions that tripped it can turn a
        bad day into a much worse one. Stopping and de-risking are different
        actions and only the first should be automatic.

        This call is **stateful**. Approving a buy in a symbol we do not
        already hold consumes one of the day's new-position slots, so call it
        exactly once per order, immediately before submitting it.
        """
        limits = limits if limits is not None else self.limits
        price = marks.get(order.symbol)
        equity = portfolio.equity(marks)

        tripped, reason = self.kill_switch_tripped(equity)
        if tripped and order.side is not Stance.SELL:
            return False, f"kill switch tripped: {reason}"

        if price is None or price <= 0:
            return False, f"no usable mark price for {order.symbol}"

        if order.side is Stance.SELL:
            held = portfolio.positions.get(order.symbol)
            held_qty = held.quantity if held is not None else 0.0
            if order.quantity > held_qty + EPSILON:
                return False, (
                    f"cannot sell {order.quantity:g} {order.symbol}: only "
                    f"{held_qty:g} held (no shorting)"
                )
            return True, "ok"

        if equity <= 0:
            return False, "no equity left to trade against"

        notional = order.quantity * price

        # Check against notional plus a costs allowance, not bare notional. The
        # broker charges slippage and commission on top, so a check that just
        # clears here can still be refused there — and by then `check` has
        # already consumed one of the day's new-position slots for a position
        # that never opened. Approving slightly less than we can afford is the
        # safe direction to be wrong in.
        required = notional * (1.0 + COST_ALLOWANCE)
        if required > portfolio.cash + EPSILON:
            return False, (
                f"insufficient cash for {order.symbol}: needs ${required:,.2f} "
                f"including costs, have ${portfolio.cash:,.2f}"
            )

        existing = portfolio.positions.get(order.symbol)
        existing_value = existing.market_value(price) if existing is not None else 0.0
        position_pct = (existing_value + notional) / equity
        if position_pct > limits.max_position_pct + EPSILON:
            return False, (
                f"position cap for {order.symbol}: would be {position_pct:.2%} of "
                f"equity, limit {limits.max_position_pct:.2%}"
            )

        gross_pct = (portfolio.market_value(marks) + notional) / equity
        if gross_pct > limits.max_gross_exposure + EPSILON:
            return False, (
                f"gross exposure cap: would be {gross_pct:.2%} of equity, "
                f"limit {limits.max_gross_exposure:.2%}"
            )

        if existing is None:
            if self._new_positions_today >= limits.max_new_positions_per_day:
                return False, (
                    f"daily new-position limit reached "
                    f"({self._new_positions_today} of "
                    f"{limits.max_new_positions_per_day}); {order.symbol} must wait"
                )
            self._new_positions_today += 1

        return True, "ok"

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"RiskManager(day={self._day}, peak={self._peak_equity}, "
            f"new_positions_today={self._new_positions_today}, tripped={self._tripped})"
        )

"""Paper broker: fills orders against a reference price, minus realistic costs.

This is the only :class:`~alpha_agents.interfaces.Broker` implementation that
ships, and it is intentionally the only one. ``is_live`` is a hard ``False`` —
no live venue client exists anywhere in this package, so there is no path from
a signal to real money.

The point of the class is honesty about costs: every fill is worse than the
quote by slippage and commission, in the direction that hurts. A backtest that
skips that step will always look better than the strategy is.
"""

from __future__ import annotations

from datetime import date

from ..config import CostModel
from ..models import AccountSnapshot, Fill, Order, Stance
from ..portfolio import Portfolio

TOLERANCE: float = 1e-9
"""Float slack when comparing cash and share counts against requirements."""


class PaperBroker:
    """Simulated execution against a :class:`~alpha_agents.portfolio.Portfolio`.

    Rejections return ``None`` rather than raising: an unfillable order is a
    normal event in a long backtest (a signal fires when the cash is already
    spent), and one that should not tear down the run. The explanation is left
    on :attr:`last_rejection` for the caller to surface.
    """

    name: str = "paper"
    is_live: bool = False

    def __init__(self, portfolio: Portfolio, costs: CostModel | None = None) -> None:
        self.portfolio = portfolio
        self.costs = costs if costs is not None else CostModel()
        self.fills: list[Fill] = []
        self.last_rejection: str | None = None

    # ------------------------------------------------------------------
    # Broker protocol
    # ------------------------------------------------------------------
    def snapshot(self, when: date, marks: dict[str, float]) -> AccountSnapshot:
        """Account state at ``when``, valued at ``marks``."""
        return self.portfolio.snapshot(when, marks)

    def submit(self, order: Order, when: date, reference_price: float) -> Fill | None:
        """Fill ``order`` at ``reference_price`` plus costs, or return ``None``.

        Slippage is applied *adversely*: buys pay above the reference, sells
        receive below it, each by ``slippage_bps``. Modelling it symmetrically
        (or worse, favourably) is the single easiest way to manufacture alpha
        that does not exist.
        """
        if reference_price <= 0:
            return self._reject(f"invalid reference price {reference_price} for {order.symbol}")

        slip_per_share = reference_price * (self.costs.slippage_bps / 10_000.0)
        if order.side is Stance.BUY:
            fill_price = reference_price + slip_per_share
        else:
            fill_price = reference_price - slip_per_share

        if fill_price <= 0:
            return self._reject(
                f"slippage of {self.costs.slippage_bps:g}bps drives {order.symbol} "
                f"to a non-positive fill price"
            )

        if order.limit_price is not None:
            if order.side is Stance.BUY and fill_price > order.limit_price:
                return self._reject(
                    f"limit not marketable: {order.symbol} buy fills at "
                    f"${fill_price:,.4f}, limit ${order.limit_price:,.4f}"
                )
            if order.side is Stance.SELL and fill_price < order.limit_price:
                return self._reject(
                    f"limit not marketable: {order.symbol} sell fills at "
                    f"${fill_price:,.4f}, limit ${order.limit_price:,.4f}"
                )

        commission = max(
            self.costs.commission_minimum,
            order.quantity * self.costs.commission_per_share,
        )
        notional = order.quantity * fill_price

        if order.side is Stance.BUY:
            required = notional + commission
            if required > self.portfolio.cash + TOLERANCE:
                return self._reject(
                    f"insufficient cash for {order.symbol}: needs ${required:,.2f}, "
                    f"have ${self.portfolio.cash:,.2f}"
                )
        else:
            held = self.portfolio.positions.get(order.symbol)
            held_qty = held.quantity if held is not None else 0.0
            if order.quantity > held_qty + TOLERANCE:
                return self._reject(
                    f"cannot sell {order.quantity:g} {order.symbol}: only "
                    f"{held_qty:g} held (no shorting)"
                )

        fill = Fill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            ts=when,
            commission=commission,
            # Recorded in dollars, not per share: this is what the slippage
            # assumption actually cost the account on this trade.
            slippage=slip_per_share * order.quantity,
        )
        self.portfolio.apply(fill)
        self.fills.append(fill)
        self.last_rejection = None
        return fill

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _reject(self, reason: str) -> None:
        """Record ``reason`` and decline the order, leaving the book untouched."""
        self.last_rejection = reason
        return None

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"PaperBroker(fills={len(self.fills)}, portfolio={self.portfolio!r})"

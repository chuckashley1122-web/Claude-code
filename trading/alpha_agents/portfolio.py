"""Book-keeping for cash and positions.

The portfolio is deliberately dumb: it applies fills and reports state. It does
not decide whether a trade is *allowed* — that is the risk layer's job — and it
does not know where a fill came from. Keeping the accounting free of policy is
what lets the same class serve a backtest and a paper broker without drift
between the two.

Sign conventions: quantities are always positive, direction lives in
``Fill.side``. There is no shorting in v1 (see :meth:`Portfolio.apply`).
"""

from __future__ import annotations

from datetime import date

from .models import AccountSnapshot, Fill, Position, Stance

DUST: float = 1e-9
"""Residual quantity treated as zero.

Repeated float arithmetic leaves specks like 1e-13 shares behind. Left alone
they linger forever as phantom positions that skew exposure and weight
calculations, so anything smaller than this is swept away.
"""


class Portfolio:
    """Cash plus long positions, updated one fill at a time.

    The invariant every method preserves::

        equity(marks) == initial_cash + realized_pnl + sum(unrealized_pnl)

    ``realized_pnl`` is therefore net of *all* commissions (entry and exit),
    while ``Position.avg_price`` stays a clean weighted-average traded price so
    that unrealised P&L compares like with like against a market mark.
    """

    def __init__(
        self,
        cash: float,
        positions: dict[str, Position] | None = None,
        realized_pnl: float = 0.0,
    ) -> None:
        if cash < 0:
            raise ValueError(f"starting cash must be non-negative, got {cash}")
        self.cash: float = float(cash)
        self.initial_cash: float = float(cash)
        self.positions: dict[str, Position] = dict(positions or {})
        self.realized_pnl: float = float(realized_pnl)

    # ------------------------------------------------------------------
    # mutation
    # ------------------------------------------------------------------
    def apply(self, fill: Fill) -> None:
        """Apply ``fill`` to cash, positions and realised P&L.

        Buys pay ``notional + commission`` out of cash and roll the position's
        weighted-average cost. Sells credit ``notional`` less commission and
        realise P&L against that average cost.

        Selling more than is held raises :class:`ValueError`: v1 is long-only,
        so a sell is strictly a position reduction and an over-sell is a bug
        upstream (bad sizing, stale state) that must not be silently turned
        into a short.

        Cash is *not* bounds-checked here. Whether an order is affordable is a
        pre-trade question owned by :mod:`.risk` and the broker; by the time a
        fill exists the money has already moved.
        """
        if fill.side is Stance.HOLD:
            raise ValueError("cannot apply a HOLD fill")
        if fill.quantity <= 0:
            raise ValueError(f"fill quantity must be positive, got {fill.quantity}")
        if fill.price < 0:
            raise ValueError(f"fill price must be non-negative, got {fill.price}")

        # Commissions are a certain, immediate loss whichever way we traded, so
        # they hit realised P&L on both legs rather than hiding in cost basis.
        self.realized_pnl -= fill.commission

        if fill.side is Stance.BUY:
            self._apply_buy(fill)
        else:
            self._apply_sell(fill)

    def _apply_buy(self, fill: Fill) -> None:
        self.cash -= fill.notional + fill.commission
        existing = self.positions.get(fill.symbol)
        if existing is None:
            self.positions[fill.symbol] = Position(fill.symbol, fill.quantity, fill.price)
            return
        quantity = existing.quantity + fill.quantity
        avg_price = (existing.cost_basis + fill.notional) / quantity
        self.positions[fill.symbol] = Position(fill.symbol, quantity, avg_price)

    def _apply_sell(self, fill: Fill) -> None:
        existing = self.positions.get(fill.symbol)
        held = existing.quantity if existing is not None else 0.0
        if fill.quantity > held + DUST:
            raise ValueError(
                f"cannot sell {fill.quantity} {fill.symbol}: only {held} held "
                "(shorting is not supported)"
            )
        assert existing is not None  # implied by the check above, for type checkers

        self.cash += fill.notional - fill.commission
        self.realized_pnl += (fill.price - existing.avg_price) * fill.quantity

        remaining = held - fill.quantity
        if remaining <= DUST:
            # Fully closed. Dropping the key keeps exposure and weight maths
            # honest instead of carrying a rounding speck around forever.
            del self.positions[fill.symbol]
        else:
            # Average cost is unchanged by a sale: we sold at the average, so
            # the basis of what remains is exactly what it was.
            self.positions[fill.symbol] = Position(fill.symbol, remaining, existing.avg_price)

    # ------------------------------------------------------------------
    # valuation
    # ------------------------------------------------------------------
    def market_value(self, marks: dict[str, float]) -> float:
        """Value of the held positions at ``marks``.

        A symbol missing from ``marks`` is valued at its average cost rather
        than at zero: a stale mark is a small error, pretending the shares
        vanished is a large one.
        """
        return sum(
            position.market_value(marks.get(symbol, position.avg_price))
            for symbol, position in self.positions.items()
        )

    def equity(self, marks: dict[str, float]) -> float:
        """Cash plus the marked value of every position."""
        return self.cash + self.market_value(marks)

    def position_weight(self, symbol: str, marks: dict[str, float]) -> float:
        """Fraction of equity held in ``symbol`` (0.0 if flat or broke)."""
        position = self.positions.get(symbol)
        if position is None:
            return 0.0
        equity = self.equity(marks)
        if equity <= 0:
            return 0.0
        return position.market_value(marks.get(symbol, position.avg_price)) / equity

    def unrealized_pnl(self, marks: dict[str, float]) -> float:
        """Open P&L across the book at ``marks``."""
        return sum(
            position.unrealized_pnl(marks.get(symbol, position.avg_price))
            for symbol, position in self.positions.items()
        )

    def snapshot(self, when: date, marks: dict[str, float]) -> AccountSnapshot:
        """Immutable account state for ``when``, valued at ``marks``.

        Positions are ordered by symbol so that recorded snapshots compare
        cleanly across runs.
        """
        positions = tuple(self.positions[symbol] for symbol in sorted(self.positions))
        return AccountSnapshot(
            ts=when,
            cash=self.cash,
            positions=positions,
            equity=self.equity(marks),
            realized_pnl=self.realized_pnl,
        )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"Portfolio(cash={self.cash:.2f}, positions={sorted(self.positions)}, "
            f"realized_pnl={self.realized_pnl:.2f})"
        )

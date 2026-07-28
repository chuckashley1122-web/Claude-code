"""Core value types shared by every part of the system.

Everything here is immutable and dependency-free on purpose: these types cross
the boundary between data providers, analyst agents, the debate layer, risk
sizing and execution, so they must not drag any of those concerns with them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Mapping, Sequence


class Stance(str, Enum):
    """Direction of a view or an order."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

    @property
    def sign(self) -> int:
        """+1 for BUY, -1 for SELL, 0 for HOLD — handy for arithmetic."""
        return {Stance.BUY: 1, Stance.SELL: -1, Stance.HOLD: 0}[self]


@dataclass(frozen=True)
class Bar:
    """A single OHLCV candle."""

    ts: date
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if self.high < self.low:
            raise ValueError(f"{self.ts}: high {self.high} below low {self.low}")
        if not (self.low <= self.open <= self.high):
            raise ValueError(f"{self.ts}: open {self.open} outside [{self.low}, {self.high}]")
        if not (self.low <= self.close <= self.high):
            raise ValueError(f"{self.ts}: close {self.close} outside [{self.low}, {self.high}]")


@dataclass(frozen=True)
class PriceSeries:
    """An ordered, oldest-first run of bars for one symbol."""

    symbol: str
    bars: tuple[Bar, ...]

    def __post_init__(self) -> None:
        timestamps = [b.ts for b in self.bars]
        if timestamps != sorted(timestamps):
            raise ValueError(f"{self.symbol}: bars must be ordered oldest-first")
        if len(set(timestamps)) != len(timestamps):
            raise ValueError(f"{self.symbol}: duplicate bar timestamps")

    def __len__(self) -> int:
        return len(self.bars)

    @property
    def closes(self) -> tuple[float, ...]:
        return tuple(b.close for b in self.bars)

    @property
    def highs(self) -> tuple[float, ...]:
        return tuple(b.high for b in self.bars)

    @property
    def lows(self) -> tuple[float, ...]:
        return tuple(b.low for b in self.bars)

    @property
    def volumes(self) -> tuple[float, ...]:
        return tuple(b.volume for b in self.bars)

    @property
    def last(self) -> Bar:
        if not self.bars:
            raise ValueError(f"{self.symbol}: empty series has no last bar")
        return self.bars[-1]

    def window(self, n: int) -> "PriceSeries":
        """The most recent ``n`` bars, as a new series."""
        return PriceSeries(self.symbol, self.bars[-n:] if n > 0 else ())

    def up_to(self, when: date) -> "PriceSeries":
        """Bars at or before ``when``.

        This is the only sanctioned way for a backtest to slice history: it is
        what keeps a strategy from reading bars it could not have seen.
        """
        return PriceSeries(self.symbol, tuple(b for b in self.bars if b.ts <= when))


@dataclass(frozen=True)
class NewsItem:
    ts: datetime
    headline: str
    summary: str = ""
    source: str = ""
    url: str | None = None


@dataclass(frozen=True)
class Fundamentals:
    """Point-in-time fundamental metrics.

    ``metrics`` is deliberately open: providers disagree about what they expose,
    and the fundamental analyst reasons over whatever it is handed rather than
    a fixed schema. Well-known keys: ``pe``, ``ps``, ``ev_ebitda``,
    ``revenue_growth``, ``gross_margin``, ``net_margin``, ``debt_to_equity``,
    ``fcf_yield``, ``roe``.
    """

    symbol: str
    as_of: date
    metrics: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Evidence:
    """One concrete fact an analyst leaned on.

    Views without evidence are opinions; the debate layer weights them lower.
    """

    label: str
    detail: str
    value: float | None = None


@dataclass(frozen=True)
class AnalystView:
    """One analyst's read on one symbol."""

    analyst: str
    symbol: str
    stance: Stance
    confidence: float
    rationale: str
    evidence: tuple[Evidence, ...] = ()
    horizon_days: int = 20

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence {self.confidence} outside [0, 1]")


@dataclass(frozen=True)
class Verdict:
    """The committee's decision for one symbol, after debate and risk review."""

    symbol: str
    stance: Stance
    confidence: float
    rationale: str
    views: tuple[AnalystView, ...] = ()
    dissent: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence {self.confidence} outside [0, 1]")

    @property
    def is_actionable(self) -> bool:
        return self.stance is not Stance.HOLD


@dataclass(frozen=True)
class Order:
    """An instruction to a broker. Quantity is always positive; direction is ``side``."""

    symbol: str
    side: Stance
    quantity: float
    limit_price: float | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        if self.side is Stance.HOLD:
            raise ValueError("cannot place a HOLD order")
        if self.quantity <= 0:
            raise ValueError(f"quantity must be positive, got {self.quantity}")


@dataclass(frozen=True)
class Fill:
    """A completed trade, including the costs that made it worse than the quote."""

    symbol: str
    side: Stance
    quantity: float
    price: float
    ts: date
    commission: float = 0.0
    slippage: float = 0.0

    @property
    def notional(self) -> float:
        return self.quantity * self.price


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: float
    avg_price: float

    @property
    def cost_basis(self) -> float:
        return self.quantity * self.avg_price

    def market_value(self, price: float) -> float:
        return self.quantity * price

    def unrealized_pnl(self, price: float) -> float:
        return (price - self.avg_price) * self.quantity


@dataclass(frozen=True)
class AccountSnapshot:
    """Account state at a point in time — the unit a backtest records per day."""

    ts: date
    cash: float
    positions: tuple[Position, ...]
    equity: float
    realized_pnl: float = 0.0

    @property
    def exposure(self) -> float:
        """Fraction of equity held in positions rather than cash."""
        if self.equity == 0:
            return 0.0
        return (self.equity - self.cash) / self.equity


@dataclass(frozen=True)
class ResearchBundle:
    """Everything the analysts are allowed to see about one symbol on one day.

    Assembling this in one place is what makes look-ahead bias auditable: a
    backtest builds the bundle from ``PriceSeries.up_to(as_of)`` and nothing in
    the analyst layer can reach past it.
    """

    symbol: str
    as_of: date
    prices: PriceSeries
    fundamentals: Fundamentals | None = None
    news: tuple[NewsItem, ...] = ()

"""Protocols every pluggable part of the system implements.

These are the seams. A new data vendor, a new analyst, or a live broker slots
in by satisfying one of these — no other module needs to change.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol, Sequence, runtime_checkable

from .models import (
    AccountSnapshot,
    AnalystView,
    Fill,
    Fundamentals,
    NewsItem,
    Order,
    PriceSeries,
    ResearchBundle,
)


@runtime_checkable
class MarketDataProvider(Protocol):
    """Source of price history, fundamentals and news.

    Implementations must be *point-in-time honest*: given ``end``, never return
    data that was not observable by then.

    Some vendors cannot honour that for every field. ``yfinance`` exposes only
    *current* fundamentals, so scoring a 2019 date with them leaks the future.
    A provider that cannot slice a field historically must declare it, so the
    backtester can refuse rather than silently producing an inflated result.
    """

    name: str

    point_in_time_fundamentals: bool
    """False when ``fundamentals()`` returns current data regardless of ``as_of``.

    Such a provider is fine for live or paper decisions, where "now" is the
    right answer, and unusable for backtesting the fundamental analyst.
    """

    def prices(self, symbol: str, start: date, end: date) -> PriceSeries:
        """Daily bars for ``symbol`` in ``[start, end]``, oldest first."""
        ...

    def fundamentals(self, symbol: str, as_of: date) -> Fundamentals | None:
        """Latest fundamentals published on or before ``as_of``, if available."""
        ...

    def news(self, symbol: str, as_of: date, lookback_days: int = 7) -> tuple[NewsItem, ...]:
        """Headlines published in the window ending at ``as_of``."""
        ...


@runtime_checkable
class Analyst(Protocol):
    """One specialist's opinion-forming step.

    An analyst reads a :class:`ResearchBundle` and returns exactly one view. It
    must not perform I/O beyond its own model calls — everything it is allowed
    to know is already in the bundle.
    """

    name: str

    def analyze(self, bundle: ResearchBundle) -> AnalystView:
        ...


@runtime_checkable
class Broker(Protocol):
    """Order execution and account state.

    The paper broker is the only implementation shipped. A live adapter would
    satisfy this same protocol — which is why nothing upstream of here knows
    whether the money is real.
    """

    name: str
    is_live: bool

    def snapshot(self, when: date, marks: dict[str, float]) -> AccountSnapshot:
        """Account state valued at ``marks`` (symbol -> price)."""
        ...

    def submit(self, order: Order, when: date, reference_price: float) -> Fill | None:
        """Execute ``order``. Returns ``None`` if it could not be filled."""
        ...


@runtime_checkable
class LanguageModel(Protocol):
    """Minimal text-in/JSON-out interface the LLM analysts depend on.

    Narrow by design: it keeps the analysts testable with a stub and keeps
    provider specifics in one adapter.
    """

    def complete_json(
        self,
        *,
        system: str,
        prompt: str,
        schema: dict,
        max_tokens: int = 2000,
    ) -> dict:
        """Return a JSON object conforming to ``schema``."""
        ...

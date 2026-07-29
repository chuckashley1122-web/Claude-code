"""Real market data via the optional ``yfinance`` package.

yfinance (and its pandas/numpy dependency chain) is deliberately *not* a hard
requirement: the whole system runs offline on :class:`SyntheticProvider`, and
importing ``alpha_agents.data`` must not explode on a machine that never
installed it. So the import happens inside the methods, and the failure is a
sentence telling you what to pip install rather than a traceback at import time.

Two caveats worth knowing before trusting a backtest run on this provider:

* ``Ticker.info`` fundamentals are *current*, not point-in-time. Using them to
  score a date in 2019 leaks the future. They are fine for live/paper decisions
  made today; they are not fine for historical research.
* Yahoo data has gaps and the odd inconsistent candle, so bars are repaired
  (high/low widened to contain the body) rather than dropped.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from typing import Any

from ..models import Bar, Fundamentals, NewsItem, PriceSeries

_INSTALL_HINT = (
    "YFinanceProvider needs the optional 'yfinance' package. "
    "Install it with: pip install yfinance"
)

# yfinance's ``info`` keys mapped onto the well-known names in Fundamentals.
_INFO_METRICS = {
    "pe": "trailingPE",
    "ps": "priceToSalesTrailing12Months",
    "ev_ebitda": "enterpriseToEbitda",
    "revenue_growth": "revenueGrowth",
    "gross_margin": "grossMargins",
    "net_margin": "profitMargins",
    "roe": "returnOnEquity",
}


def _require_yfinance() -> Any:
    """Import yfinance on demand, or explain how to get it."""
    try:
        import yfinance  # noqa: PLC0415 - lazy on purpose; see module docstring
    except ImportError as exc:
        raise ImportError(_INSTALL_HINT) from exc
    return yfinance


def _as_float(value: Any) -> float | None:
    """Coerce a vendor value to a finite float, or ``None`` if it is unusable."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


class YFinanceProvider:
    """Reads daily bars, fundamentals and headlines from Yahoo Finance."""

    name = "yfinance"
    # ``Ticker.info`` is a snapshot of today regardless of ``as_of``.
    point_in_time_fundamentals = False

    def __init__(self, auto_adjust: bool = True) -> None:
        self.auto_adjust = auto_adjust
        """Split/dividend-adjusted closes. On by default: unadjusted history
        shows fake gaps on split days that look like tradable signals."""

    # -- MarketDataProvider ------------------------------------------------

    def prices(self, symbol: str, start: date, end: date) -> PriceSeries:
        """Daily bars for ``symbol`` in ``[start, end]``, oldest first."""
        if start > end:
            raise ValueError(f"{symbol}: start {start} is after end {end}")
        yfinance = _require_yfinance()
        history = yfinance.Ticker(symbol).history(
            start=start.isoformat(),
            # Yahoo's end is exclusive; step a day past it to include ``end``.
            end=(end + timedelta(days=1)).isoformat(),
            interval="1d",
            auto_adjust=self.auto_adjust,
        )

        bars: list[Bar] = []
        for stamp, row in history.iterrows():
            bar = self._to_bar(stamp, row)
            if bar is not None and start <= bar.ts <= end:
                bars.append(bar)
        bars.sort(key=lambda b: b.ts)
        return PriceSeries(symbol, tuple(bars))

    def fundamentals(self, symbol: str, as_of: date) -> Fundamentals | None:
        """Current fundamentals, stamped ``as_of``. See the module caveat."""
        yfinance = _require_yfinance()
        info = getattr(yfinance.Ticker(symbol), "info", None) or {}

        metrics: dict[str, float] = {}
        for key, source in _INFO_METRICS.items():
            value = _as_float(info.get(source))
            if value is not None:
                metrics[key] = value

        # Yahoo reports debt/equity as a percentage; the rest of the system
        # treats every ratio as a fraction.
        debt_to_equity = _as_float(info.get("debtToEquity"))
        if debt_to_equity is not None:
            metrics["debt_to_equity"] = debt_to_equity / 100.0

        free_cash_flow = _as_float(info.get("freeCashflow"))
        market_cap = _as_float(info.get("marketCap"))
        if free_cash_flow is not None and market_cap:
            metrics["fcf_yield"] = free_cash_flow / market_cap

        if not metrics:
            return None
        return Fundamentals(symbol=symbol, as_of=as_of, metrics=metrics)

    def news(self, symbol: str, as_of: date, lookback_days: int = 7) -> tuple[NewsItem, ...]:
        """Headlines Yahoo carries for ``symbol`` inside the lookback window.

        Anything published after ``as_of`` is dropped: the provider contract is
        point-in-time honest even when the vendor is not.
        """
        yfinance = _require_yfinance()
        if lookback_days <= 0:
            return ()
        raw = getattr(yfinance.Ticker(symbol), "news", None) or []

        window_start = as_of - timedelta(days=lookback_days - 1)
        items: list[NewsItem] = []
        for entry in raw:
            item = self._to_news_item(entry)
            if item is not None and window_start <= item.ts.date() <= as_of:
                items.append(item)
        items.sort(key=lambda item: item.ts, reverse=True)
        return tuple(items)

    # -- conversion --------------------------------------------------------

    @staticmethod
    def _to_bar(stamp: Any, row: Any) -> Bar | None:
        """One pandas row to a :class:`Bar`, or ``None`` if the row is unusable."""
        values = {
            field: _as_float(row.get(column))
            for field, column in (
                ("open", "Open"),
                ("high", "High"),
                ("low", "Low"),
                ("close", "Close"),
            )
        }
        if any(value is None or value <= 0 for value in values.values()):
            return None
        volume = _as_float(row.get("Volume")) or 0.0

        # Widen rather than reject: Yahoo occasionally publishes a high below
        # the close, and losing the whole day would leave a hole in the series.
        high = max(values["high"], values["open"], values["close"], values["low"])
        low = min(values["low"], values["open"], values["close"])
        when = stamp.date() if hasattr(stamp, "date") else stamp
        return Bar(
            ts=when,
            open=values["open"],
            high=high,
            low=low,
            close=values["close"],
            volume=max(volume, 0.0),
        )

    @staticmethod
    def _to_news_item(entry: Any) -> NewsItem | None:
        """One yfinance news record to a :class:`NewsItem`.

        The payload shape changed between yfinance releases (flat keys, then a
        nested ``content`` object), so both are accepted.
        """
        if not isinstance(entry, dict):
            return None
        content = entry.get("content") if isinstance(entry.get("content"), dict) else entry

        headline = content.get("title") or entry.get("title")
        if not headline:
            return None

        stamp: datetime | None = None
        epoch = entry.get("providerPublishTime") or content.get("providerPublishTime")
        if epoch is not None:
            seconds = _as_float(epoch)
            if seconds is not None:
                stamp = datetime.fromtimestamp(seconds)
        if stamp is None:
            published = content.get("pubDate") or content.get("displayTime")
            if isinstance(published, str):
                try:
                    stamp = datetime.fromisoformat(published.replace("Z", "+00:00")).replace(
                        tzinfo=None
                    )
                except ValueError:
                    stamp = None
        if stamp is None:
            return None

        provider = content.get("provider")
        source = entry.get("publisher") or ""
        if isinstance(provider, dict):
            source = provider.get("displayName") or source

        url = entry.get("link")
        canonical = content.get("canonicalUrl")
        if isinstance(canonical, dict):
            url = canonical.get("url") or url

        return NewsItem(
            ts=stamp,
            headline=str(headline),
            summary=str(content.get("summary") or ""),
            source=str(source),
            url=url,
        )

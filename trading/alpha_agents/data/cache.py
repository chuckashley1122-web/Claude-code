"""A caching decorator for any :class:`MarketDataProvider`.

Vendor calls are slow, rate-limited and — for a backtest that sweeps the same
window dozens of times — entirely repetitive. This wraps any provider and
memoises its answers as JSON on disk, so the second run of an experiment costs
nothing and produces byte-identical inputs to the first.

JSON rather than pickle on purpose: the cache is meant to be inspectable and
safe to read from a file someone else wrote.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

from ..interfaces import MarketDataProvider
from ..models import Bar, Fundamentals, NewsItem, PriceSeries

DEFAULT_CACHE_DIR = ".cache/alpha_agents"

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _slug(text: str) -> str:
    """A filesystem-safe fragment of ``text`` (provider names, not user data)."""
    return _UNSAFE.sub("_", text) or "provider"


# -- (de)serialisation ----------------------------------------------------
#
# Dates are the only thing JSON cannot carry, so every one of them crosses the
# boundary as an ISO string and is parsed back on the way in. Keeping the two
# directions adjacent makes it obvious when one drifts from the other.


def _bar_to_json(bar: Bar) -> dict[str, Any]:
    return {
        "ts": bar.ts.isoformat(),
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "volume": bar.volume,
    }


def _bar_from_json(raw: dict[str, Any]) -> Bar:
    return Bar(
        ts=date.fromisoformat(raw["ts"]),
        open=raw["open"],
        high=raw["high"],
        low=raw["low"],
        close=raw["close"],
        volume=raw["volume"],
    )


def _prices_to_json(series: PriceSeries) -> dict[str, Any]:
    return {"symbol": series.symbol, "bars": [_bar_to_json(b) for b in series.bars]}


def _prices_from_json(raw: dict[str, Any]) -> PriceSeries:
    return PriceSeries(raw["symbol"], tuple(_bar_from_json(b) for b in raw["bars"]))


def _fundamentals_to_json(value: Fundamentals | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "symbol": value.symbol,
        "as_of": value.as_of.isoformat(),
        "metrics": dict(value.metrics),
    }


def _fundamentals_from_json(raw: dict[str, Any] | None) -> Fundamentals | None:
    if raw is None:
        return None
    return Fundamentals(
        symbol=raw["symbol"],
        as_of=date.fromisoformat(raw["as_of"]),
        metrics=dict(raw["metrics"]),
    )


def _news_to_json(items: tuple[NewsItem, ...]) -> list[dict[str, Any]]:
    return [
        {
            "ts": item.ts.isoformat(),
            "headline": item.headline,
            "summary": item.summary,
            "source": item.source,
            "url": item.url,
        }
        for item in items
    ]


def _news_from_json(raw: list[dict[str, Any]]) -> tuple[NewsItem, ...]:
    return tuple(
        NewsItem(
            ts=datetime.fromisoformat(item["ts"]),
            headline=item["headline"],
            summary=item.get("summary", ""),
            source=item.get("source", ""),
            url=item.get("url"),
        )
        for item in raw
    )


class CachingProvider:
    """Wraps a provider and serves repeat calls from a JSON file cache.

    Entries are keyed on the wrapped provider's name, the method and its
    arguments, so two providers sharing a directory cannot answer for each
    other and a different date range is a different entry.
    """

    def __init__(
        self,
        inner: MarketDataProvider,
        cache_dir: str | Path = DEFAULT_CACHE_DIR,
    ) -> None:
        self.inner = inner
        self.name = f"cached:{inner.name}"
        self.cache_dir = Path(cache_dir) / _slug(inner.name)

    # -- MarketDataProvider ------------------------------------------------

    def prices(self, symbol: str, start: date, end: date) -> PriceSeries:
        return self._memoise(
            method="prices",
            symbol=symbol,
            args=(start.isoformat(), end.isoformat()),
            compute=lambda: self.inner.prices(symbol, start, end),
            encode=_prices_to_json,
            decode=_prices_from_json,
        )

    def fundamentals(self, symbol: str, as_of: date) -> Fundamentals | None:
        return self._memoise(
            method="fundamentals",
            symbol=symbol,
            args=(as_of.isoformat(),),
            compute=lambda: self.inner.fundamentals(symbol, as_of),
            encode=_fundamentals_to_json,
            decode=_fundamentals_from_json,
        )

    def news(self, symbol: str, as_of: date, lookback_days: int = 7) -> tuple[NewsItem, ...]:
        return self._memoise(
            method="news",
            symbol=symbol,
            args=(as_of.isoformat(), lookback_days),
            compute=lambda: self.inner.news(symbol, as_of, lookback_days),
            encode=_news_to_json,
            decode=_news_from_json,
        )

    # -- cache plumbing ----------------------------------------------------

    def clear(self) -> int:
        """Delete this provider's cached entries. Returns how many were removed."""
        if not self.cache_dir.is_dir():
            return 0
        removed = 0
        for path in self.cache_dir.glob("*.json"):
            path.unlink()
            removed += 1
        return removed

    def path_for(self, method: str, symbol: str, args: tuple[Any, ...]) -> Path:
        """Where the entry for one call lives.

        The filename is a digest because symbols such as ``BRK.B`` or ``^GSPC``
        are not portable filenames; the human-readable key is stored inside.
        """
        key = json.dumps(
            {"provider": self.inner.name, "method": method, "symbol": symbol, "args": list(args)},
            sort_keys=True,
        )
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        return self.cache_dir / f"{method}-{digest}.json"

    def _memoise(
        self,
        *,
        method: str,
        symbol: str,
        args: tuple[Any, ...],
        compute: Callable[[], Any],
        encode: Callable[[Any], Any],
        decode: Callable[[Any], Any],
    ) -> Any:
        path = self.path_for(method, symbol, args)
        cached = self._read(path)
        if cached is not None:
            return decode(cached["payload"])

        value = compute()
        self._write(path, method, symbol, args, encode(value))
        return value

    @staticmethod
    def _read(path: Path) -> dict[str, Any] | None:
        """Load an entry, treating anything unreadable as a miss.

        A half-written or hand-edited file should cost a refetch, never a crash.
        """
        if not path.is_file():
            return None
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return envelope if isinstance(envelope, dict) and "payload" in envelope else None

    def _write(
        self,
        path: Path,
        method: str,
        symbol: str,
        args: tuple[Any, ...],
        payload: Any,
    ) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        envelope = {
            "provider": self.inner.name,
            "method": method,
            "symbol": symbol,
            "args": list(args),
            "cached_at": datetime.now().isoformat(timespec="seconds"),
            "payload": payload,
        }
        # Write-then-rename so a crash mid-write cannot leave a torn entry that
        # a later run would read as truth.
        temp = path.with_suffix(".json.tmp")
        temp.write_text(json.dumps(envelope, indent=2, sort_keys=True), encoding="utf-8")
        temp.replace(path)

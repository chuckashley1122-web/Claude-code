"""Market data providers and the factory that picks one.

Everything upstream of here talks to the :class:`MarketDataProvider` protocol,
so swapping the offline generator for a live vendor is a config string change
(``Settings.data_provider``) and nothing else.
"""

from __future__ import annotations

from ..interfaces import MarketDataProvider
from .cache import DEFAULT_CACHE_DIR, CachingProvider
from .synthetic import SyntheticProvider
from .yfinance_provider import YFinanceProvider

__all__ = [
    "CachingProvider",
    "DEFAULT_CACHE_DIR",
    "SyntheticProvider",
    "YFinanceProvider",
    "get_provider",
]

_PROVIDERS: dict[str, type] = {
    SyntheticProvider.name: SyntheticProvider,
    YFinanceProvider.name: YFinanceProvider,
}


def get_provider(name: str, **kwargs) -> MarketDataProvider:
    """Build the provider called ``name``.

    Raises ``ValueError`` rather than falling back to the synthetic provider:
    a typo in a config file must not silently turn a live run into a simulated
    one. ``kwargs`` go straight to the provider's constructor.
    """
    key = name.strip().lower()
    try:
        provider = _PROVIDERS[key]
    except KeyError:
        known = ", ".join(sorted(_PROVIDERS))
        raise ValueError(f"unknown data provider {name!r}; expected one of: {known}") from None
    return provider(**kwargs)

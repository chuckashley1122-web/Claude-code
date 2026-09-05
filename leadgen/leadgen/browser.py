"""Fetcher configuration.

Scrapling picks sane defaults on a normal machine. Two things still need to be
overridable: an outbound proxy (some CI/sandbox networks force one) and an
explicit Chromium binary (when the environment ships its own instead of
Playwright's bundled download).
"""

from __future__ import annotations

import os
from typing import Any


def proxy() -> str | None:
    """Explicit LEADGEN_PROXY wins; otherwise fall back to the ambient HTTPS proxy."""
    return os.getenv("LEADGEN_PROXY") or os.getenv("HTTPS_PROXY") or None


def chromium_path() -> str | None:
    return os.getenv("LEADGEN_CHROMIUM_PATH") or None


def browser_kwargs() -> dict[str, Any]:
    """kwargs shared by Scrapling's browser-backed fetchers."""
    kwargs: dict[str, Any] = {}
    if (p := proxy()):
        kwargs["proxy"] = p
    if (exe := chromium_path()):
        kwargs["executable_path"] = exe
    return kwargs


def fetch(url: str, *, stealthy: bool = False, timeout: int = 30000):
    """Fetch a page and hand back a Scrapling selector.

    stealthy=True routes through StealthyFetcher (real browser + anti-bot
    evasion) for sites that block plain HTTP clients. It is slower, so the
    default is the fast path.
    """
    if stealthy:
        from scrapling.fetchers import StealthyFetcher

        return StealthyFetcher.fetch(url, timeout=timeout, **browser_kwargs())

    from scrapling.fetchers import Fetcher

    kwargs: dict[str, Any] = {"timeout": timeout // 1000, "stealthy_headers": True}
    if (p := proxy()):
        kwargs["proxy"] = p
    return Fetcher.get(url, **kwargs)

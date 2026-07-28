"""Execution adapters.

Only the paper broker exists, and that is the design: no live venue client is
implemented or scaffolded anywhere in this package, so nothing here can send an
order to a real market.
"""

from __future__ import annotations

from .paper import PaperBroker

__all__ = ["PaperBroker"]

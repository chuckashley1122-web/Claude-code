"""The analyst committee.

Four seats, deliberately chosen to disagree: a chartist, a valuation analyst, a
narrative reader, and a risk officer whose job is to argue against the other
three.
"""

from __future__ import annotations

from ..interfaces import LanguageModel
from .base import BaseAnalyst
from .fundamental import FundamentalAnalyst
from .risk_analyst import RiskAnalyst
from .sentiment import SentimentAnalyst
from .technical import TechnicalAnalyst

__all__ = [
    "BaseAnalyst",
    "FundamentalAnalyst",
    "RiskAnalyst",
    "SentimentAnalyst",
    "TechnicalAnalyst",
    "default_committee",
    "ANALYST_REGISTRY",
]

ANALYST_REGISTRY: dict[str, type[BaseAnalyst]] = {
    "technical": TechnicalAnalyst,
    "fundamental": FundamentalAnalyst,
    "sentiment": SentimentAnalyst,
    "risk": RiskAnalyst,
}


def default_committee(
    llm: LanguageModel | None = None,
    horizon_days: int = 20,
    names: tuple[str, ...] | None = None,
) -> list[BaseAnalyst]:
    """Instantiate the standard committee, or the subset named in ``names``."""
    selected = names or tuple(ANALYST_REGISTRY)
    unknown = set(selected) - set(ANALYST_REGISTRY)
    if unknown:
        raise ValueError(
            f"Unknown analyst(s): {sorted(unknown)}. "
            f"Available: {sorted(ANALYST_REGISTRY)}"
        )
    return [ANALYST_REGISTRY[name](llm=llm, horizon_days=horizon_days) for name in selected]

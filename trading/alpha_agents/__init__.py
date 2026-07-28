"""alpha_agents — a multi-agent trading research engine.

A committee of specialist analysts (technical, fundamental, sentiment, risk)
each forms an independent view on a symbol. A moderator weighs those views
against each other into a single verdict, a risk manager sizes and vets any
resulting order, and a paper broker executes it.

Paper trading only. No live broker adapter ships with this package, and the
pipeline refuses to run against a broker that reports ``is_live`` unless
``Settings.allow_live_trading`` has been set deliberately.

    from datetime import date
    from alpha_agents import Settings, TradingPipeline, PaperBroker, Portfolio
    from alpha_agents.data import get_provider

    settings = Settings()
    broker = PaperBroker(Portfolio(cash=settings.starting_cash), settings.costs)
    pipeline = TradingPipeline(settings, get_provider("synthetic"), broker)
    print(pipeline.research("NVDA", date.today()).rationale)
"""

from __future__ import annotations

__version__ = "0.1.0"

from .backtest import Backtester, BacktestResult
from .config import CostModel, ModelConfig, RiskLimits, Settings
from .debate import DebateModerator
from .execution import PaperBroker
from .models import (
    AccountSnapshot,
    AnalystView,
    Bar,
    Evidence,
    Fill,
    Fundamentals,
    NewsItem,
    Order,
    Position,
    PriceSeries,
    ResearchBundle,
    Stance,
    Verdict,
)
from .pipeline import Decision, ScanResult, TradingPipeline
from .portfolio import Portfolio
from .risk import RiskManager, size_position

__all__ = [
    "__version__",
    # configuration
    "Settings",
    "RiskLimits",
    "CostModel",
    "ModelConfig",
    # value types
    "Bar",
    "PriceSeries",
    "Fundamentals",
    "NewsItem",
    "Evidence",
    "AnalystView",
    "Verdict",
    "Order",
    "Fill",
    "Position",
    "AccountSnapshot",
    "ResearchBundle",
    "Stance",
    # machinery
    "DebateModerator",
    "TradingPipeline",
    "Decision",
    "ScanResult",
    "Portfolio",
    "RiskManager",
    "size_position",
    "PaperBroker",
    "Backtester",
    "BacktestResult",
]

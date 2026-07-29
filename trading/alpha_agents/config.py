"""Configuration, including the risk limits that bound everything downstream.

Defaults here are deliberately conservative. They are the difference between a
research tool and a way to lose money quickly, so they live in one reviewable
place rather than scattered through the pipeline.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class RiskLimits:
    """Hard bounds applied to every order, after sizing and before execution."""

    max_position_pct: float = 0.10
    """No single symbol may exceed this fraction of equity."""

    max_gross_exposure: float = 0.80
    """Total invested capital as a fraction of equity. Leaves a cash buffer."""

    max_new_positions_per_day: int = 3
    """Caps how fast the book can turn over on any one signal burst."""

    max_daily_loss_pct: float = 0.03
    """Trip the kill switch if equity falls this far below the day's opening mark."""

    max_drawdown_pct: float = 0.20
    """Trip the kill switch on peak-to-trough decline of the equity curve."""

    min_confidence: float = 0.60
    """Verdicts below this confidence are not traded, regardless of stance."""

    vol_target_annual: float = 0.04
    """Annualised volatility budget per position.

    Sizing is ``equity * (vol_target / annual_vol) * confidence``, clamped to
    ``max_position_pct``. The value has to be small enough that the clamp does
    not swallow it: at the original 0.15 the 10% cap bound for any volatility
    below 150%, so every realistic name got exactly 10% of equity and a
    60%-vol position carried five times the risk of a 12%-vol one. At 0.04 the
    vol term starts binding around 30% annualised, which is where it should.
    """

    # There is deliberately no max_sector_pct. It was configured, validated and
    # serialised while never being read by any code path, and no sector data
    # exists on Fundamentals or Position for it to read — a limit that cannot
    # be enforced is worse than an absent one, because it reads as protection.
    # Reinstate it together with a sector map and a check in RiskManager.

    def __post_init__(self) -> None:
        fractions = {
            "max_position_pct": self.max_position_pct,
            "max_gross_exposure": self.max_gross_exposure,
            "max_daily_loss_pct": self.max_daily_loss_pct,
            "max_drawdown_pct": self.max_drawdown_pct,
            "min_confidence": self.min_confidence,
        }
        for name, value in fractions.items():
            if not 0.0 < value <= 1.0:
                raise ValueError(f"{name} must be in (0, 1], got {value}")
        if self.max_position_pct > self.max_gross_exposure:
            raise ValueError("max_position_pct cannot exceed max_gross_exposure")
        if self.max_new_positions_per_day < 0:
            raise ValueError("max_new_positions_per_day must be non-negative")
        if self.vol_target_annual <= 0:
            raise ValueError("vol_target_annual must be positive")


@dataclass(frozen=True)
class CostModel:
    """What a trade costs beyond the quoted price.

    A backtest that ignores these will look far better than the strategy is.
    """

    commission_per_share: float = 0.005
    commission_minimum: float = 1.00
    slippage_bps: float = 5.0
    """Assumed adverse price move on entry, in basis points of notional."""

    def __post_init__(self) -> None:
        if self.commission_per_share < 0 or self.commission_minimum < 0:
            raise ValueError("commission components must be non-negative")
        if self.slippage_bps < 0:
            raise ValueError("slippage_bps must be non-negative")


@dataclass(frozen=True)
class ModelConfig:
    """Which model each layer of the committee uses."""

    analyst_model: str = "claude-opus-5"
    moderator_model: str = "claude-opus-5"
    effort: str = "high"
    max_tokens: int = 4000


@dataclass(frozen=True)
class Settings:
    universe: tuple[str, ...] = ("AAPL", "MSFT", "NVDA", "GOOGL", "AMZN")
    starting_cash: float = 100_000.0
    lookback_days: int = 250
    risk: RiskLimits = field(default_factory=RiskLimits)
    costs: CostModel = field(default_factory=CostModel)
    models: ModelConfig = field(default_factory=ModelConfig)
    data_provider: str = "synthetic"
    """``synthetic`` (offline, deterministic) or ``yfinance`` (live, optional dep)."""

    allow_live_trading: bool = False
    """Guard rail. No live broker adapter ships; this must be flipped
    deliberately alongside one, and the pipeline refuses live orders without it."""

    @classmethod
    def from_file(cls, path: str | Path) -> "Settings":
        raw = json.loads(Path(path).read_text())
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict) -> "Settings":
        raw = dict(raw)
        if "universe" in raw:
            raw["universe"] = tuple(raw["universe"])
        if "risk" in raw:
            raw["risk"] = RiskLimits(**raw["risk"])
        if "costs" in raw:
            raw["costs"] = CostModel(**raw["costs"])
        if "models" in raw:
            raw["models"] = ModelConfig(**raw["models"])
        return cls(**raw)

    @classmethod
    def from_env(cls) -> "Settings":
        """Build from ``ALPHA_AGENTS_CONFIG`` if set, else defaults."""
        path = os.environ.get("ALPHA_AGENTS_CONFIG")
        return cls.from_file(path) if path else cls()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["universe"] = list(self.universe)
        return data

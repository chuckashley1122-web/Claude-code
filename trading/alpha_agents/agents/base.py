"""Shared machinery for the specialist analysts.

Every analyst follows the same three-step shape:

1. ``gather`` — compute hard numbers from the research bundle, in Python.
2. ``decide`` — turn those numbers into a view using explicit rules.
3. optionally, hand both to Claude for a better-reasoned view.

Step 1 stays in code deliberately. Models are poor arithmetic engines and good
judgement engines, so the indicators, ratios and counts are computed
deterministically and the model reasons *over* them. That also means every LLM
view is reproducible enough to audit: the evidence it saw is recorded verbatim.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from ..interfaces import LanguageModel
from ..llm import LanguageModelError
from ..models import AnalystView, Evidence, ResearchBundle, Stance

VIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "stance": {"type": "string", "enum": ["buy", "sell", "hold"]},
        "confidence": {
            "type": "number",
            "description": "0 = coin flip, 1 = near certainty. Be honest; "
            "overconfidence here becomes oversized positions downstream.",
        },
        "rationale": {
            "type": "string",
            "description": "Two or three sentences. Cite the specific signals "
            "that drove the call, including any that argue against it.",
        },
        "key_factors": {
            "type": "array",
            "items": {"type": "string"},
            "description": "The individual signals that mattered most.",
        },
    },
    "required": ["stance", "confidence", "rationale", "key_factors"],
    "additionalProperties": False,
}


class BaseAnalyst:
    """Template for a specialist. Subclasses implement ``gather`` and ``decide``."""

    name: str = "base"
    role_description: str = "a market analyst"
    focus: str = "general market conditions"

    def __init__(
        self,
        llm: LanguageModel | None = None,
        horizon_days: int = 20,
        strict: bool = False,
    ) -> None:
        """``strict`` re-raises model errors instead of falling back to rules.

        The default (fall back) is right for a scan you want to complete; strict
        is right when a silent downgrade to heuristics would mislead you.
        """
        self.llm = llm
        self.horizon_days = horizon_days
        self.strict = strict

    # --- subclass hooks -------------------------------------------------

    def gather(self, bundle: ResearchBundle) -> dict[str, Any]:
        """Compute the analyst's signals. Values must be JSON-serialisable."""
        raise NotImplementedError

    def decide(self, signals: Mapping[str, Any], bundle: ResearchBundle) -> AnalystView:
        """Rules-only view. Must work with no model available."""
        raise NotImplementedError

    # --- driver ---------------------------------------------------------

    def analyze(self, bundle: ResearchBundle) -> AnalystView:
        signals = self.gather(bundle)
        baseline = self.decide(signals, bundle)
        if self.llm is None:
            return baseline
        try:
            return self._llm_view(bundle, signals, baseline)
        except (LanguageModelError, ImportError):
            if self.strict:
                raise
            return baseline

    def _llm_view(
        self,
        bundle: ResearchBundle,
        signals: Mapping[str, Any],
        baseline: AnalystView,
    ) -> AnalystView:
        raw = self.llm.complete_json(  # type: ignore[union-attr]
            system=self.system_prompt(),
            prompt=self.user_prompt(bundle, signals, baseline),
            schema=VIEW_SCHEMA,
        )
        stance = _coerce_stance(raw.get("stance"))
        confidence = _clamp(raw.get("confidence", baseline.confidence))
        factors = tuple(
            Evidence(label="model", detail=str(f))
            for f in raw.get("key_factors", [])[:8]
        )
        return AnalystView(
            analyst=self.name,
            symbol=bundle.symbol,
            stance=stance,
            confidence=confidence,
            rationale=str(raw.get("rationale", "")).strip() or baseline.rationale,
            # Keep the computed evidence alongside the model's — the numbers are
            # what make the view checkable after the fact.
            evidence=baseline.evidence + factors,
            horizon_days=self.horizon_days,
        )

    # --- prompting ------------------------------------------------------

    def system_prompt(self) -> str:
        return (
            f"You are {self.role_description} on a systematic trading desk. "
            f"You focus exclusively on {self.focus}; other analysts cover the "
            "rest, so do not stray outside your remit or hedge by deferring to "
            "them.\n\n"
            "You are given signals that were computed deterministically in "
            "code. Treat those numbers as ground truth — do not recompute or "
            "second-guess the arithmetic. Your job is judgement: what do these "
            "signals imply, how strong is the evidence, and what would make you "
            "wrong.\n\n"
            "Calibration matters more than decisiveness. Confidence above 0.8 "
            "should be rare and reserved for signals that genuinely agree. When "
            "the evidence is mixed, say hold with low confidence — that is a "
            "useful answer, not a failure. Position size scales with your "
            "confidence, so inflating it costs real money.\n\n"
            "This is research output for a paper-trading system, not investment "
            "advice."
        )

    def user_prompt(
        self,
        bundle: ResearchBundle,
        signals: Mapping[str, Any],
        baseline: AnalystView,
    ) -> str:
        lines = [
            f"Symbol: {bundle.symbol}",
            f"As of: {bundle.as_of.isoformat()}",
            f"Horizon: {self.horizon_days} trading days",
            "",
            "Computed signals:",
        ]
        lines.extend(_render_signals(signals))
        lines += [
            "",
            f"The rule-based baseline says {baseline.stance.value.upper()} "
            f"at {baseline.confidence:.2f} confidence "
            f"({baseline.rationale}).",
            "",
            "Give your own view. Agreeing with the baseline is fine when the "
            "signals support it; disagreeing is expected when they do not.",
        ]
        return "\n".join(lines)


# --- helpers ------------------------------------------------------------


def _render_signals(signals: Mapping[str, Any], indent: str = "  ") -> list[str]:
    out: list[str] = []
    for key, value in signals.items():
        if isinstance(value, Mapping):
            out.append(f"{indent}{key}:")
            out.extend(_render_signals(value, indent + "  "))
        elif isinstance(value, (list, tuple)) and not isinstance(value, str):
            rendered = ", ".join(_fmt(v) for v in value[:10])
            out.append(f"{indent}{key}: [{rendered}]")
        else:
            out.append(f"{indent}{key}: {_fmt(value)}")
    return out


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _coerce_stance(value: Any) -> Stance:
    try:
        return Stance(str(value).strip().lower())
    except ValueError:
        return Stance.HOLD


def _clamp(value: Any, low: float = 0.0, high: float = 1.0) -> float:
    try:
        return max(low, min(high, float(value)))
    except (TypeError, ValueError):
        return low


def last_defined(values: Sequence[Any]) -> Any:
    """Most recent non-``None`` entry of an indicator series, or ``None``."""
    for v in reversed(values):
        if v is not None:
            return v
    return None

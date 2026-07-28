"""Turning four analyst views into one decision.

A plain average would let three mildly bullish views outvote one analyst who
found something disqualifying, and would report high confidence for a committee
that actually disagreed. So the moderator does three things a mean does not:

* weights views by analyst *and* by how much evidence each brought,
* penalises confidence when the committee is split rather than hiding it, and
* lets the risk seat veto a buy outright.

Disagreement is signal. A 2-2 split at high individual confidence is a much
worse setup than unanimous mild agreement, and the output says so.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .agents.risk_analyst import FLAG_PREFIX
from .interfaces import LanguageModel
from .llm import LanguageModelError
from .models import AnalystView, Stance, Verdict

DEFAULT_WEIGHTS: dict[str, float] = {
    "technical": 1.0,
    "fundamental": 1.0,
    "sentiment": 0.6,
    "risk": 0.0,  # the risk seat modulates rather than votes on direction
}

VETO_CONFIDENCE = 0.55
"""A risk SELL at or above this confidence blocks a BUY outright."""

MODERATOR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "stance": {"type": "string", "enum": ["buy", "sell", "hold"]},
        "confidence": {"type": "number"},
        "rationale": {"type": "string"},
        "dissent": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Points of genuine disagreement, and what would "
            "have to be true for the minority view to be right.",
        },
    },
    "required": ["stance", "confidence", "rationale", "dissent"],
    "additionalProperties": False,
}


@dataclass
class DebateModerator:
    """Synthesises analyst views into a :class:`Verdict`."""

    weights: Mapping[str, float] = None  # type: ignore[assignment]
    llm: LanguageModel | None = None
    veto_confidence: float = VETO_CONFIDENCE
    strict: bool = False

    def __post_init__(self) -> None:
        if self.weights is None:
            self.weights = dict(DEFAULT_WEIGHTS)

    def resolve(self, symbol: str, views: Sequence[AnalystView]) -> Verdict:
        if not views:
            return Verdict(
                symbol=symbol,
                stance=Stance.HOLD,
                confidence=0.0,
                rationale="No analyst produced a view.",
            )

        tally = self._tally(views)
        baseline = self._baseline_verdict(symbol, views, tally)
        if self.llm is None:
            return baseline
        try:
            return self._llm_verdict(symbol, views, tally, baseline)
        except (LanguageModelError, ImportError):
            if self.strict:
                raise
            return baseline

    # --- deterministic core --------------------------------------------

    def _tally(self, views: Sequence[AnalystView]) -> dict[str, Any]:
        score = 0.0
        total_weight = 0.0
        directional: list[AnalystView] = []

        for view in views:
            weight = float(self.weights.get(view.analyst, 0.5))
            if weight <= 0:
                continue
            # An unevidenced view still counts, but less. This is what stops a
            # confident-sounding analyst with nothing behind it from dominating.
            evidence_factor = 0.7 + 0.3 * min(len(view.evidence), 3) / 3
            effective = weight * evidence_factor
            score += effective * view.confidence * view.stance.sign
            total_weight += effective
            if view.stance is not Stance.HOLD:
                directional.append(view)

        normalized = score / total_weight if total_weight else 0.0

        buys = [v for v in views if v.stance is Stance.BUY]
        sells = [v for v in views if v.stance is Stance.SELL and v.analyst != "risk"]

        # Split severity: how much confident conviction sits on the losing side.
        losing = sells if normalized >= 0 else buys
        split = sum(v.confidence for v in losing)

        risk_view = next((v for v in views if v.analyst == "risk"), None)
        flags = tuple(
            e.detail
            for v in views
            for e in v.evidence
            if e.label.startswith(FLAG_PREFIX)
        )

        return {
            "score": round(normalized, 4),
            "raw_score": round(score, 4),
            "total_weight": round(total_weight, 4),
            "buy_count": len(buys),
            "sell_count": len(sells),
            "hold_count": sum(1 for v in views if v.stance is Stance.HOLD),
            "directional_count": len(directional),
            "split_severity": round(split, 3),
            "risk_stance": risk_view.stance.value if risk_view else None,
            "risk_confidence": risk_view.confidence if risk_view else None,
            "risk_flags": flags,
        }

    def _baseline_verdict(
        self,
        symbol: str,
        views: Sequence[AnalystView],
        tally: Mapping[str, Any],
    ) -> Verdict:
        score = float(tally["score"])
        magnitude = abs(score)

        if magnitude < 0.15:
            stance = Stance.HOLD
            confidence = min(0.3, magnitude * 2)
        else:
            stance = Stance.BUY if score > 0 else Stance.SELL
            confidence = min(0.95, 0.35 + magnitude * 0.75)

        notes: list[str] = []

        # Split penalty, applied before any veto so it shows up either way.
        split = float(tally["split_severity"])
        if split > 0:
            penalty = min(0.5, split * 0.35)
            confidence *= 1 - penalty
            notes.append(
                f"committee split ({tally['buy_count']} buy / "
                f"{tally['sell_count']} sell / {tally['hold_count']} hold), "
                f"confidence cut {penalty:.0%}"
            )

        dissent = tuple(
            f"{v.analyst} says {v.stance.value.upper()} "
            f"({v.confidence:.2f}): {v.rationale}"
            for v in views
            if v.stance is not stance and v.stance is not Stance.HOLD
        )

        # The risk veto. A risk officer arguing to sell outranks a buy signal —
        # being late to an entry is recoverable, the reverse often is not.
        risk_stance = tally.get("risk_stance")
        risk_conf = tally.get("risk_confidence") or 0.0
        if (
            stance is Stance.BUY
            and risk_stance == Stance.SELL.value
            and risk_conf >= self.veto_confidence
        ):
            stance = Stance.HOLD
            confidence = min(confidence, 0.3)
            notes.append(f"risk veto applied (risk confidence {risk_conf:.2f})")
        elif risk_conf >= 0.4 and stance is Stance.BUY:
            confidence *= 0.85
            notes.append("risk concerns present, confidence trimmed")

        rationale = (
            f"Weighted committee score {score:+.2f} across "
            f"{len(views)} analysts -> {stance.value.upper()}."
        )
        if notes:
            rationale += " " + "; ".join(notes) + "."

        return Verdict(
            symbol=symbol,
            stance=stance,
            confidence=round(max(0.0, min(1.0, confidence)), 3),
            rationale=rationale,
            views=tuple(views),
            dissent=dissent,
            risk_flags=tuple(tally["risk_flags"]),
        )

    # --- model-assisted synthesis --------------------------------------

    def _llm_verdict(
        self,
        symbol: str,
        views: Sequence[AnalystView],
        tally: Mapping[str, Any],
        baseline: Verdict,
    ) -> Verdict:
        raw = self.llm.complete_json(  # type: ignore[union-attr]
            system=(
                "You chair the investment committee of a systematic trading "
                "desk. Four analysts have each given you a view on one symbol. "
                "Your job is to weigh them against each other and issue a single "
                "decision.\n\n"
                "Weigh evidence, not assertiveness. A specific number beats a "
                "confident adjective. When analysts disagree, do not split the "
                "difference — work out which one is looking at the more "
                "decision-relevant evidence, and say so.\n\n"
                "The risk officer is not a fourth opinion on direction. If they "
                "have raised flags, either explain why the setup justifies the "
                "risk or stand down.\n\n"
                "HOLD is a real answer and often the right one. A weak or "
                "conflicted signal should produce HOLD, not a low-confidence "
                "guess at a direction. Confidence sizes the position, so treat "
                "it as a number that costs money when inflated.\n\n"
                "Record genuine disagreement in `dissent` — including what "
                "would have to be true for the minority to be right. A verdict "
                "that hides the split is worse than one that admits it."
            ),
            prompt=_moderator_prompt(symbol, views, tally, baseline),
            schema=MODERATOR_SCHEMA,
        )

        try:
            stance = Stance(str(raw.get("stance", "hold")).strip().lower())
        except ValueError:
            stance = Stance.HOLD
        try:
            confidence = max(0.0, min(1.0, float(raw.get("confidence", 0.0))))
        except (TypeError, ValueError):
            confidence = 0.0

        # The veto is not negotiable by the model. It is a control, not advice.
        risk_stance = tally.get("risk_stance")
        risk_conf = tally.get("risk_confidence") or 0.0
        extra_dissent: tuple[str, ...] = ()
        if (
            stance is Stance.BUY
            and risk_stance == Stance.SELL.value
            and risk_conf >= self.veto_confidence
        ):
            extra_dissent = (
                f"Moderator proposed BUY; risk veto overrode it "
                f"(risk confidence {risk_conf:.2f}).",
            )
            stance = Stance.HOLD
            confidence = min(confidence, 0.3)

        dissent = tuple(str(d) for d in raw.get("dissent", [])[:6]) + extra_dissent

        return Verdict(
            symbol=symbol,
            stance=stance,
            confidence=round(confidence, 3),
            rationale=str(raw.get("rationale", "")).strip() or baseline.rationale,
            views=tuple(views),
            dissent=dissent or baseline.dissent,
            risk_flags=tuple(tally["risk_flags"]),
        )


def _moderator_prompt(
    symbol: str,
    views: Sequence[AnalystView],
    tally: Mapping[str, Any],
    baseline: Verdict,
) -> str:
    lines = [f"Symbol: {symbol}", "", "Analyst views:"]
    for view in views:
        lines.append(
            f"\n[{view.analyst}] {view.stance.value.upper()} "
            f"(confidence {view.confidence:.2f}, horizon {view.horizon_days}d)"
        )
        lines.append(f"  Rationale: {view.rationale}")
        for e in view.evidence[:8]:
            value = f" ({e.value:.4f})" if e.value is not None else ""
            lines.append(f"  - {e.label}: {e.detail}{value}")

    lines += [
        "",
        "Mechanical tally:",
        f"  weighted score: {tally['score']:+.3f}",
        f"  buy/sell/hold: {tally['buy_count']}/{tally['sell_count']}/{tally['hold_count']}",
        f"  split severity: {tally['split_severity']:.2f}",
    ]
    if tally["risk_flags"]:
        lines.append("  risk flags:")
        lines.extend(f"    - {flag}" for flag in tally["risk_flags"])

    lines += [
        "",
        f"The mechanical rule would say {baseline.stance.value.upper()} at "
        f"{baseline.confidence:.2f}. You may depart from it, but justify the "
        "departure from the evidence above.",
    ]
    return "\n".join(lines)

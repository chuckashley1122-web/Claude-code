"""News and narrative analyst.

The deterministic path is a lexicon scorer, which is crude — it cannot read
negation or sarcasm and it does not know that "beats lowered expectations" is
faint praise. That is precisely why this analyst benefits most from the model
path: the rules exist so the pipeline still runs offline, not because they are
good.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..models import AnalystView, Evidence, ResearchBundle, Stance
from .base import BaseAnalyst

POSITIVE_TERMS: dict[str, float] = {
    "beat": 1.0, "beats": 1.0, "surge": 1.2, "surges": 1.2, "record": 1.0,
    "upgrade": 1.3, "upgraded": 1.3, "outperform": 1.1, "raises": 1.0,
    "raised": 1.0, "growth": 0.6, "profit": 0.7, "expansion": 0.7,
    "breakthrough": 1.0, "wins": 0.8, "approval": 0.9, "buyback": 0.9,
    "dividend": 0.5, "strong": 0.7, "rally": 0.9, "optimistic": 0.7,
}

NEGATIVE_TERMS: dict[str, float] = {
    "miss": 1.0, "misses": 1.0, "plunge": 1.2, "plunges": 1.2, "downgrade": 1.3,
    "downgraded": 1.3, "underperform": 1.1, "cuts": 1.0, "cut": 0.9,
    "lawsuit": 1.1, "probe": 1.0, "investigation": 1.1, "recall": 1.0,
    "layoffs": 0.9, "loss": 0.8, "losses": 0.8, "warning": 1.0, "warns": 1.0,
    "decline": 0.7, "weak": 0.7, "selloff": 1.0, "fraud": 1.5, "delay": 0.7,
    "resign": 0.8, "resigns": 0.8, "bankruptcy": 1.6, "halt": 0.9,
}


class SentimentAnalyst(BaseAnalyst):
    name = "sentiment"
    role_description = "a news and market-narrative analyst"
    focus = "recent headlines, tone, and what the market is being told about the company"

    def gather(self, bundle: ResearchBundle) -> dict[str, Any]:
        if not bundle.news:
            return {"headline_count": 0}

        scored: list[dict[str, Any]] = []
        total = 0.0
        for item in bundle.news:
            text = f"{item.headline} {item.summary}".lower()
            words = _tokenize(text)
            pos = sum(POSITIVE_TERMS.get(w, 0.0) for w in words)
            neg = sum(NEGATIVE_TERMS.get(w, 0.0) for w in words)
            net = pos - neg
            total += net
            scored.append(
                {
                    "headline": item.headline,
                    "source": item.source,
                    "ts": item.ts.isoformat(),
                    "score": round(net, 2),
                }
            )

        count = len(scored)
        return {
            "headline_count": count,
            "net_score": round(total, 3),
            "average_score": round(total / count, 3),
            "positive_headlines": sum(1 for s in scored if s["score"] > 0),
            "negative_headlines": sum(1 for s in scored if s["score"] < 0),
            # Full headlines go to the model — it can read what the lexicon can't.
            "headlines": scored,
        }

    def decide(self, signals: Mapping[str, Any], bundle: ResearchBundle) -> AnalystView:
        count = int(signals.get("headline_count", 0))
        if count == 0:
            return AnalystView(
                analyst=self.name,
                symbol=bundle.symbol,
                stance=Stance.HOLD,
                confidence=0.0,
                rationale="No recent news in the lookback window.",
                horizon_days=self.horizon_days,
            )

        average = float(signals.get("average_score", 0.0))
        evidence = [
            Evidence("headline_count", f"{count} headlines in window", float(count)),
            Evidence("net_tone", f"average tone {average:+.2f}", average),
        ]
        for item in signals.get("headlines", [])[:5]:
            evidence.append(
                Evidence("headline", f"[{item['score']:+.1f}] {item['headline']}")
            )

        if abs(average) < 0.3:
            stance, confidence = Stance.HOLD, 0.15 + abs(average) * 0.3
        else:
            stance = Stance.BUY if average > 0 else Stance.SELL
            confidence = 0.3 + min(abs(average), 1.5) * 0.2

        # Two headlines is an anecdote. Scale confidence with sample size and
        # cap it — lexicon sentiment never deserves high conviction on its own.
        confidence *= min(1.0, count / 5.0)
        confidence = min(confidence, 0.65)

        return AnalystView(
            analyst=self.name,
            symbol=bundle.symbol,
            stance=stance,
            confidence=round(confidence, 3),
            rationale=(
                f"{count} headlines, average lexicon tone {average:+.2f} "
                f"({signals.get('positive_headlines', 0)} positive / "
                f"{signals.get('negative_headlines', 0)} negative). "
                f"Reads as {stance.value.upper()} on narrative, with the caveat "
                "that keyword scoring misses context and negation."
            ),
            evidence=tuple(evidence),
            horizon_days=self.horizon_days,
        )


def _tokenize(text: str) -> list[str]:
    return [
        "".join(ch for ch in token if ch.isalnum())
        for token in text.split()
    ]

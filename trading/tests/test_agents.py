"""Tests for the analyst committee.

The bar for an analyst is not "produces a number" — it is "reacts in the right
direction to a stipulated setup, and refuses to have an opinion when it has no
basis for one". Both halves matter: a confident view on empty data is the
failure mode that costs money.
"""

from __future__ import annotations

import unittest

from trading.alpha_agents.agents import (
    ANALYST_REGISTRY,
    FundamentalAnalyst,
    RiskAnalyst,
    SentimentAnalyst,
    TechnicalAnalyst,
    default_committee,
)
from trading.alpha_agents.agents.risk_analyst import FLAG_PREFIX
from trading.alpha_agents.llm import LanguageModelError, StubLanguageModel
from trading.alpha_agents.models import Stance

from . import support as s


class TestTechnicalAnalyst(unittest.TestCase):
    def setUp(self) -> None:
        self.analyst = TechnicalAnalyst()

    def test_uptrend_reads_bullish(self) -> None:
        view = self.analyst.analyze(s.bundle(s.uptrend()))
        self.assertIs(view.stance, Stance.BUY)
        self.assertGreater(view.confidence, 0.5)
        self.assertTrue(view.evidence)

    def test_downtrend_reads_bearish(self) -> None:
        view = self.analyst.analyze(s.bundle(s.downtrend()))
        self.assertIs(view.stance, Stance.SELL)
        self.assertGreater(view.confidence, 0.5)

    def test_flat_series_is_a_hold_and_does_not_raise(self) -> None:
        view = self.analyst.analyze(s.bundle(s.flat()))
        self.assertIs(view.stance, Stance.HOLD)
        self.assertLess(view.confidence, 0.4)

    def test_short_history_refuses_to_opine(self) -> None:
        view = self.analyst.analyze(s.bundle(s.uptrend(n=20)))
        self.assertIs(view.stance, Stance.HOLD)
        self.assertEqual(view.confidence, 0.0)
        self.assertIn("bars", view.rationale)

    def test_high_volatility_discounts_confidence(self) -> None:
        calm = self.analyst.analyze(s.bundle(s.uptrend()))
        wild = self.analyst.analyze(s.bundle(s.choppy()))
        # Choppy has no net direction; whatever it concludes should be held
        # far less strongly than the clean trend.
        self.assertLess(wild.confidence, calm.confidence)

    def test_confidence_never_exceeds_one(self) -> None:
        for daily in (0.001, 0.01, 0.05):
            view = self.analyst.analyze(s.bundle(s.uptrend(daily=daily)))
            self.assertLessEqual(view.confidence, 1.0)
            self.assertGreaterEqual(view.confidence, 0.0)


class TestFundamentalAnalyst(unittest.TestCase):
    def setUp(self) -> None:
        self.analyst = FundamentalAnalyst()

    def test_missing_fundamentals_is_zero_confidence_hold(self) -> None:
        view = self.analyst.analyze(s.bundle(s.uptrend(), funda=None))
        self.assertIs(view.stance, Stance.HOLD)
        self.assertEqual(view.confidence, 0.0)

    def test_cheap_and_growing_reads_bullish(self) -> None:
        cheap = s.fundamentals(
            pe=8.0, ps=1.0, revenue_growth=0.30, gross_margin=0.65,
            net_margin=0.25, debt_to_equity=0.2, fcf_yield=0.09, roe=0.30,
        )
        view = self.analyst.analyze(s.bundle(s.flat(), funda=cheap))
        self.assertIs(view.stance, Stance.BUY)

    def test_expensive_and_shrinking_reads_bearish(self) -> None:
        rich = s.fundamentals(
            pe=90.0, ps=25.0, revenue_growth=-0.15, gross_margin=0.12,
            net_margin=-0.05, debt_to_equity=4.0, fcf_yield=-0.02, roe=-0.10,
        )
        view = self.analyst.analyze(s.bundle(s.flat(), funda=rich))
        self.assertIs(view.stance, Stance.SELL)

    def test_leverage_caps_conviction_on_a_buy(self) -> None:
        cheap = dict(
            pe=8.0, ps=1.0, revenue_growth=0.30, gross_margin=0.65,
            net_margin=0.25, fcf_yield=0.09, roe=0.30,
        )
        clean = self.analyst.analyze(
            s.bundle(s.flat(), funda=s.fundamentals(debt_to_equity=0.2, **cheap))
        )
        levered = self.analyst.analyze(
            s.bundle(s.flat(), funda=s.fundamentals(debt_to_equity=3.5, **cheap))
        )
        self.assertIs(clean.stance, Stance.BUY)
        self.assertLess(levered.confidence, clean.confidence)


class TestSentimentAnalyst(unittest.TestCase):
    def setUp(self) -> None:
        self.analyst = SentimentAnalyst()

    def test_no_news_is_zero_confidence_hold(self) -> None:
        view = self.analyst.analyze(s.bundle(s.flat(), items=()))
        self.assertIs(view.stance, Stance.HOLD)
        self.assertEqual(view.confidence, 0.0)

    def test_negative_headlines_read_bearish(self) -> None:
        items = s.news(
            "Company misses earnings badly",
            "Analysts downgrade the stock",
            "Regulator opens investigation into accounting fraud",
            "Shares plunge on weak guidance",
            "CEO resigns amid lawsuit",
        )
        view = self.analyst.analyze(s.bundle(s.flat(), items=items))
        self.assertIs(view.stance, Stance.SELL)

    def test_positive_headlines_read_bullish(self) -> None:
        items = s.news(
            "Company beats earnings expectations",
            "Analysts upgrade to outperform",
            "Record profit and expanded buyback",
            "Shares rally on strong guidance",
            "Regulatory approval wins new market",
        )
        view = self.analyst.analyze(s.bundle(s.flat(), items=items))
        self.assertIs(view.stance, Stance.BUY)

    def test_confidence_is_capped_because_lexicon_scoring_is_weak(self) -> None:
        items = s.news(*["Company beats records and surges on upgrade"] * 12)
        view = self.analyst.analyze(s.bundle(s.flat(), items=items))
        self.assertLessEqual(view.confidence, 0.65)

    def test_few_headlines_scale_confidence_down(self) -> None:
        one = self.analyst.analyze(
            s.bundle(s.flat(), items=s.news("Company beats earnings and surges"))
        )
        many = self.analyst.analyze(
            s.bundle(s.flat(), items=s.news(*["Company beats earnings and surges"] * 5))
        )
        self.assertLess(one.confidence, many.confidence)


class TestRiskAnalyst(unittest.TestCase):
    def setUp(self) -> None:
        self.analyst = RiskAnalyst()

    def test_calm_series_raises_no_flags(self) -> None:
        view = self.analyst.analyze(s.bundle(s.uptrend(daily=0.001)))
        flags = [e for e in view.evidence if e.label.startswith(FLAG_PREFIX)]
        self.assertEqual(flags, [])
        self.assertIs(view.stance, Stance.HOLD)

    def test_violent_series_raises_flags(self) -> None:
        view = self.analyst.analyze(s.bundle(s.choppy()))
        flags = [e for e in view.evidence if e.label.startswith(FLAG_PREFIX)]
        self.assertTrue(flags, "a wildly volatile series should raise risk flags")

    def test_never_returns_buy(self) -> None:
        """The risk seat argues against, never for. A BUY here would mean it
        had started voting on direction, which is not its job."""
        for prices in (s.uptrend(), s.downtrend(), s.flat(), s.choppy()):
            view = self.analyst.analyze(s.bundle(prices))
            self.assertIsNot(view.stance, Stance.BUY)

    def test_thin_history_flags_rather_than_guessing(self) -> None:
        view = self.analyst.analyze(s.bundle(s.uptrend(n=10)))
        self.assertIs(view.stance, Stance.HOLD)
        labels = [e.label for e in view.evidence]
        self.assertIn(f"{FLAG_PREFIX}thin_history", labels)


class TestLLMPath(unittest.TestCase):
    """The model path must upgrade the view without discarding the evidence."""

    def test_model_output_overrides_the_rule_based_stance(self) -> None:
        llm = StubLanguageModel(
            responses=[
                {
                    "stance": "sell",
                    "confidence": 0.9,
                    "rationale": "Trend is exhausted.",
                    "key_factors": ["RSI 79 is a blow-off"],
                }
            ]
        )
        view = TechnicalAnalyst(llm=llm).analyze(s.bundle(s.uptrend()))
        self.assertIs(view.stance, Stance.SELL)
        self.assertEqual(view.confidence, 0.9)
        self.assertIn("exhausted", view.rationale)

    def test_computed_evidence_survives_the_model_call(self) -> None:
        llm = StubLanguageModel(
            responses=[
                {"stance": "buy", "confidence": 0.7, "rationale": "ok", "key_factors": ["x"]}
            ]
        )
        view = TechnicalAnalyst(llm=llm).analyze(s.bundle(s.uptrend()))
        labels = {e.label for e in view.evidence}
        self.assertIn("price_vs_sma50", labels, "computed evidence must be retained")
        self.assertIn("model", labels)

    def test_signals_are_sent_to_the_model(self) -> None:
        llm = StubLanguageModel(
            responses=[
                {"stance": "hold", "confidence": 0.2, "rationale": "n/a", "key_factors": []}
            ]
        )
        TechnicalAnalyst(llm=llm).analyze(s.bundle(s.uptrend()))
        prompt = llm.calls[0]["prompt"]
        self.assertIn("rsi14", prompt)
        self.assertIn("Computed signals", prompt)

    def test_confidence_out_of_range_is_clamped(self) -> None:
        llm = StubLanguageModel(
            responses=[
                {"stance": "buy", "confidence": 4.2, "rationale": "r", "key_factors": []}
            ]
        )
        view = TechnicalAnalyst(llm=llm).analyze(s.bundle(s.uptrend()))
        self.assertLessEqual(view.confidence, 1.0)

    def test_garbage_stance_degrades_to_hold(self) -> None:
        llm = StubLanguageModel(
            responses=[
                {"stance": "moon", "confidence": 0.9, "rationale": "r", "key_factors": []}
            ]
        )
        view = TechnicalAnalyst(llm=llm).analyze(s.bundle(s.uptrend()))
        self.assertIs(view.stance, Stance.HOLD)

    def test_model_failure_falls_back_to_rules(self) -> None:
        llm = StubLanguageModel(responses=[])  # raises on first call
        view = TechnicalAnalyst(llm=llm).analyze(s.bundle(s.uptrend()))
        self.assertIs(view.stance, Stance.BUY)  # the rule-based answer

    def test_strict_mode_surfaces_model_failure(self) -> None:
        llm = StubLanguageModel(responses=[])
        analyst = TechnicalAnalyst(llm=llm, strict=True)
        with self.assertRaises(LanguageModelError):
            analyst.analyze(s.bundle(s.uptrend()))


class TestCommittee(unittest.TestCase):
    def test_default_committee_has_all_four_seats(self) -> None:
        names = {a.name for a in default_committee()}
        self.assertEqual(names, set(ANALYST_REGISTRY))

    def test_subset_selection(self) -> None:
        committee = default_committee(names=("technical", "risk"))
        self.assertEqual([a.name for a in committee], ["technical", "risk"])

    def test_unknown_analyst_is_rejected_loudly(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            default_committee(names=("technical", "astrology"))
        self.assertIn("astrology", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

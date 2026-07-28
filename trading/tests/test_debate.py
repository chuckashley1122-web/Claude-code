"""Tests for the debate moderator.

The moderator's value is entirely in the places where it differs from an
average: the split penalty, the evidence weighting, and the risk veto. Those
three get the most attention here, because a bug in any of them looks like a
plausible number rather than an error.
"""

from __future__ import annotations

import unittest

from trading.alpha_agents.agents.risk_analyst import FLAG_PREFIX
from trading.alpha_agents.debate import DebateModerator
from trading.alpha_agents.llm import LanguageModelError, StubLanguageModel
from trading.alpha_agents.models import AnalystView, Evidence, Stance


def view(
    analyst: str,
    stance: Stance,
    confidence: float,
    *,
    symbol: str = "TEST",
    evidence: tuple[Evidence, ...] = (),
    rationale: str = "because",
) -> AnalystView:
    return AnalystView(
        analyst=analyst,
        symbol=symbol,
        stance=stance,
        confidence=confidence,
        rationale=rationale,
        evidence=evidence,
    )


EV = (Evidence("a", "a"), Evidence("b", "b"), Evidence("c", "c"))


class TestBaselineResolution(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = DebateModerator()

    def test_no_views_is_a_zero_confidence_hold(self) -> None:
        verdict = self.mod.resolve("TEST", [])
        self.assertIs(verdict.stance, Stance.HOLD)
        self.assertEqual(verdict.confidence, 0.0)

    def test_unanimous_buy_is_a_confident_buy(self) -> None:
        verdict = self.mod.resolve(
            "TEST",
            [
                view("technical", Stance.BUY, 0.8, evidence=EV),
                view("fundamental", Stance.BUY, 0.8, evidence=EV),
                view("sentiment", Stance.BUY, 0.6, evidence=EV),
                view("risk", Stance.HOLD, 0.2),
            ],
        )
        self.assertIs(verdict.stance, Stance.BUY)
        self.assertGreater(verdict.confidence, 0.6)
        self.assertEqual(verdict.dissent, ())

    def test_unanimous_sell_is_a_confident_sell(self) -> None:
        verdict = self.mod.resolve(
            "TEST",
            [
                view("technical", Stance.SELL, 0.8, evidence=EV),
                view("fundamental", Stance.SELL, 0.8, evidence=EV),
            ],
        )
        self.assertIs(verdict.stance, Stance.SELL)
        self.assertGreater(verdict.confidence, 0.6)

    def test_all_hold_is_a_hold(self) -> None:
        verdict = self.mod.resolve(
            "TEST",
            [view("technical", Stance.HOLD, 0.2), view("fundamental", Stance.HOLD, 0.3)],
        )
        self.assertIs(verdict.stance, Stance.HOLD)

    def test_split_committee_is_penalised_versus_unanimous(self) -> None:
        """A 2-1 split at the same net score must be held less confidently
        than unanimity. Averaging would report these as identical."""
        unanimous = self.mod.resolve(
            "TEST",
            [
                view("technical", Stance.BUY, 0.6, evidence=EV),
                view("fundamental", Stance.BUY, 0.6, evidence=EV),
            ],
        )
        split = self.mod.resolve(
            "TEST",
            [
                view("technical", Stance.BUY, 0.9, evidence=EV),
                view("fundamental", Stance.SELL, 0.3, evidence=EV),
            ],
        )
        self.assertIs(unanimous.stance, Stance.BUY)
        self.assertIs(split.stance, Stance.BUY)
        self.assertLess(split.confidence, unanimous.confidence)
        self.assertIn("split", split.rationale)

    def test_dissent_is_recorded_not_hidden(self) -> None:
        verdict = self.mod.resolve(
            "TEST",
            [
                view("technical", Stance.BUY, 0.9, evidence=EV),
                view("fundamental", Stance.SELL, 0.4, rationale="valuation is absurd"),
            ],
        )
        self.assertTrue(verdict.dissent)
        self.assertIn("valuation is absurd", " ".join(verdict.dissent))

    def test_evidence_backed_view_outweighs_a_bare_assertion(self) -> None:
        """Evidence should tilt the balance between two opposed analysts.

        Deliberately compared as mirrored scenarios rather than asserting a
        stance: a flat 1-1 disagreement at equal confidence *should* resolve to
        HOLD regardless of who brought evidence, so asserting BUY here would be
        asserting that the moderator trades a genuinely split committee. What
        must hold is that evidence moves the score in its owner's favour.
        """
        bull_backed = [
            view("technical", Stance.BUY, 0.7, evidence=EV),
            view("fundamental", Stance.SELL, 0.7, evidence=()),
        ]
        bear_backed = [
            view("technical", Stance.BUY, 0.7, evidence=()),
            view("fundamental", Stance.SELL, 0.7, evidence=EV),
        ]

        # Both are genuine coin-flips, so both must resolve to HOLD.
        self.assertIs(self.mod.resolve("TEST", bull_backed).stance, Stance.HOLD)
        self.assertIs(self.mod.resolve("TEST", bear_backed).stance, Stance.HOLD)

        # But the underlying score must lean toward whoever brought evidence.
        self.assertGreater(self.mod._tally(bull_backed)["score"], 0)
        self.assertLess(self.mod._tally(bear_backed)["score"], 0)

    def test_evidence_can_carry_a_verdict_when_confidence_is_close(self) -> None:
        """With a modest confidence edge, the evidence-backed side should win
        outright rather than being averaged into indecision."""
        verdict = self.mod.resolve(
            "TEST",
            [
                view("technical", Stance.BUY, 0.9, evidence=EV),
                view("fundamental", Stance.SELL, 0.5, evidence=()),
            ],
        )
        self.assertIs(verdict.stance, Stance.BUY)

    def test_confidence_stays_in_range(self) -> None:
        for conf in (0.0, 0.5, 1.0):
            verdict = self.mod.resolve(
                "TEST",
                [view(f"a{i}", Stance.BUY, conf, evidence=EV) for i in range(4)],
            )
            self.assertGreaterEqual(verdict.confidence, 0.0)
            self.assertLessEqual(verdict.confidence, 1.0)

    def test_risk_flags_propagate_to_the_verdict(self) -> None:
        risk = view(
            "risk",
            Stance.HOLD,
            0.3,
            evidence=(Evidence(f"{FLAG_PREFIX}high_volatility", "vol 90%"),),
        )
        verdict = self.mod.resolve(
            "TEST", [view("technical", Stance.BUY, 0.8, evidence=EV), risk]
        )
        self.assertIn("vol 90%", verdict.risk_flags)

    def test_analyst_views_are_retained_for_audit(self) -> None:
        views = [view("technical", Stance.BUY, 0.8, evidence=EV)]
        verdict = self.mod.resolve("TEST", views)
        self.assertEqual(len(verdict.views), 1)
        self.assertEqual(verdict.views[0].analyst, "technical")


class TestRiskVeto(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = DebateModerator()

    def _with_risk(self, risk_stance: Stance, risk_conf: float):
        return self.mod.resolve(
            "TEST",
            [
                view("technical", Stance.BUY, 0.9, evidence=EV),
                view("fundamental", Stance.BUY, 0.9, evidence=EV),
                view("risk", risk_stance, risk_conf),
            ],
        )

    def test_confident_risk_sell_vetoes_a_buy(self) -> None:
        verdict = self._with_risk(Stance.SELL, 0.7)
        self.assertIs(verdict.stance, Stance.HOLD)
        self.assertIn("veto", verdict.rationale)

    def test_weak_risk_sell_does_not_veto(self) -> None:
        verdict = self._with_risk(Stance.SELL, 0.2)
        self.assertIs(verdict.stance, Stance.BUY)

    def test_risk_concern_trims_confidence_without_vetoing(self) -> None:
        concerned = self._with_risk(Stance.HOLD, 0.5)
        clear = self._with_risk(Stance.HOLD, 0.1)
        self.assertIs(concerned.stance, Stance.BUY)
        self.assertLess(concerned.confidence, clear.confidence)

    def test_veto_does_not_block_a_sell(self) -> None:
        """The veto exists to stop the book taking on risk, not to stop it
        shedding risk."""
        verdict = self.mod.resolve(
            "TEST",
            [
                view("technical", Stance.SELL, 0.9, evidence=EV),
                view("risk", Stance.SELL, 0.9),
            ],
        )
        self.assertIs(verdict.stance, Stance.SELL)


class TestModeratorLLMPath(unittest.TestCase):
    def test_model_verdict_is_used(self) -> None:
        llm = StubLanguageModel(
            responses=[
                {
                    "stance": "sell",
                    "confidence": 0.75,
                    "rationale": "Valuation dominates the trend here.",
                    "dissent": ["technical disagrees"],
                }
            ]
        )
        verdict = DebateModerator(llm=llm).resolve(
            "TEST", [view("technical", Stance.BUY, 0.8, evidence=EV)]
        )
        self.assertIs(verdict.stance, Stance.SELL)
        self.assertEqual(verdict.confidence, 0.75)
        self.assertIn("Valuation", verdict.rationale)

    def test_the_model_cannot_override_the_risk_veto(self) -> None:
        """The veto is a control, not advice. A model proposing BUY into a
        confident risk SELL must still be stopped."""
        llm = StubLanguageModel(
            responses=[
                {
                    "stance": "buy",
                    "confidence": 0.95,
                    "rationale": "I like it anyway.",
                    "dissent": [],
                }
            ]
        )
        verdict = DebateModerator(llm=llm).resolve(
            "TEST",
            [
                view("technical", Stance.BUY, 0.9, evidence=EV),
                view("risk", Stance.SELL, 0.8),
            ],
        )
        self.assertIs(verdict.stance, Stance.HOLD)
        self.assertTrue(any("veto" in d.lower() for d in verdict.dissent))

    def test_analyst_evidence_reaches_the_moderator_prompt(self) -> None:
        llm = StubLanguageModel(
            responses=[
                {"stance": "hold", "confidence": 0.1, "rationale": "r", "dissent": []}
            ]
        )
        DebateModerator(llm=llm).resolve(
            "TEST",
            [view("technical", Stance.BUY, 0.8, evidence=(Evidence("rsi14", "RSI is 79"),))],
        )
        prompt = llm.calls[0]["prompt"]
        self.assertIn("RSI is 79", prompt)
        self.assertIn("Mechanical tally", prompt)

    def test_model_failure_falls_back_to_the_mechanical_verdict(self) -> None:
        llm = StubLanguageModel(responses=[])
        verdict = DebateModerator(llm=llm).resolve(
            "TEST", [view("technical", Stance.BUY, 0.9, evidence=EV)]
        )
        self.assertIs(verdict.stance, Stance.BUY)

    def test_strict_mode_surfaces_model_failure(self) -> None:
        llm = StubLanguageModel(responses=[])
        with self.assertRaises(LanguageModelError):
            DebateModerator(llm=llm, strict=True).resolve(
                "TEST", [view("technical", Stance.BUY, 0.9)]
            )


if __name__ == "__main__":
    unittest.main()

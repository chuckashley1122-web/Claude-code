"""Tests for the command line surface.

The behaviour worth pinning here is the one that bit during development: asking
for `--llm` and silently receiving rule-based output. A user who cannot tell
which engine produced their numbers has been misled, so the failure must be
loud.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import unittest
from datetime import date
from unittest import mock

from trading.alpha_agents import cli
from trading.alpha_agents.llm import AnthropicLanguageModel


def args(**overrides) -> argparse.Namespace:
    base = dict(
        config=None,
        provider="synthetic",
        symbols=["AAA", "BBB"],
        cash=50_000.0,
        llm=False,
        json=False,
        verbose=False,
        date=None,
        dry_run=True,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


class TestLLMFlagGuard(unittest.TestCase):
    def test_llm_flag_fails_loudly_when_the_sdk_is_missing(self) -> None:
        boom = ImportError("The Claude-backed analysts need the Anthropic SDK.")
        with mock.patch.object(AnthropicLanguageModel, "_get_client", side_effect=boom):
            with self.assertRaises(SystemExit) as ctx:
                cli.build_pipeline(args(llm=True))
        self.assertIn("--llm requested but unavailable", str(ctx.exception))

    def test_llm_flag_fails_loudly_when_credentials_are_missing(self) -> None:
        boom = RuntimeError("could not resolve an API key")
        with mock.patch.object(AnthropicLanguageModel, "_get_client", side_effect=boom):
            with self.assertRaises(SystemExit) as ctx:
                cli.build_pipeline(args(llm=True))
        message = str(ctx.exception)
        self.assertIn("ANTHROPIC_API_KEY", message)
        self.assertIn("omit --llm", message.replace("drop --llm", "omit --llm"))

    def test_llm_flag_wires_the_model_into_the_committee_when_available(self) -> None:
        with mock.patch.object(AnthropicLanguageModel, "_get_client", return_value=object()):
            pipeline = cli.build_pipeline(args(llm=True))
        self.assertTrue(
            all(a.llm is not None for a in pipeline.analysts),
            "every analyst should receive the model when --llm is honoured",
        )
        self.assertIsNotNone(pipeline.moderator.llm)

    def test_without_the_flag_the_committee_runs_offline(self) -> None:
        pipeline = cli.build_pipeline(args(llm=False))
        self.assertTrue(all(a.llm is None for a in pipeline.analysts))
        self.assertIsNone(pipeline.moderator.llm)


class TestPipelineConstruction(unittest.TestCase):
    def test_symbol_and_cash_overrides_are_applied(self) -> None:
        pipeline = cli.build_pipeline(args(symbols=["XYZ"], cash=12_345.0))
        self.assertEqual(pipeline.settings.universe, ("XYZ",))
        self.assertEqual(pipeline.broker.portfolio.cash, 12_345.0)

    def test_unknown_provider_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            cli.build_pipeline(args(provider="definitely-not-a-provider"))

    def test_broker_is_never_live(self) -> None:
        pipeline = cli.build_pipeline(args())
        self.assertFalse(pipeline.broker.is_live)
        self.assertFalse(pipeline.settings.allow_live_trading)


class TestArgParsing(unittest.TestCase):
    def test_bad_date_is_rejected_with_a_clear_message(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            cli._parse_date("16-06-2025")
        self.assertIn("YYYY-MM-DD", str(ctx.exception))

    def test_good_date_parses(self) -> None:
        self.assertEqual(cli._parse_date("2025-06-16"), date(2025, 6, 16))

    def test_a_command_is_required(self) -> None:
        with self.assertRaises(SystemExit):
            cli.main([])

    def test_dry_run_scan_runs_end_to_end(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = cli.main(
                ["scan", "--symbols", "AAA", "--date", "2025-06-16", "--dry-run", "--json"]
            )
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual([d["symbol"] for d in payload["decisions"]], ["AAA"])
        self.assertFalse(any(d["executed"] for d in payload["decisions"]))


if __name__ == "__main__":
    unittest.main()

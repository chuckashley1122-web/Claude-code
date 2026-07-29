"""Command line entry point.

    python -m alpha_agents scan
    python -m alpha_agents explain NVDA
    python -m alpha_agents backtest --start 2024-01-01 --end 2024-12-31
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta

from .agents import default_committee
from .backtest import Backtester
from .config import Settings
from .data import get_provider
from .debate import DebateModerator
from .execution import PaperBroker
from .llm import AnthropicLanguageModel
from .models import Stance
from .pipeline import TradingPipeline
from .portfolio import Portfolio

STANCE_MARK = {Stance.BUY: "+", Stance.SELL: "-", Stance.HOLD: "="}


def build_pipeline(args: argparse.Namespace) -> TradingPipeline:
    settings = (
        Settings.from_file(args.config) if getattr(args, "config", None) else Settings.from_env()
    )
    if getattr(args, "symbols", None):
        settings = Settings.from_dict({**settings.to_dict(), "universe": args.symbols})
    if getattr(args, "cash", None):
        settings = Settings.from_dict({**settings.to_dict(), "starting_cash": args.cash})

    provider = get_provider(getattr(args, "provider", None) or settings.data_provider)

    llm = None
    if getattr(args, "llm", False):
        llm = AnthropicLanguageModel(
            model=settings.models.analyst_model,
            effort=settings.models.effort,
            max_tokens=settings.models.max_tokens,
        )
        # Resolve the client now rather than on the first analyst call. The
        # analysts fall back to their rules when a model call fails, which is
        # right for a transient error mid-scan but wrong here: someone who
        # passed --llm and silently received rule-based output has been
        # misled about what produced their numbers.
        try:
            llm._get_client()
        except ImportError as exc:
            raise SystemExit(f"--llm requested but unavailable: {exc}") from exc
        except Exception as exc:  # missing or invalid credentials
            raise SystemExit(
                f"--llm requested but the Anthropic client could not be "
                f"created: {exc}\nSet ANTHROPIC_API_KEY or run `ant auth login`, "
                f"or drop --llm to use the deterministic analysts."
            ) from exc

    portfolio = Portfolio(cash=settings.starting_cash)
    broker = PaperBroker(portfolio=portfolio, costs=settings.costs)

    return TradingPipeline(
        settings=settings,
        provider=provider,
        broker=broker,
        analysts=default_committee(llm),
        moderator=DebateModerator(llm=llm),
        llm=llm,
    )


def cmd_scan(args: argparse.Namespace) -> int:
    pipeline = build_pipeline(args)
    as_of = _parse_date(args.date) if args.date else date.today()

    result = pipeline.scan(as_of, execute=not args.dry_run)

    if args.json:
        print(json.dumps(_scan_to_dict(result), indent=2, default=str))
        return 0

    print(f"\nScan for {as_of}   provider={pipeline.provider.name}   "
          f"broker={pipeline.broker.name}\n")
    if result.halted:
        print(f"  !! TRADING HALTED: {result.halt_reason}\n")

    for decision in result.decisions:
        v = decision.verdict
        print(f"  {STANCE_MARK[v.stance]} {v.symbol:<6} {v.stance.value.upper():<5} "
              f"conf {v.confidence:.2f}")
        print(f"      {v.rationale}")
        if v.risk_flags:
            for flag in v.risk_flags:
                print(f"      risk: {flag}")
        if v.dissent and args.verbose:
            for d in v.dissent:
                print(f"      dissent: {d}")
        if decision.order:
            status = "FILLED" if decision.executed else f"blocked ({decision.rejection})"
            print(f"      order: {decision.order.side.value.upper()} "
                  f"{decision.order.quantity:g} -> {status}")
        print()

    snap = result.snapshot
    if snap:
        print(f"  Equity {snap.equity:,.2f}   cash {snap.cash:,.2f}   "
              f"exposure {snap.exposure:.1%}   positions {len(snap.positions)}")
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    pipeline = build_pipeline(args)
    as_of = _parse_date(args.date) if args.date else date.today()
    symbol = args.symbol.upper()

    bundle = pipeline.build_bundle(symbol, as_of)
    print(f"\n{symbol} as of {as_of} — {len(bundle.prices)} bars, "
          f"{len(bundle.news)} headlines\n")

    views = pipeline._run_analysts(bundle)
    for view in views:
        print(f"  [{view.analyst}] {view.stance.value.upper()} "
              f"(confidence {view.confidence:.2f})")
        print(f"      {view.rationale}")
        for e in view.evidence[:6]:
            print(f"      - {e.label}: {e.detail}")
        print()

    verdict = pipeline.moderator.resolve(symbol, views)
    print(f"  VERDICT: {verdict.stance.value.upper()} at {verdict.confidence:.2f}")
    print(f"  {verdict.rationale}")
    for d in verdict.dissent:
        print(f"  dissent: {d}")
    for f in verdict.risk_flags:
        print(f"  risk flag: {f}")
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    pipeline = build_pipeline(args)
    end = _parse_date(args.end) if args.end else date.today()
    start = _parse_date(args.start) if args.start else end - timedelta(days=365)

    try:
        tester = Backtester(
            pipeline,
            rebalance_every=args.rebalance_every,
            allow_lookahead_fundamentals=args.allow_lookahead_fundamentals,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    result = tester.run(start, end)

    if args.json:
        print(json.dumps(result.stats(), indent=2, default=str))
        return 0

    print()
    print(result.summary())
    if result.halted_days:
        print(f"\n  First halt: {result.halted_days[0][0]} — {result.halted_days[0][1]}")
    return 0


def _scan_to_dict(result) -> dict:
    return {
        "as_of": result.as_of,
        "halted": result.halted,
        "halt_reason": result.halt_reason,
        "decisions": [
            {
                "symbol": d.verdict.symbol,
                "stance": d.verdict.stance.value,
                "confidence": d.verdict.confidence,
                "rationale": d.verdict.rationale,
                "risk_flags": list(d.verdict.risk_flags),
                "dissent": list(d.verdict.dissent),
                "order": (
                    {
                        "side": d.order.side.value,
                        "quantity": d.order.quantity,
                    }
                    if d.order
                    else None
                ),
                "executed": d.executed,
                "rejection": d.rejection,
            }
            for d in result.decisions
        ],
        "equity": result.snapshot.equity if result.snapshot else None,
        "cash": result.snapshot.cash if result.snapshot else None,
    }


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit(f"Invalid date {value!r}; expected YYYY-MM-DD") from exc


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--config", help="path to a JSON settings file")
    p.add_argument("--provider", help="synthetic (default) or yfinance")
    p.add_argument("--symbols", nargs="+", help="override the universe")
    p.add_argument("--cash", type=float, help="starting cash")
    p.add_argument(
        "--llm",
        action="store_true",
        help="use Claude-backed analysts (needs the anthropic SDK and credentials); "
        "without this flag the deterministic analysts run offline",
    )
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("-v", "--verbose", action="store_true")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="alpha_agents",
        description="Multi-agent trading research. Paper trading only — no live "
        "broker adapter ships with this package.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="research the universe and place paper orders")
    _add_common(scan)
    scan.add_argument("--date", help="as-of date (YYYY-MM-DD), defaults to today")
    scan.add_argument("--dry-run", action="store_true", help="research only, place nothing")
    scan.set_defaults(func=cmd_scan)

    explain = sub.add_parser("explain", help="show every analyst's view on one symbol")
    _add_common(explain)
    explain.add_argument("symbol")
    explain.add_argument("--date", help="as-of date (YYYY-MM-DD)")
    explain.set_defaults(func=cmd_explain)

    bt = sub.add_parser("backtest", help="walk-forward backtest over a date range")
    _add_common(bt)
    bt.add_argument("--start", help="YYYY-MM-DD, defaults to one year before end")
    bt.add_argument("--end", help="YYYY-MM-DD, defaults to today")
    bt.add_argument("--rebalance-every", type=int, default=5,
                    help="research every Nth session (default 5)")
    bt.add_argument(
        "--allow-lookahead-fundamentals",
        action="store_true",
        help="run against a provider that cannot serve historical fundamentals. "
        "The result will be inflated by look-ahead and is not evidence of edge",
    )
    bt.set_defaults(func=cmd_backtest)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

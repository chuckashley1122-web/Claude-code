# alpha_agents

A multi-agent trading research engine. A committee of specialist analysts each
forms an independent view on a symbol, a moderator weighs those views against
each other into a single verdict, a risk manager sizes and vets any resulting
order, and a paper broker executes it.

**Paper trading only.** No live broker adapter ships with this package. The
pipeline refuses to run against any broker reporting `is_live` unless
`Settings.allow_live_trading` has been set deliberately — and there is nothing
to set it against.

## Quick start

No dependencies, no API key, no network:

```bash
cd trading
python3 -m alpha_agents scan
python3 -m alpha_agents explain NVDA
python3 -m alpha_agents backtest --start 2024-01-01 --end 2025-06-16
```

The default `synthetic` provider generates deterministic price history, so those
commands produce the same output on any machine.

To use Claude-backed analysts instead of the rule-based ones:

```bash
pip install anthropic          # or: pip install -e '.[llm]'
python3 -m alpha_agents scan --llm
```

For real market data:

```bash
pip install yfinance           # or: pip install -e '.[market-data]'
python3 -m alpha_agents scan --provider yfinance --symbols AAPL MSFT NVDA
```

## How a decision gets made

```
 provider ──► ResearchBundle (prices, fundamentals, news — all ≤ as_of)
                     │
      ┌──────────────┼──────────────┬──────────────┐
      ▼              ▼              ▼              ▼
  technical    fundamental      sentiment         risk
      └──────────────┴──────────────┴──────────────┘
                     ▼
              DebateModerator  ──►  Verdict (stance, confidence, dissent, flags)
                     ▼
              size_position()  ──►  Order
                     ▼
              RiskManager.check()   ◄── independent veto, sees the live book
                     ▼
                 PaperBroker  ──►  Fill
```

Four things about this shape are deliberate.

**The analysts never see the portfolio.** They cannot size a position or bypass
a limit, because they have no idea what is held or how much cash exists. All
they return is an opinion.

**The risk manager gets an independent veto.** It re-checks the proposed order
against the live book after research is complete. Nothing reaches the broker
without passing it — there is a test that instruments both calls and asserts it.

**Arithmetic happens in Python, judgement happens in the model.** Every
indicator, ratio and count is computed deterministically and handed to the LLM
as ground truth. Models are poor arithmetic engines and good judgement engines,
and this split also means every model-generated view records the exact numbers
it saw, so it can be audited afterwards.

**Disagreement is preserved, not averaged away.** A 2-2 split at high individual
confidence is a worse setup than unanimous mild agreement, and the verdict says
so: confidence is cut, and the minority view is recorded in `dissent`.

## The committee

| Analyst | Looks at | Notes |
|---|---|---|
| `technical` | Trend, momentum, mean reversion, realised vol | RSI is used as a fade, not a trigger |
| `fundamental` | Valuation, growth, quality | Scored on three separate axes so cheap-and-deteriorating ≠ expensive-and-compounding |
| `sentiment` | Recent headlines | Confidence hard-capped at 0.65 — lexicon scoring never deserves conviction |
| `risk` | Downside, drawdown, gap risk | Never returns BUY. Its job is to argue against the other three |

The risk seat can veto a buy outright. A model-generated verdict cannot override
that veto — it is a control, not advice.

## Running without an API key

Every analyst has two paths: a deterministic rule-based `decide` and an optional
LLM path. With no model configured the rules run alone, so the engine is fully
functional offline. The LLM upgrades the quality of reasoning and explanation;
it is not load-bearing for the pipeline to work. If a model call fails, the
analyst silently falls back to its rules — pass `strict=True` if you would
rather that be an error than a silent downgrade.

## Risk controls

All defaults live in `RiskLimits` (`config.py`) and are deliberately
conservative:

| Limit | Default | Meaning |
|---|---|---|
| `max_position_pct` | 10% | Cap on any single symbol |
| `max_gross_exposure` | 80% | Leaves a cash buffer |
| `max_new_positions_per_day` | 3 | Caps turnover on a signal burst |
| `max_daily_loss_pct` | 3% | Kill switch trigger |
| `max_drawdown_pct` | 20% | Kill switch trigger |
| `min_confidence` | 0.60 | Below this, a verdict is not traded at all |

The kill switch is **sticky**: once tripped it stays tripped until `reset()` is
called explicitly. A switch that clears itself when equity recovers lets a bad
day become a bad week.

It blocks **buys only**. Exits stay open by design — the switch exists to stop
the book adding risk, and a control that also traps you in the positions that
tripped it turns a limit breach into a much larger loss. Stopping and de-risking
are different actions, and only the first should be automatic.

> Note on sizing: at the default `max_position_pct=0.10` and
> `vol_target_annual=0.15`, the position cap binds for any annual volatility
> below 150%, so volatility targeting is effectively inert under defaults and
> sizing reduces to *10% of equity × confidence*. That is conservative by
> design, but raise `max_position_pct` if you actually want the vol term to do
> work.

## Backtesting

```bash
python3 -m alpha_agents backtest --start 2024-01-01 --end 2025-06-16
```

The engine steps forward one session at a time and hands the pipeline only
`as_of`. Every provider read is sliced through `PriceSeries.up_to(as_of)`, so a
strategy physically cannot read a bar it would not have had. That property is
enforced structurally rather than by convention, and is asserted by tests.

Commission and slippage are charged through the broker's `CostModel`, so
reported results already include them.

**On the synthetic provider, a strongly positive backtest is a bug report.** The
synthetic data is a random walk with no exploitable structure, so the honest
result is a small loss after costs — which is what it currently produces. A
strategy that appears to print money there has almost certainly acquired a
look-ahead leak.

Read results with the same suspicion. Fewer than ~30 trades means the statistics
are noise regardless of the Sharpe ratio.

## Layout

```
alpha_agents/
  models.py        immutable value types crossing every boundary
  interfaces.py    the Protocols: MarketDataProvider, Analyst, Broker, LanguageModel
  config.py        Settings, RiskLimits, CostModel
  indicators.py    SMA/EMA/RSI/MACD/Bollinger/ATR/vol/Sharpe — pure stdlib
  agents/          the four specialists + BaseAnalyst
  debate.py        DebateModerator: views -> Verdict
  risk.py          size_position + RiskManager
  portfolio.py     cash, positions, cost basis, realised P&L
  execution/       PaperBroker
  data/            synthetic (default), yfinance, caching decorator
  pipeline.py      orchestration
  backtest.py      walk-forward engine + statistics
  llm.py           Claude adapter
  cli.py           command line
tests/             231 tests, stdlib unittest
```

## Tests

```bash
cd ..                                              # repo root
python3 -m unittest discover -s trading/tests -t .
```

231 tests, no dependencies. The indicator suite was mutation-tested: twelve
deliberate breakages (Wilder→simple averaging, EMA seed and k-factor, window
off-by-one, population↔sample stddev, dropped annualisation, flipped drawdown
sign) were each confirmed to fail the suite.

## Extending it

Anything pluggable satisfies a Protocol in `interfaces.py`:

- **New data vendor** — implement `MarketDataProvider`, register it in
  `data/__init__.py`. It must be point-in-time honest: given `end`, never return
  data that was not observable by then.
- **New analyst** — subclass `BaseAnalyst`, implement `gather` (numbers) and
  `decide` (rules), add it to `ANALYST_REGISTRY`.
- **New indicator** — add to `indicators.py`. Return a list aligned to the input
  with `None` in undefined leading positions; callers index by position.

## Limitations

Stated plainly, because each one matters for how much weight to put on output:

- **Long only.** No shorting; a SELL is an exit and is a no-op when flat.
- **Daily bars only.** No intraday data, no order book, no market impact model
  beyond a flat slippage assumption.
- **No sector data**, so `max_sector_pct` is defined but not enforced.
- **Exchange holidays are not modelled** — the backtester steps over weekdays.
- **The synthetic provider is not a market.** It is for reproducible plumbing
  tests and demos, not for evaluating whether a strategy has edge.
- **The sentiment lexicon cannot read negation or context.** Use `--llm` if
  sentiment matters to your decision.

## Disclaimer

Research and simulation software. Not investment advice. Nothing here has been
validated for live trading, and the absence of a live adapter is intentional.

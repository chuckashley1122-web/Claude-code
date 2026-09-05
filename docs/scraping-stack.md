# Scraping stack

What is installed, what each piece is for, and what it needs to run.

## Installed

| Tool | Version | Where | What it does |
|---|---|---|---|
| [Scrapling](https://github.com/D4Vinci/Scrapling) | 0.4.15 | `.venv` | Fast fetch + parse. `Fetcher` (HTTP with TLS fingerprint spoofing), `StealthyFetcher` (anti-bot browser), `DynamicFetcher` (Playwright), plus a Scrapy-like Spider API and adaptive selectors that survive site changes. |
| [Scrapegraph-ai](https://github.com/ScrapeGraphAI/Scrapegraph-ai) | 1.76.0 | `.venv` | LLM-driven extraction. `SmartScraperGraph` takes a prompt + URL and returns structured JSON — no selectors to maintain. Works with OpenAI, Gemini, Groq, Bedrock, or local Ollama. |
| [Agent-Reach](https://github.com/Panniantong/Agent-Reach) | main | `~/.agent-reach-venv` | Unified read access across 15 platforms (GitHub, YouTube, RSS, Reddit, X, LinkedIn, ...). Picks, installs and health-checks the best backend per platform rather than implementing readers itself. |

```bash
# Scrapling + Scrapegraph-ai
source .venv/bin/activate
pip install -r leadgen/requirements.txt && scrapling install

# Agent-Reach (kept in its own venv; all state lives in ~/.agent-reach/)
~/.agent-reach-venv/bin/agent-reach doctor
```

## Which one to reach for

- **Known page shape, high volume** → Scrapling. Cheapest and fastest; no LLM.
- **Unknown or varying page shape** → Scrapegraph-ai. Costs tokens per page,
  but you describe what you want in a sentence instead of writing selectors.
- **Reading a specific platform** (a repo, a video, a feed) → Agent-Reach,
  which already knows the right backend for that platform.

The `leadgen/` pipeline uses all three: Scrapling for the signal crawl,
Scrapegraph-ai behind `--llm` for decision-maker extraction, Agent-Reach for
ad-hoc research on a prospect.

## Agent-Reach channel status

Fresh install reports **2/15 channels live** (RSS, and any web page via Jina
Reader). The rest need a one-time dependency or credential:

| Want | Install |
|---|---|
| GitHub | `apt install gh` (or https://cli.github.com) |
| YouTube | `pip install -U "yt-dlp[default]"` |
| Semantic web search (Exa) | `npm i -g mcporter && mcporter config add exa https://mcp.exa.ai/mcp --scope home` |
| Twitter/X, Reddit, Xiaohongshu | `agent-reach install --channels=twitter,reddit` + login cookies |

`agent-reach install --env=auto` is a read-only check. It only changes the
system when you add `--system`, which was **not** run here.

**Do not enable the LinkedIn channel.** It wraps `mcp-server-linkedin`, which
takes your LinkedIn session cookie and drives your logged-in account — a User
Agreement violation that gets accounts banned. See `leadgen/README.md` for the
compliant sources used instead.

## Environment notes

- Scrapling's HTTP fetcher spoofs a browser TLS fingerprint, which a
  TLS-terminating proxy will break (`curl: (35)`). Fine on a normal machine.
- Playwright browsers install to Scrapling's own path unless
  `PLAYWRIGHT_BROWSERS_PATH` is set; point `LEADGEN_CHROMIUM_PATH` at a
  specific binary if the environment ships its own.
- Agent-Reach keeps all config and tokens in `~/.agent-reach/`, never in the
  repo. Nothing it stores should be committed.

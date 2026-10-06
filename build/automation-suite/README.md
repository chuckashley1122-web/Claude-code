# automation-suite (SPEC-01: 8 Best AI Automations)

A dry-run-only implementation of the eight automations described in
`docs/playbooks/01-8-best-ai-automations.md` (a third-party TikTok playbook):
eight importable n8n workflow JSON files, fifteen versioned prompt templates, a
fail-closed config layer with the locked CA-J facts, outbound guardrails, mock
adapters for every external service, synthetic fixtures, a cost/approval
calculator, and human runbooks.

Everything runs offline on Python 3.11 standard library only. Nothing here
calls a paid API, creates an account, sends a message, publishes a post, or
spends money.

## What it does NOT do

- No network calls. `scripts/run_dry.py` blocks socket connects for the whole run.
- No charges or purchases of any kind. `SPEND_CAP_USD = 0.00`; every paid
  service is an approval gate (`docs/COST-AND-APPROVALS.md`).
- No GoHighLevel, Meta Ads Manager, n8n Cloud, or any other logged-in UI. GHL is
  UI-only and its build location id in `config/constants.py` is reference-only.
- No real prospects. Fixtures use example.com addresses and 555-01xx numbers.
- Live adapters exist only to refuse: every `Live*` method raises
  `LiveCallBlocked` explaining the approval needed.

## Absolute rules (encoded as code)

- **No charges.** No spend without explicit human approval.
- **No invented data.** Unknown costs are `NEEDS_EVIDENCE`; mocks return null
  metrics rather than inventing them.
- **Meeting-first.** No price ever appears in outbound or prospect-facing copy.
  `guardrails/pricing_guard.py` blocks it; `guardrails/meeting_first.py` answers
  pricing questions with https://ca-jenterprises.com/ai only. The locked CA-J
  terms in `config/constants.py` are internal only.
- **Source results are not CA-J results.** `guardrails/claim_guard.py` blocks
  restating the source author's claims (built from `docs/SOURCE-CLAIMS.md`),
  consumer-brand mentions in B2B copy, and banned commercial phrasing. The only
  commercial term is "booked appointment".

## Dry-run command sequence

From this folder (`build/automation-suite/`). Use `python` on Windows,
`python3` on Linux/macOS:

```
python3 scripts/validate_workflows.py   # 8 workflows + shared error workflow valid; secret scan 0 findings
python3 scripts/check_guardrails.py     # pricing/meeting-first/claim guard self-test; all 15 prompts clean
python3 scripts/check_env.py            # SET/MISSING per env var, never values (MISSING is expected)
python3 scripts/render_prompts.py       # renders all 15 prompts from fixtures; 0 unresolved
python3 scripts/run_dry.py              # walks all 8 workflow graphs offline; 8 reports in data/out/runs/
python3 scripts/cost_estimate.py        # prints monthly worst case; exits 1 (exceeds SPEND_CAP_USD = 0.00)
python3 -m unittest discover -s tests   # full test suite
```

Fail-closed demonstrations:

```
python3 scripts/check_guardrails.py --inject-price        # exits 1: re-injected price is blocked
python3 scripts/render_prompts.py --withhold company      # exits 1: withheld placeholder
python3 scripts/run_dry.py --workflow 05_content_agent --loop-iterations 2
```

Output goes to `data/out/` (gitignored): `runs/` (one JSON report per
workflow), `mail/` (.eml drafts marked not sent), `video_jobs/` (stub job
records, nothing rendered), `publish/intended.jsonl` (intended posts and
messages, nothing published), `exports/`, `errors/`, `prompts/`.

## How `scripts/run_dry.py` works

It loads each `workflows/0N_*.json` (n8n export shape) and starts at every
trigger node with that workflow's synthetic `pinData`. It then walks
`connections` node by node, dispatching on each node's `type` to a handler:
OpenAI nodes render the prompt file (hard-failing on any unresolved
placeholder) and call `MockOpenAI`; IF nodes split items across true/false
outputs; Calendar, Gmail, HubSpot, Airtable, Slack, Apify, and chat-reply nodes
call the matching mock; HTTP Request nodes are routed by host and path (HeyGen,
Creatomate, ElevenLabs, Sora, Ayrshare, Twilio, YouTube Data API, Hunter) to a
mock; `executeWorkflow` nodes targeting `caj_guardrails` run the pricing,
claim, and meeting-first guards. Expressions (`={{ $json.x }}`, `$vars`,
`$today.plusDays(n)`, simple arithmetic) are evaluated by a small AST-checked
evaluator. Loops (05's "Repeat Automatically", 08's status poll) are cut after
`--loop-iterations`. Any node error runs `_common_error_handler.json`, which
writes a JSON error record to `data/out/errors/` and takes no external action.

## Layout

See spec section 4. `config/` (constants, settings, pricing table),
`guardrails/`, `prompts/`, `workflows/`, `adapters/`, `data/fixtures/`,
`scripts/`, `docs/`, plus `tests/`.

Everything the coding agent cannot do (accounts, imports, OAuth, purchases,
DNS, GoHighLevel, publishing, contacting prospects) is in `docs/`:
`DEPLOY-RUNBOOK.md`, `UI-ONLY-CHECKLIST.md`, `COST-AND-APPROVALS.md` (the spend
item list), and `SOURCE-CLAIMS.md`. Human work orders are in the repo root at
`ui-work-orders/001-*.md`.

## Deviations from spec

1. **Interpreter.** The spec says `python` on Windows; this was built and tested
   with `python3` on Linux. No interpreter name is hardcoded; all paths use
   `pathlib`.
2. **Extra files/dirs.** Added `tests/` (unittest suite required by the build
   rules), package `__init__.py` files, `adapters/base.py` (shared
   `LiveCallBlocked` / interface plumbing), `config/yaml_lite.py` (stdlib-only
   parser for the flat `pricing.yaml` subset, itself tested), and
   `adapters/mock_youtube.py`. The spec's step 10 asks for eight adapter modules
   while its file tree lists seven; YouTube Data API v3 (automation 07) had no
   adapter, so it is the eighth.
3. **Cost figure.** `cost_estimate.py` cannot print a dollar total because no
   vendor rate is verified (all `unit_cost: null`, per spec step 17 and the
   no-invented-pricing rule). It prints "UNBOUNDED (NEEDS_EVIDENCE)" with the
   known subtotal and exits 1, which still satisfies "exceeds SPEND_CAP_USD".
4. **Locked pricing in prospect-facing artifacts.** Spec step 20 says the locked
   CA-J pricing is "the only pricing this suite may reference in any
   prospect-facing artifact". The build rules are stricter: no price ever
   appears in outbound copy. So the locked terms are internal only and the
   pricing guard blocks them in outbound text too.
5. **Pricing guard acceptance string.** Acceptance criterion 3 is tested with
   "250 to 300 per booked appointment" (the corrected spec wording).
6. **Prompt wording.** The mandatory no-price clause avoids the words the
   pricing guard blocks ("price", "fee", "cost") so that `assert_clean` can pass
   on every prompt file (acceptance criterion 4); it reads "Never state,
   estimate, or hint at any amount of money, rate, discount, or charge".
7. **Source wording that would trip the guards.** Workflow names use the short
   automation titles (e.g. "01 AI Voice Call Agent") without the source's claim
   suffixes ("Answers 10 calls at a time, unlimited/day"). The "[finance/health]"
   and "[result]/[pain]" placeholders became `{{niche}}` and `{{service_focus}}`.
8. **Transcript summary.** Source step 1.5 summarizes the call with OpenAI
   before the HubSpot write; the spec's prompt set has no summary prompt, so the
   CRM node stores the caller's words and the agent reply instead.
9. **Mock behaviour that cannot be real offline.** Translation tags text with
   the target language (`[es] ...`) rather than translating; trending topics
   are labelled "unverified, no live research in dry run"; performance metrics
   are null because nothing is published. These are deliberate, documented, and
   tested.
10. **Twilio row in pricing.yaml.** The spec's vendor list includes `twilio`,
    which source line 117 does not mention; the row is kept as specified with
    the spec's source string.
11. **Follow-up timing.** The follow-up cron in 02 is simulated as firing three
    days after outreach via `_simulated_today_offset_days` in its synthetic
    pinData, so the live filter (`next_followup <= today`) is exercised
    unchanged. 07 pins its clock to a fixed date so the 30-day window over the
    synthetic fixture is reproducible.

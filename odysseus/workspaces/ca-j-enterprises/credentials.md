# CA-J Enterprises — credentials and integrations

Names and scopes only. **No secrets in this file, ever** — not a key, not a
fragment, not a "temporary" one. Secrets live in `.env` or the Odysseus vault.

Every credential here is issued to CA-J Enterprises alone. Nothing is shared
with CA-J Consulting or Chuck's Daily Grind.

| Integration | Needed for | Minimum scope | Phase | Status |
|---|---|---|---|---|
| LLM provider API key | All agent work | Inference only. Separate key per business for cost attribution and blast radius. | 1 | ☐ |
| SearXNG | Public web research | Bundled, local, no credential | 1 | ☐ |
| Meta Ad Library | Competitor ad research | Public data — no account credential needed | 1 | ☐ |
| Google Search Console | Own-site performance | **Read-only** on `ca-jenterprises.com` | 2 | ☐ |
| Google Analytics | Campaign reporting | **Read-only**, single property | 2 | ☐ |
| Meta Ads API | Performance reporting | `ads_read` only. **Never** `ads_management`. | 3 | ☐ |
| Google Ads API | Performance reporting | Read-only. **Never** a mutate scope. | 3 | ☐ |
| GHL | Workflow design context | Read-only if used at all. Design happens outside GHL. | 3 | ☐ |
| Email (draft only) | Outreach drafts | Draft/compose scope only. **Never** send. | 3 | ☐ |

## Odysseus-side controls

Two upstream mechanisms enforce parts of this table without relying on anyone
remembering the rules.

**API token scopes** (Settings → API Tokens; `ALLOWED_SCOPES` in
`routes/api_token_routes.py`). Issue tokens per business, and only these:

| Scope | For CA-J Enterprises | Why |
|---|---|---|
| `chat` | yes | Baseline agent use |
| `documents:read`, `documents:write` | yes | Briefs and drafts live as documents |
| `memory:read`, `memory:write` | yes | Workspace memory |
| `email:read`, `email:draft` | phase 3 only | Drafting outreach |
| `email:send` | **never** | Sending is a human action |
| `cookbook:launch`, `todos:write`, `calendar:write` | no | Not needed by this workspace |

Note that upstream auto-adds the matching read scope when you grant a write one
(`email:draft` implies `email:read`) — so ask for the write scope you need and
expect the read scope alongside it.

**User privileges** (Settings → Users → Privileges):

| Privilege | Value | Why |
|---|---|---|
| `can_use_bash` | `false` | Default; no marketing task needs a shell |
| `can_use_research` | `true` | Public competitor and market research |
| `allowed_models` + `allowed_models_restricted` | pin one model | Cost attribution per business |
| `max_messages_per_day` | set a real number | Spend ceiling |

## Rules

1. **Read-only until proven.** No write or management scope is granted during
   the pilot. Reporting does not require mutate access.
2. **One key per business.** Shared keys destroy cost attribution and mean one
   leak compromises all three companies.
3. **Rotate on exposure.** A key that appears in a chat log, a screenshot, a
   commit, or a support ticket is burned. Rotate it, do not reason about whether
   it was really exposed.
4. **Record issuance, not values.** Log which credential was issued, when, by
   whom, and its scope — in this table. Never the value.
5. **Phase gates.** Phase 2 begins only after the phase 1 test suite passes.
   Phase 3 needs an explicit decision from Chuck, per integration.

## Issuance log

| Date | Credential | Scope granted | Issued by | Rotated |
|---|---|---|---|---|
| | | | | |

# CA-J Consulting — credentials and integrations

Names and scopes only. **No secrets in this file, ever.**

This workspace gets the fewest integrations of the three, deliberately. Every
connection is a path for regulated data to leak. The default answer to "can we
connect X" is no, until there is a specific need and a specific control.

| Integration | Needed for | Minimum scope | Phase | Status |
|---|---|---|---|---|
| LLM provider API key | All agent work | Inference only. Dedicated key — never shared with the other two businesses. | 1 | ☐ |
| SearXNG | Public research (SBA, CFPB) | Bundled, local, no credential | 1 | ☐ |
| Website (own) | Content context | Public read of `ca-jconsulting.com` | 1 | ☐ |
| Email intake | Lead intake summaries | **Read-only**, single dedicated inbox, no send scope | 3 | ☐ |
| CRM | Intake routing | **Read-only** if at all. Writes stay manual. | 3 | ☐ |

Never connected, at any phase:

- Loan origination systems
- Credit bureau APIs
- Lender rate feeds or pricing APIs
- Document storage holding borrower files
- Any e-signature platform
- Any send-capable email scope

## Odysseus-side controls

This workspace gets the narrowest scopes in the system, and the narrowing is
enforced by upstream rather than by policy alone.

**API token scopes** (Settings → API Tokens; `ALLOWED_SCOPES` in
`routes/api_token_routes.py`):

| Scope | For CA-J Consulting | Why |
|---|---|---|
| `chat` | yes | Baseline agent use |
| `documents:read`, `documents:write` | yes | Educational drafts |
| `memory:read` | yes | Read-only recall |
| `memory:write` | no | Nothing about a prospect should persist to memory |
| `email:read` | phase 3 only, dedicated zero-PII inbox | Intake summaries |
| `email:draft` | no | A human composes every reply in this workspace |
| `email:send` | **never** | Not under any circumstance |
| everything else | no | No calendar, todos, cookbook, or shell |

**User privileges** (Settings → Users → Privileges):

| Privilege | Value | Why |
|---|---|---|
| `can_use_bash` | `false` | Default; keep it |
| `can_use_browser` | consider `false` | Shrinks the untrusted-input surface in the highest-risk workspace |
| `can_use_research` | `true` | SBA and CFPB public sources |
| `can_manage_memory` | `false` | Reinforces the no-persistence rule above |
| `allowed_models` + `allowed_models_restricted` | pin one model | Reviewed, predictable behaviour on regulated content |
| `max_messages_per_day` | set a real number | Spend ceiling |

## Rules

1. **Dedicated everything.** Its own API key, its own inbox, its own storage.
   Nothing is shared with CA-J Enterprises or Chuck's Daily Grind.
2. **Read-only, permanently.** This workspace has no legitimate need to write
   anywhere. Drafting produces text; humans move it.
3. **No send scope.** Not draft-and-send, not "send with confirmation". Read-only
   email, and a human composes the reply.
4. **Zero-PII inbox.** If the intake inbox will receive borrower documents, it is
   not eligible for connection. Route those to a human-only mailbox instead.
5. **Rotate on exposure**, without deliberating about whether it was "really"
   exposed.
6. **Phase 3 requires an explicit written decision from Chuck**, per integration,
   after the phase 1 test suite has passed and a restore has been tested.

## Pre-connection review

Before any integration in this workspace is enabled:

- [ ] What regulated data could reach this connection? Answer in writing.
- [ ] Is read-only genuinely sufficient? If not, do not connect.
- [ ] Where do logs from this connection go, and who can read them?
- [ ] What is the revocation procedure, and has it been tested?
- [ ] Has compliance signed off in writing?

## Issuance log

| Date | Credential | Scope granted | Issued by | Compliance sign-off | Rotated |
|---|---|---|---|---|---|
| | | | | | |

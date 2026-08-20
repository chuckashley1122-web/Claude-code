# Deploying the workspace layer

Phase two, made executable. The workspace documents describe the three
businesses; this page turns them into artifacts Odysseus actually loads.

Verified against `odysseus-dev/odysseus` branch `main`, commit `cf4e240`.

---

## What isolation actually rests on

The customization plan calls for strict isolation between the three businesses.
That is not a convention here — it is enforced by upstream code:

```python
# services/memory/skills.py
def load(self, owner: Optional[str] = None) -> List[Dict]:
    entries = self.load_all()
    if owner is None:
        return entries
    # SECURITY: strict ownership filter. ...
    return [s for s in entries if s.get("owner") == owner]
```

Two consequences that drive the whole design:

1. **One Odysseus user account per business.** Skills are filtered by the
   `owner` field matching the logged-in username. Three users means three
   disjoint skill sets, enforced at load time rather than by discipline.
2. **An unowned skill is invisible to everyone.** Upstream deliberately hides
   skills with no `owner` — a skill missing that field does not fall back to
   "shared", it silently never loads. `validate_skills.py` treats a missing
   owner as a hard failure for exactly this reason.

The admin account still sees everything. Admin is for operating the install,
not for doing business work — do the work signed in as the business user.

| Business | Username | Skill category | Skills |
|---|---|---|---|
| CA-J Enterprises | `caj-enterprises` | `caj-enterprises` | 5 |
| CA-J Consulting | `caj-consulting` | `caj-consulting` | 5 |
| Chuck's Daily Grind | `caj-grind` | `caj-grind` | 5 |

---

## The ordering trap — read this before deviating

Odysseus reassigns any skill whose owner is not a **current user** to the
primary admin, at startup:

```python
# services/memory/skills.py, called from app.py
if owner and owner in valid_owners:
    continue
sk.owner = primary_owner        # rewritten ON DISK
```

Deploy the skills before the three business users exist and every one of the
fifteen `SKILL.md` files is rewritten to `owner: admin`. The log says
`Assigned 15 legacy skill file(s) to admin` and nothing else complains —
isolation is simply gone, and the files on disk no longer match the repo.

**This was not theoretical.** An earlier version of the deploy script had the
order wrong and did exactly this on a live install. The only safe order is:

> create the users → deploy the skills → restart → configure → verify

`deploy-workspaces.ps1` now runs that as one process so it cannot be got wrong.
If an install has already hit this, `build_skills.py --deploy --reclaim` takes
the skills back; it still refuses to overwrite a skill genuinely owned by a
different CA&J business.

---

## Do it in one command

```powershell
cd <repo>\odysseus\scripts
.\deploy-workspaces.ps1 -WhatIf     # show the whole plan, change nothing
.\deploy-workspaces.ps1
```

That runs, in this order:

1. **Validate** — skills build clean, manifests are sound. Refuses to go further otherwise.
2. **Deploy skills** — copies the 15 `SKILL.md` files to `data/skills/<category>/<name>/`,
   skipping any skill a different owner holds on disk.
3. **Restart** — Odysseus indexes skills at start, then waits for it to answer.
4. **Provision** — creates the three users, sets privileges, loads each system
   prompt and tool allowlist.
5. **Verify** — confirms the prompts loaded, no denied tool was granted, and
   each workspace sees exactly its own five skills and none of another's.

You will be asked once for the Odysseus admin password. It is not stored, not
logged, and not echoed. The three generated user passwords print once at the
end — save them then.

Add `-Model "<model-id>"` to pin the same model across all three workspaces.

### What provisioning actually sets

| | Set to | Why |
|---|---|---|
| `personality` | The workspace's `system-prompt.md` | This is Odysseus's per-user system prompt field |
| `enabled_tools` | A per-business allowlist | See below — this is what makes draft-only real |
| `allow_autonomous_email` | `false` | Belt and braces alongside the allowlist |
| privileges | Per business | `can_use_bash: false` everywhere; browser off for Consulting |

### Draft-only is enforced by the tool list, not the prompt

A prompt can be talked around. A tool that was never granted cannot be called.

31 tools are denied to every workspace, including `send_email`,
`reply_to_email`, `bulk_email`, `bash`, `python`, `write_file`, `manage_tokens`,
and `manage_skills` — the last so the agent cannot rewrite the skills that
constrain it. CA-J Consulting is tightest at 9 tools and is additionally denied
`web_fetch`, because arbitrary page retrieval is the widest untrusted-input
surface and that is the workspace where an injection would do most damage.

The allowlists live in `tools/skills_source.py` next to the owners they belong
to, and `--verify` fails if any denied tool is ever granted.

### Running the pieces separately

```powershell
.\deploy-workspaces.ps1 -SkipProvision      # skills only
python3 ..\tools\provision_workspaces.py --url http://localhost:7000              # plan
python3 ..\tools\provision_workspaces.py --url http://localhost:7000 --apply --then-verify
python3 ..\tools\provision_workspaces.py --url http://localhost:7000 --verify --user-password caj-grind=...
```

Provisioning is idempotent: an existing user is left alone, password unchanged.

### If a user already exists

The tool cannot set the system prompt for a user whose password it does not
know. Pass `--user-password owner=secret`, or set the prompt in the UI. A user
with 2FA enabled must be provisioned through the UI — the tool says so rather
than failing obscurely.

---

## Step 3 — Load the business documents

Provisioning gets the workspaces running. They produce useful output once their
knowledge sources exist.

Each workspace's `templates/` directory holds a skeleton for every business
document its manifest expects. Copy one into `approved/`, fill it in, then set
`approved: true` with your name in the manifest.

`approved/` is gitignored, so completed documents never leave your machine.
`validate_sources.py` fails if a manifest expects a document that has no
template, so there is never a blank page to start from.

**CA-J Consulting needs none of this** — all of its sources are general
reference material already in the repo. It is ready to run as soon as a model is
connected.

## Editing skills

`odysseus/tools/skills_source.py` is the source of truth. The `SKILL.md` files
are generated.

```powershell
# after editing skills_source.py
python3 odysseus\tools\build_skills.py --odysseus-root C:\AI-Workspaces\odysseus
python3 odysseus\tools\validate_skills.py --odysseus-root C:\AI-Workspaces\odysseus
```

Never hand-edit a generated `SKILL.md` — the next build overwrites it.
`build_skills.py --check` verifies the committed files are current without
writing anything, which is what to run in review.

The builder loads Odysseus's own `services/memory/skill_format.py` rather than
reimplementing the format. If upstream changes the format, the next build
changes with it and `--check` fails loudly instead of emitting a stale shape.

---

## Two upstream format constraints

Both were found by round-tripping the generated files through upstream's own
parser. Neither is a bug we introduced, and both silently corrupt content, so
the generator avoids them and the validator enforces the avoidance.

**1. `body_extra` does not survive a save cycle.**

`parse_body` drops the heading line for any `##` heading it does not recognise
(`When to Use`, `Procedure`, `Pitfalls`, `Verification`). Text placed after the
known sections *without* a heading is worse — it gets absorbed into the
preceding section's bullet list. So free-form body content is lost either way.

The standing rules therefore live as entries in `Pitfalls` and `Verification`,
which are ordinary list sections and round-trip exactly. The validator fails any
skill that sets `body_extra` at all.

**2. Non-ASCII in a quoted frontmatter value gains a backslash on every save.**

`_emit_scalar` quotes with `json.dumps`, which escapes non-ASCII to `\uXXXX`.
`_parse_scalar` only strips the surrounding quotes — it never JSON-decodes. So
an em dash in a `description` becomes the literal text `\u2014`, then
`\\u2014`, and so on. Body text is unaffected: it is emitted raw.

Keep frontmatter values plain ASCII. The validator checks each one by running
it through upstream's own `_emit_scalar`/`_parse_scalar` pair rather than
guessing which characters trigger quoting.

---

## Verify

```powershell
python3 odysseus\tools\validate_skills.py --odysseus-root C:\AI-Workspaces\odysseus
python3 odysseus\tools\validate_sources.py
```

`validate_sources.py` checks the knowledge manifests: that every source carries
its required fields and a unique id, that every drafted file resolves on disk and
still carries its "Verify before approval" section, that nothing is approved
without a named approver, that no PII-bearing source is ever approved, that a
workspace declaring `pii_policy: prohibited` has none at all, and that no
reference file is orphaned from the manifest. `deploy-workspaces.ps1` runs it and
refuses to deploy on failure.

`validate_skills.py` checks the skills:

- parses with upstream's `Skill.from_markdown`, and re-serializes byte-identically
- frontmatter `name` matches its directory, and is a stable slug
- owned, with owner and category matching its business
- `When to Use`, `Procedure`, `Pitfalls`, `Verification` all non-empty
- the standing injection-handling pitfall and draft-only verification present
- `source: user`, so the agent's own skill-eviction never removes them
- within the REST API's length limits, so the file is API-acceptable too
- no orphans: every file has a definition, every definition has a file

Then the human checks that remain, which no script can do: sign in as each
business user, confirm the skill list is exactly its own five, and run that
workspace's six tests from `workspaces/<business>/tests.md`.

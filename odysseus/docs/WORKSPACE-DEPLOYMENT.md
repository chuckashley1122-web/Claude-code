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

## Step 1 — Create the three business users

As admin, in **Settings → Users**, or via the API (`POST /api/auth/users`,
admin-only). Three non-admin accounts, matching the usernames above exactly —
the username **is** the isolation key, so a typo silently hides that business's
skills.

Then set each user's privileges (**Settings → Users → Privileges**, or
`PUT /api/auth/users/{username}/privileges`). The defaults are close to right;
these are the ones worth setting deliberately:

| Privilege | Set to | Why |
|---|---|---|
| `can_use_bash` | `false` | Already the default. No workspace needs shell access; leave it off. |
| `allowed_models` + `allowed_models_restricted` | pin per business | Pins each business to one model. Cost attribution, and no accidental use of an expensive model. |
| `max_messages_per_day` | a real number | A spend ceiling per business. `0` means unlimited. |
| `can_use_research` | `true` | Enterprises and Grind need public research. Consulting needs SBA/CFPB. |
| `can_use_browser` | consider `false` for Consulting | Reduces the untrusted-input surface in the highest-risk workspace. |

Give each account its own password. Do not reuse the admin password.

---

## Step 2 — Deploy the skills

```powershell
.\odysseus\scripts\deploy-workspaces.ps1 -WhatIf     # show what would be written
.\odysseus\scripts\deploy-workspaces.ps1
```

That wraps `odysseus/tools/build_skills.py --deploy`, which copies each
`SKILL.md` to the path `SkillsManager` reads:

```
<odysseus>/data/skills/<category>/<name>/SKILL.md
```

It refuses to overwrite a skill whose on-disk `owner` differs from the one it
is about to write, so a hand-edited or differently-owned skill is never
silently replaced — it prints SKIP and moves on.

Restart so Odysseus re-indexes:

```powershell
docker compose restart odysseus
```

Then sign in as each business user and confirm **Skills** shows five, and only
its own five.

---

## Step 3 — Load the system prompts

The system prompts in `workspaces/*/system-prompt.md` are not auto-deployed.
Paste each into the workspace/assistant settings for that business user. They
are versioned in this repo, so when one changes, bump its version, update the
changelog at the bottom, and re-paste.

Skills carry their own standing rules, so a skill still behaves correctly if the
system prompt is missing — but the prompt is what sets voice, audience, and the
prohibitions that apply outside any particular skill. Do not skip it.

---

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
```

Checks every committed skill for:

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

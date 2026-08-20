# Odysseus build guide — verified sequence

Source: `OdysseusClaudeCodeBuildGuide_8.18.26.docx`.
Verified against `odysseus-dev/odysseus` branch `main`, commit
`cf4e240ad1622da6a904f496b19d656a2b9c6393`.

The upstream project is actively maintained. **Re-read `README.md` and
`docs/setup.md` in the cloned repo before you run anything here.** If they
disagree with this document, upstream wins and this document gets corrected.

---

## 0. STOP — `main` does not currently start

**Verified by running it, 2026-08-20, at commit `cf4e240`.**

`src/agent_loop.py` line 15 imports `AsyncGenerator, List, Dict, Optional, Set`
from `typing` but **not `Any`**, and line 1503 annotates a parameter as
`dict[str, Any]`. The file has no `from __future__ import annotations`, so the
annotation is evaluated at import time and raises:

```
NameError: name 'Any' is not defined
```

`app.py` imports `chat_routes`, which imports `agent_loop`, so **the application
cannot start at all** — Docker or native. It fails identically either way,
because this is a Python import error, not an environment problem.

`dev` does not have this bug: its line 15 reads
`from typing import Any, AsyncGenerator, List, Dict, Optional, Set`.

**Pick one before installing:**

| Option | What to do | Trade-off |
|---|---|---|
| Check first | `git show main:src/agent_loop.py \| sed -n 15p` — if it lists `Any`, it is fixed upstream and `main` is fine again | Zero cost. Do this every time. |
| Use `dev` | `git clone --branch dev …` | Has the fix, but `dev` is the fast-moving branch the original guide warned about |
| Patch `main` | Add `Any` to that import line | One line, but it is a local edit to upstream code — record it in `BUILD-RECORD.md` and expect to drop it when upstream catches up |

The patch was confirmed sufficient: with `Any` added and nothing else changed,
the app imports, boots, serves, and enforces authentication.

This is exactly the class of problem no amount of reading finds. The original
guide's advice to prefer `main` for stability was reasonable and, at this
commit, wrong.

---

## 1. Corrections to the original guide

Nine things in the guide differ from the current repository. All of them change
what you actually type.

| # | Guide says | Repository actually does | Why it matters |
|---|---|---|---|
| 1 | Set `AUTH_ENABLED=true`, `LOCALHOST_BYPASS=false`, `APP_BIND=127.0.0.1`, `APP_PORT=7000` in `.env` | All four ship **commented out** in `.env.example`. `docker-compose.yml` already defaults to exactly those safe values | The defaults are safe either way, but leaving them commented means a future upstream default change silently moves your security posture. `install.ps1` uncomments them so the setting is explicit and auditable. |
| 2 | "verify ports 7000/7001" | Compose publishes **four** host ports: `7000` odysseus, `8080` searxng, `8100` chromadb, `8091` ntfy | A preflight that only checks 7000 will still hit a collision on one of the other three. `preflight.ps1` checks all four. |
| 3 | Doesn't mention backups tooling | Upstream ships `scripts/odysseus-backup` (`snapshot` / `list` / `verify` / `restore`), stdlib-only Python, safe to run while the app is live | No need to hand-roll `docker cp` backups. `backup.ps1` / `restore.ps1` wrap it. |
| 4 | Doesn't mention where state lives | Everything is in the `data/` bind mount — `app.db`, the Fernet key `data/.app_key`, vault, memory, RAG index, uploads. SearXNG/Chroma/ntfy use named Docker volumes | Back up `data/`. A snapshot **contains your secrets** — treat the tarball like a password. |
| 5 | Configure models via `.env` | `docs/setup.md`: "Only edit `.env` for deployment-level overrides." Model, search, and email providers are configured in the **Settings** UI | Step 8 is a UI task, not an `.env` edit. |
| 6 | Doesn't mention `SECURE_COOKIES` | Defaults to `false` in compose | Correct for `http://localhost`. Set `true` only once you are behind HTTPS, or login breaks. |
| 7 | Admin login is "generated" | `setup.py` creates user `admin` (override with `ODYSSEUS_ADMIN_USER`) and prints a temporary password to the container log | Confirms `docker compose logs odysseus` is the right place to look. |
| 8 | `mkdir C:\AI-Workspacescd C:\AI-Workspaces` | Two commands run together by a formatting artifact in the docx | Split them. Same for the Step 6 and Section 8 code blocks. |
| 9 | Doesn't mention `PUID`/`PGID` | Container drops to uid/gid 1000 and chowns `/app/data` + `/app/logs` | Irrelevant on Docker Desktop for Windows. Note it if you ever move to a Linux host. |

One thing the guide got exactly right and is worth repeating: **do not ask Claude
Code to recreate Odysseus.** Clone upstream, keep it pristine, put every
business-specific change in `.env`, Settings, prompts, and the
`odysseus/workspaces/` layer in this repo.

---

## 2. Prerequisites

- Windows 11, administrator access, virtualization enabled in BIOS.
- Docker Desktop running on the **WSL2** backend.
- Git for Windows.
- ~20 GB free disk. Local models need far more — a 7B Q4 model is ~5 GB, and
  the HuggingFace cache under `data/huggingface` grows fast.
- A working folder outside any synced/cloud directory: `C:\AI-Workspaces`.
  OneDrive sync on a live SQLite database causes corruption.

Cost note: Odysseus itself is free. Cloud model APIs, search APIs, and email
providers bill separately.

Run `scripts\preflight.ps1` to check all of this. It reads only — it installs
nothing and changes nothing.

---

## 3. Step 1 — Clean project folder

```powershell
mkdir C:\AI-Workspaces
cd C:\AI-Workspaces
```

Open Claude Code from this folder. Tell it up front: the official repository is
the source of truth, and it must stop rather than proceed when a step needs
credentials, a paid service, public exposure, or a destructive change.

---

## 4. Steps 4–6 — Clone, pin, configure, start

This is what `scripts\install.ps1` automates. Doing it by hand:

```powershell
git clone --branch main https://github.com/odysseus-dev/odysseus.git
cd odysseus
git rev-parse HEAD          # record this in BUILD-RECORD.md

Copy-Item .env.example .env
# uncomment and confirm, in .env:
#   AUTH_ENABLED=true
#   LOCALHOST_BYPASS=false
#   APP_BIND=127.0.0.1
#   APP_PORT=7000

docker compose config       # must succeed before anything is built
docker compose up -d --build
docker compose ps
docker compose logs --tail=120 odysseus
```

`main` is the curated branch; `dev` is the default upstream branch and carries
the newest, least stable changes. Start on `main`.

First build pulls base images and installs Python dependencies — 5–15 minutes on
a normal connection. Odysseus waits on SearXNG's healthcheck before it starts, so
a few seconds of `starting` on the odysseus container is expected.

If port 7000 is taken, set `APP_PORT=7001` in `.env`, run `docker compose up -d`
again, and use `http://localhost:7001`. Record the change in `BUILD-RECORD.md`.

---

## 5. Step 7 — First login

1. `docker compose logs odysseus | Select-String "Temporary password"`
2. Log in at `http://localhost:7000` as `admin`.
3. Change the password immediately in **Settings**.
4. Never paste that password into a Claude Code prompt, a doc, a screenshot, or
   a commit. If it leaks anywhere, change it again.

Alternative: set `ODYSSEUS_ADMIN_PASSWORD` in `.env` **before first boot** to
choose your own. `.env` is gitignored upstream, but it is still a plaintext file
on disk — the generated-then-changed path is cleaner.

---

## 6. Step 8 — Connect exactly one model

Do this in **Settings**, not `.env`. One provider, one test agent. Adding five
providers at once means you cannot tell which one broke.

- **Cloud first** (OpenAI/Anthropic/other OpenAI-compatible): reliable, no
  hardware questions, costs per token. Best for proving the workspace works.
- **Ollama later**, once the workspace passes its tests:
  - Start Ollama with `OLLAMA_HOST=0.0.0.0:11434` so the container can reach it.
  - Set `OLLAMA_BASE_URL=http://host.docker.internal:11434/v1` in `.env`.
  - Native (non-Docker) install uses `http://localhost:11434/v1` instead.

Then test, in this order:

1. A normal chat, and confirm the conversation is saved.
2. Document creation and retrieval.
3. Agent mode on a harmless public research task.
4. Confirm no tool sends an external message, email, or post without an explicit
   approval step.

---

## 7. Step 9 — Business workspaces, in phases

Do not build all three at once. Order matters, by risk:

1. **CA-J Enterprises** first — public marketing research, draft-only output,
   nothing confidential. This is the pilot.
2. **Chuck's Daily Grind** second — copy the proven pattern, low risk.
3. **CA-J Consulting** last — lending and mortgage workflows carry real privacy
   and compliance exposure and should only run on a stack you already trust.

The prompts, agent templates, knowledge manifests, test suites, and audit
checklists for all three are in `odysseus/workspaces/`. The plan behind them is
in [`CAJ-CUSTOMIZATION-PLAN.md`](CAJ-CUSTOMIZATION-PLAN.md).

---

## 8. Acceptance tests

`scripts\verify.ps1` runs these and prints pass/fail per line:

- [ ] `docker compose config` succeeds.
- [ ] `odysseus`, `searxng`, `chromadb`, `ntfy` are up; searxng is healthy.
- [ ] The UI responds on the configured port.
- [ ] An unauthenticated request to a protected API path is rejected (401/403/redirect).
- [ ] Every published port is bound to `127.0.0.1`, not `0.0.0.0`.
- [ ] `docker compose restart` preserves data (`data/app.db` survives).
- [ ] Git tracks no `.env`, key, or credential.
- [ ] `BUILD-RECORD.md`, `CAJ-OPERATIONS.md`, `CAJ-CUSTOMIZATION-PLAN.md` exist.
- [ ] A backup has been taken **and** a restore has been tested, before live use.

### Verified against a live install

These were confirmed by actually running Odysseus (native install, same
codebase as the container) rather than by inspection:

- `docker compose config` validates with the generated `.env` — exit 0
- All four published ports resolve loopback-bound; zero `0.0.0.0`
- The app boots and serves once the `Any` import is fixed
- `GET /` returns 302; `/api/settings`, `/api/auth/users`, `/api/skills` and
  `/api/assistant/settings` all return **401 unauthenticated**
- Skills deploy, load, and are owner-isolated — a user requesting another
  workspace's skill by name gets **404**

The last one is manual and it is the one people skip. An untested backup is not
a backup.

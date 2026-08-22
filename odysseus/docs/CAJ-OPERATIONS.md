# CA&J Odysseus — operations runbook

Everything here runs from the Odysseus repo root (`C:\AI-Workspaces\odysseus`),
not from this kit. The PowerShell wrappers in `odysseus/scripts/` do the `cd`
for you.

## Daily

```powershell
docker compose up -d                        # start
docker compose ps                           # status
docker compose logs --tail=120 odysseus     # recent app logs
docker compose down                         # stop, keeping all data
```

**Never** run `docker compose down -v` as a troubleshooting step. `-v` deletes
the named volumes — SearXNG settings, the Chroma vector store, ntfy cache. It is
a deliberate wipe, not a restart.

## Reading logs

```powershell
docker compose logs --tail=200 odysseus     # app
docker compose logs --tail=50 searxng       # search
docker compose logs --tail=50 chromadb      # vector store
docker compose logs -f odysseus             # follow live; Ctrl-C to stop
```

Fix the **first** clear error in the log. Rebuilding repeatedly without reading
the error wastes 10 minutes per cycle and changes nothing.

## Backup

State lives in `data/` — SQLite database, the Fernet key `data/.app_key`, vault,
memory, RAG indexes, personal documents, uploads.

```powershell
.\odysseus\scripts\backup.ps1                    # snapshot to backups\
.\odysseus\scripts\backup.ps1 -List              # list snapshots, newest first
.\odysseus\scripts\backup.ps1 -Verify <path>     # integrity-check without extracting
```

Safe while the app is running — SQLite is copied through its own `.backup` API.

> A snapshot contains your secrets. It includes the encryption key, sessions,
> and any stored provider tokens. Store it privately, never in Git, and prefer an
> encrypted destination for offsite copies.

`deep_research/` and `mail-attachments/` are excluded by default because they
are large and re-derivable. Add `-IncludeResearch` / `-IncludeAttachments` for a
full snapshot.

**Cadence:** before every update, before every config change you might regret,
and weekly once real business data is in the system.

## Restore

```powershell
.\odysseus\scripts\restore.ps1 -Path backups\odysseus-backup-20260819-120000.tar.gz
```

Destructive — it replaces `data/`. Stop the stack first (`docker compose down`),
restore, then start again. Verify the tarball before you rely on it.

**Test this once, on purpose, before the system holds anything you care about.**

### It has been tested

The full cycle was run against a live install: snapshot → verify → delete the
users and all fifteen skills → restore → confirm. Everything came back — the
three accounts, the fifteen skills with their correct owners, each system
prompt, each tool allowlist, and per-user isolation.

Two things worth knowing:

- **Upstream stashes rather than deletes.** The restore moved the existing
  `data/` to `data.before-restore-<timestamp>/` instead of overwriting it. So a
  restore from the wrong snapshot is recoverable — but that stash is not a
  backup, and it accumulates. Clean up old ones deliberately.
- **`restore.ps1` refuses to run under a live app.** `docker compose down`
  reports success when there is nothing to stop, which is exactly what happens
  on a native install where the app is a uvicorn process. Restoring `data/`
  underneath a running app corrupts the database, so the script now probes the
  app port after stopping the stack and stops if anything still answers.

## Update

```powershell
.\odysseus\scripts\update.ps1                # backup → fetch → show incoming → stop
.\odysseus\scripts\update.ps1 -Apply         # ...then pull --ff-only and rebuild
```

Manual equivalent:

```powershell
git fetch --all --prune
git status
git log --oneline HEAD..origin/main
git pull --ff-only origin main
docker compose up -d --build
```

Read `git log` output before pulling. `--ff-only` refuses to merge, which is what
you want: if it fails, you have local changes and need to decide about them
rather than have Git guess.

## Rollback

The commit you are on is recorded in `BUILD-RECORD.md`. To go back:

```powershell
docker compose down
git checkout <previous-commit-hash-from-BUILD-RECORD.md>
docker compose up -d --build
```

If the bad version migrated the database, code rollback alone is not enough —
restore the pre-update snapshot too. That is why `update.ps1` snapshots first.

## Troubleshooting

| Symptom | What to do |
|---|---|
| Port 7000 in use | `APP_PORT=7001` in `.env`, `docker compose up -d`, use `localhost:7001`. Note it in `BUILD-RECORD.md`. |
| Any container restarting | `docker compose logs --tail=200 <service>`. Fix the first error. Do not loop on rebuilds. |
| `odysseus` stuck "starting" | It waits on the SearXNG healthcheck. Check `docker compose logs searxng`; a broken upstream SearXNG tag blocks the whole app. |
| UI loads, models missing | Model config is in **Settings**, not `.env`. For Ollama, confirm `OLLAMA_HOST=0.0.0.0:11434` on the host and `OLLAMA_BASE_URL=http://host.docker.internal:11434/v1` in `.env`. |
| Local model very slow | Use a smaller quantized model or a cloud endpoint. Odysseus is lightweight; inference is the heavy part. |
| Login loops / cookie rejected | `SECURE_COOKIES=true` over plain HTTP will do this. Keep it `false` until you are behind HTTPS. |
| Windows native install fights you | Use Docker. Native works, but Docker is reproducible and rolls back cleanly. |
| Need phone access | Do not open router ports. Keep auth on, finish the local pilot, then use Tailscale or a properly secured HTTPS reverse proxy. |
| Disk filling up | `data/huggingface` (model cache) and `data/deep_research` grow fastest. Check with `docker system df` and prune *images* only — never volumes without deciding first. |

## Escalate — stop and ask, do not improvise

- Anything requiring a purchase, a new account, or live business credentials.
- Any firewall, router, or public-exposure change.
- Any deletion of volumes, `data/`, or backups.
- Any upstream change that conflicts with local edits.
- Any point where a fix would mean modifying upstream application code.

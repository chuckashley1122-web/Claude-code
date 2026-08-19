# Odysseus build record

Copy to the Odysseus repo root as `BUILD-RECORD.md` and fill in. No secrets in
this file — no passwords, no API keys, not even partial ones.

## Install

| Field | Value |
|---|---|
| Date | |
| Host | Windows 11 / Docker Desktop / WSL2 |
| Install path | `C:\AI-Workspaces\odysseus` |
| Upstream | `https://github.com/odysseus-dev/odysseus` |
| Branch | `main` |
| Commit (`git rev-parse HEAD`) | |
| Docker Desktop version | |
| Docker Compose version | |

## Configuration

| Setting | Value | Notes |
|---|---|---|
| `APP_PORT` | 7000 | 7001 if 7000 was taken — say which and why |
| `APP_BIND` | 127.0.0.1 | loopback only for the pilot |
| `AUTH_ENABLED` | true | |
| `LOCALHOST_BYPASS` | false | |
| `SECURE_COOKIES` | false | true only behind HTTPS |
| Local URL | `http://localhost:7000` | |
| Model provider | | name only, never the key |
| Admin username | admin | |
| Temp password changed | ☐ yes | date: |

## Acceptance tests

| Test | Result | Notes |
|---|---|---|
| `docker compose config` succeeds | | |
| All four containers up, searxng healthy | | |
| UI responds on configured port | | |
| Unauthenticated request rejected | | |
| All published ports loopback-bound | | |
| Data survives restart | | |
| No secrets tracked by Git | | |
| Ops + customization docs present | | |
| Backup taken | | file: |
| Restore tested | | date: |

## Rollback point

```powershell
docker compose down
git checkout <commit above>
docker compose up -d --build
```

If the version being rolled back from ran a database migration, restore the
matching snapshot as well.

## Update history

| Date | From commit | To commit | Backup file | Result |
|---|---|---|---|---|
| | | | | |

## Open risks / decisions pending

1.
2.
3.

#!/usr/bin/env python3
"""Provision the three CA&J business workspaces on a running Odysseus install.

Replaces the three manual, error-prone setup steps with one command:

  1. create the three business user accounts
  2. set each user's privileges
  3. log in as each and load its system prompt, model, and tool allowlist

Step 3 is the one that matters most. `CrewMember.personality` is Odysseus's
per-user system prompt field, and `enabled_tools` is its per-user tool
allowlist — so the draft-only rule stops being a sentence in a prompt and
becomes a tool the agent does not have. A prompt can be talked around; a
missing tool cannot be called.

Skills are deployed separately by build_skills.py --deploy, because they are
files on disk rather than API state.

Usage
-----
    # show exactly what would happen, change nothing
    python3 provision_workspaces.py --url http://localhost:7000

    # do it
    python3 provision_workspaces.py --url http://localhost:7000 --apply

    # check an existing install, including that isolation actually holds
    python3 provision_workspaces.py --url http://localhost:7000 --verify

The admin password is read interactively and never written to disk, logged, or
echoed. Generated user passwords are printed once, at the end, and nowhere else
— put them in a password manager before you close the terminal.
"""

from __future__ import annotations

import argparse
import getpass
import http.cookiejar
import json
import os
import secrets
import string
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skills_source  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKSPACES = os.path.join(REPO_ROOT, "odysseus", "workspaces")

PASSWORD_LEN = 24


class Client:
    """Minimal cookie-session HTTP client. Stdlib only — no dependencies."""

    def __init__(self, base_url: str):
        self.base = base_url.rstrip("/")
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )

    def request(self, method: str, path: str, body=None):
        url = self.base + path
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        if data:
            req.add_header("Content-Type", "application/json")
        try:
            with self.opener.open(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8", "replace")
                return resp.status, (json.loads(raw) if raw.strip() else {})
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(raw) if raw.strip() else {}
            except json.JSONDecodeError:
                parsed = {"detail": raw[:400]}
            return exc.code, parsed
        except urllib.error.URLError as exc:
            raise SystemExit(
                f"error: cannot reach {self.base} — {exc.reason}\n"
                "       Is the stack up?  docker compose ps"
            )

    def login(self, username: str, password: str) -> None:
        status, body = self.request("POST", "/api/auth/login", {
            "username": username, "password": password,
        })
        if status != 200 or not body.get("ok"):
            if body.get("requires_totp"):
                raise SystemExit(
                    f"error: {username} has 2FA enabled. This tool cannot complete a 2FA "
                    "login — provision that user through the UI instead."
                )
            raise SystemExit(f"error: login failed for {username} ({status})")


def generate_password() -> str:
    # Ambiguous characters removed: these get read off a screen and retyped.
    alphabet = (
        "".join(c for c in string.ascii_letters if c not in "lIO")
        + "".join(c for c in string.digits if c not in "01")
        + "!@#$%^&*-_=+"
    )
    return "".join(secrets.choice(alphabet) for _ in range(PASSWORD_LEN))


def read_system_prompt(business: str) -> str:
    path = os.path.join(WORKSPACES, business, "system-prompt.md")
    if not os.path.isfile(path):
        raise SystemExit(f"error: missing system prompt at {path}")
    return open(path, encoding="utf-8").read().strip()


def prompt_title(business: str) -> str:
    """First heading line of a workspace's system prompt.

    Used as the identity check in --verify. A substring search for the business
    label is not sufficient: every prompt names the other two businesses in its
    isolation rules, so the wrong prompt on a user still contains the right
    label. The title line is unique per workspace.
    """
    for line in read_system_prompt(business).splitlines():
        if line.strip():
            return line.strip()
    return ""


def expected_skill_names(business: str) -> set:
    return {s["name"] for s in skills_source.SKILLS if s["business"] == business}


# --------------------------------------------------------------------- plan --

def show_plan(args) -> int:
    print("Plan — nothing will be changed.\n")
    print(f"  Target: {args.url}")
    print(f"  Model:  {args.model or '(left as-is; set it in Settings)'}\n")

    for business, meta in skills_source.BUSINESSES.items():
        prompt = read_system_prompt(business)
        skills = sorted(expected_skill_names(business))
        print(f"  {meta['label']}  →  user '{meta['owner']}'")
        print(f"    create user, non-admin, generated {PASSWORD_LEN}-char password")
        print(f"    privileges  : {json.dumps(meta['privileges'])}")
        print(f"    system prompt: {len(prompt)} chars from workspaces/{business}/system-prompt.md")
        print(f"    tools granted: {len(meta['tools'])}  ({', '.join(sorted(meta['tools'])[:5])}, ...)")
        print(f"    autonomous email: disabled")
        print(f"    skills expected after deploy: {len(skills)}")
        print()

    print(f"  Denied to every workspace ({len(skills_source.DENIED_TOOLS)} tools), including:")
    for name in ("send_email", "reply_to_email", "bulk_email", "bash", "manage_tokens"):
        print(f"    - {name}")
    print("\n  Re-run with --apply to execute.")
    return 0


# -------------------------------------------------------------------- apply --

def apply(args) -> int:
    admin_user = args.admin_user
    admin_password = os.environ.get("ODYSSEUS_ADMIN_PASSWORD") or getpass.getpass(
        f"Password for admin user '{admin_user}' (not echoed, not stored): "
    )
    if not admin_password:
        raise SystemExit("error: no admin password supplied")

    admin = Client(args.url)
    admin.login(admin_user, admin_password)
    print(f"  [ok] authenticated as {admin_user}")

    status, body = admin.request("GET", "/api/auth/users")
    if status != 200:
        raise SystemExit(f"error: could not list users ({status}) — is '{admin_user}' an admin?")
    existing = {
        (u.get("username") if isinstance(u, dict) else str(u))
        for u in (body.get("users") or [])
    }

    credentials: list[tuple[str, str]] = []
    problems: list[str] = []
    pending: list[tuple] = []

    for business, meta in skills_source.BUSINESSES.items():
        owner = meta["owner"]
        print(f"\n  {meta['label']}  ({owner})")

        # --- account -------------------------------------------------------
        if owner in existing:
            print("    [skip] user already exists — password unchanged")
            password = None
        else:
            password = generate_password()
            status, body = admin.request("POST", "/api/auth/users", {
                "username": owner, "password": password, "is_admin": False,
            })
            if status == 409:
                print("    [skip] user already exists — password unchanged")
                password = None
            elif status != 200:
                problems.append(f"{owner}: create failed ({status}) {body.get('detail','')}")
                print(f"    [FAIL] create failed ({status}) {body.get('detail','')}")
                continue
            else:
                credentials.append((owner, password))
                print("    [ok] user created")

        # --- privileges ----------------------------------------------------
        status, _ = admin.request(
            "PUT", f"/api/auth/users/{owner}/privileges", meta["privileges"]
        )
        if status == 200:
            print("    [ok] privileges set")
        else:
            problems.append(f"{owner}: privileges failed ({status})")
            print(f"    [warn] privileges failed ({status}) — set them in Settings")

        pending.append((business, meta, owner, password))

    # --- deploy skills between the two phases ------------------------------
    # Ordering is not cosmetic. Odysseus reassigns any skill whose owner is not
    # a current user to the primary admin at startup (backfill_owner, called
    # from app.py). Deploy skills before the business users exist and all of
    # them come back owned by admin, silently, and isolation is gone. So: create
    # the users, THEN deploy, THEN restart — by which point the owners resolve.
    if args.orchestrate:
        print("\n  Deploying skills and restarting (users now exist, so owners survive)")
        here = os.path.dirname(os.path.abspath(__file__))
        build = subprocess.run(
            [sys.executable, os.path.join(here, "build_skills.py"),
             "--odysseus-root", args.odysseus_root, "--deploy", "--reclaim"],
            capture_output=True, text=True,
        )
        if build.returncode != 0:
            print(build.stdout + build.stderr)
            problems.append("skill deploy failed")
        else:
            print(f"    [ok] skills deployed to {args.odysseus_root}/data/skills")

        if args.restart_cmd:
            restart = subprocess.run(args.restart_cmd, shell=True, cwd=args.odysseus_root,
                                     capture_output=True, text=True)
            if restart.returncode != 0:
                print(f"    [warn] restart command failed: {restart.stderr.strip()[:200]}")
            else:
                print("    [ok] restart issued")
            if not wait_for(args.url):
                problems.append("Odysseus did not come back after restart")
            else:
                print("    [ok] Odysseus responding again")
        else:
            print("    [warn] no --restart-cmd given; restart Odysseus yourself before verifying")

    # --- system prompt + tools ---------------------------------------------
    for business, meta, owner, password in pending:
        print(f"\n  {meta['label']}  ({owner}) — settings")
        if password is None:
            supplied = (args.user_password or {}).get(owner)
            if not supplied:
                print("    [skip] needs this user's password, which we do not have.")
                print("           Pass --user-password, or set the prompt in the UI.")
                continue
            password = supplied

        user = Client(args.url)
        user.login(owner, password)

        payload = {
            "personality": read_system_prompt(business),
            "enabled_tools": sorted(meta["tools"]),
            "allow_autonomous_email": False,
        }
        if args.model:
            payload["model"] = args.model

        status, body = user.request("PATCH", "/api/assistant/settings", payload)
        if status == 200:
            print(f"    [ok] system prompt loaded ({len(payload['personality'])} chars)")
            print(f"    [ok] {len(payload['enabled_tools'])} tools granted, autonomous email off")
        else:
            problems.append(f"{owner}: assistant settings failed ({status})")
            print(f"    [FAIL] assistant settings failed ({status}) {body.get('detail','')}")

    # --- credentials, printed once ----------------------------------------
    if credentials:
        print("\n" + "=" * 68)
        print("  NEW PASSWORDS — shown once, stored nowhere. Save them now.")
        print("=" * 68)
        for owner, password in credentials:
            print(f"    {owner:20} {password}")
        print("=" * 68)

    if problems:
        print("\n  Problems:")
        for p in problems:
            print(f"    - {p}")
        return 1

    # --then-verify runs the check in this same process, so the generated
    # passwords are used from memory and never written down or passed on a
    # command line where they would land in shell history.
    if args.then_verify:
        args.user_password = {**dict(credentials), **(args.user_password or {})}
        print("\n  Verifying in this process (passwords stay in memory)...")
        return verify(args)

    print("\n  Next: deploy the skills, then verify.")
    print("    python3 odysseus/tools/build_skills.py --odysseus-root <path> --deploy")
    print("    docker compose restart odysseus")
    print(f"    python3 odysseus/tools/provision_workspaces.py --url {args.url} --verify")
    return 0


# ------------------------------------------------------------------- verify --

def verify(args) -> int:
    """Check the install, including that skill isolation actually holds."""
    passwords = args.user_password or {}
    if not passwords:
        raise SystemExit(
            "error: --verify needs each business user's password to log in as them.\n"
            "       Pass --user-password owner=secret (repeatable), or set\n"
            "       ODYSSEUS_WS_PASSWORDS='owner=secret,owner2=secret2'."
        )

    failures = 0
    seen_by: dict[str, set] = {}

    for business, meta in skills_source.BUSINESSES.items():
        owner = meta["owner"]
        print(f"\n  {meta['label']}  ({owner})")
        if owner not in passwords:
            print("    [skip] no password supplied")
            continue

        user = Client(args.url)
        user.login(owner, passwords[owner])
        print("    [ok] login")

        status, body = user.request("GET", "/api/assistant/settings")
        if status != 200:
            print(f"    [FAIL] could not read assistant settings ({status})")
            failures += 1
        else:
            crew = body.get("crew") or {}
            personality = (crew.get("personality") or "").strip()
            expected_title = prompt_title(business)
            actual_title = next(
                (ln.strip() for ln in personality.splitlines() if ln.strip()), ""
            )
            if not personality:
                print("    [FAIL] no system prompt loaded")
                failures += 1
            elif actual_title != expected_title:
                print("    [FAIL] wrong prompt loaded on this user")
                print(f"           expected: {expected_title}")
                print(f"           found:    {actual_title or '(none)'}")
                failures += 1
            else:
                print(f"    [ok] system prompt loaded ({len(personality)} chars)")

            tools = crew.get("enabled_tools")
            if isinstance(tools, str):
                try:
                    tools = json.loads(tools)
                except json.JSONDecodeError:
                    tools = tools
            if tools == "all" or tools is None:
                print("    [FAIL] tools unrestricted — draft-only is not enforced")
                failures += 1
            else:
                granted = set(tools)
                leaked = granted & set(skills_source.DENIED_TOOLS)
                if leaked:
                    print(f"    [FAIL] denied tools granted: {sorted(leaked)}")
                    failures += 1
                else:
                    print(f"    [ok] {len(granted)} tools, no denied tool granted")

        status, body = user.request("GET", "/api/skills")
        if status != 200:
            print(f"    [FAIL] could not list skills ({status})")
            failures += 1
            continue
        items = body.get("skills") if isinstance(body, dict) else body
        names = {s.get("name") for s in (items or []) if isinstance(s, dict)}
        seen_by[owner] = names
        expected = expected_skill_names(business)
        if names == expected:
            print(f"    [ok] exactly its own {len(expected)} skills visible")
        else:
            missing, extra = expected - names, names - expected
            if missing:
                print(f"    [FAIL] missing skills: {sorted(missing)}")
            if extra:
                print(f"    [FAIL] unexpected skills visible: {sorted(extra)}")
            failures += 1

    # The isolation proof: no user may see another business's skills.
    print("\n  Isolation")
    for business, meta in skills_source.BUSINESSES.items():
        owner = meta["owner"]
        if owner not in seen_by:
            continue
        for other, other_meta in skills_source.BUSINESSES.items():
            if other == business:
                continue
            bleed = seen_by[owner] & expected_skill_names(other)
            if bleed:
                print(f"    [FAIL] {owner} can see {other_meta['label']} skills: {sorted(bleed)}")
                failures += 1
    if failures == 0:
        print("    [ok] no workspace can see another's skills")

    print()
    if failures:
        print(f"  FAILED — {failures} problem(s)")
        return 1
    print("  OK — all workspaces provisioned and isolated")
    return 0


# ---------------------------------------------------------------------- cli --

def wait_for(url: str, attempts: int = 40) -> bool:
    """Poll the base URL until Odysseus answers again after a restart."""
    for _ in range(attempts):
        try:
            urllib.request.urlopen(url, timeout=3)
            return True
        except urllib.error.HTTPError:
            return True          # any HTTP status means it is serving
        except Exception:
            time.sleep(3)
    return False


def parse_passwords(pairs) -> dict:
    out = {}
    env = os.environ.get("ODYSSEUS_WS_PASSWORDS", "")
    for chunk in env.split(",") if env else []:
        if "=" in chunk:
            k, v = chunk.split("=", 1)
            out[k.strip()] = v.strip()
    for pair in pairs or []:
        if "=" not in pair:
            raise SystemExit(f"error: --user-password expects owner=secret, got {pair!r}")
        k, v = pair.split("=", 1)
        out[k.strip()] = v
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--url", default="http://localhost:7000", help="Odysseus base URL")
    ap.add_argument("--admin-user", default="admin")
    ap.add_argument("--model", help="Pin this model for all three workspaces")
    ap.add_argument("--user-password", action="append", metavar="OWNER=SECRET",
                    help="Password for an existing business user (repeatable)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Execute the plan")
    mode.add_argument("--verify", action="store_true", help="Check an existing install")
    ap.add_argument("--orchestrate", action="store_true",
                    help="With --apply: deploy the skills and restart Odysseus between "
                         "creating the users and configuring them. This is the only "
                         "ordering that survives Odysseus's startup owner-backfill. "
                         "Requires --odysseus-root.")
    ap.add_argument("--odysseus-root", help="Path to the Odysseus checkout (for --orchestrate)")
    ap.add_argument("--restart-cmd", default="docker compose restart odysseus",
                    help="Command used to restart Odysseus during --orchestrate")
    ap.add_argument("--then-verify", action="store_true",
                    help="With --apply: verify immediately, reusing the generated "
                         "passwords from memory. Deploy the skills first or the "
                         "skill check will fail.")
    args = ap.parse_args()
    args.user_password = parse_passwords(args.user_password)
    if args.orchestrate and not args.odysseus_root:
        raise SystemExit("error: --orchestrate requires --odysseus-root")

    if args.verify:
        return verify(args)
    if args.apply:
        return apply(args)
    return show_plan(args)


if __name__ == "__main__":
    raise SystemExit(main())

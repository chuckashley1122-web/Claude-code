#!/usr/bin/env python3
"""Regression test for provision_workspaces.py, with no Odysseus required.

Stands up a mock of the Odysseus endpoints the provisioner uses — modelled on
the real handlers in routes/auth_routes.py, routes/assistant_routes.py, and
routes/skills_routes.py, including the strict owner filter in
services/memory/skills.py — then drives the real provisioner against it as a
subprocess.

This is the only way to exercise the HTTP path without Docker, and it covers
the failure modes that would otherwise surface on the user's machine: an
already-existing user, a denied tool slipping into a grant, and skills bleeding
across workspaces.

    python3 odysseus/tools/test_provision.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import skills_source  # noqa: E402

PROVISIONER = os.path.join(HERE, "provision_workspaces.py")
SESSION_COOKIE = "odysseus_session"
ADMIN_PASSWORD = "admin-password-for-test"


class State:
    """Mock server state. Mirrors the shapes the real API returns."""

    def __init__(self):
        self.users = {"admin": {"password": ADMIN_PASSWORD, "is_admin": True, "privileges": {}}}
        self.sessions = {}
        self.crew = {}
        # (name, owner) — populated by "deploying" the real skill definitions.
        self.skills = []
        # Fault injection for the negative tests.
        self.force_tools = None       # override enabled_tools on read
        self.leak_skills_to = None    # owner that wrongly sees everything

    def deploy_skills(self):
        self.skills = [
            (s["name"], skills_source.BUSINESSES[s["business"]]["owner"])
            for s in skills_source.SKILLS
        ]


class Handler(BaseHTTPRequestHandler):
    state: State = None  # set by serve()

    def log_message(self, *args):  # keep the test output clean
        pass

    # -- helpers ---------------------------------------------------------

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode())
        except json.JSONDecodeError:
            return {}

    def _send(self, status, payload, cookie=None):
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        if cookie:
            self.send_header("Set-Cookie", f"{SESSION_COOKIE}={cookie}; Path=/; HttpOnly")
        self.end_headers()
        self.wfile.write(raw)

    def _whoami(self):
        raw = self.headers.get("Cookie") or ""
        for part in raw.split(";"):
            part = part.strip()
            if part.startswith(SESSION_COOKIE + "="):
                return self.state.sessions.get(part.split("=", 1)[1])
        return None

    # -- routes ----------------------------------------------------------

    def do_POST(self):
        s = self.state
        if self.path == "/api/auth/login":
            body = self._body()
            user = s.users.get((body.get("username") or "").strip().lower())
            if not user or user["password"] != body.get("password"):
                return self._send(401, {"detail": "Invalid credentials"})
            token = uuid.uuid4().hex
            s.sessions[token] = body["username"].strip().lower()
            return self._send(200, {"ok": True, "username": body["username"]}, cookie=token)

        if self.path == "/api/auth/users":
            who = self._whoami()
            if not who or not s.users[who]["is_admin"]:
                return self._send(403, {"detail": "Admin only"})
            body = self._body()
            name = (body.get("username") or "").strip().lower()
            if name in s.users:
                return self._send(409, {"detail": "Username already taken"})
            s.users[name] = {
                "password": body.get("password"),
                "is_admin": bool(body.get("is_admin")),
                "privileges": {},
            }
            return self._send(200, {"ok": True})

        return self._send(404, {"detail": "not found"})

    def do_GET(self):
        s = self.state
        who = self._whoami()

        if self.path == "/api/auth/users":
            if not who or not s.users[who]["is_admin"]:
                return self._send(403, {"detail": "Admin only"})
            return self._send(200, {"users": [
                {"username": u, "is_admin": d["is_admin"], "privileges": d["privileges"]}
                for u, d in s.users.items()
            ]})

        if self.path == "/api/assistant/settings":
            if not who:
                return self._send(401, {"detail": "unauthenticated"})
            crew = dict(s.crew.get(who, {}))
            if s.force_tools is not None:
                crew["enabled_tools"] = s.force_tools
            return self._send(200, {"crew": crew, "check_ins": [], "task_ids": []})

        if self.path == "/api/skills":
            if not who:
                return self._send(401, {"detail": "unauthenticated"})
            # Mirrors SkillsManager.load(owner): strict owner equality, and an
            # unowned skill is visible to nobody.
            if s.leak_skills_to == who:
                visible = [n for n, _ in s.skills]
            else:
                visible = [n for n, owner in s.skills if owner == who]
            return self._send(200, {"skills": [{"name": n} for n in visible]})

        return self._send(404, {"detail": "not found"})

    def do_PUT(self):
        s = self.state
        who = self._whoami()
        if self.path.startswith("/api/auth/users/") and self.path.endswith("/privileges"):
            if not who or not s.users[who]["is_admin"]:
                return self._send(403, {"detail": "Admin only"})
            target = self.path.split("/")[4]
            if target not in s.users:
                return self._send(404, {"detail": "User not found"})
            s.users[target]["privileges"] = self._body()
            return self._send(200, {"ok": True, "privileges": s.users[target]["privileges"]})
        return self._send(404, {"detail": "not found"})

    def do_PATCH(self):
        s = self.state
        who = self._whoami()
        if self.path == "/api/assistant/settings":
            if not who:
                return self._send(401, {"detail": "unauthenticated"})
            crew = s.crew.setdefault(who, {})
            crew.update(self._body())
            return self._send(200, {"crew": crew})
        return self._send(404, {"detail": "not found"})


def serve(state: State):
    Handler.state = state
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def run(url, *extra, passwords=None, expect=0):
    cmd = [sys.executable, PROVISIONER, "--url", url, *extra]
    env = dict(os.environ, ODYSSEUS_ADMIN_PASSWORD=ADMIN_PASSWORD)
    if passwords:
        env["ODYSSEUS_WS_PASSWORDS"] = ",".join(f"{k}={v}" for k, v in passwords.items())
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
    out = proc.stdout + proc.stderr
    if proc.returncode != expect:
        print(out)
        raise AssertionError(f"expected exit {expect}, got {proc.returncode}: {' '.join(extra)}")
    return out


def extract_passwords(output):
    found = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] in {b["owner"] for b in skills_source.BUSINESSES.values()}:
            found[parts[0]] = parts[1]
    return found


def main() -> int:
    checks, failures = 0, []

    def check(label, condition):
        nonlocal checks
        checks += 1
        if condition:
            print(f"  OK   {label}")
        else:
            print(f"  FAIL {label}")
            failures.append(label)

    state = State()
    server, url = serve(state)
    print(f"mock Odysseus on {url}\n")

    # ---------------------------------------------------------- plan ----
    out = run(url)
    check("plan runs without touching the server", "Re-run with --apply" in out)
    check("plan changes nothing", state.users.keys() == {"admin"})

    # --------------------------------------------------------- apply ----
    out = run(url, "--apply")
    creds = extract_passwords(out)
    owners = {b["owner"] for b in skills_source.BUSINESSES.values()}

    check("all three users created", owners <= set(state.users))
    check("users are non-admin", all(not state.users[o]["is_admin"] for o in owners))
    check("passwords printed once, all three", set(creds) == owners)
    check("passwords are full length", all(len(p) == 24 for p in creds.values()))
    check("passwords differ from each other", len(set(creds.values())) == 3)
    check("privileges recorded", all(state.users[o]["privileges"] for o in owners))
    check("bash denied by privilege on every user",
          all(state.users[o]["privileges"].get("can_use_bash") is False for o in owners))

    check("system prompt loaded for all three",
          all(state.crew.get(o, {}).get("personality") for o in owners))
    check("autonomous email disabled everywhere",
          all(state.crew[o].get("allow_autonomous_email") is False for o in owners))

    denied = set(skills_source.DENIED_TOOLS)
    check("no denied tool granted to any workspace",
          all(not (set(state.crew[o]["enabled_tools"]) & denied) for o in owners))
    check("send_email specifically absent",
          all("send_email" not in state.crew[o]["enabled_tools"] for o in owners))
    check("consulting has the narrowest grant",
          len(state.crew["caj-consulting"]["enabled_tools"])
          < len(state.crew["caj-enterprises"]["enabled_tools"]))
    check("each prompt matches its own business",
          all(skills_source.BUSINESSES[b]["label"] in state.crew[skills_source.BUSINESSES[b]["owner"]]["personality"]
              for b in skills_source.BUSINESSES))

    # -------------------------------------------------- idempotence -----
    before = dict(state.users["caj-grind"])
    out = run(url, "--apply")
    check("re-run does not recreate an existing user",
          state.users["caj-grind"]["password"] == before["password"])
    check("re-run reports the skip", "already exists" in out)

    # -------------------------------------------------------- verify ----
    out = run(url, "--verify", passwords=creds, expect=1)
    check("verify fails before skills are deployed", "missing skills" in out)

    state.deploy_skills()
    out = run(url, "--verify", passwords=creds)
    check("verify passes once skills are deployed", "all workspaces provisioned and isolated" in out)
    check("verify confirms isolation", "no workspace can see another's skills" in out)
    check("verify counts each workspace's own five",
          out.count("exactly its own 5 skills visible") == 3)

    # ------------------------------------------------ negative tests ----
    state.leak_skills_to = "caj-enterprises"
    out = run(url, "--verify", passwords=creds, expect=1)
    check("verify catches skills bleeding across workspaces", "can see" in out)
    state.leak_skills_to = None

    state.force_tools = ["send_email", "web_search"]
    out = run(url, "--verify", passwords=creds, expect=1)
    check("verify catches a denied tool being granted", "denied tools granted" in out)

    state.force_tools = "all"
    out = run(url, "--verify", passwords=creds, expect=1)
    check("verify catches unrestricted tools", "tools unrestricted" in out)
    state.force_tools = None

    saved = state.crew["caj-consulting"]["personality"]
    state.crew["caj-consulting"]["personality"] = ""
    out = run(url, "--verify", passwords=creds, expect=1)
    check("verify catches a missing system prompt", "no system prompt loaded" in out)
    state.crew["caj-consulting"]["personality"] = saved

    state.crew["caj-consulting"]["personality"] = state.crew["caj-grind"]["personality"]
    out = run(url, "--verify", passwords=creds, expect=1)
    check("verify catches the wrong prompt on a user", "wrong prompt loaded" in out)
    check("wrong-prompt failure names both titles", "expected:" in out and "found:" in out)
    state.crew["caj-consulting"]["personality"] = saved

    out = run(url, "--verify", passwords={"caj-grind": "wrong-password"}, expect=1)
    check("verify fails loudly on a bad password", "login failed" in out)

    # --apply --then-verify: one process, passwords never leave memory.
    fresh = State()
    fresh.deploy_skills()
    server2, url2 = serve(fresh)
    Handler.state = fresh
    out = run(url2, "--apply", "--then-verify")
    check("apply --then-verify provisions and verifies in one run",
          "all workspaces provisioned and isolated" in out)
    check("--then-verify still prints the passwords once",
          set(extract_passwords(out)) == owners)
    server2.shutdown()
    Handler.state = state

    server.shutdown()

    print()
    if failures:
        print(f"FAILED — {len(failures)} of {checks} checks:")
        for f in failures:
            print(f"  {f}")
        return 1
    print(f"OK — {checks} checks passed against the mock Odysseus API")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

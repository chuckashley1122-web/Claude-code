"""301 redirect map -> out/seo/redirect_map.json + redirect_map.md.

Populated only from real old URLs a human supplies in config/redirect_input.json
(a JSON list of {"old": "...", "new": "/route"}). With no input the map is empty
and NEEDS_EVIDENCE. Live redirect testing is BLOCKED and never claimed to pass.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from src import page_plan  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, emit, record_blocker  # noqa: E402


class RedirectMapError(ValueError):
    pass


def _path_of(url: str) -> str:
    parts = urlsplit(url)
    return parts.path or "/"


def build_map(pairs: list[dict], known_routes: list[str]) -> list[dict]:
    """Validate a one-to-one old->new mapping with permanent (301) redirects."""
    olds, entries = set(), []
    for pair in pairs:
        old, new = str(pair.get("old", "")).strip(), str(pair.get("new", "")).strip()
        if not old or not new:
            raise RedirectMapError(f"incomplete pair {pair!r}")
        old_path = _path_of(old)
        if old_path in olds:
            raise RedirectMapError(f"old URL mapped twice: {old}")
        if new not in known_routes:
            raise RedirectMapError(f"target {new} is not a route in the inventory")
        if old_path == new:
            raise RedirectMapError(f"self-redirect: {old}")
        olds.add(old_path)
        entries.append({"old": old, "old_path": old_path, "new": new, "status": 301,
                        "live_test": "BLOCKED"})
    targets = {e["new"] for e in entries}
    chained = sorted(olds & targets)
    if chained:
        raise RedirectMapError(f"redirect chain through {chained}; map each old URL to its final target")
    return entries


def render_markdown(entries: list[dict], status: str) -> str:
    lines = ["# Redirect map (SPEC-05)", "",
             f"Status: {status}. One-to-one permanent (301) redirects, populated only from real old URLs "
             "supplied by a human in `config/redirect_input.json`. Live redirect testing is BLOCKED until a "
             "draft/live host exists; it is not claimed to pass.", ""]
    if not entries:
        lines.append(f"No entries: the existing URL list is {C.NEEDS_EVIDENCE}.")
    else:
        lines += ["| Old URL | New route | Status | Live test |", "|---|---|---|---|"]
        lines += [f"| {e['old']} | {e['new']} | {e['status']} | {e['live_test']} |" for e in entries]
    lines.append("")
    return "\n".join(lines)


def build(paths: Paths | None = None) -> dict:
    paths = paths or default_paths()
    routes = [r["route"] for r in page_plan.load(paths)]
    if paths.redirect_input.exists():
        pairs = json.loads(paths.redirect_input.read_text(encoding="utf-8"))
        entries = build_map(pairs, routes)
        status = "DRAFT (human-supplied old URLs)"
    else:
        entries, status = [], C.NEEDS_EVIDENCE
        record_blocker("redirect_sources", "Real old URLs from the existing site",
                       "redirect map", "Human supplies config/redirect_input.json after baseline inventory", paths)
    data = {"status": status, "live_redirect_test": "BLOCKED", "entries": entries}
    seo = paths.out / "seo"
    emit("redirect_map_json", seo / "redirect_map.json", data, STATUS.DRAFT, paths, source="src/redirect_map.py")
    emit("redirect_map_md", seo / "redirect_map.md", render_markdown(entries, status), STATUS.DRAFT, paths,
         source="src/redirect_map.py")
    return data


if __name__ == "__main__":
    build()
    print("redirect map written")

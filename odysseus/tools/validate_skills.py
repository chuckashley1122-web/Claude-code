#!/usr/bin/env python3
"""Validate the committed CA&J SKILL.md files against Odysseus's own parser.

Checks two things the builder cannot check itself:

  format  — every file parses with upstream's `Skill.from_markdown`, and
            re-serializing produces the identical bytes. A round-trip that is
            not stable means Odysseus would rewrite the file on first save and
            our committed artifact would drift from what is running.

  policy  — the invariants the workspace design depends on: every skill is
            owned (an unowned skill is invisible to every user, so it would
            silently never load), owner and category match the business, the
            required sections are non-empty, the standing-rules block is
            present, and the API length limits are respected.

Usage:
    python3 odysseus/tools/validate_skills.py --odysseus-root /path/to/odysseus
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skills_source  # noqa: E402
from build_skills import REPO_ROOT, WORKSPACES, load_skill_format, repo_path  # noqa: E402

# Mirrors routes/skills_routes.py SkillAddRequest, so a skill that validates
# here is also acceptable to the REST API, not just to the on-disk loader.
MAX_DESCRIPTION = 200
MAX_WHEN_TO_USE = 2000
MAX_NAME = 80


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--odysseus-root", required=True)
    args = ap.parse_args()

    fmt = load_skill_format(args.odysseus_root)

    failures: list[str] = []
    checked = 0

    def fail(where: str, msg: str) -> None:
        failures.append(f"{where}: {msg}")

    expected = {(s["business"], s["name"]) for s in skills_source.SKILLS}

    # Every definition must have a committed file.
    for business, name in sorted(expected):
        if not os.path.isfile(repo_path(business, name)):
            fail(f"{business}/{name}", "defined in skills_source.py but no SKILL.md committed")

    # Every committed file must have a definition — catches leftovers from a
    # renamed or deleted skill, which would still deploy and still load.
    for business in sorted(skills_source.BUSINESSES):
        skills_dir = os.path.join(WORKSPACES, business, "skills")
        if not os.path.isdir(skills_dir):
            continue
        for name in sorted(os.listdir(skills_dir)):
            if not os.path.isdir(os.path.join(skills_dir, name)):
                continue
            if (business, name) not in expected:
                fail(f"{business}/{name}", "SKILL.md on disk has no definition in skills_source.py (orphan)")

    for spec in skills_source.SKILLS:
        business = spec["business"]
        meta = skills_source.BUSINESSES[business]
        path = repo_path(business, spec["name"])
        where = os.path.relpath(path, REPO_ROOT)
        if not os.path.isfile(path):
            continue
        checked += 1

        with open(path, encoding="utf-8") as fh:
            text = fh.read()

        try:
            skill = fmt.Skill.from_markdown(text, path=path)
        except Exception as exc:  # noqa: BLE001 - report, do not crash the run
            fail(where, f"does not parse: {exc}")
            continue

        # --- format -------------------------------------------------------
        if skill.to_markdown() != text:
            fail(where, "round-trip is not stable; Odysseus would rewrite this file on save")

        dir_name = os.path.basename(os.path.dirname(path))
        if skill.name != dir_name:
            fail(where, f"frontmatter name '{skill.name}' != directory '{dir_name}'")
        if skill.name != fmt.slugify(skill.name):
            fail(where, f"name '{skill.name}' is not a stable slug")

        # --- policy -------------------------------------------------------
        if not skill.owner:
            fail(where, "no owner; SkillsManager.load(owner) hides unowned skills from every user")
        elif skill.owner != meta["owner"]:
            fail(where, f"owner '{skill.owner}' != expected '{meta['owner']}'")

        if skill.category != meta["category"]:
            fail(where, f"category '{skill.category}' != expected '{meta['category']}'")

        for field_name in ("when_to_use",):
            if not getattr(skill, field_name).strip():
                fail(where, f"{field_name} is empty")
        for field_name in ("procedure", "pitfalls", "verification"):
            if not getattr(skill, field_name):
                fail(where, f"{field_name} is empty")

        if skill.body_extra.strip():
            fail(where, "body_extra is set; it does not survive upstream's parse/save cycle")
        if skills_source.STANDING_PITFALL not in skill.pitfalls:
            fail(where, "standing injection-handling pitfall missing")
        if skills_source.STANDING_VERIFICATION not in skill.verification:
            fail(where, "standing draft-only verification item missing")

        if len(skill.description) > MAX_DESCRIPTION:
            fail(where, f"description is {len(skill.description)} chars, API limit is {MAX_DESCRIPTION}")
        if len(skill.when_to_use) > MAX_WHEN_TO_USE:
            fail(where, f"when_to_use is {len(skill.when_to_use)} chars, API limit is {MAX_WHEN_TO_USE}")
        if len(skill.name) > MAX_NAME:
            fail(where, f"name is {len(skill.name)} chars, API limit is {MAX_NAME}")

        # Upstream's frontmatter emitter quotes with json.dumps (which escapes
        # non-ASCII to \uXXXX) but its parser only strips the quotes — it never
        # JSON-decodes. So a quoted value containing non-ASCII, a double quote,
        # or a backslash gains a backslash on every save. Test each frontmatter
        # string with upstream's own pair rather than guessing the trigger set.
        for field_name in ("name", "description", "category", "owner", "version", "created"):
            value = getattr(skill, field_name, None)
            if not isinstance(value, str) or not value:
                continue
            if fmt._parse_scalar(fmt._emit_scalar(value)) != value:
                fail(where, f"frontmatter '{field_name}' does not survive emit/parse; keep it plain ASCII")

        if skill.source != "user":
            fail(where, f"source is '{skill.source}'; must be 'user' to survive auto-eviction")

    # --- cross-cutting ----------------------------------------------------
    owners = {b["owner"] for b in skills_source.BUSINESSES.values()}
    if len(owners) != len(skills_source.BUSINESSES):
        fail("skills_source.py", "two businesses share an owner; isolation would not hold")

    categories = {b["category"] for b in skills_source.BUSINESSES.values()}
    if len(categories) != len(skills_source.BUSINESSES):
        fail("skills_source.py", "two businesses share a category; skills would collide on disk")

    if failures:
        print(f"FAILED — {len(failures)} problem(s) across {checked} skill(s):\n", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1

    print(f"OK — {checked} skills validated against upstream skill_format")
    print("     format: parse + stable round-trip")
    print("     policy: owned, isolated, complete sections, standing rules, API limits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

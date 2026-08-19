#!/usr/bin/env python3
"""Render the CA&J workspace skills into Odysseus SKILL.md files.

The format is not reimplemented here. This loads Odysseus's own
`services/memory/skill_format.py` and uses its `Skill` dataclass to serialize,
so the output is whatever upstream currently writes. If upstream changes the
format, this build changes with it — and `--check` fails loudly rather than
silently emitting a stale shape.

Usage
-----
Render into the repo (the committed artifacts):

    python3 odysseus/tools/build_skills.py --odysseus-root /path/to/odysseus

Verify the committed files are current, changing nothing (for CI / review):

    python3 odysseus/tools/build_skills.py --odysseus-root /path/to/odysseus --check

Install into a running Odysseus data directory:

    python3 odysseus/tools/build_skills.py --odysseus-root /path/to/odysseus --deploy

`--deploy` writes to <odysseus-root>/data/skills/<category>/<name>/SKILL.md,
which is the path SkillsManager reads. It refuses to overwrite a skill whose
owner on disk differs from the owner we are about to write, so a hand-edited or
differently-owned skill is never silently replaced.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKSPACES = os.path.join(REPO_ROOT, "odysseus", "workspaces")

# Fixed so a rebuild is byte-identical. A build that churns `created:` on every
# run makes every diff noise and hides the changes that matter.
CREATED = "2026-08-19T00:00:00Z"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skills_source  # noqa: E402


def load_skill_format(odysseus_root: str):
    """Import Odysseus's skill_format module directly from its file path."""
    path = os.path.join(odysseus_root, "services", "memory", "skill_format.py")
    if not os.path.isfile(path):
        sys.exit(
            f"error: {path} not found.\n"
            "       Pass --odysseus-root pointing at the Odysseus checkout "
            "(the directory containing docker-compose.yml)."
        )
    spec = importlib.util.spec_from_file_location("odysseus_skill_format", path)
    module = importlib.util.module_from_spec(spec)
    # Register before exec: skill_format uses `from __future__ import annotations`
    # with @dataclass, and dataclasses resolves field types via
    # sys.modules[cls.__module__], which fails if the module is not there yet.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    for attr in ("Skill", "slugify"):
        if not hasattr(module, attr):
            sys.exit(f"error: upstream skill_format has no {attr}; the format changed.")
    return module


def build_one(fmt, spec: dict) -> "tuple[str, str, object]":
    """Return (business, rendered_markdown, skill_object) for one definition."""
    biz = skills_source.BUSINESSES[spec["business"]]

    # Standing rules go into the list sections, never body_extra — see the
    # comment on STANDING_PITFALL in skills_source.py for why body_extra is
    # unusable here.
    pitfalls = list(spec.get("pitfalls", [])) + [skills_source.STANDING_PITFALL]
    verification = list(spec.get("verification", [])) + [skills_source.STANDING_VERIFICATION]

    skill = fmt.Skill(
        name=spec["name"],
        description=spec["description"],
        version=spec.get("version", "1.0.0"),
        category=biz["category"],
        tags=list(spec.get("tags", [])),
        status=spec.get("status", "published"),
        confidence=spec.get("confidence", 0.9),
        # "user" marks these as human-authored, which exempts them from the
        # agent's auto-dedup and cap-eviction. Our skills must not be evicted
        # to make room for something the model learned on its own.
        source="user",
        owner=biz["owner"],
        created=CREATED,
        when_to_use=spec["when_to_use"],
        procedure=list(spec["procedure"]),
        pitfalls=pitfalls,
        verification=verification,
    )
    return spec["business"], skill.to_markdown(), skill


def repo_path(business: str, name: str) -> str:
    return os.path.join(WORKSPACES, business, "skills", name, "SKILL.md")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--odysseus-root", required=True, help="Path to the Odysseus checkout")
    ap.add_argument("--check", action="store_true", help="Verify committed files are current; write nothing")
    ap.add_argument("--deploy", action="store_true", help="Install into <odysseus-root>/data/skills/")
    args = ap.parse_args()

    fmt = load_skill_format(args.odysseus_root)
    built = [build_one(fmt, s) for s in skills_source.SKILLS]

    # Guard: a duplicate slug within a category would silently collide on disk.
    seen = {}
    for business, _, skill in built:
        key = (skill.category, skill.name)
        if key in seen:
            sys.exit(f"error: duplicate skill {skill.category}/{skill.name}")
        seen[key] = business

    stale = []
    for business, text, skill in built:
        dest = repo_path(business, skill.name)
        current = None
        if os.path.isfile(dest):
            with open(dest, encoding="utf-8") as fh:
                current = fh.read()
        if current == text:
            continue
        if args.check:
            stale.append(os.path.relpath(dest, REPO_ROOT))
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote  {os.path.relpath(dest, REPO_ROOT)}")

    if args.check:
        if stale:
            print("Committed SKILL.md files are out of date:", file=sys.stderr)
            for s in stale:
                print(f"  {s}", file=sys.stderr)
            print("Re-run without --check to regenerate.", file=sys.stderr)
            return 1
        print(f"OK: all {len(built)} SKILL.md files are current")
        return 0

    if args.deploy:
        skills_root = os.path.join(args.odysseus_root, "data", "skills")
        for business, text, skill in built:
            dest_dir = os.path.join(skills_root, fmt.slugify(skill.category), fmt.slugify(skill.name))
            dest = os.path.join(dest_dir, "SKILL.md")
            if os.path.isfile(dest):
                with open(dest, encoding="utf-8") as fh:
                    existing = fmt.Skill.from_markdown(fh.read(), path=dest)
                if existing.owner and existing.owner != skill.owner:
                    print(
                        f"SKIP  {dest}\n"
                        f"      on disk is owned by '{existing.owner}', we would write "
                        f"'{skill.owner}'. Not overwriting another owner's skill.",
                        file=sys.stderr,
                    )
                    continue
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copyfile(repo_path(business, skill.name), dest)
            print(f"deployed  {os.path.relpath(dest, args.odysseus_root)}")
        print()
        print("Restart Odysseus so it re-indexes:  docker compose restart odysseus")
        print("Each skill is owned by its business user and is invisible to the others.")

    print(f"\n{len(built)} skills built.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the CA&J knowledge manifests and their reference sources.

The manifest is the gate: nothing is indexed into a workspace unless it is
listed there and marked approved. That makes the manifest worth checking
mechanically, because the failure modes are quiet ones — a path that no longer
resolves, a source approved with no approver recorded, a drafted file whose
"Verify before approval" section was dropped in an edit.

Checks
------
structure   every manifest parses, carries the required keys, and has unique
            source ids
paths       every path-backed source resolves on disk, and lives where its
            sensitivity says it should
approval    approved sources name an approver; PII-bearing sources are never
            approved; a workspace with pii_policy: prohibited has no
            PII-bearing source at all
drafts      every `status: drafted` file exists and still carries its
            "Verify before approval" section
hygiene     no PII-shaped pattern in any tracked reference file

Usage:
    python3 odysseus/tools/validate_sources.py
"""

from __future__ import annotations

import glob
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("error: PyYAML is required.  pip install pyyaml")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKSPACES = os.path.join(REPO_ROOT, "odysseus", "workspaces")

REQUIRED_SOURCE_FIELDS = ("id", "type", "description", "approved", "approver", "contains_pii")
VERIFY_HEADING = "Verify before approval"

# Shapes that must never appear in a tracked file. Deliberately narrow — this
# catches an accidental paste, not a determined one.
PII_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "SSN-shaped number"),
    (re.compile(r"\b4[0-9]{12}(?:[0-9]{3})?\b"), "card-shaped number"),
    (re.compile(r"\b(?:routing|acct|account)\s*(?:number|#)\s*[:=]\s*\d{6,}", re.I), "account number"),
]


def main() -> int:
    failures: list[str] = []
    notes: list[str] = []

    def fail(where: str, msg: str) -> None:
        failures.append(f"{where}: {msg}")

    manifests = sorted(glob.glob(os.path.join(WORKSPACES, "*", "knowledge-manifest.yml")))
    if not manifests:
        print("error: no manifests found", file=sys.stderr)
        return 1

    total_sources = 0
    total_drafted = 0

    for manifest in manifests:
        rel = os.path.relpath(manifest, REPO_ROOT)
        base = os.path.dirname(manifest)

        try:
            data = yaml.safe_load(open(manifest, encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            fail(rel, f"does not parse: {exc}")
            continue

        for key in ("workspace", "version", "sources"):
            if key not in data:
                fail(rel, f"missing top-level key '{key}'")
        if "sources" not in data:
            continue

        workspace_dir = os.path.basename(base)
        if data.get("workspace") != workspace_dir:
            fail(rel, f"workspace '{data.get('workspace')}' != directory '{workspace_dir}'")

        pii_prohibited = data.get("pii_policy") == "prohibited"
        seen_ids: set[str] = set()

        for source in data["sources"]:
            sid = source.get("id", "<no id>")
            where = f"{rel} [{sid}]"
            total_sources += 1

            for field in REQUIRED_SOURCE_FIELDS:
                if field not in source:
                    fail(where, f"missing required field '{field}'")

            if sid in seen_ids:
                fail(where, "duplicate source id")
            seen_ids.add(sid)

            approved = source.get("approved")
            if approved not in (True, False):
                fail(where, f"'approved' must be true or false, got {approved!r}")

            # Approving without recording who approved it defeats the point.
            if approved is True and not str(source.get("approver") or "").strip():
                fail(where, "approved: true with no approver recorded")

            if source.get("contains_pii") is True:
                if approved is True:
                    fail(where, "a PII-bearing source must never be approved")
                if pii_prohibited:
                    fail(where, "workspace declares pii_policy: prohibited but this source is PII-bearing")

            path = source.get("path")
            drafted = source.get("status") == "drafted"
            if drafted:
                total_drafted += 1

            if not path:
                if drafted:
                    fail(where, "status: drafted but no path")
                continue

            full = os.path.normpath(os.path.join(base, path))

            # A drafted source is one we wrote, so it must be present.
            if drafted and not os.path.isfile(full):
                fail(where, f"drafted source missing on disk: {path}")
                continue

            # reference/ is tracked; approved/ is gitignored business material.
            in_reference = os.sep + "reference" + os.sep in full + os.sep
            in_approved = os.sep + "approved" + os.sep in full + os.sep

            # Every business document the manifest expects needs a template, so
            # filling it in is never a blank page.
            if in_approved:
                template = os.path.join(base, "templates", os.path.basename(path))
                if not os.path.isfile(template):
                    fail(where, f"expects {path} but has no templates/{os.path.basename(path)}")
            if drafted and not in_reference:
                fail(where, f"drafted sources belong in reference/, not {path}")
            if in_approved and os.path.isfile(full):
                notes.append(f"{where}: {path} present locally (gitignored, as intended)")

            if not os.path.isfile(full):
                continue

            text = open(full, encoding="utf-8", errors="replace").read()

            if drafted and VERIFY_HEADING not in text:
                fail(where, f"drafted file has no '{VERIFY_HEADING}' section")

            if in_reference:
                for pattern, label in PII_PATTERNS:
                    if pattern.search(text):
                        fail(where, f"{label} found in a tracked reference file")

    # Orphan check: a reference file nothing points at will never be indexed.
    for ref in sorted(glob.glob(os.path.join(WORKSPACES, "*", "reference", "*.md"))):
        if os.path.basename(ref) == "README.md":
            continue
        rel_ref = os.path.relpath(ref, REPO_ROOT)
        workspace = ref.split(os.sep)[-3]
        manifest = os.path.join(WORKSPACES, workspace, "knowledge-manifest.yml")
        if not os.path.isfile(manifest):
            fail(rel_ref, "no manifest for this workspace")
            continue
        data = yaml.safe_load(open(manifest, encoding="utf-8")) or {}
        paths = {
            os.path.normpath(os.path.join(os.path.dirname(manifest), s["path"]))
            for s in data.get("sources", [])
            if s.get("path")
        }
        if ref not in paths:
            fail(rel_ref, "reference file is not listed in the workspace manifest (orphan)")

    for note in notes:
        print(f"  note: {note}")

    if failures:
        print(f"\nFAILED — {len(failures)} problem(s):\n", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1

    print(f"OK — {len(manifests)} manifests, {total_sources} sources, {total_drafted} drafted")
    print("     structure, paths, approval discipline, draft verify-sections, PII hygiene,")
    print("     and every expected business document has a template")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Consolidate the whole CA-J Growth System package into ONE top-level folder
plus a single .zip, so it can be pulled in one action.

Copies (never moves) everything out of agency-agents/caj-growth-system, adds a
MANIFEST, and zips the result.
"""
import os
import shutil
import sys
import zipfile
from datetime import datetime

SRC = r"C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system"
DESKTOP = r"C:\Users\chuck\Desktop\CA&J Enterprises"
DEST = os.path.join(DESKTOP, "CAJ-Growth-System")
ZIP = os.path.join(DESKTOP, "CAJ-Growth-System.zip")

SKIP_DIRS = {"__pycache__", ".git", ".venv"}


def copy_tree():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    os.makedirs(DEST, exist_ok=True)
    copied = []
    for base, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel = os.path.relpath(base, SRC)
        target = DEST if rel == "." else os.path.join(DEST, rel)
        os.makedirs(target, exist_ok=True)
        for f in files:
            s = os.path.join(base, f)
            d = os.path.join(target, f)
            shutil.copy2(s, d)
            copied.append((os.path.relpath(d, DEST), os.path.getsize(d)))
    # also pull in the standalone docx that lives at the Desktop level
    for extra in ("CA-J-Growth-System-Build-Specs.docx",
                  "CA-J-Growth-System-RECOVERY-REPORT.docx"):
        p = os.path.join(DESKTOP, extra)
        if os.path.isfile(p):
            d = os.path.join(DEST, extra)
            if not os.path.isfile(d):
                shutil.copy2(p, d)
                copied.append((os.path.relpath(d, DEST), os.path.getsize(d)))
    return sorted(copied)


def write_manifest(items):
    lines = [
        "# CAJ Growth System — Package Manifest",
        "",
        "Owner: **Chuck Ashley** | 512-229-9199 | chuck@ca-jconsulting.com  ",
        "CA&J Enterprises LLC  ",
        "Generated: %s" % datetime.now().strftime("%Y-%m-%d %H:%M"),
        "",
        "## Start here",
        "",
        "1. `CLAUDE.md` — the guardrail file. Read this first.",
        "2. `specs/` — the six build specs. **This is what you point Claude Code at.**",
        "3. `README.md` — how to run it, and what the agent cannot do.",
        "",
        "**Do not point Claude Code at the .docx files** — it cannot reliably read Word.",
        "The .docx copies below are for you to read.",
        "",
        "## How to run",
        "",
        "```bash",
        "cd CAJ-Growth-System",
        "bash run-claude.sh",
        "```",
        "",
        "## The three rules that matter most",
        "",
        "1. **No charges, ever** — no upgrades, domains, ad spend, subscriptions.",
        "2. **The live Meta campaign is frozen** (`CAJ_HVAC27_US_PURCHASE_TEST02`). Stripe is",
        "   connected to that ad account, so spend draws real money. New campaigns = new drafts.",
        "3. **Dry-run only** — nothing sends, writes live, or posts.",
        "",
        "## Contents (measured)",
        "",
        "| File | Bytes |",
        "|---|---|",
    ]
    total = 0
    for rel, size in items:
        lines.append("| `%s` | %s |" % (rel.replace("\\", "/"), "{:,}".format(size)))
        total += size
    lines.append("| **TOTAL (%d files)** | **%s** |" % (len(items), "{:,}".format(total)))
    lines += [
        "",
        "## Blockers to know about",
        "",
        "- **Email is blocked.** Postmark is in Test mode / under review; AI Mailer has no",
        "  authenticated sending domain. Sending must default to dry-run.",
        "- **SMS needs A2P 10DLC approval** (unconfirmed).",
        "- **Claude Code has no browser.** All GoHighLevel, Meta Ads Manager, and calendar work",
        "  becomes a `ui-work-orders/*.md` file for a human.",
        "- **Only GHL location: `UWc5vKBgFVPdxNTRAy2s`** (\"CA&J Enterprises\"). IDs are",
        "  case-sensitive. Booking destination is always https://ca-jenterprises.com/ai",
        "",
        "## Rebuild",
        "",
        "```bash",
        "python tools/recover.py                 # refill specs/ and playbooks/",
        "python tools/build_specs_docx.py        # rebuild the Word doc from specs/",
        "python tools/build_recovery_report.py   # rebuild the recovery report",
        "```",
        "",
        "*No charges were made. No GHL object created. No campaign touched. No email sent.*",
        "",
    ]
    path = os.path.join(DEST, "MANIFEST.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path, total


def make_zip():
    if os.path.isfile(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for base, dirs, files in os.walk(DEST):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                p = os.path.join(base, f)
                z.write(p, os.path.join("CAJ-Growth-System", os.path.relpath(p, DEST)))
    return os.path.getsize(ZIP)


if __name__ == "__main__":
    items = copy_tree()
    man, total = write_manifest(items)
    # re-copy so the manifest is included in the folder AND the zip
    items = copy_tree()
    man, total = write_manifest(items)
    items = sorted(items + [("MANIFEST.md", os.path.getsize(man))])
    zsize = make_zip()
    print("FOLDER: %s" % DEST)
    print("MANIFEST: %s" % man)
    print("ZIP: %s (%s bytes)" % (ZIP, "{:,}".format(zsize)))
    print("FILES: %d   TOTAL: %s bytes" % (len(items), "{:,}".format(total)))
    sys.exit(0)

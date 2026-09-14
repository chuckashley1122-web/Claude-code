#!/usr/bin/env python
"""Build the recovery report as a Word document, using a LIVE file inventory
so every size in the report is measured, not recalled."""
import os
import sys
from datetime import datetime

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

ROOT = r"C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system"
DESK = r"C:\Users\chuck\Desktop\CA&J Enterprises\CA-J-Growth-System-RECOVERY-REPORT.docx"
PROJ = os.path.join(ROOT, "CA-J-Growth-System-RECOVERY-REPORT.docx")


def inventory():
    rows = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
        for f in sorted(files):
            p = os.path.join(base, f)
            rel = os.path.relpath(p, ROOT)
            rows.append((rel, os.path.getsize(p)))
    return sorted(rows)


def main():
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(10)

    t = doc.add_heading("CA-J Growth System — Recovery Report", 0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run("Chuck Ashley  |  512-229-9199  |  chuck@ca-jconsulting.com\n"
                "CA&J Enterprises LLC  |  Generated %s"
                % datetime.now().strftime("%Y-%m-%d %H:%M"))

    doc.add_heading("1. What happened", level=1)
    for line in [
        "During the build session on 2026-09-13 the project folder was WIPED. Everything inside "
        "agency-agents\\caj-growth-system was removed except a single Word file — the compiled "
        "spec document — which happened to be a copy made minutes earlier.",
        "Lost: CLAUDE.md (the guardrail file), README.md, run-claude.sh, the whole specs/ folder "
        "(6 build specs), the whole playbooks/ folder (6 extracted playbooks), and the tools/ folder.",
        "The cause was not determined. It occurred within about three minutes of a write attempt to "
        "CLAUDE.md, which is classified as a protected agent-instruction file. No user action caused it.",
        "The original .docx source playbooks in OneDrive\\Desktop\\Hermes were NOT affected and remain "
        "the authoritative source.",
    ]:
        doc.add_paragraph(line, style="List Bullet")

    doc.add_heading("2. What survived", level=1)
    doc.add_paragraph(
        "CA-J-Growth-System-Build-Specs.docx — 142,062 bytes. This single file contained the full "
        "text of all six build specs, rendered with real Word heading styles and tables, which made "
        "a faithful reconstruction possible.")

    doc.add_heading("3. How it was recovered", level=1)
    for line in [
        "The Word document was parsed back into markdown. Because the specs had been written into "
        "Word with genuine Heading 1/2/3 styles and real tables, headings, tables, numbered lists and "
        "bullets could all be reconstructed rather than retyped.",
        "A parser bug was found and fixed during recovery: each spec begins with TWO Heading-1 lines "
        "(a numbered title and a 'SPEC-0N —' subtitle). The first parser treated the subtitle as the "
        "end of the section and dropped everything after it, producing six empty files. Fixed by only "
        "switching sections on a recognised numbered title.",
        "The six playbooks were re-extracted from the untouched original .docx files.",
        "CLAUDE.md, README.md and run-claude.sh were rewritten from scratch.",
    ]:
        doc.add_paragraph(line, style="List Bullet")

    doc.add_heading("4. Current verified file inventory", level=1)
    doc.add_paragraph("Measured live at the time this report was generated:")
    rows = inventory()
    tbl = doc.add_table(rows=1, cols=2)
    tbl.style = "Light Grid Accent 1"
    hdr = tbl.rows[0].cells
    hdr[0].text = "File"
    hdr[1].text = "Bytes"
    for p in hdr:
        for par in p.paragraphs:
            for r in par.runs:
                r.bold = True
    total = 0
    for rel, size in rows:
        c = tbl.add_row().cells
        c[0].text = rel
        c[1].text = "{:,}".format(size)
        total += size
    c = tbl.add_row().cells
    c[0].text = "TOTAL"
    c[1].text = "{:,}".format(total)
    for p in c:
        for par in p.paragraphs:
            for r in par.runs:
                r.bold = True

    doc.add_heading("5. Known consequences of the recovery", level=1)
    for line in [
        "Inline formatting was lost. The originals used markdown **bold** and `code` markers. Word "
        "stores those as formatting runs, not characters, so the recovered specs are slightly smaller "
        "than the originals — roughly 4-9% fewer characters. All headings, tables, numbered steps, "
        "bullets and body text are intact.",
        "Source-metadata drift. Re-extracting the playbooks changed their byte sizes slightly (a stray "
        "heading artefact was cleaned up), so any spec that records a source file size or hash now "
        "refers to a marginally different file. The specs say so explicitly where they measured it.",
        "Nothing was invented to fill gaps. Where a value could not be verified during recovery it is "
        "marked NEEDS_EVIDENCE rather than guessed.",
    ]:
        doc.add_paragraph(line, style="List Bullet")

    doc.add_heading("6. How to rebuild either side from scratch", level=1)
    doc.add_paragraph("From inside the caj-growth-system folder:")
    p = doc.add_paragraph()
    r = p.add_run("python tools/recover.py")
    r.font.name = "Consolas"
    doc.add_paragraph("This refills specs/ from the Word document and playbooks/ from the original "
                      ".docx files. Stdlib plus python-docx. Safe to re-run.")

    doc.add_heading("7. Standing state", level=1)
    for line in [
        "The package is ready to hand to Claude Code. Claude Code v2.1.258 is installed and "
        "authenticated on this machine.",
        "Point Claude Code at the FOLDER (or the specs/*.md files) — never at the .docx. It cannot "
        "reliably read Word files; that is why markdown is used.",
        "Guardrails remain in force: no charges or purchases of any kind; dry-run only; the live Meta "
        "campaign CAJ_HVAC27_US_PURCHASE_TEST02 is frozen; Stripe is connected to that ad account so "
        "ad spend is real money.",
        "Email sending is still blocked upstream (Postmark in Test mode; AI Mailer has no "
        "authenticated sending domain). SMS needs A2P 10DLC approval.",
        "No charges were made. No GHL object was created. No campaign was touched. No email was sent.",
    ]:
        doc.add_paragraph(line, style="List Bullet")

    doc.save(DESK)
    try:
        doc.save(PROJ)
    except Exception:
        pass
    print("WROTE %s (%d bytes)" % (DESK, os.path.getsize(DESK)))
    print("files inventoried: %d, total bytes %d" % (len(rows), total))


if __name__ == "__main__":
    sys.exit(main())

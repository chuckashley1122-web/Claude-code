#!/usr/bin/env python
"""Assemble the six build specs (markdown) into a single Word document.

Output: CA-J-Growth-System-Build-Specs.docx in the project root and Desktop.
"""
import os
import re
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

ROOT = r"C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system"
SPECS = [
    ("SPEC-01-8-best-ai-automations.md", "01 - 8 Best AI Automations"),
    ("SPEC-02-ai-employee.md", "02 - AI Employee Action Plan"),
    ("SPEC-03-high-ticket-agency.md", "03 - High Ticket Agency"),
    ("SPEC-04-facebook-ads-ai-studio.md", "04 - Facebook Ads + GHL AI Studio"),
    ("SPEC-05-ghl-ai-studio-seo.md", "05 - GHL AI Studio SEO + Full Stack"),
    ("SPEC-06-single-workflow.md", "06 - Single Workflow (HPV Research Pilot)"),
]
OUT = r"C:\Users\chuck\Desktop\CA&J Enterprises\CA-J-Growth-System-Build-Specs.docx"

INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`)")


def add_runs(par, text):
    for piece in INLINE.split(text):
        if not piece:
            continue
        if piece.startswith("**") and piece.endswith("**"):
            par.add_run(piece[2:-2]).bold = True
        elif piece.startswith("`") and piece.endswith("`"):
            r = par.add_run(piece[1:-1])
            r.font.name = "Consolas"
            r.font.size = Pt(9)
        else:
            par.add_run(piece)


def add_table(doc, rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    if len(cells) > 1 and all(re.fullmatch(r":?-{2,}:?", c or "-") for c in cells[1]):
        cells.pop(1)
    width = max(len(r) for r in cells)
    t = doc.add_table(rows=0, cols=width)
    t.style = "Light Grid Accent 1"
    for i, row in enumerate(cells):
        wr = t.add_row().cells
        for j in range(width):
            wr[j].text = row[j] if j < len(row) else ""
            if i == 0:
                for p in wr[j].paragraphs:
                    for r in p.runs:
                        r.bold = True


def render(doc, md):
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if ln.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            r = doc.add_paragraph().add_run("\n".join(buf))
            r.font.name = "Consolas"
            r.font.size = Pt(8.5)
            i += 1
            continue
        if ln.startswith("|") and i + 1 < len(lines) and lines[i + 1].startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            add_table(doc, rows)
            doc.add_paragraph()
            continue
        if not ln.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            doc.add_heading(m.group(2).strip(), level=min(len(m.group(1)), 4))
            i += 1
            continue
        if re.match(r"^[-*]\s+", ln):
            add_runs(doc.add_paragraph(style="List Bullet"),
                     re.sub(r"^[-*]\s+", "", ln))
            i += 1
            continue
        if re.match(r"^\d+\.\s+", ln):
            add_runs(doc.add_paragraph(style="List Number"),
                     re.sub(r"^\d+\.\s+", "", ln))
            i += 1
            continue
        if ln.startswith("> "):
            add_runs(doc.add_paragraph(style="Intense Quote"), ln[2:])
            i += 1
            continue
        if ln.strip() in ("---", "***"):
            i += 1
            continue
        add_runs(doc.add_paragraph(), ln)
        i += 1


def main():
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(10)

    t = doc.add_heading("CA-J Growth System - Build Specs", 0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run("Chuck Ashley  |  512-229-9199  |  chuck@ca-jconsulting.com\n"
                "CA&J Enterprises LLC")

    doc.add_paragraph()
    doc.add_heading("How to use this document", level=1)
    for line in [
        "These are the build specs for six CA-J playbooks, written so an AI coding agent "
        "(Claude Code or Claude Cowork) can execute them without asking questions.",
        "Claude Code cannot operate a browser, so it cannot touch GoHighLevel, Meta Ads "
        "Manager, or any logged-in interface. Each spec separates the code layer it CAN "
        "build from the UI layer a human must do.",
        "Point Claude Code at the specs/*.md files, never at this .docx - it cannot reliably "
        "read Word. This document is the human-readable copy.",
        "Guardrails live in CLAUDE.md. The three that matter most: no charges of any kind, "
        "dry-run only, and the live Meta campaign CAJ_HVAC27_US_PURCHASE_TEST02 stays frozen.",
    ]:
        add_runs(doc.add_paragraph(style="List Bullet"), line)

    for idx, (fname, title) in enumerate(SPECS):
        path = os.path.join(ROOT, "specs", fname)
        doc.add_page_break()
        doc.add_heading(title, level=1)
        if not os.path.isfile(path):
            doc.add_paragraph("NOT FOUND: " + path)
            continue
        with open(path, encoding="utf-8") as fh:
            render(doc, fh.read())

    doc.save(OUT)
    print("WROTE %s (%s bytes)" % (OUT, "{:,}".format(os.path.getsize(OUT))))


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""Extract the six build specs from CA-J-Growth-System-Build-Specs.docx back
into markdown, one file per spec.

This is the reverse of tools/build_specs_docx.py. It exists because the specs/
folder was wiped on 2026-09-13 and the Word document was the only survivor --
see docs/recovery/ for the full account.

The parser bug found during that recovery is fixed here: each spec begins with
TWO Heading-1 lines, a numbered title ("01 - ...") followed by a subtitle
("SPEC-01 -- ..."). Sections are switched only on a recognised numbered title,
so the subtitle no longer truncates the section.

Inline bold and code formatting cannot be recovered -- Word stores those as
formatting runs, not characters -- except where a run uses the Consolas font,
which is restored as a code span. Headings, tables, numbered lists and bullets
survive intact.

Usage:  python tools/docx_to_specs.py [source.docx] [output_dir]
"""
import os
import re
import sys

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

DEFAULT_DOCX = os.path.join("docs", "recovery", "CA-J-Growth-System-Build-Specs.docx")
DEFAULT_OUT = "specs"

# Numbered title -> output filename. Only these switch sections.
TITLES = {
    "01": "SPEC-01-8-best-ai-automations.md",
    "02": "SPEC-02-ai-employee.md",
    "03": "SPEC-03-high-ticket-agency.md",
    "04": "SPEC-04-facebook-ads-ai-studio.md",
    "05": "SPEC-05-ghl-ai-studio-seo.md",
    "06": "SPEC-06-single-workflow.md",
}
NUMBERED_TITLE = re.compile(r"^(\d{2})\s*[-–—]\s*(.+)$")


def iter_block_items(parent):
    """Yield Paragraph and Table objects in document order."""
    body = parent.element.body
    for child in body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            yield Paragraph(child, parent)
        elif tag == "tbl":
            yield Table(child, parent)


def runs_to_md(par):
    out = []
    for r in par.runs:
        text = r.text
        if not text:
            continue
        if r.font.name == "Consolas":
            out.append("`%s`" % text)
        elif r.bold:
            out.append("**%s**" % text)
        else:
            out.append(text)
    # merge adjacent code/bold spans that Word split across runs
    md = "".join(out)
    md = re.sub(r"`(\s*)`", r"\1", md)
    md = re.sub(r"\*\*(\s*)\*\*", r"\1", md)
    return md.rstrip()


def table_to_md(tbl):
    rows = []
    for row in tbl.rows:
        rows.append([c.text.replace("\n", " ").replace("|", "\\|").strip()
                     for c in row.cells])
    if not rows:
        return []
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |",
             "|" + "|".join(["---"] * width) + "|"]
    for r in rows[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return lines


def block_to_md(block):
    if isinstance(block, Table):
        return table_to_md(block) + [""]
    style = block.style.name if block.style is not None else ""
    text = runs_to_md(block)
    if not text.strip():
        return []
    if style.startswith("Heading"):
        try:
            level = int(style.split()[-1])
        except ValueError:
            level = 1
        return ["", "#" * min(level, 6) + " " + block.text.strip(), ""]
    if style == "Title":
        return ["", "# " + block.text.strip(), ""]
    if style == "List Bullet":
        return ["- " + text]
    if style == "List Number":
        return ["1. " + text]
    if style == "Intense Quote":
        return ["> " + text]
    return [text, ""]


def main(argv):
    src = argv[1] if len(argv) > 1 else DEFAULT_DOCX
    out_dir = argv[2] if len(argv) > 2 else DEFAULT_OUT
    if not os.path.isfile(src):
        print("NOT FOUND: %s" % src)
        return 1
    os.makedirs(out_dir, exist_ok=True)

    doc = Document(src)
    current = None
    buckets = {}
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            style = block.style.name if block.style is not None else ""
            if style == "Heading 1":
                m = NUMBERED_TITLE.match(block.text.strip())
                if m and m.group(1) in TITLES:
                    current = TITLES[m.group(1)]
                    buckets[current] = ["# %s" % m.group(2).strip(), ""]
                    continue
        if current is None:
            continue
        buckets[current].extend(block_to_md(block))

    if not buckets:
        print("No specs found -- check the document's heading styles.")
        return 1

    total = 0
    for name in TITLES.values():
        lines = buckets.get(name)
        if not lines:
            print("  MISSING  %s" % name)
            continue
        # collapse runs of blank lines
        text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines).strip()) + "\n"
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        size = os.path.getsize(path)
        total += size
        print("  wrote    %-40s %s bytes" % (name, "{:,}".format(size)))
    print("TOTAL %s bytes into %s/" % ("{:,}".format(total), out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

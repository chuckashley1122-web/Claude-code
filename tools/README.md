# Tools

Helper scripts for the CA-J Growth System package. They render the playbooks and
build specs into Word documents and consolidate the package for handoff.

| Script | Purpose |
|--------|---------|
| `build_specs_docx.py` | Renders `specs/SPEC-01..06-*.md` into one Word document with real heading styles and tables. |
| `build_recovery_report.py` | Builds the recovery report, taking a **live** file inventory so every size in it is measured rather than recalled. |
| `consolidate.py` | Copies the whole package into one top-level folder, writes `MANIFEST.md`, and zips it. Copies, never moves. |
| `dbgdocx.py` | Prints paragraph counts, a style histogram, and every heading in a `.docx`. Used to debug the markdown→Word→markdown round trip. |
| `docx_to_specs.py` | The reverse of `build_specs_docx.py`: extracts the six build specs from the Word document back into `specs/*.md`. Written during the 2026-09-13 recovery, with the section-splitting bug fixed. |

## Known constraints

These scripts are committed **as they were written**, which means:

- **Paths are hardcoded** to `C:\Users\chuck\Desktop\CA&J Enterprises\...`.
  They will not run as-is outside that machine. Edit `ROOT` / `SRC` / `DESK` at
  the top of each file, or parameterize them, before running elsewhere.
- `build_specs_docx.py` reads from [`../specs/`](../specs/) but expects it under
  its hardcoded `ROOT`, not the repository root. Point `ROOT` at this repo before
  running it.
- `consolidate.py` and `build_recovery_report.py` both reference
  `tools/recover.py`, which was not part of the supplied set. `docx_to_specs.py`
  covers the half of that job that refills `specs/`; the playbook half is
  already satisfied by [`../docs/playbooks/`](../docs/playbooks/).
- `docx_to_specs.py` is the exception to the hardcoded-path rule — it takes
  optional source and output arguments and defaults to the paths in this
  repository, so it runs as-is:

  ```bash
  python tools/docx_to_specs.py
  ```
- Requires `python-docx`. Everything else is standard library.

## Why the recovery report exists

On 2026-09-13 the `caj-growth-system` project folder was wiped during a build
session — specs, playbooks, tools, and guardrail files — leaving only a Word
document copied minutes earlier. Because the specs had been written into Word
with genuine heading styles and real tables, they could be parsed back into
markdown rather than retyped. The original `.docx` playbooks were untouched and
remain authoritative. Inline formatting (bold, code spans) did not survive the
round trip; headings, tables, numbered steps, and body text did.

The lesson the report encodes: keep the markdown as the source of truth, keep a
measured inventory, and mark anything unverifiable as `NEEDS_EVIDENCE` instead of
filling the gap.

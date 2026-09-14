# Recovery

The two Word documents kept here are the human-readable copies of the package.

| File | What it is |
|------|------------|
| `CA-J-Growth-System-Build-Specs.docx` | All six build specs in one document, with real Word heading styles and tables. 142,062 bytes. This is the file that survived the 2026-09-13 wipe and made reconstruction possible. |
| `CA-J-Growth-System-RECOVERY-REPORT.docx` | The account of what was lost, what survived, how it was recovered, and what the recovery cost in fidelity. |

**Do not point a coding agent at these.** Word files do not read reliably — that
is the entire reason the markdown in [`../../specs/`](../../specs/) and
[`../playbooks/`](../playbooks/) exists. Use those.

## What happened, in short

On 2026-09-13 the `caj-growth-system` project folder was wiped during a build
session. Lost: the guardrail file, the README, the run script, all six build
specs, all six extracted playbooks, and the tools folder. The cause was never
determined; no user action caused it. It occurred within about three minutes of a
write attempt to a protected agent-instruction file.

What survived was a single Word document copied minutes earlier. Because the
specs had been written into Word with genuine heading styles and real tables
rather than flattened text, they could be parsed back into markdown instead of
retyped. The original `.docx` playbooks in OneDrive were untouched and remain
authoritative.

A parser bug surfaced during the recovery and is fixed in
[`../../tools/docx_to_specs.py`](../../tools/docx_to_specs.py): each spec begins
with *two* Heading-1 lines — a numbered title and a `SPEC-0N —` subtitle. The
first parser treated the subtitle as the end of the section and dropped
everything after it, producing six empty files. Sections now switch only on a
recognised numbered title.

Nothing was invented to fill gaps. Values that could not be verified during
recovery are marked `NEEDS_EVIDENCE` rather than guessed.

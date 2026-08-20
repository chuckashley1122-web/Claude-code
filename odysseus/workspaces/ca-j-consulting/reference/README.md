# Reference sources — ca-j-consulting

General reference material: definitions, standards, process explanations, rules.
**Tracked in Git**, because it should be reviewed, versioned, and improved over
time like any other source file.

This is deliberately separate from `../approved/`, which holds real business
documents — brand guidelines, product and pricing data, case studies, client
material — and is gitignored so none of it is ever committed.

| | `reference/` | `approved/` |
|---|---|---|
| Contains | General knowledge, rules, standards | Real business documents |
| In Git | Yes | No, never |
| Contains PII | Never | Must still never contain PII |
| Who writes it | Anyone, reviewed before approval | The business |

Both are governed identically by the knowledge manifest: **a file here is not
used until its manifest entry says `approved: true` with a named approver.**
Being committed is not approval.

Files marked `status: drafted` in the manifest were drafted by Claude Code and
have not been checked by a human. Each carries a "Verify before approval"
section listing what to confirm. Work through it before flipping `approved`.

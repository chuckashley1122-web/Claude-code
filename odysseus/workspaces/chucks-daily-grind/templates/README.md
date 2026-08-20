# Templates — chucks-daily-grind

Skeletons for the business documents this workspace needs. **Tracked in Git**;
the filled-in versions are not.

## How to use one

1. Copy it into `../approved/` under the filename the manifest expects.
2. Fill it in. Delete every `[bracket]` — unreplaced brackets are read by the
   agent as literal text.
3. In `../knowledge-manifest.yml`, set that source's `approved: true` and put
   your name in `approver`.
4. Re-index the workspace in Odysseus.

`../approved/` is gitignored, so the completed documents never leave your
machine.

## Why the agent needs these

The skills are built to refuse unsourced claims. With an empty catalogue,
`product-copy-and-email` produces flagged placeholders rather than invented
origin detail — correct behaviour, but not useful copy. These files are what
turn refusal into output.

Start with whichever unblocks the work you actually want to do first. A partly
filled file is more useful than none, and the placeholders will tell you exactly
what is still missing.

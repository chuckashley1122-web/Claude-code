---
description: Read the data folder and write today's CEO report — the morning briefing.
---

Run the `ceo` agent against whatever is currently in `data/`. Do not run the
department agents first — this is a read of the current state, not a refresh.

If some department files are stale or were never written, the report says so per
department. Do not fill in a quiet department with plausible-sounding activity;
"Marketing: not updated since Tuesday" is the useful output.

When it's done, render the full report in the conversation so I can read it
without opening the file, and lead with the single most important thing in it.

$ARGUMENTS

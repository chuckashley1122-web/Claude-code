---
description: Run a single department agent — sales, marketing, support, finance, or operations.
argument-hint: sales | marketing | support | finance | operations
---

Run the single department agent named in the arguments below, and only that one.

Delegate to the matching subagent, let it write its own file in `data/`, then
report back: what it wrote, what it flagged, and what it needs from me. Don't
run the CEO agent afterwards unless I ask — use `/ceo-report` for that.

If no department is named, ask which one rather than guessing. If the named
agent depends on input I haven't provided this session (Support needs customer
questions, Finance needs financial data), say what's missing before running.

Department: $ARGUMENTS

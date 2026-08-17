---
description: Run all six agents in order (Sales → Marketing → Support → Finance → Operations → CEO), pausing after each.
---

Run the full business cycle. Order matters — each agent reads what the previous
ones wrote — so do not parallelize this.

1. `sales` → writes `data/1-sales.md`
2. `marketing` → reads `1-sales.md`, writes `data/2-marketing.md`
3. `support` → writes `data/3-support.md`
4. `finance` → writes `data/4-finance.md`
5. `operations` → reads the department files, writes `data/5-operations.md`
6. `ceo` → reads 1–5, writes `data/6-ceo-report.md`

After each agent finishes, give me a two-line summary of what it wrote and
anything it flagged, then continue to the next one. Stop and ask if an agent
reports it's blocked — for example `business.md` is still the blank template, or
Finance has no data to work from. A blocked department is fine; a department
that invents its way past being blocked is not.

Agents 3 and 4 depend on inputs I supply. If I haven't given you customer
questions or financial data this session, say so and let those agents write an
honest "nothing new this run" file rather than skipping them silently.

Nothing sends, posts, or spends. Everything lands as a draft for my approval.

End with the CEO report rendered in full in the conversation.

$ARGUMENTS

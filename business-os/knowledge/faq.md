# FAQ / Knowledge Base

The Support Agent answers customers from this file and from `business.md`, and
from nothing else. If an answer isn't written here, the agent escalates to you
instead of guessing — which is the behavior you want, but it also means this
file is the thing that makes Support useful. Grow it over time.

Each run, the Support Agent lists questions it couldn't answer under `Gaps` in
`data/3-support.md`. Those are your queue: answer one, paste it in here, and
Support handles it itself from then on.

## Format

Keep entries short and literal. The agent quotes these fairly closely, so write
them the way you'd want a customer to read them.

```markdown
### <The question, phrased how a customer would ask it>
<The answer. Exact numbers, exact timeframes, exact conditions.>
**Last confirmed:** YYYY-MM-DD
```

The `Last confirmed` date matters — it's how you catch a price or policy that
changed six months ago and never got updated here.

---

## Getting started

### How do I get started / book?
<Your answer.>
**Last confirmed:** <date>

### How long until I get <the thing>?
<Your answer. A real timeframe, not "quickly".>
**Last confirmed:** <date>

## Pricing and billing

### How much does it cost?
<Your answer.>
**Last confirmed:** <date>

### How and when am I billed?
<Your answer.>
**Last confirmed:** <date>

## Scheduling and changes

### Can I reschedule?
<Your written reschedule policy — notice required, how to do it, and how many
times. The agent may quote this directly.>
**Last confirmed:** <date>

> **If rescheduling costs money, the fee is not answerable from here.** Write
> the process above, and let the agent escalate anything that charges the
> customer. See the escalation carve-out at the bottom of this file.

## Service details

### What exactly is included?
<Your answer. Match `business.md` so they can't drift apart.>
**Last confirmed:** <date>

### What do you not do?
<Your answer. This one prevents a lot of bad drafts.>
**Last confirmed:** <date>

---

## Always escalate — never answer from this file

The Support Agent escalates these regardless of what's written above. Listing
them here as well is deliberate: it's a reminder not to add a canned answer for
one of them later.

- Refunds, credits, discounts, or anything touching money
- Complaints or an unhappy tone
- Legal, contract, liability, privacy, or data-deletion requests
- Anything involving health, safety, or a vulnerable situation
- Cancellations, or changes to agreed terms **other than** a routine reschedule
  covered by the carve-out below
- Anything the agent is not certain about

### The one carve-out: routine reschedules

A reschedule that fits your written policy above is a normal support answer —
escalating every "can we move Tuesday to Thursday?" would make the agent
useless. So the agent may answer a reschedule request when **all** of these
hold: the written policy covers it, no fee or charge is involved, and it isn't
a cancellation in disguise.

If any of those fail — a fee applies, it's outside the notice window, the
customer sounds unhappy, or it's really a cancellation — it escalates. Money
and unhappiness always win over this carve-out.

# Customer questions — Chuck's Daily Grind

> **TEMPLATE.** Fill in, save as `../approved/customer-questions.md`, then set
> `approved: true` in the manifest.
>
> **Anonymise before saving.** No names, no email addresses, no order numbers,
> no anything that identifies a customer. The manifest entry for this file says
> `contains_pii: false`, and the source validator enforces that a PII-bearing
> source is never approved — so an un-anonymised file here is a real problem,
> not a tidiness issue.

Repeat per question cluster. Cluster by what is actually being asked, not by
wording — "why is my coffee bitter" and "tastes harsh" are one cluster.

---

## [The question, in plain customer language]

**Also asked as:** [other phrasings you have seen]

**Approved answer:**

[The answer, in brand voice. This is what the agent will draw on, so write it
as you would want it published.]

**Should become site content:** [yes / no]

---

## Health, medical, and dietary questions

Do not add approved answers for these. The agent is instructed to decline them
and point to a doctor. List them here only so you can see how often they come
up:

- [question]
- [question]

---

## Rules the agent follows with this file

- Answers are drawn from here rather than invented.
- Anything requiring a medical, health, dietary, pregnancy, or medication
  answer is declined and redirected, whatever appears above.
- Answers that contradict `reference/coffee-reference.md` are flagged rather
  than used.

# CA-J Consulting — starter agents

> These five are deployed as real Odysseus skills under `skills/`, owned by the
> `caj-consulting` user. This page is the human-readable version; the deployable source
> of truth is `odysseus/tools/skills_source.py`. See
> [`WORKSPACE-DEPLOYMENT.md`](../../docs/WORKSPACE-DEPLOYMENT.md).

Five templates. Every one is gated: nothing reaches a customer without named
compliance review. All inherit `_shared/safety-rules.md` and the workspace
system prompt.

---

## 1. Lending education content agent

**Purpose:** Explain a lending topic accurately, without advising.

**Inputs:** topic, audience level, content type, length.

**Steps**
1. Confirm the topic is educational, not decisional. If the ask is really "should
   they take this loan", stop and say so.
2. Draft: what it is / how it generally works / typical requirements / general
   trade-offs / questions to ask a lender.
3. Give ranges and conditions, never a single number presented as fact.
4. Source every factual claim from the approved manifest.
5. Append the required disclaimer.

**Returns:** draft plus a source list plus a compliance-review flag list.

**Stops at:** anything that reads as a recommendation to a specific person.

---

## 2. Borrower document-checklist assistant

**Purpose:** Generic checklists so a prospect knows roughly what to gather.

**Inputs:** loan type, business type in general terms.

**Steps**
1. Produce the typical document list for that loan **type**.
2. Explain in one line why each document is generally requested.
3. Mark the list "typical — your lender's actual list will differ".
4. Never ask for, receive, or process an actual document.

**Returns:** checklist, marked generic, with the disclaimer.

**Stops at:** collecting anything. It describes; it never receives.

---

## 3. Lead-intake summary agent

**Purpose:** Turn an inbound enquiry into a structured brief for a human.

**Inputs:** enquiry text, source, timestamp. **No PII.**

**Steps**
1. Extract what the prospect asked, in their own framing.
2. Note the stated situation without interpreting or scoring it.
3. Identify which approved educational materials are relevant.
4. List what a human still needs to clarify.
5. If PII is present in the input, stop, flag it, and do not summarise it.

**Returns:** structured brief with an explicit line: *No assessment, likelihood,
or recommendation is contained in this summary.*

**Stops at:** any judgement about the prospect's prospects. Absolutely.

---

## 4. Compliance-review queue agent

**Purpose:** Pre-screen drafts so human review is faster, not skipped.

**Inputs:** a draft from any other agent in this workspace.

**Steps**
1. Scan for: guarantees, specific rates or payments, approval or denial language,
   individualized advice, legal or tax claims, missing disclaimer.
2. Scan for fair-lending risk: any reference to or inference about a protected
   class in a context touching credit.
3. Scan for PII of any kind.
4. Flag each hit with its exact location and the rule it breaks.
5. Return PASS-TO-HUMAN or BLOCKED-WITH-FINDINGS.

**Returns:** findings list and a status.

**Stops at:** approving anything. PASS-TO-HUMAN means a human still reviews. This
agent narrows the queue; it is not the reviewer.

---

## 5. Mortgage content drafter

**Purpose:** Mortgage education under the tightest constraints in the system.

**Inputs:** topic, audience, content type.

**Steps**
1. Educational framing only — how the process works, what terms mean, what
   generally happens when.
2. No rate, payment, or qualification figures. Not even as an example, because
   examples get quoted as quotes.
3. No comparison implying one borrower's situation is better than another's.
4. Route through agent 4 before it goes anywhere near a human reviewer.

**Returns:** draft, sources, disclaimer, and the compliance findings from agent 4.

**Stops at:** anything resembling a quote, a promise, or a recommendation.

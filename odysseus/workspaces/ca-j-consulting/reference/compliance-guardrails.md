# Compliance guardrails — CA-J Consulting

**Status:** DRAFT. Not yet approved. `approved: false` in the knowledge manifest.

> **This document was drafted by Claude Code from general knowledge of the US
> regulatory landscape. It is not legal advice and it has not been reviewed by
> counsel.** It is a starting point for a qualified compliance professional or
> an attorney licensed in Texas to correct, cut, and approve. Until that review
> happens, treat every rule below as provisional and every citation as something
> to verify rather than rely on. A "verify before approval" list is at the end.

This is the source of truth the `compliance-review-screen` skill checks against,
and every other CA-J Consulting skill routes through it.

---

## 1. The distinction everything hangs on

CA-J Consulting **educates**. It does not originate, broker, advise, or decide.

| Educating | Advising or originating |
|---|---|
| "SBA 7(a) loans are generally used for..." | "You should get an SBA 7(a)." |
| "Lenders typically look at time in business, revenue, and credit." | "With your numbers you'd qualify." |
| "Rates vary by lender, borrower, and market conditions." | "You're looking at around 9%." |
| "Here are the documents lenders usually request." | "Send me your tax returns and I'll review them." |
| "Here's what a term sheet contains." | "This term sheet is a good deal, take it." |

The left column is content. The right column is regulated activity that requires
licensing, creates liability, or both. Everything this workspace produces lives
in the left column.

---

## 2. Two regulatory regimes, and why the difference matters

The rules are **not the same** for the two halves of this business. Getting this
backwards is the most likely serious error.

### Business-purpose credit (commercial lending)

- **TILA / Regulation Z generally does not apply.** Reg Z exempts credit
  extended primarily for a business, commercial, or agricultural purpose
  (12 CFR 1026.3(a)). So the consumer-credit advertising machinery — triggering
  terms, APR disclosure format — is generally not triggered by business-loan
  content.
- **ECOA / Regulation B does apply.** Reg B covers business credit, with
  modified notice and record-retention requirements. Anti-discrimination and the
  prohibition on *discouraging* applicants apply in full.
- **UDAP / UDAAP applies.** FTC Act §5 and Dodd-Frank §1031 reach deceptive or
  unfair conduct regardless of purpose.
- **State law applies.** Texas has its own finance code provisions, and several
  states now impose commercial-financing disclosure requirements. Verify current
  Texas requirements.

Practical effect: business-lending content has more room on *format*, and none
at all on *honesty or discrimination*.

### Consumer mortgage credit

Assume the strictest reading. Mortgage content is governed by, at minimum:

- **TILA / Regulation Z** — including the advertising rules in §1026.24.
- **Regulation N, the MAP Rule** (12 CFR 1014) — prohibits misrepresentation in
  commercial communications about mortgage credit. It applies broadly, including
  to parties who are not lenders.
- **Fair Housing Act** — residential real-estate-related transactions, including
  advertising.
- **RESPA** — settlement services, referrals, and fees.
- **SAFE Act and Texas licensing** — who may take an application or offer or
  negotiate terms.

Practical effect: for mortgage content, **no figures at all** is the safe and
adopted position. See §4.

---

## 3. Anti-discrimination — the hardest line

### Prohibited bases

**ECOA / Regulation B** (12 CFR 1002.2(z)) — race, color, religion, national
origin, sex, marital status, age (provided the applicant has capacity to
contract), receipt of income from a public assistance program, and the good-faith
exercise of rights under the Consumer Credit Protection Act. The CFPB has
interpreted "sex" to include sexual orientation and gender identity.

**Fair Housing Act** (42 USC 3604, 3605) — race, color, religion, sex, familial
status, national origin, and disability. Note that FHA adds **familial status**
and **disability**, which ECOA does not name.

Use the union of both lists for any mortgage or housing-related content.

### The rule that actually catches marketing

Regulation B §1002.4(b) prohibits a creditor from making any oral or written
statement that would **discourage** a reasonable person from applying. This is
not limited to refusals. Content, imagery, tone, and targeting can all
discourage. Fair Housing Act §3604(c) similarly reaches discriminatory
statements and advertising.

So the compliance question is never only "did we refuse anyone." It is: **would
this content discourage a reasonable person in a protected class from applying?**

### Operating rules

1. Never reference or infer a protected characteristic in content touching
   credit, product suitability, or likelihood of approval.
2. No proxies. Neighborhood, ZIP code, school district, "this kind of area,"
   language, surname, and national-origin-adjacent descriptors can all function
   as proxies for a protected basis.
3. No steering. Do not suggest that a particular group should look at a
   particular product.
4. Comparable information regardless of who is asking. The same question gets
   the same answer.
5. Example borrowers must be neutral. If an illustration names an age, a marital
   status, a family situation, or an ethnicity, remove it — it is doing no work
   and creates exposure.
6. Imagery counts as content. Photo selection in marketing has been the subject
   of fair-lending findings.

---

## 4. Advertising rules

### Adopted position: no figures in customer-facing content

Whatever the regime technically permits, this workspace states **no rate, no
payment, no term, no down-payment amount, and no finance charge** in
customer-facing content. Not as a fact, not as an illustration, not as an
example, not as a range.

The reason is practical, not just legal: an example figure gets quoted back as a
quote. "On a $300k loan at 6%..." is read as an offer by the person reading it,
regardless of the label around it.

### Why this matters most for mortgage — triggering terms

Under Reg Z §1026.24(d), if a closed-end consumer credit ad states any of:

- the amount or percentage of any down payment,
- the number of payments or the period of repayment,
- the amount of any payment, or
- the amount of any finance charge,

then the advertisement must **also** disclose the down payment terms, the terms
of repayment, and the annual percentage rate — spelled out, and with a statement
that the rate may increase if it can.

These are the **triggering terms**. Stating one drags a full disclosure set into
the piece. Note that stating the APR alone is not a triggering term, and general
statements like "affordable monthly payments" are generally not triggering
because they contain no amount. Verify the current text of §1026.24 before
relying on any of this.

Also under §1026.24(c): if content states a rate of finance charge, it must be
stated as an **"annual percentage rate,"** using that term.

By stating no figures at all, this workspace never reaches these rules. That is
the entire point of the adopted position.

### The MAP Rule — misrepresentation

Regulation N (12 CFR 1014.3) prohibits material misrepresentation in commercial
communications about mortgage credit, across a long list of subjects including
interest rates, the existence or amount of fees, the terms or amount of
payments, the existence of any government affiliation or endorsement, and
whether the consumer is preapproved or guaranteed to qualify.

It reaches advertising by parties who are not the lender. Assume it applies to
CA-J Consulting mortgage content.

### Never say

Absolute, in both regimes:

- "Guaranteed approval", "you're approved", "pre-approved", "you qualify"
- "Everyone qualifies", "no credit check" (where untrue), "bad credit OK — guaranteed"
- "Rates as low as X" — a figure, and it invites the triggering-terms analysis
- "Lock in before rates rise" — a prediction and an urgency tactic
- "Government-backed" phrasing that implies government affiliation or endorsement
- "Free" for anything with a cost, condition, or contingency
- Any claim about a specific lender's decision, timeline, or standards
- Any implication that the reader in particular is likely to qualify

### Approach with care

- "Fast", "quick", "same-day" — verify against reality, and attach conditions
- "Up to $X" — implies availability that may not be general
- "No fees" — almost always incomplete
- Testimonials — generally require substantiation and, in some contexts,
  disclosure that results are not typical
- Comparisons to named competitors — substantiation, and defamation exposure

---

## 5. Licensing boundaries

**SAFE Act and Texas mortgage licensing.** An individual who takes a residential
mortgage loan application, or offers or negotiates terms of a residential
mortgage loan, for compensation or gain, generally must be a licensed mortgage
loan originator. Texas administers this through the Department of Savings and
Mortgage Lending.

General education does not require an MLO license. Taking an application,
quoting terms to an individual, or negotiating does. CA-J Consulting content
stays on the education side of that line, and no content should invite an
individual to begin an application through this workspace.

**RESPA §8** prohibits giving or accepting a fee, kickback, or thing of value
for the referral of settlement service business involving a federally related
mortgage loan. If any part of the business involves referral relationships,
compensation arrangements need counsel review before any content describes,
promotes, or implies them.

**Verify:** whether CA-J Consulting itself holds, or needs, any Texas license
for its business-lending activity. That answer changes what this workspace may
publish, and it is not assumed here.

---

## 6. Data and privacy

- **No PII in this workspace.** SSN, DOB, driver's license, bank statements, tax
  returns, credit reports, loan applications, account numbers. See
  `_shared/safety-rules.md` rules 15–17.
- **FCRA.** Credit report data may only be obtained and used for a permissible
  purpose. Prescreened offers carry firm-offer-of-credit and opt-out notice
  requirements. This workspace touches none of it — and must not start to
  without counsel review.
- **Adverse action.** If any process here ever contributes to a decision to
  decline or offer less favorable terms, ECOA adverse action notice
  requirements attach. This is a strong reason the workspace produces no
  assessments at all.
- **Outreach.** TCPA governs calls and texts, including consent and revocation.
  CAN-SPAM governs commercial email. This workspace drafts; it does not send,
  and consent status is a human's responsibility before anything goes out.

---

## 7. Required disclaimer

Every customer-facing draft ends with this, verbatim:

> This is general educational information, not financial, legal, or tax advice.
> It is not an offer, a commitment to lend, or a guarantee of approval. Terms,
> rates, and eligibility vary by lender and by borrower. Consult a qualified
> professional about your specific situation.

The disclaimer does not cure a violation. Content that quotes a rate is not
fixed by a disclaimer underneath it. The disclaimer is a floor, not a defense.

---

## 8. Reviewer checklist

Used by `compliance-review-screen` and by the human reviewer.

**Blocking — any hit stops the deliverable**

- [ ] No approval, denial, or pre-qualification, stated or implied
- [ ] No guarantee of rate, amount, term, timeline, or outcome
- [ ] No rate, payment, down payment, term length, or finance charge figure — including in examples
- [ ] No individualized advice to a named or identifiable person
- [ ] No legal or tax advice
- [ ] No claim of government affiliation or endorsement
- [ ] No urgency or scarcity framing on a financial product
- [ ] Disclaimer present, verbatim

**Fair lending**

- [ ] No protected characteristic referenced or inferred
- [ ] No geographic, linguistic, or demographic proxy
- [ ] No steering toward or away from a product by group
- [ ] Example borrowers carry no protected-class signal
- [ ] Content would not discourage a reasonable person in a protected class from applying

**Accuracy**

- [ ] Every factual claim traces to an approved source
- [ ] No invented statistic, program name, requirement, or regulation
- [ ] Program details verified current — SBA and agency terms change
- [ ] Uncertainty stated where it exists

**Data**

- [ ] No PII in input or output
- [ ] No borrower name paired with financial detail
- [ ] Nothing sourced from another CA&J business

---

## 9. Escalate to a human — always

- Any question about a specific person's eligibility, terms, or options
- Any request to review an actual document, application, or term sheet
- Anything touching a live transaction
- Any request for a referral to a specific lender
- Anything a reader could reasonably act on financially
- Any regulation or program detail not confirmed by an approved source

---

## 10. Verify before approval

This document is a draft. Before it is marked `approved: true`, a qualified
reviewer should confirm each of these — several are the kind of thing that
changes, and one wrong detail here propagates into every piece of content the
workspace produces:

1. **Every citation.** 12 CFR 1026.24 (triggering terms and rate disclosure),
   12 CFR 1026.3(a) (business-purpose exemption), 12 CFR 1014 (MAP Rule),
   12 CFR 1002.2(z) and 1002.4(b) (Reg B bases and discouragement),
   42 USC 3604/3605 (FHA), 12 USC 2607 (RESPA §8). Confirm current text and
   that each says what §§2–5 claim it says.
2. **The business-purpose exemption**, and whether any CA-J Consulting activity
   involves consumer-purpose credit that would pull Reg Z back in.
3. **Texas-specific requirements** — Finance Code, SML mortgage rules, OCCC, and
   any state commercial-financing disclosure law now in force.
4. **Licensing status** — what CA-J Consulting holds, and what its actual
   activities require.
5. **Whether any referral or compensation arrangement exists** that RESPA §8 or
   state law would reach.
6. **The disclaimer text**, approved as written by counsel.
7. **Whether the no-figures position should be relaxed** for business-lending
   content, and if so, exactly where the new line sits.
8. **Whether definitional illustrations count as figures.** §4 says no figures
   "not as an illustration, not as an example." Read strictly, that also bars
   explaining what a factor rate *is* by showing one — see the factor rate entry
   in `lending-glossary.md`, which is currently the only such case in the
   reference set. Removing it would weaken the most useful consumer-protection
   explanation in the glossary; keeping it is a narrow, deliberate exception for
   mechanism rather than price. **Decide explicitly and record the decision
   here** — this is the kind of ambiguity that otherwise gets resolved
   differently by every person who writes a draft.

Record the reviewer's name and the review date in the knowledge manifest when
this is approved.

# Six demonstration questions

Source: playbook lines 175-181 (demo questions) and 182-183 (expected evidence).
Run these against the private demo agent, and again against the production agent
using production facts (source step 30). Running them is a human, logged-in task in
the GoHighLevel agent test interface or widget; this file only defines them.

Fill `[verified city]` with a city that appears in the verified Business_Facts
"service area" row, and `[service the company does not offer]` with a service from
the verified "excluded services" row. Never fill them from guesswork.

| # | Question asked to the agent | Expected behaviour |
|---|---|---|
| 1 | Do you serve [verified city]? | Answers from the verified service-area fact only. |
| 2 | My AC stopped cooling tonight. What can I do to arrange service? | Collects service, location, name, callback number one question at a time; follows the owner-approved after-hours or emergency procedure; gives no repair instructions. |
| 3 | How much will my repair cost? | No invented figure. States the team must confirm and creates a recorded follow-up (pairs with acceptance test T02). |
| 4 | Can you book me tomorrow? | Uses the configured scheduling action; confirms only after the action returns success; otherwise records a request and says so (T03/T04). |
| 5 | I want to speak to a person. | Follows the handoff rule; if transfer fails, collects callback details and creates the follow-up task; never claims a dispatcher received it unless the action succeeded (T05). |
| 6 | Do you offer [service the company does not offer]? | Deliberately unanswerable from the offered-services list: the agent must say the business does not list that service or that the team must confirm. It must not say yes. |

## Evidence to capture (human)

- One text transcript and one voice test log per run (source line 183).
- Any failed question: correct the knowledge source or action mapping, then rerun
  that question before showing the prospect.
- Store the evidence location in `records/Test_Results.csv` through
  `scripts/run_test_checklist.py`, not by hand-editing the CSV.

# WF04 Knowledge maintenance

Source: playbook line 252 and step 50 (line 356). **Implementation lives in the
GoHighLevel workflow builder (or task scheduler) and is human-executed.** Nothing in
this repository creates or edits a workflow.

| Field | Specification |
|---|---|
| Trigger | Weekly schedule. |
| Filter | Active clients only (opportunity stage **Active**). |
| Dedupe key | Client location ID plus ISO week (one review task per active client per week). |
| Action | Create a weekly internal review task per active client: review unanswered questions and failed actions, obtain verified answers from the customer, update the knowledge base, and retest the affected scenario. |
| Notification destination permission | Internal task to the account owner only. |
| Failure / review route | Facts the customer cannot confirm stay NEEDS_EVIDENCE in `records/Business_Facts.csv` and are added to `records/Blockers.csv`. Do not assume conversations automatically retrain the assistant. |
| Verified by | Rerun of the six demo questions (`agent/demo-questions.md`) and acceptance test T01 after each update. |

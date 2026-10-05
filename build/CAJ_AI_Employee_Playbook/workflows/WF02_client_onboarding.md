# WF02 Client onboarding

Source: playbook line 250. **Implementation lives in the GoHighLevel workflow builder
and is human-executed.** Nothing in this repository creates or edits a workflow.

| Field | Specification |
|---|---|
| Trigger | Verified successful purchase of the specified recurring product (product id recorded in `records/Asset_Register.csv`). A success-page visit is never a trigger and never proof of payment. |
| Filter | Subscription is active and the paying customer matches the contact and opportunity. |
| Dedupe key | Subscription ID. One onboarding task set per subscription ID, ever. |
| Action | Create one onboarding task set (intake, provisioning, knowledge base, routing, tests) and update the opportunity to **Paid and onboarding**. |
| Notification destination permission | Internal tasks to the onboarding owner only. No customer message unless separately authorized. |
| Failure / review route | Failed, partial, refunded, or ambiguous payment events (customer mismatch, missing subscription, duplicate subscription ID) go to a human review task. Never activate as paid on an ambiguous event. |
| Verified by | Acceptance test T10 plus the processor's supported test procedure in test mode (source step 24). |

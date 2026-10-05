# WF03 Human follow-up

Source: playbook line 251. **Implementation lives in the GoHighLevel workflow builder
and is human-executed.** Nothing in this repository creates or edits a workflow.

| Field | Specification |
|---|---|
| Trigger | The AI agent's configured handoff action fires (see `agent/handoff-rule.md`). |
| Filter | Only handoffs from the client's own location and agent; ignore test records outside a test run. |
| Dedupe key | Interaction ID (conversation ID or call ID). One task per interaction ID. |
| Action | Attach contact, summary, urgency, and the conversation or call ID; create a task for the confirmed dispatcher. |
| Notification destination permission | Use only notification destinations the owner authorized in writing (recorded in `agent/handoff-rule.md`). |
| Failure / review route | Unresolved tasks are marked visibly for review; a handoff with no confirmed dispatcher goes to the owner's review queue. The agent never tells the customer a dispatcher received it unless the action succeeded. |
| Verified by | Acceptance tests T05, T06, and T10. |

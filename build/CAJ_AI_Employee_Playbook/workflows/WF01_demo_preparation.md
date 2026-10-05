# WF01 Demo preparation

Source: playbook line 249. **Implementation lives in the GoHighLevel workflow builder
and is human-executed.** Nothing in this repository creates or edits a workflow.

| Field | Specification |
|---|---|
| Trigger | A new appointment is created in the agency demo calendar (CAJ HVAC AI Demo, calendar id recorded in `records/Asset_Register.csv`). |
| Filter | Exclude cancelled appointments and test records (synthetic contacts tagged as test). |
| Dedupe key | Appointment ID. A second event with the same appointment ID must not create a second opportunity update or task. |
| Action | Find the existing opportunity for the contact (or update the same one; never create a duplicate), move it to **Demo booked**, and create a demo preparation task due before the meeting start time. |
| Notification destination permission | The preparation task is assigned to Chuck or the confirmed salesperson only. No customer-facing message is sent by this workflow. |
| Failure / review route | If no matching contact or opportunity is found, or the appointment ID was already processed, create an internal review task instead of acting. |
| Verified by | Acceptance test T10 (duplicate events) and a synthetic booking (source step 12). |

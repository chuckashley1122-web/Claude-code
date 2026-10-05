# Runbook: GoHighLevel account confirmation and snapshot

Covers source steps 01, 03, 26, 27. **Human-only.** GoHighLevel is UI-only; the
coding agent cannot log in, create subaccounts, or request/apply snapshots. GHL menu
paths in the source are "navigation targets to confirm in the live account" (source
line 11), not verified UI truth.

Approval gate: `REQUIRE_HUMAN_APPROVAL_FOR_GHL = True`.

## A. Confirm the target account (step 01)

1. Log in to the authorized GoHighLevel agency account.
2. Open the build location and confirm on screen that the location ID is exactly
   `UWc5vKBgFVPdxNTRAy2s` (case-sensitive) and the name is "CA&J Enterprises".
   The location ID printed in the source playbook is stale and must not be used.
3. Record in `records/Build_Log.csv` (step 01): account_id, timestamp (UTC),
   evidence = screenshot path.
4. If the ID on screen differs, stop. Record a REQUIRED blocker in `records/Blockers.csv`.

## B. Inventory access and training assets (step 03)

1. Check permissions for subaccounts, snapshots, websites, AI agents, knowledge bases,
   calendars, payments, workflows, and phone settings. Record each as available /
   missing in the Build_Log.
2. Locate the licensed HVAC pack in Chuck's authorized training access. Record its
   name, version, and usage rights in `records/Asset_Register.csv` (asset_type
   `snapshot`). If missing, record a blocker. Never substitute an unrelated snapshot.
3. Missing source materials (seven-page SOP, previous demo workshop, niche scripts,
   outbound email SOP, phone registration SOP, lab account request form): record the
   link and version when found; never reconstruct their contents.

## C. Create the customer account (step 26) - only after a verified sale

1. Confirm the subscription is active (WF02 evidence). No paid status, no account.
2. Use the agency's subaccount creation process or the lab's account request form.
   Enter the customer's exact business details and request the correct HVAC snapshot.
3. If a customer account already exists, inspect it first; do not import a snapshot
   over live assets without a written, scoped change plan.
4. Record: new location ID, snapshot name and version, provisioning owner, timestamp.
   Spend: subaccount and snapshot costs are NEEDS_EVIDENCE and need approval
   (`docs/COST-AND-APPROVALS.md`).

## D. Audit the imported snapshot (step 27)

1. Review workflows, calendars, custom values, forms, AI agents, knowledge bases, and
   phone assignments.
2. Disable inherited outbound sequences and triggers during staging.
3. Replace template names, URLs, phone numbers, emails, and business hours; remove
   example customer facts.
4. Confirm review, referral, and reactivation workflows stay outside the initial scope.
5. Save screenshots or an export sufficient to reverse the changes; record the path.

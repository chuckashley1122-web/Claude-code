# UI work order 003-A: Build the high-ticket HVAC sales system in GoHighLevel

**Spec:** SPEC-03 (High-Ticket Agency). **Build root:** `build/03-high-ticket/`. **Owner:** Chuck Ashley.
**Why a human:** GoHighLevel needs a logged-in browser; the build is code-only and touched nothing in GHL.

## Before you start

1. Run `python tools/build_all.py` inside `build/03-high-ticket/` so `out/` and `ui-tasks/` are current.
2. Open GHL location `UWc5vKBgFVPdxNTRAy2s` (exact case). Do not use any other location ID from the source playbook.
3. Do not modify the existing pipeline `CA&J Demo - Lead Pipeline` or the existing HVAC Review System funnel.

## Steps

Follow `build/03-high-ticket/ui-tasks/GHL-BUILD-CHECKLIST.md` item by item. Each item lists the object, field, exact value
and a "verify by" check. In summary:

1. Inventory existing calendars, pipelines, forms, workflows, payment products and connected Pages; record IDs.
2. Create pipeline `CAJ-HT-HVAC-Sales` with its 11 stages, and the 21 contact custom fields.
3. Create calendar `HVAC Growth Strategy Session` (45 min, America/Chicago if confirmed, 3-day horizon, 2-hour notice, 15-minute buffers).
4. In Settings > Integrations, confirm the Facebook Page and lead form, set new leads only, map fields per `out/field_map.json`.
5. Build workflows 01-Intake, 02-Unbooked, 03-Booked, 04-Outcome from `out/workflows/`, and leave every one UNPUBLISHED.
6. Insert message fields with the account field picker (bracketed tokens are placeholders) and send test previews.
7. Run test cases T01-T14 with designated test contacts and record evidence; update the test log.

## Approval gates

Creating a payment product, any GHL upgrade and any SMS fees: REQUIRES EXPLICIT HUMAN APPROVAL.

## Done when

Every checklist item is verified by its "verify by" line, all workflows are still unpublished, and the T-case evidence is saved.

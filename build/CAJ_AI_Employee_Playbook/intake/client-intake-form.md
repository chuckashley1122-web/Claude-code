# Client intake form (production)

Source: playbook line 208 (step 28). The owner or an authorized manager answers every
item. Each answer needs a source (owner written confirmation with date, or a URL on
the business's own website). Unknown answers stay blank and are tracked as
NEEDS_EVIDENCE; nothing is guessed. A filled form can be checked with:

    python3 scripts/validate_records.py --intake path/to/filled-intake.json

(the JSON shape is defined by `intake/intake.schema.json`).

| # | Field (JSON key) | Question for the owner |
|---|---|---|
| 1 | `business_name` | Exact legal or trading name the assistant should use. |
| 2 | `main_phone` | Advertised main phone number. |
| 3 | `timezone` | Business timezone (default assumption: America/Chicago; confirm). |
| 4 | `hours` | Owner-confirmed business hours for each day. |
| 5 | `holidays` | Holiday closures and holiday coverage. |
| 6 | `covered_areas` | Covered ZIP codes or cities. |
| 7 | `services_offered` | Services offered. |
| 8 | `services_excluded` | Services not offered. |
| 9 | `approved_price_statements` | Exact price statements the assistant may repeat, if any. Leave empty if none; the assistant then never states a price. |
| 10 | `escalation_instructions` | Emergency and escalation instructions (who, how, when). |
| 11 | `dispatcher_contact` | Dispatcher or human-transfer destination. |
| 12 | `website_admin_access` | Who grants website admin access, and how (no passwords in this form). |
| 13 | `calendar_owner` | Who owns the booking calendar. |
| 14 | `phone_provider` | Current phone provider (carrier or VoIP). |
| 15 | `booking_permission` | May the assistant create confirmed appointments, or only requests? (`confirmed_appointments` or `requests_only`) |
| 16 | `handoff_recipient` | Who receives and acts on handoffs. |
| 17 | `handoff_response_time` | How quickly they can realistically respond. |
| 18 | `confirmed_by` / `confirmed_date` | Name of the person confirming and the date. |

Never collect card numbers, security codes, or passwords in this form. Payment is
entered by the client directly in the secure checkout.

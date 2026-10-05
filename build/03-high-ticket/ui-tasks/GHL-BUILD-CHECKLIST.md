# GHL build checklist

Target location for every item: `UWc5vKBgFVPdxNTRAy2s` (exact case). Every workflow stays unpublished. Mark items done only in your own tracker after verifying.

### GHL-01 Sub-account: Location ID

- Object: Sub-account
- Field: Location ID
- Value: UWc5vKBgFVPdxNTRAy2s
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Browser URL contains /location/UWc5vKBgFVPdxNTRAy2s/ in exact case; record the displayed business name
- Status: Not started

### GHL-02 Source playbook location reference: Location ID

- Object: Source playbook location reference
- Field: Location ID
- Value: Do NOT use the source playbook's location ID (it is DISALLOWED_LOCATION_ID in config/constants.py)
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: No object, note or workflow references that ID
- Status: Not started

### GHL-03 Existing objects inventory: Calendars, pipelines, forms, workflows, payment products, connected Pages

- Object: Existing objects inventory
- Field: Calendars, pipelines, forms, workflows, payment products, connected Pages
- Value: Record each object name + ID; duplicate before materially changing any live asset
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Inventory saved to config/decision_log.jsonl by the operator
- Status: Not started

### GHL-04 Existing pipeline: Name / ID

- Object: Existing pipeline
- Field: Name / ID
- Value: CA&J Demo - Lead Pipeline = U95kdMryqjDqu7JeFrdw (do not modify)
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Pipeline unchanged after the build
- Status: Not started

### GHL-05 Existing offer: $27 HVAC Review System funnel

- Object: Existing offer
- Field: $27 HVAC Review System funnel
- Value: Do not replace or merge with this high-ticket offer
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Funnel and its workflows unchanged
- Status: Not started

### GHL-06 Pipeline: Name

- Object: Pipeline
- Field: Name
- Value: CAJ-HT-HVAC-Sales
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Pipeline appears under Opportunities with exact name
- Status: Not started

### GHL-07 Pipeline CAJ-HT-HVAC-Sales: Stage 1

- Object: Pipeline CAJ-HT-HVAC-Sales
- Field: Stage 1
- Value: New lead
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Stage 1 reads exactly 'New lead'
- Status: Not started

### GHL-08 Pipeline CAJ-HT-HVAC-Sales: Stage 2

- Object: Pipeline CAJ-HT-HVAC-Sales
- Field: Stage 2
- Value: Qualified unbooked
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Stage 2 reads exactly 'Qualified unbooked'
- Status: Not started

### GHL-09 Pipeline CAJ-HT-HVAC-Sales: Stage 3

- Object: Pipeline CAJ-HT-HVAC-Sales
- Field: Stage 3
- Value: Booked
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Stage 3 reads exactly 'Booked'
- Status: Not started

### GHL-10 Pipeline CAJ-HT-HVAC-Sales: Stage 4

- Object: Pipeline CAJ-HT-HVAC-Sales
- Field: Stage 4
- Value: Confirmed
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Stage 4 reads exactly 'Confirmed'
- Status: Not started

### GHL-11 Pipeline CAJ-HT-HVAC-Sales: Stage 5

- Object: Pipeline CAJ-HT-HVAC-Sales
- Field: Stage 5
- Value: Attended
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Stage 5 reads exactly 'Attended'
- Status: Not started

### GHL-12 Pipeline CAJ-HT-HVAC-Sales: Stage 6

- Object: Pipeline CAJ-HT-HVAC-Sales
- Field: Stage 6
- Value: Proposal sent
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Stage 6 reads exactly 'Proposal sent'
- Status: Not started

### GHL-13 Pipeline CAJ-HT-HVAC-Sales: Stage 7

- Object: Pipeline CAJ-HT-HVAC-Sales
- Field: Stage 7
- Value: Won pending payment
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Stage 7 reads exactly 'Won pending payment'
- Status: Not started

### GHL-14 Pipeline CAJ-HT-HVAC-Sales: Stage 8

- Object: Pipeline CAJ-HT-HVAC-Sales
- Field: Stage 8
- Value: Paid onboarding
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Stage 8 reads exactly 'Paid onboarding'
- Status: Not started

### GHL-15 Pipeline CAJ-HT-HVAC-Sales: Stage 9

- Object: Pipeline CAJ-HT-HVAC-Sales
- Field: Stage 9
- Value: Active client
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Stage 9 reads exactly 'Active client'
- Status: Not started

### GHL-16 Pipeline CAJ-HT-HVAC-Sales: Stage 10

- Object: Pipeline CAJ-HT-HVAC-Sales
- Field: Stage 10
- Value: Lost
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Stage 10 reads exactly 'Lost'
- Status: Not started

### GHL-17 Pipeline CAJ-HT-HVAC-Sales: Stage 11

- Object: Pipeline CAJ-HT-HVAC-Sales
- Field: Stage 11
- Value: Disqualified
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Stage 11 reads exactly 'Disqualified'
- Status: Not started

### GHL-18 Custom field (contact): Niche

- Object: Custom field (contact)
- Field: Niche
- Value: key=niche; type=TEXT
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Niche' exists with type TEXT
- Status: Not started

### GHL-19 Custom field (contact): Business name

- Object: Custom field (contact)
- Field: Business name
- Value: key=business_name; type=TEXT
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Business name' exists with type TEXT
- Status: Not started

### GHL-20 Custom field (contact): Website

- Object: Custom field (contact)
- Field: Website
- Value: key=website; type=TEXT
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Website' exists with type TEXT
- Status: Not started

### GHL-21 Custom field (contact): Service area

- Object: Custom field (contact)
- Field: Service area
- Value: key=service_area; type=TEXT
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Service area' exists with type TEXT
- Status: Not started

### GHL-22 Custom field (contact): Decision maker answer

- Object: Custom field (contact)
- Field: Decision maker answer
- Value: key=decision_maker_answer; type=SINGLE_OPTIONS:Yes|No
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Decision maker answer' exists with type SINGLE_OPTIONS
- Status: Not started

### GHL-23 Custom field (contact): Offer version

- Object: Custom field (contact)
- Field: Offer version
- Value: key=offer_version; type=TEXT
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Offer version' exists with type TEXT
- Status: Not started

### GHL-24 Custom field (contact): Campaign ID

- Object: Custom field (contact)
- Field: Campaign ID
- Value: key=campaign_id; type=TEXT
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Campaign ID' exists with type TEXT
- Status: Not started

### GHL-25 Custom field (contact): Ad ID

- Object: Custom field (contact)
- Field: Ad ID
- Value: key=ad_id; type=TEXT
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Ad ID' exists with type TEXT
- Status: Not started

### GHL-26 Custom field (contact): Form ID

- Object: Custom field (contact)
- Field: Form ID
- Value: key=form_id; type=TEXT
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Form ID' exists with type TEXT
- Status: Not started

### GHL-27 Custom field (contact): Meta lead ID

- Object: Custom field (contact)
- Field: Meta lead ID
- Value: key=meta_lead_id; type=TEXT
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Meta lead ID' exists with type TEXT
- Status: Not started

### GHL-28 Custom field (contact): Lead received time

- Object: Custom field (contact)
- Field: Lead received time
- Value: key=lead_received_time; type=DATE_TIME
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Lead received time' exists with type DATE_TIME
- Status: Not started

### GHL-29 Custom field (contact): First response time

- Object: Custom field (contact)
- Field: First response time
- Value: key=first_response_time; type=DATE_TIME
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'First response time' exists with type DATE_TIME
- Status: Not started

### GHL-30 Custom field (contact): Qualification status

- Object: Custom field (contact)
- Field: Qualification status
- Value: key=qualification_status; type=SINGLE_OPTIONS:Pending|Qualified|Disqualified
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Qualification status' exists with type SINGLE_OPTIONS
- Status: Not started

### GHL-31 Custom field (contact): Appointment ID

- Object: Custom field (contact)
- Field: Appointment ID
- Value: key=appointment_id; type=TEXT
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Appointment ID' exists with type TEXT
- Status: Not started

### GHL-32 Custom field (contact): Appointment confirmation

- Object: Custom field (contact)
- Field: Appointment confirmation
- Value: key=appointment_confirmation; type=SINGLE_OPTIONS:Unconfirmed|Confirmed|Ambiguous
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Appointment confirmation' exists with type SINGLE_OPTIONS
- Status: Not started

### GHL-33 Custom field (contact): Deal amount

- Object: Custom field (contact)
- Field: Deal amount
- Value: key=deal_amount; type=MONETARY
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Deal amount' exists with type MONETARY
- Status: Not started

### GHL-34 Custom field (contact): Payment reference

- Object: Custom field (contact)
- Field: Payment reference
- Value: key=payment_reference; type=TEXT
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Payment reference' exists with type TEXT
- Status: Not started

### GHL-35 Custom field (contact): Loss reason

- Object: Custom field (contact)
- Field: Loss reason
- Value: key=loss_reason; type=TEXT
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Loss reason' exists with type TEXT
- Status: Not started

### GHL-36 Custom field (contact): Consent source

- Object: Custom field (contact)
- Field: Consent source
- Value: key=consent_source; type=TEXT
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Consent source' exists with type TEXT
- Status: Not started

### GHL-37 Custom field (contact): Consent wording version

- Object: Custom field (contact)
- Field: Consent wording version
- Value: key=consent_wording_version; type=TEXT
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Consent wording version' exists with type TEXT
- Status: Not started

### GHL-38 Custom field (contact): Consent timestamp

- Object: Custom field (contact)
- Field: Consent timestamp
- Value: key=consent_timestamp; type=DATE_TIME
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Field 'Consent timestamp' exists with type DATE_TIME
- Status: Not started

### GHL-39 Calendar: Name

- Object: Calendar
- Field: Name
- Value: HVAC Growth Strategy Session
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Test booking on desktop and phone shows the expected setting
- Status: Not started

### GHL-40 Calendar: Duration

- Object: Calendar
- Field: Duration
- Value: 45 minutes
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Test booking on desktop and phone shows the expected setting
- Status: Not started

### GHL-41 Calendar: Timezone

- Object: Calendar
- Field: Timezone
- Value: America/Chicago (confirm account setting)
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Test booking on desktop and phone shows the expected setting
- Status: Not started

### GHL-42 Calendar: Working hours

- Object: Calendar
- Field: Working hours
- Value: NEEDS_EVIDENCE
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Test booking on desktop and phone shows the expected setting
- Status: Not started

### GHL-43 Calendar: Max booking horizon

- Object: Calendar
- Field: Max booking horizon
- Value: 3 days
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Test booking on desktop and phone shows the expected setting
- Status: Not started

### GHL-44 Calendar: Minimum notice

- Object: Calendar
- Field: Minimum notice
- Value: 2 hours
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Test booking on desktop and phone shows the expected setting
- Status: Not started

### GHL-45 Calendar: Buffers

- Object: Calendar
- Field: Buffers
- Value: 15 minutes
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Test booking on desktop and phone shows the expected setting
- Status: Not started

### GHL-46 Calendar: Meeting link

- Object: Calendar
- Field: Meeting link
- Value: Google Meet if available
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Test booking on desktop and phone shows the expected setting
- Status: Not started

### GHL-47 Calendar: Booking fields

- Object: Calendar
- Field: Booking fields
- Value: Name, email, phone + communication disclosures
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Test booking on desktop and phone shows the expected setting
- Status: Not started

### GHL-48 Settings > Integrations > Facebook: Page and lead form access

- Object: Settings > Integrations > Facebook
- Field: Page and lead form access
- Value: The verified Page and the qualification form
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Integration lists the Page and form
- Status: Not started

### GHL-49 Settings > Integrations > Facebook: Import mode

- Object: Settings > Integrations > Facebook
- Field: Import mode
- Value: New leads only
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: No historical leads imported
- Status: Not started

### GHL-50 Facebook lead field mapping: Decision-maker question

- Object: Facebook lead field mapping
- Field: Decision-maker question
- Value: custom field decision_maker_answer
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Test lead shows the answer in that field
- Status: Not started

### GHL-51 Workflow: Name / publish state

- Object: Workflow
- Field: Name / publish state
- Value: CAJ-HT-HVAC-01-Intake - UNPUBLISHED during assembly
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Workflow saved as draft; logic matches out/workflows/01-intake.md
- Status: Not started

### GHL-52 Workflow: Name / publish state

- Object: Workflow
- Field: Name / publish state
- Value: CAJ-HT-HVAC-02-Unbooked - UNPUBLISHED during assembly
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Workflow saved as draft; logic matches out/workflows/02-unbooked.md
- Status: Not started

### GHL-53 Workflow: Name / publish state

- Object: Workflow
- Field: Name / publish state
- Value: CAJ-HT-HVAC-03-Booked - UNPUBLISHED during assembly
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Workflow saved as draft; logic matches out/workflows/03-booked.md
- Status: Not started

### GHL-54 Workflow: Name / publish state

- Object: Workflow
- Field: Name / publish state
- Value: CAJ-HT-HVAC-04-Outcome - UNPUBLISHED during assembly
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Workflow saved as draft; logic matches out/workflows/04-outcome.md
- Status: Not started

### GHL-55 Message templates: Placeholders

- Object: Message templates
- Field: Placeholders
- Value: Replace every [TOKEN] using the account field picker
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Test preview shows correct name, date, timezone, links and sender
- Status: Not started

### GHL-56 Pre-call page: Visibility

- Object: Pre-call page
- Field: Visibility
- Value: Private/unlisted draft from out/precall_page/index.html
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Opens without login; no invented outcomes
- Status: Not started

### GHL-57 Welcome page + intake form: Fields

- Object: Welcome page + intake form
- Field: Fields
- Value: From out/welcome_page/index.html and out/intake_form.json
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: No password fields
- Status: Not started

### GHL-58 Payment product: Create checkout/invoice item

- Object: Payment product
- Field: Create checkout/invoice item
- Value: Locked CA-J terms; test mode first; no automatic subscription - REQUIRES EXPLICIT HUMAN APPROVAL
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Test-mode checkout shows correct amount, buyer, description and renewal behavior
- Spend: REQUIRES EXPLICIT HUMAN APPROVAL
- Status: Not started

### GHL-59 Test contacts: Run T01-T14

- Object: Test contacts
- Field: Run T01-T14
- Value: Designated test contacts only (example.com emails, 555-01xx numbers)
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Results recorded in out/tests/ evidence and test log
- Status: Not started

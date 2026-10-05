# GHL checklist (human, logged in to https://app.gohighlevel.com)

Target location ID: `UWc5vKBgFVPdxNTRAy2s` (case-sensitive). Do not use any other location.

## 1. Sub-account and AI Studio
- [ ] Confirm the sub-account for location `UWc5vKBgFVPdxNTRAy2s` (create only with approval - spend item).
- [ ] Sub-account > Settings > Labs > search 'AI Studio' > Activate Feature (availability on this account is NEEDS_EVIDENCE).
- [ ] Confirm AI Studio appears in the left nav.

## 2. Pipeline (out/pipeline_spec.md)
- [ ] Opportunities > Pipelines > Create New Pipeline: `Meta Ads Leads`.
- [ ] Stages in order: New Lead, Hot Lead / Responded, Closed (won), Lost.
- [ ] Do NOT edit `CA&J Demo - Lead Pipeline` (`U95kdMryqjDqu7JeFrdw`).
- [ ] Custom field 'Service Needed' (insert via field picker; key NEEDS_EVIDENCE).

## 3. Workflows (build from the specs, keep in Draft until approved)
- [ ] Workflow 01 'New Lead Automation' per out/workflows/01-new-lead-automation.md.
- [ ] Workflow 02 'Hot Lead - Replied' per out/workflows/02-hot-lead-replied.md (Remove from Workflow 01 FIRST).
- [ ] Workflow 03 'Landing Page CAPI - Lead' per out/workflows/03-landing-page-capi-lead.md.
- [ ] Insert every {{...}} field with the field picker; send a preview of each message.
- [ ] Field mapping: confirm the AI Studio form fields map to native contact fields (name, email, phone, service needed).
- [ ] A2P 10DLC: confirm status (NEEDS_EVIDENCE); until approved, use the email fallback to chuck@ca-jconsulting.com.
- [ ] Publishing workflows: REQUIRES EXPLICIT HUMAN APPROVAL.

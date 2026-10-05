# CAJ AI Employee Playbook - project controls

Version-controlled, machine-checkable file layer for the "AI Employee: Sales &
Fulfillment" plan (spec `specs/SPEC-02-ai-employee.md`, source
`docs/playbooks/02-ai-employee-action-plan.md`). It holds the five control records and
their validator, the HVAC agent prompt and demo questions, the T01-T12 acceptance
checklist, the four workflow specs, price-free outreach drafts with guardrails, the
client intake pack, human runbooks, and approval-gated documentation.

**Nothing in this repository creates a GoHighLevel object, places a call, sends a
message, charges a card, or changes live routing.** Every such step is a human runbook
step (`docs/UI-ONLY-CHECKLIST.md`, `docs/DEPLOY-RUNBOOK.md`).

## Absolute rules

1. **No charges or purchases of any kind.** Spend cap is 0.00; every paid item is listed
   in `docs/COST-AND-APPROVALS.md` with "approval required" and cost NEEDS_EVIDENCE.
2. **Never invent data.** Unknown facts are marked `NEEDS_EVIDENCE`. Every business fact
   needs an evidence URL or owner confirmation, a verification date, and a status.
3. **Meeting-first.** Never quote a price in an email, DM, call, chat, page, ad, or AI
   reply. Pricing intent routes to a meeting at https://ca-jenterprises.com/ai.
4. **Source results are not CA-J results.** Every figure in the source is the
   presenter's, an attendee's, or a proposal (`docs/SOURCE-CLAIMS.md`).

## Locked business facts

| Fact | Value |
|---|---|
| Owner | Chuck Ashley |
| Phone | 512-229-9199 |
| Email | chuck@ca-jconsulting.com |
| Legal entity | CA&J Enterprises LLC |
| GHL build location | `UWc5vKBgFVPdxNTRAy2s` ("CA&J Enterprises"), reference only, case-sensitive; a human verifies it on screen |
| Booking URL | https://ca-jenterprises.com/ai |
| Commercial terms (internal only) | $650/mo tech fee; setup fee waived; $250 to $300 per booked appointment |

The live Meta campaign CAJ_HVAC27_US_PURCHASE_TEST02 stays frozen; nothing here
touches it. `DRY_RUN` defaults to true and no live code path exists.

## Commands (run from this folder; Python 3.11, standard library only)

On Chuck's machine use `python` in place of `python3`.

```
python3 scripts/validate_records.py      # exit 0: five records schema-valid, zero findings
python3 scripts/check_guardrails.py      # exit 0: every forbidden sample blocked
python3 scripts/run_test_checklist.py    # exit 1 until all critical tests PASS (expected now)
python3 scripts/render_templates.py      # exit 0: email draft rendered to out/
python3 scripts/render_templates.py --omit first_name   # exit 3: withheld variable
python3 scripts/cost_estimate.py         # prints contribution; exit 3 while rates unverified
python3 -m unittest discover -s tests    # full test suite
```

Other useful commands:

```
python3 scripts/run_test_checklist.py --test-id T03 --result PASS --evidence "<appointment id / log path>"
python3 scripts/render_templates.py --template agent/system-prompt.md --vars <vars.json>
python3 scripts/render_templates.py --facts-form          # business-facts intake form -> out/
python3 scripts/validate_records.py --intake <filled-intake.json>
```

Exit codes are documented at the top of each script.

## Layout

See spec section 4. `records/` control CSVs; `schemas/` JSON schemas; `agent/` prompt,
demo questions, handoff rule, facts template; `tests/` T01-T12 checklist, run protocol,
and the unit tests; `workflows/` WF01-WF04; `pipeline/` stages and prospect template;
`outreach/` drafts and cadence; `intake/` client intake pack; `guardrails/` pricing,
meeting-first, and claim guards; `runbooks/` human procedures; `scripts/` tools;
`docs/` deploy runbook, UI-only checklist, cost and approvals, source claims.

## Deviations from spec

1. **Extra files beyond the section 4 tree** (needed to make the spec runnable and
   tested): `guardrails/locked_pricing.json` and `rates.yaml` (both named in spec
   section 5 but missing from the tree); `scripts/mini_yaml.py` (stdlib parser for
   `rates.yaml`, per build rules); `outreach/render-vars.example.json` (synthetic
   default vars for `render_templates.py`); `guardrails/__init__.py`,
   `scripts/__init__.py`; unit tests `tests/test_*.py`, `tests/_paths.py`, and
   `tests/fixtures/intake.synthetic.json`. Generated output goes to `out/` (ignored).
2. **Status enums.** The spec's `NEEDS_EVIDENCE|VERIFIED|BLOCKED|N/A` enum is used for
   Business_Facts and Asset_Register. Build_Log uses
   `NOT_STARTED|IN_PROGRESS|DONE|NEEDS_EVIDENCE|BLOCKED|N/A` (the spec itself refers
   to "done" rows) and Blockers uses `OPEN|RESOLVED|N/A`. Test_Results uses the spec's
   `PASS|FAIL|NOT_RUN|N/A`.
3. **Fourteen facts.** The spec lists thirteen fact names but requires fourteen; "hours
   and holidays" is split into "business hours" and "holidays" (matching the intake
   list at source line 208).
4. **Where results are stored.** `tests/T01-T12.csv` stays the unedited checklist (all
   `NOT_RUN`); `run_test_checklist.py` writes results to `records/Test_Results.csv`.
   All twelve tests are marked critical because the source does not say which are;
   `N/A` counts as resolved only with a written reason.
5. **Pricing guard strictness by channel.** Outbound channels block amounts and price
   words. The agent system prompt is rendered as `internal_instructions`, which blocks
   amounts only, because the prompt must say "never state any price".
6. **COST-AND-APPROVALS.md** refers to the source's pricing figures by description and
   claim ID rather than restating the digits, so that acceptance criterion 11 (those
   figures appear only in SOURCE-CLAIMS.md and the guardrail denylist) holds.
7. **Mailing address.** The email signature needs a mailing address that is not a
   known fact; it is the `sender_mailing_address` variable, `NEEDS_EVIDENCE` in the
   example vars. Draft rendering warns; `--for-send` refuses.
8. **Acceptance commands that exit non-zero by design.** `run_test_checklist.py` exits
   1 and `cost_estimate.py` exits 3 in the current state; that is the behaviour the
   spec's acceptance criteria 7 and 9 require.
9. **Line references.** The source's recurring-fee and setup-fee draft defaults are on
   lines 108 and 112 of the copy in this repo (spec cites 104-107); both are recorded.
10. **Interpreter.** Commands are shown with `python3` (this host); scripts never
    hardcode an interpreter and use `pathlib` throughout.

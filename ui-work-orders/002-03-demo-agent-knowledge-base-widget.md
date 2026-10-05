# UI work order 002-03: Build a private prospect demo (agent, knowledge base, widget)

Build: SPEC-02 AI Employee (`build/CAJ_AI_Employee_Playbook/`). Human, logged-in work only; the coding agent cannot do any of this.

- **Platform:** GoHighLevel AI Agents, Knowledge Base, chat widget, site builder
- **Source steps:** 14-19, 21
- **Procedure:** build/CAJ_AI_Employee_Playbook/runbooks/demo-page-and-calendar.md (private personalized demo); build/CAJ_AI_Employee_Playbook/agent/
- **Approval gate:** Approval: GHL changes; AI usage (NEEDS_EVIDENCE).

## Actions

1. Build the labelled private preview; never replace the prospect's live site.
2. Duplicate the licensed agent and KB, or paste the rendered prototype prompt (`python3 scripts/render_templates.py --template agent/system-prompt.md --vars <file>`).
3. Crawl and review facts; check text and voice widget mappings separately.
4. Run the six questions in `agent/demo-questions.md`; save a text transcript and a voice log.

## Evidence to capture

- Agent ID, KB ID, widget ID, transcripts.

## Standing rules

- No purchase, subscription, number, domain, or ad spend without Chuck's written approval of the specific item and amount (all costs NEEDS_EVIDENCE).
- No price in any outbound message, page, or AI reply (meeting-first); pricing questions go to https://ca-jenterprises.com/ai.
- Synthetic test contacts only (example.com addresses, 555-01xx numbers) until activation is approved.
- GoHighLevel build location is `UWc5vKBgFVPdxNTRAy2s` (case-sensitive); confirm on screen before any change.
- Record every object ID, timestamp, and evidence path in `build/CAJ_AI_Employee_Playbook/records/` and run `python3 scripts/validate_records.py` from the build root.

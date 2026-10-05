# Handoff rule and callback task

Source: playbook line 174 (handoff in the starter prompt), lines 228-229 (human
takeover rule), and WF03 (line 251). The text in the "Rendered rule" sections is what
fills `[HANDOFF RULE]` and `[FOLLOWUP TASK]` in `agent/system-prompt.md`; the
destinations stay as named placeholders until a human confirms them.

## Destinations (human fills, owner confirms in writing)

| Item | Value | Evidence |
|---|---|---|
| Dispatcher / human transfer destination | `{{dispatcher_destination}}` | owner confirmation, date |
| Coverage hours for live transfer (America/Chicago unless owner says otherwise) | `{{transfer_coverage_hours}}` | owner confirmation, date |
| Follow-up task assignee | `{{followup_assignee}}` | owner confirmation, date |
| Expected callback window the business can actually meet | `{{callback_window}}` | owner confirmation, date |

The transfer destination must not forward back to the AI number (see
`runbooks/phone-routing.md`).

## Rendered rule: [HANDOFF RULE]

Offer to connect the customer with the team. Use the configured transfer action to
{{dispatcher_destination}} only during {{transfer_coverage_hours}}. Tell the customer
you are attempting the transfer; do not say anyone has answered until the action
returns success. Outside those hours, or if the action fails, do not transfer:
collect callback details instead.

## Rendered rule: [FOLLOWUP TASK]

A follow-up task assigned to {{followup_assignee}} containing the contact name,
callback number, service requested, location, urgency, a short summary, and the
conversation or call ID. Tell the customer the team will follow up within
{{callback_window}} and nothing more specific.

## Owner takeover (bot pause)

1. When the owner or a team member takes over a conversation, the bot is paused using
   the supported conversation or automation setting in GoHighLevel.
2. The bot resumes only under the rule the owner agreed to in writing (for example,
   after the conversation is closed by the team). Record that rule here:
   `{{bot_resume_rule}}`.
3. If the pause/takeover function cannot be verified in the live account (acceptance
   test T06), route every handoff to a separate, supported process (for example, a
   task to the dispatcher with no further bot replies on that thread) and document the
   limitation in `records/Blockers.csv` before activation.
4. Pausing and resuming are human, logged-in actions. Nothing in this repository can
   pause or resume a live bot.

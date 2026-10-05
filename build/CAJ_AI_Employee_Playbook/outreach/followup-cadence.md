# Follow-up cadence

**Not specified in the source.** The playbook (line 350) labels this schedule as a
suggestion that is "not specified in the video". It is a CA&J operating default and
can be changed by Chuck.

| Touch | Timing | Template |
|---|---|---|
| First contact | Day 0 | `email-draft.txt`, `dm-draft.txt`, or `call-script.txt` (one channel) |
| Follow-up 1 | 3 business days after first contact | short reply on the same thread or channel |
| Final follow-up | 7 business days after first contact | short reply on the same thread or channel |

Maximum follow-ups: 2 (`FOLLOWUPS_MAX`).

## Stop conditions

Stop immediately, on every channel, on any of:

- a reply (move to Replied and handle personally),
- an opt-out ("no", "stop", "unsubscribe", "not interested", "do not contact"),
- a disqualifying status (wrong business, not HVAC, outside the service region,
  bounced address, wrong number).

## Rules

- Never run simultaneous repeated messages across multiple channels. One channel per
  touch per prospect.
- Each channel (email, Instagram DM, calls) needs its own launch authorization from
  Chuck before anything is sent. Sending is never done by this repository.
- First email batch is small and reviewed (`EMAIL_INITIAL_BATCH = 10`). The source's
  daily email volume is a training target, not a starting volume (see
  `docs/SOURCE-CLAIMS.md`).
- No follow-up may contain a price or fee; pricing questions get the meeting-first
  reply and the booking link https://ca-jenterprises.com/ai.
- Opt-outs are recorded in `pipeline/prospects.template.csv` copies (`opt_out = yes`)
  and honored permanently.

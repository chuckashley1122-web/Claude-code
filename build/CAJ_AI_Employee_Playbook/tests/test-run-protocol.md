# Acceptance test run protocol (T01-T12)

Source: playbook lines 253-292. The pass conditions in `T01-T12.csv` are copied
verbatim from the source. Running these tests is a human, logged-in task: every test
needs a live agent, a live calendar, or a live phone route in GoHighLevel. This
repository only defines the tests and records the results.

## Rules

1. **Synthetic contacts only.** Use invented test contacts (example.com email
   addresses, 555-01xx numbers where a number is only displayed). Never use a real
   prospect or customer as a test contact.
2. **Authorized test destinations only.** Test calls, transfers, and messages go only
   to numbers and inboxes the owner has authorized in writing for testing.
3. **Every PASS needs an evidence reference.** A transcript file, a call log ID, an
   appointment ID, or a screenshot path. Record results only with
   `python3 scripts/run_test_checklist.py --test-id Txx --result PASS --evidence "<reference>"`.
   The tool refuses an empty or self-referential reference ("pass", "ok", the test's
   own name) and refuses anything that looks like card data.
4. **No activation before all critical tests pass.** All twelve tests are marked
   critical. All enabled-channel critical tests must pass before activation (source
   line 292). `run_test_checklist.py` exits non-zero until they do.
5. **Out-of-scope features** may be recorded `N/A` only with a written reason
   (`--reason`), for example "voice channel not in the agreed scope". N/A is never a
   way to skip a failing test.
6. **Retest only what changed.** After a fix, re-test the failed behaviour and the
   dependencies affected by its fix (source line 292). The tool stamps
   `retest_date` when a test is recorded again.
7. **Record actual results honestly.** For each test record the actual result, the
   object ID or log, pass or fail, and the fix (source line 292).

## Per-test notes

| Test | What the human does | Typical evidence |
|---|---|---|
| T01 | Ask hours, location, services, and an excluded service | text transcript file |
| T02 | Ask for a repair price | transcript plus follow-up task ID |
| T03 | Book an available slot as a synthetic customer | appointment ID in the correct calendar |
| T04 | Book with the integration disabled or an unavailable slot | transcript showing no false confirmation |
| T05 | Ask for a person, during and outside transfer hours | call log ID or callback task ID |
| T06 | Owner takes over a live test conversation | transcript showing the bot stopped |
| T07 | Test call in business hours, after hours, and unanswered | call log IDs per mode |
| T08 | Ask about another prospect's or client's facts | transcript with no foreign facts |
| T09 | Describe an urgent situation | transcript showing approved escalation, no repair advice |
| T10 | Re-send the same event (booking, purchase, handoff) | single opportunity/appointment/task ID |
| T11 | Desktop chat plus intended voice modes | transcript and voice log |
| T12 | Restore the original route and place one inbound call | rollback record plus call log ID |

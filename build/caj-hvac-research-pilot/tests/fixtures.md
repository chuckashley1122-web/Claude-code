# Test fixtures (labeled mock companies)

All four fixtures are controlled mock pages for fictional companies. They exist only
to test the pipeline.

- `mock://` labels are valid only in fixture mode.
- `mock://` values are never accepted as live website inputs (input validation accepts
  only `http://` / `https://` URLs).
- Fixture results must never be mixed into real prospect output. Every fixture run
  writes `"fixture_mode": true` in `run.json`, and the validator rejects `mock://` in any
  non-fixture run.

| Fixture | File | Label | Supplied facts |
|---|---|---|---|
| A | `fixtures/fixture_a_page.md` | `mock://fixture-a` | Company `Sample HVAC A`; service area `Round Rock`; services `AC repair` and `heating maintenance`; contact method an explicitly written phone number `(512) 555-0142` (555 example range). Expected: `complete` (T01). |
| B | `fixtures/fixture_b_page.md` | `mock://fixture-b` | Company `Sample HVAC B`; services `AC installation`; service area and contact details omitted. Expected: `partial`, omitted fields read `Not found in reviewed pages` (T02). |
| C | `fixtures/fixture_c_other_business_page.md` | `mock://fixture-c` | A page written for a different business, `Sample HVAC C`. Used only for the identity-mismatch test: the input row supplies the name `Sample HVAC X`. Expected: `blocked` / `IDENTITY_MISMATCH`, zero facts (T05). |
| D | `fixtures/fixture_d_unavailable.md` | `mock://fixture-d` | Retrieval-failure input; first line `RETRIEVAL_FAILURE`. Expected: one retry, then `blocked`, other rows continue (T04). |

Built-in fixture demo rows (used by `--retriever fixtures` when `inputs/companies.csv`
has no rows): `fixture-a,Sample HVAC A,https://sample-hvac-a.example.com`,
`fixture-b,Sample HVAC B,https://sample-hvac-b.example.com`,
`fixture-c,Sample HVAC X,https://sample-hvac-x.example.com`.

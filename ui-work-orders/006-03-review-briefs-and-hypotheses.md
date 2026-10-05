# 006-03 Review each brief's observations and hypotheses

**Why:** The pipeline proves structure and source binding, but only Chuck can judge
whether each observation is specific and each hypothesis is fairly qualified (playbook
Day 3). Until then every brief stays `user review pending`.

**Where:** `build/caj-hvac-research-pilot/outputs/<run_id>/brief.md` and `evidence.md`
for the latest real (non-fixture) run.

**Steps:**
1. Open `brief.md`. For each company, read the Verified facts.
2. For each fact, find its row in `evidence.md` (Claim-to-source mapping) and read the
   verbatim excerpt. Confirm the excerpt supports the fact.
3. Open the original page (or the saved `inputs/pages/<company_id>/` file) and confirm
   the excerpt is really there.
4. Read the observation: is it specific and true of the page?
5. Read the hypothesis: is it clearly an idea to test, not a claim the company is
   losing business?
6. Note any wrong fact, weak observation, or overclaiming hypothesis in
   `tests/test_log.md` (T09 row) and in `changelog.md` if a fix is requested.

**Verify:** The T09 row in `tests/test_log.md` names the run id, says which source
mappings were checked, and records pass or fail with the evidence path.

**Blocked by:** 006-01 and 006-02 (a real run must exist first).

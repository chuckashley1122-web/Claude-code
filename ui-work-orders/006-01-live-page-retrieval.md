# 006-01 Live page retrieval (save real page text for the pilot)

**Why:** The HVAC research pilot cannot fetch web pages. The coding agent has no browser
and no web tool, and `LiveRetriever` refuses every call with `LiveCallBlocked` until a
human approves a retrieval path. Real page content enters only as text files a human saves.

**Where:** A normal web browser (not logged in to anything), and the folder
`build/caj-hvac-research-pilot/inputs/pages/` in this repo.

**Steps:**
1. Complete work order 006-02 first so each company has a `company_id` in `inputs/companies.csv`.
2. For each company, create a folder `inputs/pages/<company_id>/`.
3. Open the company's homepage in the browser as a normal visitor. Do not log in. Do not
   bypass any access restriction, paywall, or bot check.
4. Select the visible page text, copy it, and save it as `01-home.txt` (plain UTF-8 text).
5. Optionally save up to two more pages on the **same domain** (Services, About, or
   Contact) as `02-<slug>.txt` and `03-<slug>.txt`. No more than three files per company.
6. If a page will not load, save a file whose first line is `RETRIEVAL_FAILURE` and a
   second line describing the error you saw.
7. Check whether the site's terms or robots policy allow saving its text for research.
   If unsure, skip that company.
8. Run `python scripts/run_research.py --retriever filedrop --input inputs/companies.csv`
   from `build/caj-hvac-research-pilot/`.

**Verify:** The command prints a run id, output paths, and complete/partial/blocked
counts; `outputs/<run_id>/run.json` shows `"fixture_mode": false`; `output validation: passed`
is printed.

**Blocked by:** 006-02 (real company rows). Any automated live retrieval (HTTP client,
scraping service, browser automation) needs Chuck's explicit approval, a named owner,
and a cost figure; cost is NEEDS_EVIDENCE and SPEND_CAP_USD is 0.00.

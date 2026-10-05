# 006-02 Supply one to three real HVAC company URLs

**Why:** `inputs/companies.csv` ships header-only, so the live run reports
`INPUT_REQUIRED` and test T09 is `not run`. The agent must never invent businesses or URLs.

**Where:** `build/caj-hvac-research-pilot/inputs/companies.csv` in this repo (any text
editor).

**Steps:**
1. Choose one to three real, public HVAC company websites Chuck wants researched.
2. Under the header `company_id,company_name,website_url`, add one row per company, e.g.
   `acme-hvac,Acme Heating and Air,https://www.example.com` (use the real values).
3. `company_id`: short, unique, no spaces. `company_name`: the business name as the
   website itself writes it (the identity check needs the name to appear on the page).
   `website_url`: full `https://` address of the homepage.
4. Do not add a fourth row; the pilot rejects more than three.
5. Confirm on the live site that the page really belongs to that business (identity).
6. Confirm the project path: if Chuck's machine uses the pinned path
   `C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system\build\caj-hvac-research-pilot\`,
   update the first line of `workflow.md` to that path after checking it exists.

**Verify:** `python scripts/run_research.py --retriever filedrop` no longer prints
`INPUT_REQUIRED` (it will report blocked companies until 006-01 pages are saved).

**Blocked by:** Chuck's choice of companies. Nothing else.

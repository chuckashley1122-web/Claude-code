PROJECT_ROOT: /home/user/Claude-code/build/caj-hvac-research-pilot (resolved build path in this repo; on Chuck's machine the spec pins C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system\build\caj-hvac-research-pilot\ - confirm per work order 006-02 notes)

# Workflow contract - CA-J HVAC research pilot

This is the one active workflow. Everything else waits in `backlog.md`.

| Field | Value |
|---|---|
| Owner | Chuck Ashley |
| Business unit | CA-J Enterprises |
| Purpose | Prepare a concise public HVAC company research brief: one source-backed brief and one draft marketing observation per company |
| Trigger | manual run |
| Input | `inputs/companies.csv` (header `company_id,company_name,website_url`) |
| Maximum companies | three per run |
| Outputs | `outputs/<run_id>/brief.md` and `outputs/<run_id>/results.csv` |
| Evidence | `outputs/<run_id>/evidence.md` and `outputs/<run_id>/run.json`, in the same run folder |
| External writes | no external writes |
| Operating environment | Python 3.11 standard library, run as `python scripts/run_research.py` from PROJECT_ROOT. The source playbook assumes a Hermes session; no Hermes session was available to this build (see `environment.md`, work order 006-05). |
| Version | 0.1.0 |

## Non-goals

- No outreach (no email, SMS, DM, or call).
- No GHL change of any kind (no reads, no writes).
- No advertising; the live Meta campaign is frozen and untouched.
- No manager agent.
- No scheduler.
- No tenant screening. The source video's property-management opening example does not make tenant screening part of this pilot.

## Seven-day ledger

Day 1 is the first successful **live** run (a real-company run that passes validation and whose sources Chuck has checked), never the date of this document. Rows are added only for days that actually happened. Never backfill.

| day | date | action | evidence_path |
|---|---|---|---|

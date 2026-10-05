"""Orchestration: validate -> run identity -> retrieve -> extract -> render -> validate -> report.

Sequential, one company at a time. Writes only inside outputs/<run_id>/. Transmits nothing.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field, replace
from pathlib import Path

import config
from src import extraction, input_validation, output_validation, render, run_identity
from src.contract import CompanyResult, RunManifest
from src.retrieval import FIXTURE_DEMO_ROWS, Retriever, retrieve_with_retry


@dataclass
class CompletionReport:
    state: str  # "RUN", "INPUT_REQUIRED", "INPUT_INVALID"
    run_id: str = ""
    run_dir: Path | None = None
    paths: dict = field(default_factory=dict)
    counts: dict = field(default_factory=dict)
    overall_status: str = ""
    gaps: list = field(default_factory=list)
    next_repair: str = ""
    errors: list = field(default_factory=list)
    validation_findings: list = field(default_factory=list)
    attempts: dict = field(default_factory=dict)
    message: str = ""

    def render(self) -> str:
        if self.state != "RUN":
            return self.message
        c = self.counts
        lines = [
            f"run_id: {self.run_id}",
            f"overall_status: {self.overall_status}",
            f"counts: complete={c.get('complete', 0)} partial={c.get('partial', 0)} blocked={c.get('blocked', 0)}",
            "outputs:",
        ]
        lines += [f"  {name}: {path}" for name, path in self.paths.items()]
        lines.append("factual gaps:" if self.gaps else "factual gaps: none")
        lines += [f"  - {g}" for g in self.gaps]
        lines.append(f"next repair: {self.next_repair}")
        if self.errors:
            lines.append("recorded execution errors:")
            lines += [f"  - {e}" for e in self.errors]
        if self.validation_findings:
            lines.append("VALIDATION FAILED:")
            lines += [f"  - {f}" for f in self.validation_findings]
        else:
            lines.append("output validation: passed")
        lines.append("These are drafts for Chuck's review. Nothing was sent, posted, or synced.")
        return "\n".join(lines)


def fixture_demo_csv_bytes() -> bytes:
    buf = io.StringIO(newline="")
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(config.INPUT_CSV_HEADER)
    writer.writerows(FIXTURE_DEMO_ROWS)
    return buf.getvalue().encode("utf-8")


def _next_repair(results: list[CompanyResult]) -> str:
    for r in results:
        if r.blocked_reason == "IDENTITY_MISMATCH":
            return (f"Confirm whether the pages supplied for {r.company_id} belong to {r.company_name!r}; "
                    "replace them or correct the company name (work order 006-02).")
    for r in results:
        if r.status == "blocked":
            return f"Resupply readable page text for {r.company_id} under inputs/pages/{r.company_id}/ (work order 006-01)."
    for r in results:
        if r.status == "partial":
            return (f"Supply a Services or Contact page for {r.company_id} if the site has one; "
                    "otherwise accept the gap as reported.")
    return "None required."


def _gaps(results: list[CompanyResult]) -> list[str]:
    gaps = []
    for r in results:
        if r.status == "blocked":
            gaps.append(f"{r.company_id}: blocked ({r.blocked_reason}); no facts recorded")
            continue
        for key, label in render.FACT_LABELS:
            missing = (not r.services) if key == "services" else getattr(r, key) == config.MISSING_LABEL
            if missing:
                gaps.append(f"{r.company_id}: {label} - {config.MISSING_LABEL}")
    return gaps


def run_pipeline(
    input_path: Path,
    retriever: Retriever,
    out_root: Path,
    fixture_mode: bool,
    use_fixture_demo_when_empty: bool = False,
    max_pages: int | None = None,
    max_retries: int | None = None,
) -> CompletionReport:
    input_path = Path(input_path)
    # 1. validate input (fail closed, before any retrieval)
    raw = input_path.read_bytes() if input_path.is_file() else b""
    result = input_validation.validate_file(input_path)
    input_label = str(input_path)
    if result.state == "INPUT_INVALID":
        return CompletionReport("INPUT_INVALID", message=result.describe() + "\nNo retrieval was attempted and no run folder was created.")
    if result.state == "INPUT_REQUIRED":
        if not (fixture_mode and use_fixture_demo_when_empty):
            return CompletionReport("INPUT_REQUIRED", message=(
                f"INPUT_REQUIRED: {input_path} has a header and no company rows. Supply one to three real "
                "HVAC company rows (work order 006-02). No run folder was created."))
        raw = fixture_demo_csv_bytes()
        input_label = "builtin:fixture-demo (inputs/companies.csv has no rows: INPUT_REQUIRED for the live run)"
        result = input_validation.validate_bytes(raw)
        if not result.ok:  # pragma: no cover - the built-in rows are fixed
            return CompletionReport("INPUT_INVALID", message=result.describe())

    # mock:// website inputs never get this far: input_validation accepts only http(s) URLs.

    # 2. run identity
    started = run_identity.utc_now_iso()
    run_id, run_dir = run_identity.create_run_dir(Path(out_root), run_identity.make_run_id(raw))

    # 3+4. retrieve and extract, sequentially
    results: list[CompanyResult] = []
    errors: list[str] = []
    attempts: dict[str, int] = {}
    for company in result.companies:
        outcome = retrieve_with_retry(retriever, company, max_pages=max_pages, max_retries=max_retries)
        attempts[company.company_id] = outcome.attempts
        checked = run_identity.utc_now_iso()
        if not outcome.ok:
            errors.append(f"{company.company_id}: retrieval failed after {outcome.attempts} attempt(s): {outcome.error}")
            results.append(extraction.blocked_result(company, "RETRIEVAL_FAILED", outcome.pages, checked, outcome.attempts))
            continue
        res = extraction.extract(company, outcome.pages, checked, outcome.attempts)
        if res.blocked_reason == "IDENTITY_MISMATCH":
            page_name = extraction.dominant_business_name(
                next(p.text for p in outcome.pages if p.retrieval_status == "ok"))
            errors.append(f"{company.company_id}: IDENTITY_MISMATCH (supplied {company.company_name!r}, "
                          f"page names {page_name!r}); no facts assigned")
        results.append(res)

    # 5. render
    counts = {s: 0 for s in config.COMPANY_STATUSES}
    for r in results:
        counts[r.status] += 1
    provisional = "completed" if all(r.status == "complete" for r in results) else "partial"
    manifest = RunManifest(
        run_id=run_id, workflow_version=config.WORKFLOW_VERSION, input_path=input_label,
        input_hash=run_identity.input_hash(raw), started_at_utc=started,
        finished_at_utc=run_identity.utc_now_iso(), record_count=len(results),
        counts_by_status=counts, overall_status=provisional, fixture_mode=fixture_mode,
        errors=tuple(errors),
    )
    paths = render.write_all(run_dir, manifest, results)

    # 6. validate
    findings = output_validation.validate_run_dir(run_dir, expected_ids=[c.company_id for c in result.companies])
    if findings:
        manifest = replace(manifest, overall_status="failed",
                           errors=tuple(errors) + tuple(f"VALIDATION: {f}" for f in findings))
        render.write_run_json(paths["run.json"], manifest)

    # 7. report
    return CompletionReport(
        state="RUN", run_id=run_id, run_dir=run_dir, paths=paths, counts=counts,
        overall_status=manifest.overall_status, gaps=_gaps(results), next_repair=_next_repair(results),
        errors=list(errors), validation_findings=findings, attempts=attempts,
    )


def load_manifest(run_dir: Path) -> dict:
    return json.loads((Path(run_dir) / "run.json").read_text(encoding="utf-8"))

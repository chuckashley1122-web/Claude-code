"""Writers for the four run artifacts. Writes only inside outputs/<run_id>/."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import config
from src.contract import CompanyResult, RunManifest

MISSING = config.MISSING_LABEL
FACT_LABELS = (
    ("service_area", "Service area"),
    ("services", "Services"),
    ("contact_method", "Contact method"),
    ("observation", "Observation"),
)
REVIEW_LINE = "Draft for Chuck's review; user review pending"


def claims_for(result: CompanyResult) -> list[tuple[str, str, object]]:
    """(field, value, SourceRef) for every bound fact, in a stable order."""
    out = []
    if "service_area" in result.field_sources:
        out.append(("service_area", result.service_area, result.field_sources["service_area"]))
    for svc in result.services:
        out.append(("services", svc, result.field_sources[f"services:{svc}"]))
    if "contact_method" in result.field_sources:
        ref = result.field_sources["contact_method"]
        out.append(("contact_method", ref.matched_text, ref))
    if "observation" in result.field_sources:
        ref = result.field_sources["observation"]
        out.append(("observation", ref.matched_text, ref))
    return out


def source_urls(result: CompanyResult) -> str:
    labels = []
    for ref in result.source_refs:
        if ref.label not in labels:
            labels.append(ref.label)
    return "; ".join(labels) if labels else MISSING


def write_results_csv(path: Path, results: list[CompanyResult]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(config.RESULTS_CSV_COLUMNS)
        for r in results:
            writer.writerow([
                r.company_id, r.company_name, r.website_url, r.resolved_url, r.status,
                r.service_area, r.services_cell, r.contact_method, r.observation, r.hypothesis,
                source_urls(r), r.checked_at_utc,
            ])


def _fence(text: str) -> str:
    longest = max((len(m) for m in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def _cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def write_evidence_md(path: Path, run_id: str, results: list[CompanyResult], fixture_mode: bool) -> None:
    lines = [f"# Evidence - run {run_id}", ""]
    lines.append(f"fixture_mode: {'true' if fixture_mode else 'false'}")
    if fixture_mode:
        lines.append("FIXTURE RUN: mock:// sources are controlled test pages, not real businesses.")
    lines += ["", "## Sources reviewed", "",
              "| company_id | source_label | retrieval_status | retrieved_at_utc | attempts | blocked_reason |",
              "|---|---|---|---|---|---|"]
    for r in results:
        for ref in r.source_refs or ():
            lines.append(f"| {_cell(r.company_id)} | {_cell(ref.label)} | {ref.retrieval_status} | "
                         f"{ref.retrieved_at_utc} | {r.retrieval_attempts} | {_cell(r.blocked_reason)} |")
    lines += ["", "## Claim-to-source mapping", "",
              "| claim_id | company_id | field | value | matched_text | source_label | retrieved_at_utc |",
              "|---|---|---|---|---|---|---|"]
    excerpts = []
    n = 0
    for r in results:
        for field_name, value, ref in claims_for(r):
            n += 1
            cid = f"C{n}"
            lines.append(f"| {cid} | {_cell(r.company_id)} | {field_name} | {_cell(value)} | "
                         f"{_cell(ref.matched_text)} | {_cell(ref.label)} | {ref.retrieved_at_utc} |")
            fence = _fence(ref.excerpt)
            excerpts += [f"### {cid}", "", f"source_label: {ref.label}", "", fence + "text", ref.excerpt, fence, ""]
    if n == 0:
        lines.append("")
        lines.append("No factual claims were extracted in this run.")
    lines += ["", "## Verbatim excerpts", ""] + excerpts
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_brief_md(path: Path, manifest: RunManifest, results: list[CompanyResult]) -> None:
    c = manifest.counts_by_status
    lines = [f"# HVAC research brief - run {manifest.run_id}", "", f"Review status: {REVIEW_LINE}", ""]
    if manifest.fixture_mode:
        lines += ["FIXTURE RUN: mock companies and mock:// sources only. Not prospect output.", ""]
    lines += [
        "## Run summary", "",
        f"- Workflow version: {manifest.workflow_version}",
        f"- Input: {manifest.input_path} (sha256 {manifest.input_hash})",
        f"- Companies: {manifest.record_count} (complete {c.get('complete', 0)}, partial {c.get('partial', 0)}, blocked {c.get('blocked', 0)})",
        "- Hypotheses are ideas to test, not claims that a company is losing business.",
        "",
    ]
    for r in results:
        lines += [f"## {r.company_id} - {r.company_name}", "",
                  f"- Status: {r.status}" + (f" ({r.blocked_reason})" if r.blocked_reason else ""),
                  f"- Supplied website: {r.website_url}", ""]
        lines += ["### Verified facts", ""]
        facts = 0
        for key, label in FACT_LABELS:
            if key == "services":
                if r.services:
                    parts = [f"{s} [source: {r.field_sources['services:' + s].label}]" for s in r.services]
                    lines.append(f"- {label}: " + "; ".join(parts))
                    facts += 1
                continue
            value = getattr(r, key)
            if value != MISSING:
                lines.append(f"- {label}: {value} [source: {r.field_sources[key].label}]")
                facts += 1
        if facts == 0:
            lines.append("- None")
        lines += ["", "### Missing information", ""]
        missing = [label for key, label in FACT_LABELS
                   if (not r.services if key == "services" else getattr(r, key) == MISSING)]
        lines += [f"- {label}: {MISSING}" for label in missing] or ["- None"]
        lines += ["", "### Marketing hypothesis (draft idea to test)", ""]
        if r.hypothesis != MISSING:
            lines.append(f"- Hypothesis: {r.hypothesis} [based on: {r.field_sources['observation'].label}]")
        else:
            lines.append(f"- Hypothesis: {MISSING}")
        lines += ["", f"Review status: {REVIEW_LINE}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_run_json(path: Path, manifest: RunManifest) -> None:
    path.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8")


def write_all(run_dir: Path, manifest: RunManifest, results: list[CompanyResult]) -> dict[str, Path]:
    run_dir = Path(run_dir)
    paths = {name: run_dir / name for name in ("brief.md", "results.csv", "evidence.md", "run.json")}
    write_brief_md(paths["brief.md"], manifest, results)
    write_results_csv(paths["results.csv"], results)
    write_evidence_md(paths["evidence.md"], manifest.run_id, results, manifest.fixture_mode)
    write_run_json(paths["run.json"], manifest)
    return paths

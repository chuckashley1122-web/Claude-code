"""Validate the five project-control records against their JSON schemas.

Usage (from the build root):
    python3 scripts/validate_records.py
    python3 scripts/validate_records.py --records DIR --schemas DIR
    python3 scripts/validate_records.py --intake path/to/intake.json

Fails (exit 1) on:
  * schema errors (header/column order, required fields, enums, patterns, dates)
  * a DONE / PASS / VERIFIED / RESOLVED row with an empty or NEEDS_EVIDENCE evidence field
  * NEEDS_EVIDENCE anywhere in a "done" row
  * a VERIFIED row without verified_date
  * any money amount in any cell while MEETING_FIRST is in force
  * any GoHighLevel location id other than the build location (case-sensitive)
  * any unresolved placeholder left in a record
Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardrails import pricing_guard  # noqa: E402

LOCKED = json.loads((ROOT / "guardrails" / "locked_pricing.json").read_text(encoding="utf-8"))
BUILD_LOCATION_ID = LOCKED["GHL_BUILD_LOCATION_ID"]
MEETING_FIRST = bool(LOCKED["MEETING_FIRST"])

RECORD_SCHEMAS = {
    "Build_Log.csv": "build_log.schema.json",
    "Asset_Register.csv": "asset_register.schema.json",
    "Business_Facts.csv": "business_facts.schema.json",
    "Test_Results.csv": "test_results.schema.json",
    "Blockers.csv": "blockers.schema.json",
}

# GoHighLevel location ids are 20-character mixed-case alphanumeric tokens.
_LOCATION_TOKEN = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9]{20}(?![A-Za-z0-9])")
_PLACEHOLDER = re.compile(
    r"\{\{[^{}]*\}\}|\[[A-Za-z][A-Za-z0-9 _/-]*\]|<<[^<>]*>>|\bTBD\b|\bTODO\b|\bFILL[ _]?ME\b"
)


# --------------------------------------------------------------------------- schema subset
def _check_format(fmt: str, value: str) -> bool:
    try:
        if fmt == "date":
            date.fromisoformat(value)
            return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))
        if fmt == "date-time":
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?Z", value):
                return False
            datetime.fromisoformat(value[:-1])
            return True
    except ValueError:
        return False
    return True


_TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int, "number": (int, float)}


def validate_instance(schema: dict, instance, path: str = "$") -> list[str]:
    """Validate ``instance`` against a JSON-Schema subset.

    Supported keywords: type, required, properties, additionalProperties(false),
    enum, pattern, minLength, format(date, date-time), items, minItems.
    """
    errors: list[str] = []
    expected = schema.get("type")
    if expected:
        py = _TYPES[expected]
        bad_bool = expected in ("integer", "number") and isinstance(instance, bool)
        if not isinstance(instance, py) or bad_bool:
            return [f"{path}: expected {expected}, got {type(instance).__name__}"]
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in {schema['enum']}")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: {instance!r} does not match {schema['pattern']}")
        if "format" in schema and not _check_format(schema["format"], instance):
            errors.append(f"{path}: {instance!r} is not a valid {schema['format']}")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if "items" in schema:
            for i, item in enumerate(instance):
                errors.extend(validate_instance(schema["items"], item, f"{path}[{i}]"))
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required '{key}'")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in props:
                    errors.append(f"{path}: unexpected property '{key}'")
        for key, sub in props.items():
            if key in instance:
                errors.extend(validate_instance(sub, instance[key], f"{path}.{key}"))
    return errors


# --------------------------------------------------------------------------- content checks
def find_foreign_location_ids(text: str, build_id: str = BUILD_LOCATION_ID) -> list[str]:
    """Return location-id-shaped tokens that are not exactly the build location id."""
    out = []
    for m in _LOCATION_TOKEN.finditer(text or ""):
        tok = m.group(0)
        looks_like_id = re.search(r"[A-Z]", tok) and re.search(r"[a-z]", tok) and re.search(r"\d", tok)
        if looks_like_id and tok != build_id:
            out.append(tok)
    return out


def find_placeholders(text: str) -> list[str]:
    return [m.group(0) for m in _PLACEHOLDER.finditer(text or "")]


@dataclass
class RecordReport:
    name: str
    rows: int = 0
    schema_errors: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.schema_errors and not self.findings


def _row_schema_view(schema: dict, row: dict) -> dict:
    """CSV cells are strings; an empty optional cell counts as absent."""
    required = set(schema.get("required", []))
    return {k: v for k, v in row.items() if v != "" or k in required}


def validate_record_file(csv_path: Path, schema: dict) -> RecordReport:
    report = RecordReport(csv_path.name)
    if not csv_path.is_file():
        report.schema_errors.append("file missing")
        return report
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            report.schema_errors.append("empty file (no header)")
            return report
        rows = [r for r in reader if any(c.strip() for c in r)]
    if header != schema["x-columns"]:
        report.schema_errors.append(f"header {header} != expected {schema['x-columns']}")
        return report
    required = set(schema.get("required", []))
    status_field = schema.get("x-status-field", "status")
    evidence_field = schema["x-evidence-field"]
    done = set(schema.get("x-done-statuses", []))
    for n, cells in enumerate(rows, start=2):
        if len(cells) != len(header):
            report.schema_errors.append(f"line {n}: {len(cells)} cells, expected {len(header)}")
            continue
        report.rows += 1
        row = dict(zip(header, cells))
        for key in required:
            if not row[key].strip():
                report.schema_errors.append(f"line {n}: required field '{key}' is empty")
        report.schema_errors.extend(
            f"line {n}: {e}" for e in validate_instance(schema, _row_schema_view(schema, row))
        )
        status = row.get(status_field, "")
        if status in done:
            ev = row.get(evidence_field, "").strip()
            if not ev or ev.upper() == "NEEDS_EVIDENCE":
                report.findings.append(f"line {n}: {status} row has no evidence in '{evidence_field}'")
            if any(v.strip().upper() == "NEEDS_EVIDENCE" for v in row.values()):
                report.findings.append(f"line {n}: NEEDS_EVIDENCE value in a {status} row")
            if status == "DONE" and not row.get("timestamp_utc", "").strip():
                report.findings.append(f"line {n}: DONE row has no timestamp_utc")
        if status == "VERIFIED":
            if "verified_date" in row and not row["verified_date"].strip():
                report.findings.append(f"line {n}: VERIFIED row has no verified_date")
            if "value" in row and not row["value"].strip():
                report.findings.append(f"line {n}: VERIFIED fact has no value")
        for key, value in row.items():
            if MEETING_FIRST:
                for v in pricing_guard.find_amounts(value):
                    report.findings.append(f"line {n}: price token {v.match!r} in '{key}' (MEETING_FIRST)")
            for tok in find_foreign_location_ids(value):
                report.findings.append(f"line {n}: foreign GHL location id {tok!r} in '{key}'")
            for ph in find_placeholders(value):
                report.findings.append(f"line {n}: unresolved placeholder {ph!r} in '{key}'")
    return report


def validate_all(records_dir: Path, schemas_dir: Path) -> list[RecordReport]:
    reports = []
    for csv_name, schema_name in RECORD_SCHEMAS.items():
        schema = json.loads((schemas_dir / schema_name).read_text(encoding="utf-8"))
        reports.append(validate_record_file(records_dir / csv_name, schema))
    return reports


def validate_intake(intake_path: Path, schema_path: Path) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    data = json.loads(intake_path.read_text(encoding="utf-8"))
    errors = validate_instance(schema, data)
    blob = json.dumps(data)
    errors += [f"foreign GHL location id {t!r}" for t in find_foreign_location_ids(blob)]
    return errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records", type=Path, default=ROOT / "records")
    ap.add_argument("--schemas", type=Path, default=ROOT / "schemas")
    ap.add_argument("--intake", type=Path, help="validate a filled intake JSON instead of the records")
    args = ap.parse_args(argv)

    if args.intake:
        errors = validate_intake(args.intake, ROOT / "intake" / "intake.schema.json")
        for e in errors:
            print(f"INTAKE  {e}")
        print("intake: " + ("OK" if not errors else f"{len(errors)} error(s)"))
        return 0 if not errors else 1

    reports = validate_all(args.records, args.schemas)
    print(f"{'record':<20} {'rows':>4}  {'schema':<7} findings")
    print("-" * 48)
    for r in reports:
        schema_state = "valid" if not r.schema_errors else "INVALID"
        print(f"{r.name:<20} {r.rows:>4}  {schema_state:<7} {len(r.findings)}")
    for r in reports:
        for e in r.schema_errors:
            print(f"SCHEMA   {r.name}: {e}")
        for f in r.findings:
            print(f"FINDING  {r.name}: {f}")
    ok = all(r.ok for r in reports)
    print("RESULT: " + ("all five records schema-valid, zero findings" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

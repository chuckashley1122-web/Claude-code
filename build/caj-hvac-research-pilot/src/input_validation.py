"""Fail-closed validation of inputs/companies.csv. Runs before any retrieval."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import config
from src.contract import Company


@dataclass(frozen=True)
class RowError:
    row_index: int  # 0 = header, 1.. = data rows
    reason: str


@dataclass(frozen=True)
class ValidationResult:
    state: str  # "OK", "INPUT_REQUIRED", or "INPUT_INVALID"
    companies: tuple[Company, ...] = ()
    errors: tuple[RowError, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return self.state == "OK"

    def describe(self) -> str:
        if self.state == "OK":
            return f"OK: {len(self.companies)} company row(s) accepted"
        if self.state == "INPUT_REQUIRED":
            return "INPUT_REQUIRED: the input has a valid header and no data rows"
        lines = ["INPUT_INVALID:"]
        lines += [f"  row {e.row_index}: {e.reason}" for e in self.errors]
        return "\n".join(lines)


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc) and " " not in value


def validate_bytes(raw: bytes, max_rows: int | None = None) -> ValidationResult:
    cap = config.max_companies() if max_rows is None else max_rows
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return ValidationResult("INPUT_INVALID", errors=(RowError(0, "file is not valid UTF-8"),))

    reader = csv.reader(io.StringIO(text, newline=""))
    rows = list(reader)
    if not rows:
        return ValidationResult("INPUT_INVALID", errors=(RowError(0, "missing header"),))

    header = tuple(cell.strip() for cell in rows[0])
    if header != config.INPUT_CSV_HEADER:
        return ValidationResult(
            "INPUT_INVALID",
            errors=(RowError(0, f"header must be exactly {','.join(config.INPUT_CSV_HEADER)}; got {','.join(header)}"),),
        )

    data_rows = [r for r in rows[1:] if any(cell.strip() for cell in r)]
    errors: list[RowError] = []
    if not data_rows:
        return ValidationResult("INPUT_REQUIRED")

    if len(data_rows) > cap:
        errors.append(
            RowError(0, f"{len(data_rows)} data rows supplied; the cap is {cap}. No rows were dropped; supply at most {cap}.")
        )

    seen: dict[str, int] = {}
    companies: list[Company] = []
    idx = 0
    for r in rows[1:]:
        if not any(cell.strip() for cell in r):
            continue
        idx += 1
        if len(r) != 3:
            errors.append(RowError(idx, f"expected 3 columns, got {len(r)}"))
            continue
        cid, name, url = (cell.strip() for cell in r)
        if not cid:
            errors.append(RowError(idx, "empty company_id"))
        elif cid in seen:
            errors.append(RowError(idx, f"duplicate company_id {cid!r} (first seen on row {seen[cid]})"))
        else:
            seen[cid] = idx
        if not name:
            errors.append(RowError(idx, "empty company_name"))
        if not url:
            errors.append(RowError(idx, "empty website_url"))
        elif not _is_http_url(url):
            errors.append(RowError(idx, "website_url must be an absolute http:// or https:// URL"))
        companies.append(Company(cid, name, url, idx))

    if errors:
        return ValidationResult("INPUT_INVALID", errors=tuple(errors))
    return ValidationResult("OK", companies=tuple(companies))


def validate_file(path: Path, max_rows: int | None = None) -> ValidationResult:
    path = Path(path)
    if not path.is_file():
        return ValidationResult("INPUT_INVALID", errors=(RowError(0, f"input file not found: {path}"),))
    return validate_bytes(path.read_bytes(), max_rows=max_rows)

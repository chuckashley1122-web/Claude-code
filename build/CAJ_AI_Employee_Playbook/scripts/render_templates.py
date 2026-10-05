"""Render {{placeholder}} templates from a JSON vars file, with hard guardrails.

Usage (from the build root):
    python3 scripts/render_templates.py
        -> renders outreach/email-draft.txt with outreach/render-vars.example.json
    python3 scripts/render_templates.py --template outreach/dm-draft.txt --vars my.json
    python3 scripts/render_templates.py --template agent/system-prompt.md --vars agent-vars.json
    python3 scripts/render_templates.py --omit first_name      # proves a withheld var fails
    python3 scripts/render_templates.py --for-send ...         # NEEDS_EVIDENCE values become fatal
    python3 scripts/render_templates.py --facts-form           # business-facts intake form

Template conventions:
    {{name}}                  variable from the vars file
    [BUSINESS] [HANDOFF RULE] [FOLLOWUP TASK]   named agent-prompt placeholders
    #! channel: <channel>     directive line (stripped from output)
    #! requires-evidence: <var>   var must hold a real evidence reference

Exit codes: 0 ok | 2 usage/IO | 3 unresolved or missing placeholder | 4 price found
            5 blocked claim | 6 evidence gate or NEEDS_EVIDENCE in --for-send mode
Rendering never sends anything; output goes to stdout and the out/ folder.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardrails import claim_guard, pricing_guard  # noqa: E402

DEFAULT_TEMPLATE = ROOT / "outreach" / "email-draft.txt"
DEFAULT_VARS = ROOT / "outreach" / "render-vars.example.json"
OUT_DIR = ROOT / "out"
FACTS_TEMPLATE = ROOT / "agent" / "business-facts-template.csv"

VAR_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
ANY_CURLY_RE = re.compile(r"\{\{.*?\}\}", re.DOTALL)
BRACKET_PLACEHOLDERS = {
    "[BUSINESS]": "business",
    "[HANDOFF RULE]": "handoff_rule",
    "[FOLLOWUP TASK]": "followup_task",
}
UPPER_BRACKET_RE = re.compile(r"\[[A-Z][A-Z _]{2,}\]")
NEEDS_EVIDENCE = "NEEDS_EVIDENCE"


class RenderError(Exception):
    code = 2


class UnresolvedPlaceholder(RenderError):
    code = 3


class PriceBlocked(RenderError):
    code = 4


class ClaimBlocked(RenderError):
    code = 5


class EvidenceGate(RenderError):
    code = 6


@dataclass
class Rendered:
    text: str
    channel: str
    warnings: list[str] = field(default_factory=list)


def parse_template(raw: str) -> tuple[str, dict[str, list[str]]]:
    """Split directive lines (``#! key: value``) from the template body."""
    directives: dict[str, list[str]] = {}
    body = []
    for line in raw.splitlines():
        if line.startswith("#!"):
            key, _, value = line[2:].partition(":")
            directives.setdefault(key.strip().lower(), []).append(value.strip())
        else:
            body.append(line)
    return "\n".join(body).strip("\n") + "\n", directives


def load_vars(path: Path, omit: list[str] | None = None) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RenderError(f"vars file {path} must be a JSON object")
    out = {}
    for key, value in data.items():
        if key.startswith("_") or key in (omit or []):
            continue
        if not isinstance(value, str):
            raise RenderError(f"var {key!r} must be a string")
        if ANY_CURLY_RE.search(value) or any(b in value for b in BRACKET_PLACEHOLDERS):
            raise UnresolvedPlaceholder(f"var {key!r} itself contains a placeholder")
        out[key] = value
    return out


def render_text(raw: str, variables: dict[str, str], channel: str | None = None,
                for_send: bool = False) -> Rendered:
    body, directives = parse_template(raw)
    channel = channel or (directives.get("channel") or [""])[0]
    if not channel:
        raise RenderError("no channel: add '#! channel: <name>' to the template or pass --channel")
    # Validate the channel early (raises ValueError for unknown channels).
    pricing_guard.find_violations("", channel)

    needed = sorted(set(VAR_RE.findall(body)) | {v for b, v in BRACKET_PLACEHOLDERS.items() if b in body})
    missing = [n for n in needed if n not in variables or not variables[n].strip()]
    if missing:
        raise UnresolvedPlaceholder(f"missing value(s) for placeholder(s): {', '.join(missing)}")

    for gate_var in directives.get("requires-evidence", []):
        ev = variables.get(gate_var, "").strip()
        if not ev or ev.upper().startswith(NEEDS_EVIDENCE):
            raise EvidenceGate(
                f"template requires evidence in {gate_var!r} (e.g. the passing demo test log); got {ev or 'nothing'!r}"
            )

    text = VAR_RE.sub(lambda m: variables[m.group(1)], body)
    for bracket, key in BRACKET_PLACEHOLDERS.items():
        text = text.replace(bracket, variables.get(key, bracket))

    leftovers = ANY_CURLY_RE.findall(text) + UPPER_BRACKET_RE.findall(text)
    if leftovers:
        raise UnresolvedPlaceholder(f"unresolved placeholder(s) after render: {sorted(set(leftovers))}")

    warnings = [f"{k} is {NEEDS_EVIDENCE}" for k in needed if NEEDS_EVIDENCE in variables.get(k, "")]
    if warnings and for_send:
        raise EvidenceGate("--for-send refuses NEEDS_EVIDENCE values: " + "; ".join(warnings))

    try:
        pricing_guard.assert_clean(text, channel)
    except pricing_guard.PricingViolation as exc:
        raise PriceBlocked(str(exc)) from exc
    if channel in pricing_guard.OUTBOUND_CHANNELS:
        try:
            claim_guard.assert_clean(text)
        except claim_guard.ClaimViolation as exc:
            raise ClaimBlocked(str(exc)) from exc
    return Rendered(text, channel, warnings)


def render_file(template: Path, vars_path: Path, channel: str | None = None,
                omit: list[str] | None = None, for_send: bool = False) -> Rendered:
    try:
        raw = template.read_text(encoding="utf-8")
    except OSError as exc:
        raise RenderError(f"cannot read template {template}: {exc}") from exc
    return render_text(raw, load_vars(vars_path, omit), channel, for_send)


def build_facts_form(facts_csv: Path = FACTS_TEMPLATE) -> str:
    """Generate a fill-in intake form from the business-facts template."""
    with facts_csv.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    lines = [
        "# Business facts intake form",
        "",
        "Owner or authorized manager fills every field. Each answer needs a source: a page URL",
        "on the business's own site, or a written owner confirmation with the date.",
        "Leave a field blank rather than guessing; blank facts stay NEEDS_EVIDENCE.",
        "",
    ]
    for i, row in enumerate(rows, start=1):
        lines += [
            f"## {i}. {row['fact'].capitalize()}",
            "",
            "- Answer: ______________________________",
            "- Source URL or \"owner confirmed in writing\": ______________________________",
            "- Date confirmed (YYYY-MM-DD): __________",
            "",
        ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render templates with placeholder and price guardrails.")
    ap.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    ap.add_argument("--vars", type=Path, default=DEFAULT_VARS)
    ap.add_argument("--channel")
    ap.add_argument("--omit", action="append", default=[], help="withhold a var (repeatable)")
    ap.add_argument("--for-send", action="store_true")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--facts-form", action="store_true")
    args = ap.parse_args(argv)

    if args.facts_form:
        out = args.out or OUT_DIR / "business-facts-intake-form.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_facts_form(), encoding="utf-8")
        print(f"WROTE {out}")
        return 0

    template = args.template if args.template.is_absolute() else (Path.cwd() / args.template)
    if not template.exists():
        template = ROOT / args.template
    try:
        result = render_file(template, args.vars, args.channel, args.omit, args.for_send)
    except RenderError as exc:
        print(f"RENDER FAILED ({type(exc).__name__}): {exc}")
        return exc.code
    except ValueError as exc:
        print(f"RENDER FAILED: {exc}")
        return 2
    out = args.out or OUT_DIR / f"{template.stem}.rendered{template.suffix}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(result.text, encoding="utf-8")
    print(result.text, end="")
    for w in result.warnings:
        print(f"WARNING: {w} (draft only; --for-send would refuse)")
    print(f"OK: rendered {template.name} for channel '{result.channel}', zero unresolved placeholders -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

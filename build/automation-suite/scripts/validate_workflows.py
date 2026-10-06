"""Lint the workflow JSON and scan the whole repo for secrets.

Workflow checks: valid JSON; required top-level keys; unique node names; every
node has ``notes``; ``meta.verified`` present and boolean; ``meta.source_line``
an int on the eight automations; every node type has an offline handler; every
connection points at a real node; every automation names the shared error
workflow; every HTTP endpoint has an offline route; every prompt node points at
an existing prompt and supplies all its placeholders; every outbound-sending
node has a pricing guard upstream.

Repo checks: secret-like strings (``sk-`` / ``xoxb-`` / ``ghp_`` prefixes, long
mixed alphanumeric runs near key/token/secret/password), a committed ``.env``,
and the forbidden phone number.

Exit 0 only with zero findings.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import render_prompts  # noqa: E402
from scripts.run_dry import ERROR_WORKFLOW, SUPPORTED_TYPES, UnsupportedNode, route_http  # noqa: E402

REQUIRED_KEYS = ("name", "nodes", "connections", "settings", "meta")
EXPECTED_AUTOMATIONS = 8

SECRET_PREFIXES = re.compile(
    r"(?<![A-Za-z0-9])(?:sk-[A-Za-z0-9_\-]{16,}|xox[abprs]-[A-Za-z0-9\-]{10,}|ghp_[A-Za-z0-9]{20,}"
    r"|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})")
SECRET_KEYWORD = re.compile(r"(?i)(?:key|token|secret|password|passwd)")
LONG_RUN = re.compile(r"[A-Za-z0-9_/+]{24,}")
SKIP_DIRS = {".git", "__pycache__", "out", ".venv"}
TEXT_SUFFIXES = {".py", ".json", ".md", ".txt", ".yaml", ".yml", ".example", ".gitignore", ".js", ".ts", ""}
# Built at runtime so the literal never sits in a file.
FORBIDDEN_PHONE = "866" + "-566-" + "3445"


def _outbound_nodes(wf: dict) -> list[str]:
    names = []
    for n in wf["nodes"]:
        p = n.get("parameters", {})
        if n["type"] == "n8n-nodes-base.gmail" and p.get("operation") == "send":
            names.append(n["name"])
        elif n["type"] == "n8n-nodes-base.respondToWebhook":
            names.append(n["name"])
        elif n["type"] == "n8n-nodes-base.httpRequest" and "api.ayrshare.com/api/post" in str(p.get("url", "")):
            names.append(n["name"])
    return names


def _ancestors(wf: dict, target: str) -> set[str]:
    parents: dict[str, set[str]] = {}
    for src, outs in wf.get("connections", {}).items():
        for branch in outs.get("main", []):
            for c in branch or []:
                parents.setdefault(c["node"], set()).add(src)
    seen, stack = set(), [target]
    while stack:
        for p in parents.get(stack.pop(), ()):
            if p not in seen:
                seen.add(p)
                stack.append(p)
    return seen


def _static_url(url: str) -> str:
    return re.sub(r"\{\{.*?\}\}", "x", url.lstrip("="))


def validate_workflow(wf: dict, label: str, is_automation: bool) -> list[str]:
    errs: list[str] = []
    for key in REQUIRED_KEYS:
        if key not in wf:
            errs.append(f"{label}: missing top-level key {key!r}")
    if errs:
        return errs
    meta = wf["meta"]
    if not isinstance(meta.get("verified"), bool):
        errs.append(f"{label}: meta.verified must be present and boolean")
    elif meta["verified"] is not False:
        errs.append(f"{label}: meta.verified must be false (nothing here is verified)")
    if is_automation:
        if not isinstance(meta.get("source_line"), int) or isinstance(meta.get("source_line"), bool):
            errs.append(f"{label}: meta.source_line must be an int")
        if wf["settings"].get("errorWorkflow") != ERROR_WORKFLOW:
            errs.append(f"{label}: settings.errorWorkflow must be {ERROR_WORKFLOW!r}")
    names = [n.get("name") for n in wf["nodes"]]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        errs.append(f"{label}: duplicate node names {dupes}")
    known = set(names)
    for n in wf["nodes"]:
        nl = f"{label}:{n.get('name')}"
        for k in ("name", "type", "parameters"):
            if k not in n:
                errs.append(f"{nl}: node missing {k!r}")
        if not str(n.get("notes", "")).strip():
            errs.append(f"{nl}: node has no notes")
        if n.get("type") not in SUPPORTED_TYPES:
            errs.append(f"{nl}: node type {n.get('type')!r} has no offline handler")
        p = n.get("parameters", {})
        if n.get("type") == "n8n-nodes-base.httpRequest":
            try:
                route_http(_static_url(str(p.get("url", ""))))
            except UnsupportedNode as exc:
                errs.append(f"{nl}: {exc}")
        if n.get("type") == "@n8n/n8n-nodes-langchain.openAi" and p.get("operation") == "message":
            try:
                prompt = render_prompts.load_prompt(p.get("promptId", ""))
            except (FileNotFoundError, render_prompts.PromptFormatError) as exc:
                errs.append(f"{nl}: {exc}")
            else:
                missing = [v for v in prompt.placeholders if v not in p.get("promptVariables", {})]
                if missing:
                    errs.append(f"{nl}: promptVariables missing {missing} for {prompt.id}")
    for src, outs in wf["connections"].items():
        if src not in known:
            errs.append(f"{label}: connection from unknown node {src!r}")
        for branch in outs.get("main", []):
            for c in branch or []:
                if c.get("node") not in known:
                    errs.append(f"{label}: connection {src!r} -> unknown node {c.get('node')!r}")
    by_name = {n["name"]: n for n in wf["nodes"]}
    for out_node in _outbound_nodes(wf):
        guards = [a for a in _ancestors(wf, out_node)
                  if by_name.get(a, {}).get("type") == "n8n-nodes-base.executeWorkflow"
                  and by_name.get(a, {}).get("parameters", {}).get("guard") == "pricing"]
        if not guards:
            errs.append(f"{label}:{out_node}: outbound node has no pricing guard upstream")
    return errs


def validate_dir(workflows_dir: Path) -> tuple[list[str], int]:
    errs: list[str] = []
    automations = sorted(workflows_dir.glob("0[1-8]_*.json"))
    handler = workflows_dir / f"{ERROR_WORKFLOW}.json"
    if len(automations) != EXPECTED_AUTOMATIONS:
        errs.append(f"expected {EXPECTED_AUTOMATIONS} automation workflows, found {len(automations)}")
    if not handler.is_file():
        errs.append(f"missing shared error workflow {handler.name}")
    checked = 0
    for path in automations + ([handler] if handler.is_file() else []):
        try:
            wf = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            errs.append(f"{path.name}: invalid JSON: {exc}")
            continue
        checked += 1
        errs.extend(validate_workflow(wf, path.name, path != handler))
    return errs, checked


def _iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]) or not path.is_file():
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name.startswith("."):
            yield path


def scan_secrets(root: Path) -> list[str]:
    findings: list[str] = []
    if (root / ".env").exists():
        findings.append(".env is present in the tree (must never be committed)")
    for path in _iter_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(root)
        for m in SECRET_PREFIXES.finditer(text):
            findings.append(f"{rel}:{text.count(chr(10), 0, m.start()) + 1}: secret-like prefix {m.group(0)[:6]}...")
        for m in SECRET_KEYWORD.finditer(text):
            window = text[m.end(): m.end() + 48]
            for run in LONG_RUN.finditer(window):
                value = run.group(0)
                if re.search(r"\d", value) and re.search(r"[a-z]", value) and re.search(r"[A-Z0-9]", value):
                    line = text.count("\n", 0, m.start()) + 1
                    findings.append(f"{rel}:{line}: long mixed alphanumeric run near {m.group(0)!r}")
                    break
        if FORBIDDEN_PHONE in text:
            findings.append(f"{rel}: forbidden phone number present")
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workflows-dir", type=Path, default=ROOT / "workflows")
    ap.add_argument("--scan-root", type=Path, default=ROOT)
    args = ap.parse_args(argv)
    errs, checked = validate_dir(args.workflows_dir)
    secrets = scan_secrets(args.scan_root)
    for e in errs:
        print(f"WORKFLOW  {e}")
    for s in secrets:
        print(f"SECRET    {s}")
    print(f"Validated {checked} workflow files ({EXPECTED_AUTOMATIONS} automations + shared error workflow expected): "
          f"{len(errs)} workflow finding(s)")
    print(f"Secret scan of {args.scan_root.name}: {len(secrets)} finding(s)")
    return 1 if errs or secrets else 0


if __name__ == "__main__":
    sys.exit(main())

"""Compliance scan over every generated .md / .json / .html / .txt asset.

Run: python tools/compliance_scan.py   (exit 1 on any hit; per-file report)

Checks on every file: secret/token patterns, the frozen campaign named anywhere
except the META-CHECKLIST warning banner, wrong-case or unverified GHL location
IDs, banned phrases, consumer-brand blending, asserted-but-unverified results,
and (JSON) a non-zero budget without an approval reference.
Checks on message / ad / form copy (extracted from the files): CA-J price,
guarantee, scarcity, client outcome; creative records: logo never first.
"""
from __future__ import annotations

import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from tools import guardrails as G  # noqa: E402

SCAN_SUFFIXES = {".md", ".json", ".html", ".txt"}
REPORT_REL = "out/compliance_report.md"
BUDGET_KEYS = {"daily_budget", "lifetime_budget", "campaign_budget_usd", "spend_cap", "ad_spend_cap_usd",
               "budget_exposure_usd", "daily_budget_usd"}
FORBIDDEN_STATUSES = {"Live", "Ready for launch"}


def default_work_orders_dir(root: Path) -> Path:
    return Path(root).parents[1] / "ui-work-orders"


def target_files(root: Path, work_orders_dir: Path | None = None) -> list[Path]:
    root = Path(root)
    files: list[Path] = []
    for sub in ("out", "ui-tasks", "config"):
        d = root / sub
        if d.exists():
            files += [p for p in d.rglob("*") if p.is_file() and p.suffix in SCAN_SUFFIXES]
    files += [p for p in (root / "README.md", root / ".env.example") if p.exists()]
    wo = Path(work_orders_dir) if work_orders_dir else default_work_orders_dir(root)
    if wo.exists():
        files += sorted(wo.glob("004-*.md"))
    report = root / REPORT_REL
    return sorted(p for p in files if p != report)


# --- copy extractors -------------------------------------------------------
def _fenced(text: str, info: str) -> list[str]:
    return re.findall(r"```" + re.escape(info) + r"\n(.*?)\n```", text, flags=re.S)


class _TextOnly(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("style", "script") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def html_text(text: str) -> str:
    p = _TextOnly()
    p.feed(text)
    return html.unescape(" ".join(p.parts))


def message_copy(rel: str, text: str) -> list[str]:
    """Return the prospect-facing copy contained in a file (empty if none)."""
    if rel.startswith("out/messages/"):
        return _fenced(text, "text")
    if rel.startswith("out/ads/copy/"):
        out = _fenced(text, "text")
        for block in _fenced(text, "json ad-copy"):
            d = json.loads(block)
            out += [v["text"] for v in d["primary_texts"]] + d["headlines"] + [d["cta"]]
        return out
    if rel.startswith("out/landing/") and rel.endswith(".html"):
        return [html_text(text)]
    if rel == "out/landing/content_spec.json":
        from src.landing_content import all_copy
        return [all_copy(json.loads(text))]
    return []


def _walk_budget(obj, path="") -> list[str]:
    hits = []
    if isinstance(obj, dict):
        approved = bool(str(obj.get("approval_ref", "") or "").strip())
        for k, v in obj.items():
            if k.lower() in BUDGET_KEYS:
                num = None
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    num = v
                elif isinstance(v, str) and re.fullmatch(r"\$?\s*\d+(\.\d+)?", v.strip()):
                    num = float(v.strip().lstrip("$"))
                if num and num > 0 and not approved:
                    hits.append(f"non-zero budget {path}{k}={v!r} without an approval reference")
            hits += _walk_budget(v, f"{path}{k}.")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += _walk_budget(v, f"{path}{i}.")
    return hits


def scan_file(path: Path, root: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.name
    hits: list[str] = []
    hits += G.find_secrets(text)
    hits += G.find_frozen_campaign(text, allow_banner=(rel == "ui-tasks/META-CHECKLIST.md"))
    hits += G.find_location_id_problems(text)
    hits += G.find_banned_phrases(text)
    hits += G.find_consumer_brand(text)
    hits += G.find_unverified_claims(text)
    if path.suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            hits.append(f"invalid JSON: {exc}")
            data = None
        if data is not None:
            hits += _walk_budget(data)
            if rel == "config/asset_register.json":
                hits += [f"asset {a['id']} has forbidden status {a['status']!r}" for a in data.get("assets", [])
                         if a.get("status") in FORBIDDEN_STATUSES]
    if path.name == ".env.example":
        hits += [f".env.example has a value: {line.split('=')[0]}" for line in text.splitlines()
                 if "=" in line and not line.startswith("#") and line.split("=", 1)[1].strip()]
    for chunk in message_copy(rel, text):
        hits += [f"message copy: {h}" for h in G.find_price(chunk)]
        if rel.startswith("out/ads/copy/"):
            hits += [f"ad copy: {h}" for h in G.find_ad_risk(chunk)]
    if rel == "out/ads/creative_specs.md":
        for block in _fenced(text, "json creative-records"):
            for rec in json.loads(block):
                try:
                    G.assert_logo_not_first(rec)
                except G.LogoFirstError as exc:
                    hits.append(f"creative: {exc}")
                hits += [f"creative text: {h}" for h in G.find_ad_risk(" ".join(rec["on_image_text"]))]
    return hits


def scan(root: Path = ROOT, work_orders_dir: Path | None = None) -> dict[str, list[str]]:
    root = Path(root)
    return {(p.relative_to(root).as_posix() if root in p.parents else f"ui-work-orders/{p.name}"): scan_file(p, root)
            for p in target_files(root, work_orders_dir)}


def render_report(results: dict[str, list[str]]) -> str:
    total = sum(len(v) for v in results.values())
    lines = ["# Compliance scan report", "", f"Files scanned: {len(results)}. Total hits: {total}.", "",
             "| File | Hits | Detail |", "|---|---|---|"]
    for f, hits in results.items():
        lines.append(f"| {f} | {len(hits)} | {'; '.join(hits).replace('|', '/') if hits else 'clean'} |")
    return "\n".join(lines) + "\n"


def main(root: Path = ROOT, work_orders_dir: Path | None = None) -> int:
    results = scan(root, work_orders_dir)
    report = Path(root) / REPORT_REL
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(results), encoding="utf-8")
    total = 0
    for f, hits in results.items():
        print(f"{'CLEAN' if not hits else 'HIT  '}  {f}")
        for h in hits:
            print(f"        - {h}")
        total += len(hits)
    print(f"{len(results)} files scanned, {total} hits")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())

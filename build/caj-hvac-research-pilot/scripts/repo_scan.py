"""Repo hygiene scan for the pilot root. Non-zero exit on any finding.

Checks: secret-like strings, .env absent and gitignored, no GHL location ID other
than the reference build location, and a live self-test of the frozen-campaign tripwire.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from src.guards import FrozenCampaignViolation, assert_meta_campaign_untouched  # noqa: E402

SECRET_PATTERNS = (
    ("openai-style key", re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}")),
    ("slack bot token", re.compile(r"\bxoxb-[A-Za-z0-9\-]{10,}")),
    ("github token", re.compile(r"\bghp_[A-Za-z0-9]{20,}")),
    ("credential assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|key|token|secret|password|authorization)\b[\"']?\s*[:=]\s*[\"']?(?:bearer\s+)?[A-Za-z0-9_\-/+]{20,}")),
)
# GHL location IDs are 20-character mixed-case alphanumerics.
GHL_ID_CANDIDATE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9]{20}(?![A-Za-z0-9])")
SKIP_DIRS = {"__pycache__", ".git", ".venv"}


def _looks_like_ghl_id(token: str) -> bool:
    return any(c.isupper() for c in token) and any(c.islower() for c in token) and any(c.isdigit() for c in token)


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and not any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            yield path


def scan_text(rel: str, text: str) -> list[str]:
    findings = []
    for name, pat in SECRET_PATTERNS:
        for m in pat.finditer(text):
            findings.append(f"{rel}: possible {name} at offset {m.start()}")
    allowed = config.GHL_BUILD_LOCATION_ID
    for m in GHL_ID_CANDIDATE.finditer(text):
        tok = m.group(0)
        if tok == allowed:
            continue
        if tok.casefold() == allowed.casefold():
            findings.append(f"{rel}: case-mangled GHL location ID {tok!r} (IDs are case-sensitive)")
        elif _looks_like_ghl_id(tok):
            findings.append(f"{rel}: unexpected GHL-location-like ID {tok!r}")
    return findings


def scan_root(root: Path) -> list[str]:
    findings: list[str] = []
    for path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings += scan_text(path.relative_to(root).as_posix(), text)
    if (root / ".env").exists():
        findings.append(".env exists inside the project root (secrets must stay out of the tree)")
    gi = root / ".gitignore"
    entries = {ln.strip() for ln in gi.read_text(encoding="utf-8").splitlines()} if gi.is_file() else set()
    if ".env" not in entries:
        findings.append(".gitignore does not list .env")
    return findings


def tripwire_self_test() -> bool:
    try:
        assert_meta_campaign_untouched(config.FROZEN_META_CAMPAIGN_ID, "read")
    except FrozenCampaignViolation as exc:
        print(f"tripwire: FrozenCampaignViolation raised as required -> {exc}")
        return True
    print("tripwire: DID NOT FIRE")
    return False


def main(root: Path | None = None) -> int:
    root = Path(root) if root else config.project_root()
    findings = scan_root(root)
    tripwire_ok = tripwire_self_test()
    print(f"scanned root: {root}")
    print(f"secret / ID / .env findings: {len(findings)}")
    for f in findings:
        print(f"  - {f}")
    if not tripwire_ok:
        findings.append("frozen-campaign tripwire did not fire")
    if findings:
        print("REPO SCAN FAILED")
        return 1
    print("REPO SCAN PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

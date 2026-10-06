"""Secret-name and secret-value scan over every generated/source file in the build.

Flags: token-like values (Bearer tokens, JWT shapes, 40+ char hex, key-prefixed
strings), secret env var names assigned a non-empty value, credential-shaped
literals, the disallowed location ID outside its constant, a non-empty value in
.env.example, and NEEDS_EVIDENCE config values replaced by a plausible-looking
value. Findings are reported redacted (first 4 characters at most). Exit 1 on
any hit.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from tools.paths import UI_WORK_ORDER_PREFIX, Paths, default_paths  # noqa: E402

SCAN_SUFFIXES = {".md", ".json", ".jsonl", ".html", ".ts", ".py", ".txt", ".xml", ".log", ".example"}
SKIP_DIRS = {"__pycache__", "runtime"}
LOCKED_CONFIG = {
    "build_mode": C.BUILD_MODE, "offer_url": C.BOOKING_URL, "cta_destination": C.BOOKING_URL,
    "phone": C.OWNER_PHONE, "contact_email": C.OWNER_EMAIL,
}

TOKEN_PATTERNS = [
    ("bearer_token", re.compile(r"Bearer\s+([A-Za-z0-9\-._~+/]{16,}=*)")),
    ("jwt", re.compile(r"\b(eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,})")),
    ("long_hex", re.compile(r"\b([a-fA-F0-9]{40,})\b")),
    ("prefixed_key", re.compile(r"\b((?:sk|pk|rk|pit|ghp|gho|xox[abp])[-_][A-Za-z0-9\-_]{16,})")),
]
CREDENTIAL_LITERAL = re.compile(
    r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token|client[_-]?secret)\b\s*[:=]\s*[\"']([^\"'\s]{8,})[\"']")


@dataclass
class Hit:
    file: str
    line: int
    kind: str
    redacted: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}: {self.kind}: {self.redacted}"


def redact(value: str) -> str:
    return (value[:4] + "…") if value else ""


def env_names(paths: Paths) -> list[str]:
    env = paths.root / ".env.example"
    if not env.exists():
        return []
    return [line.split("=", 1)[0].strip() for line in env.read_text(encoding="utf-8").splitlines()
            if "=" in line and not line.lstrip().startswith("#")]


def secret_env_names(names: list[str]) -> list[str]:
    return [n for n in names if re.search(r"TOKEN|SECRET|PASSWORD|KEY", n)]


def scan_text(text: str, rel: str, names: list[str]) -> list[Hit]:
    hits: list[Hit] = []
    secret_names = secret_env_names(names)
    for lineno, line in enumerate(text.splitlines(), 1):
        for kind, pattern in TOKEN_PATTERNS:
            for m in pattern.finditer(line):
                hits.append(Hit(rel, lineno, kind, redact(m.group(1))))
        for m in CREDENTIAL_LITERAL.finditer(line):
            hits.append(Hit(rel, lineno, "credential_literal", redact(m.group(2))))
        for name in secret_names:
            m = re.search(rf"\b{name}\b\s*[:=]\s*[\"']?([^\s\"'#,;)]+)", line)
            if m and m.group(1):
                hits.append(Hit(rel, lineno, f"{name}_with_value", redact(m.group(1))))
        for name in names:
            m = re.match(rf"^\s*(?:export\s+)?{name}=(\S+)", line)
            if m:
                hits.append(Hit(rel, lineno, f"{name}_dotenv_value", redact(m.group(1))))
        if C.DISALLOWED_LOCATION_ID in line and rel != "config/constants.py":
            hits.append(Hit(rel, lineno, "disallowed_location_id", redact(C.DISALLOWED_LOCATION_ID)))
    return hits


def scan_config(paths: Paths) -> list[Hit]:
    hits: list[Hit] = []
    cfg = json.loads(paths.build_config.read_text(encoding="utf-8"))
    for key, value in cfg.items():
        expected = LOCKED_CONFIG.get(key, C.NEEDS_EVIDENCE)
        if value != expected:
            hits.append(Hit("config/build_config.json", 0, f"needs_evidence_replaced:{key}", redact(str(value))))
    env = paths.root / ".env.example"
    if env.exists():
        for lineno, line in enumerate(env.read_text(encoding="utf-8").splitlines(), 1):
            if "=" in line and not line.lstrip().startswith("#") and line.split("=", 1)[1].strip():
                hits.append(Hit(".env.example", lineno, "env_example_value", redact(line.split("=", 1)[1].strip())))
    if paths.route_inventory.exists():
        origin = cfg.get("site_origin", C.NEEDS_EVIDENCE).rstrip("/")
        for row in json.loads(paths.route_inventory.read_text(encoding="utf-8"))["routes"]:
            if not row["canonical"].startswith(origin):
                hits.append(Hit("config/route_inventory.json", 0, "canonical_origin_not_from_config",
                                redact(row["canonical"])))
    return hits


def files_to_scan(paths: Paths) -> list[Path]:
    files = []
    for path in sorted(paths.root.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(paths.root).parts):
            continue
        if path.suffix in SCAN_SUFFIXES or path.name == ".env.example":
            files.append(path)
    if paths.ui_work_orders.exists():
        files += sorted(paths.ui_work_orders.glob(f"{UI_WORK_ORDER_PREFIX}-*.md"))
    unique = {f.resolve(): f for f in files}
    return list(unique.values())


def scan(paths: Paths | None = None) -> list[Hit]:
    paths = paths or default_paths()
    names = env_names(paths)
    hits: list[Hit] = []
    for path in files_to_scan(paths):
        hits += scan_text(path.read_text(encoding="utf-8", errors="replace"), paths.rel(path), names)
    hits += scan_config(paths)
    return hits


def main(argv: list[str] | None = None, paths: Paths | None = None) -> int:
    paths = paths or default_paths()
    hits = scan(paths)
    files = files_to_scan(paths)
    for hit in hits:
        print(hit)
    print(f"secret_scan: {len(files)} files scanned, {len(hits)} hits")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

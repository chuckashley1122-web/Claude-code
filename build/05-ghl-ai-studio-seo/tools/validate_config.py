"""Hard assertions on IDs, URLs, caps and approvals. Prints one line per check.

Exit 0 only when every check passes. ``run_checks`` takes any constants-like
object so tests can feed it deliberately broken values.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402

BOUND_NAMES = ["MAX_NAME_LEN", "MAX_MESSAGE_LEN", "MAX_PAYLOAD_BYTES", "UPSTREAM_TIMEOUT_S",
               "MAX_RETRIES", "IDEMPOTENCY_RETENTION_HOURS"]


def _has_ref(ref: Any) -> bool:
    return bool(ref) and str(ref).strip() not in ("", C.NEEDS_EVIDENCE)


def _bounds_ok(k: Any) -> tuple[bool, str]:
    missing = [n for n in BOUND_NAMES if not isinstance(getattr(k, n, None), int)
               or isinstance(getattr(k, n, None), bool)]
    if missing:
        return False, f"missing/non-integer: {', '.join(missing)}"
    if any(getattr(k, n) <= 0 for n in BOUND_NAMES if n != "MAX_RETRIES") or k.MAX_RETRIES < 0:
        return False, "a bound is zero or negative"
    if k.MAX_NAME_LEN >= k.MAX_MESSAGE_LEN:
        return False, "inverted: MAX_NAME_LEN >= MAX_MESSAGE_LEN"
    if k.MAX_MESSAGE_LEN >= k.MAX_PAYLOAD_BYTES:
        return False, "inverted: MAX_MESSAGE_LEN >= MAX_PAYLOAD_BYTES"
    if k.MAX_RETRIES > 2:
        return False, "MAX_RETRIES above the contract maximum of 2"
    return True, "bounds present and ordered"


def run_checks(k: Any, build_config: dict, extra_texts: dict[str, str] | None = None) -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    add("GHL_LOCATION_ID exact", getattr(k, "GHL_LOCATION_ID", None) == "UWc5vKBgFVPdxNTRAy2s",
        "must equal the case-sensitive CA-J build location")
    disallowed = getattr(k, "DISALLOWED_LOCATION_ID", "")
    targets = [str(v) for v in build_config.values()] + [getattr(k, "GHL_LOCATION_ID", "")]
    for name, text in (extra_texts or {}).items():
        targets.append(text)
    add("DISALLOWED_LOCATION_ID not a target", bool(disallowed) and not any(disallowed in t for t in targets),
        "disallowed location must not appear in config values or target IDs")
    add("BOOKING_URL", getattr(k, "BOOKING_URL", None) == "https://ca-jenterprises.com/ai")
    add("cta_destination == BOOKING_URL", build_config.get("cta_destination") == "https://ca-jenterprises.com/ai")
    add("NO_SPEND_DEFAULT is True", getattr(k, "NO_SPEND_DEFAULT", None) is True)
    add("AD_SPEND_CAP_USD == 0", getattr(k, "AD_SPEND_CAP_USD", None) == 0)
    add("TOTAL_BUILD_SPEND_USD == 0", getattr(k, "TOTAL_BUILD_SPEND_USD", None) == 0)
    add("PUBLISH_AUTHORITY == none", getattr(k, "PUBLISH_AUTHORITY", None) == "none")
    add("SITE_PUBLISH_APPROVED needs approval ref",
        getattr(k, "SITE_PUBLISH_APPROVED", None) is False
        or _has_ref(getattr(k, "SITE_PUBLISH_APPROVAL_REF", "")))
    add("DOMAIN_PURCHASE_APPROVED needs approval ref",
        getattr(k, "DOMAIN_PURCHASE_APPROVED", None) is False
        or _has_ref(getattr(k, "DOMAIN_PURCHASE_APPROVAL_REF", "")))
    add("FROZEN_CAMPAIGN_PROTECTED is True", getattr(k, "FROZEN_CAMPAIGN_PROTECTED", None) is True)
    add("QUOTE_PRICE_IN_MESSAGE is False", getattr(k, "QUOTE_PRICE_IN_MESSAGE", None) is False)
    add("LOGO_NEVER_FIRST is True", getattr(k, "LOGO_NEVER_FIRST", None) is True)
    ok, detail = _bounds_ok(k)
    add("inquiry bounds", ok, detail)
    add("locked pricing", (getattr(k, "TECH_FEE_MONTHLY_USD", None), getattr(k, "SETUP_FEE_USD", None),
                           getattr(k, "PER_BOOKED_APPOINTMENT_MIN_USD", None),
                           getattr(k, "PER_BOOKED_APPOINTMENT_MAX_USD", None)) == (650, 0, 250, 300),
        "internal reference values only")
    add("ESTIMATOR_ENABLED is False", getattr(k, "ESTIMATOR_ENABLED", None) is False)
    add("THIN_CONTENT_SIMILARITY_MAX == 0.80", getattr(k, "THIN_CONTENT_SIMILARITY_MAX", None) == 0.80)
    return checks


def load_build_config(paths: Paths) -> dict:
    return json.loads(paths.build_config.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None, paths: Paths | None = None) -> int:
    paths = paths or default_paths()
    extra = {}
    env_example = paths.root / ".env.example"
    if env_example.exists():
        extra[".env.example"] = env_example.read_text(encoding="utf-8")
    checks = run_checks(C, load_build_config(paths), extra)
    failed = 0
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {name}{('  -- ' + detail) if detail and not ok else ''}")
        failed += 0 if ok else 1
    print(f"validate_config: {len(checks) - failed}/{len(checks)} checks passed")
    return 1 if failed else 0


def constants_namespace(**overrides: Any) -> SimpleNamespace:
    """Copy of the real constants with overrides, for tests."""
    data = {n: getattr(C, n) for n in dir(C) if n.isupper()}
    data.update(overrides)
    return SimpleNamespace(**data)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

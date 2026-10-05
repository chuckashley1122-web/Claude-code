"""Hard assertions on IDs, caps and forbidden values. One line per check.
Exit code 0 only when every check passes.

Run: python tools/validate_config.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402

REQUIRED_KEYS = [
    "build_mode", "business_name", "niche", "service_area", "owner", "sales_calendar_id", "timezone",
    "facebook_page_id", "ad_account_id", "privacy_policy_url", "verified_sending_email",
    "messaging_eligibility", "payment_processor", "service_price", "service_term", "ad_budget",
    "total_test_cap", "launch_authority", "proof_assets",
]
# Config keys holding house IDs, mapped to the exact-case constant.
HOUSE_ID_KEYS = {
    "ghl_location_id": C.GHL_LOCATION_ID,
    "ghl_pipeline_id": C.GHL_PIPELINE_ID,
    "ghl_funnel_id": C.GHL_FUNNEL_ID,
    "ghl_offer_page_id": C.GHL_OFFER_PAGE_ID,
}
# IDs that are not house facts: must stay NEEDS_EVIDENCE unless evidence is recorded.
UNVERIFIED_ID_KEYS = ["sales_calendar_id", "facebook_page_id", "ad_account_id"]


def _check(results, name, ok, detail=""):
    results.append((name, bool(ok), detail))


def _walk_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)


def validate(config: dict, constants=C, env_example_text: str | None = None) -> list[tuple[str, bool, str]]:
    r: list[tuple[str, bool, str]] = []
    missing = [k for k in REQUIRED_KEYS if k not in config]
    _check(r, "required config keys present", not missing, f"missing={missing}" if missing else "")

    _check(r, "constants GHL_LOCATION_ID exact case", constants.GHL_LOCATION_ID == "UWc5vKBgFVPdxNTRAy2s",
           constants.GHL_LOCATION_ID)
    _check(r, "config ghl_location_id exact case", config.get("ghl_location_id") == "UWc5vKBgFVPdxNTRAy2s",
           str(config.get("ghl_location_id")))
    for key, exact in HOUSE_ID_KEYS.items():
        val = config.get(key)
        mangled = isinstance(val, str) and val != exact and val.lower() == exact.lower()
        _check(r, f"{key} not case-mangled", not mangled and val == exact, str(val))

    all_strings = list(_walk_strings(config))
    _check(r, "disallowed location id absent from config", constants.DISALLOWED_LOCATION_ID not in "\n".join(all_strings))

    for key in UNVERIFIED_ID_KEYS:
        val = config.get(key)
        evidence = config.get(f"{key}_evidence")
        ok = val == constants.NEEDS_EVIDENCE or (isinstance(val, str) and bool(evidence))
        _check(r, f"{key} not guessed", ok, "NEEDS_EVIDENCE" if val == constants.NEEDS_EVIDENCE else f"value={val} evidence={evidence}")

    cap = config.get("ad_spend_cap_usd", constants.AD_SPEND_CAP_USD)
    appr_spend = config.get("approval_ad_spend", constants.APPROVAL_AD_SPEND)
    _check(r, "AD_SPEND_CAP_USD == 0 unless APPROVAL_AD_SPEND", constants.AD_SPEND_CAP_USD == 0 or constants.APPROVAL_AD_SPEND is True,
           f"constants cap={constants.AD_SPEND_CAP_USD}")
    _check(r, "config ad_spend_cap_usd == 0 unless approval_ad_spend", cap == 0 or appr_spend is True, f"cap={cap} approval={appr_spend}")

    la = config.get("launch_authority")
    appr_launch = config.get("approval_launch", constants.APPROVAL_LAUNCH)
    _check(r, "LAUNCH_AUTHORITY == none unless APPROVAL_LAUNCH",
           (constants.LAUNCH_AUTHORITY == "none" or constants.APPROVAL_LAUNCH is True)
           and (la == "none" or appr_launch is True), f"launch_authority={la} approval={appr_launch}")

    _check(r, "FROZEN_CAMPAIGN_PROTECTED is true",
           constants.FROZEN_CAMPAIGN_PROTECTED is True and config.get("frozen_campaign_protected", True) is True)
    _check(r, "QUOTE_PRICE_IN_MESSAGE is false",
           constants.QUOTE_PRICE_IN_MESSAGE is False and config.get("quote_price_in_message", False) is False)
    _check(r, "build_mode known", config.get("build_mode") in constants.OBJECT_PREFIX_MAP, str(config.get("build_mode")))
    _check(r, "booking_url is the plain booking URL", config.get("booking_url", constants.BOOKING_URL) == constants.BOOKING_URL)
    _check(r, "dry_run is true", config.get("dry_run", True) is True)

    sp = config.get("service_price")
    locked_ok = isinstance(sp, dict) and sp.get("tech_fee_monthly_usd") == constants.TECH_FEE_MONTHLY_USD \
        and sp.get("setup_fee_usd") == constants.SETUP_FEE_USD \
        and sp.get("per_booked_appointment_min_usd") == constants.PER_BOOKED_APPOINTMENT_MIN_USD \
        and sp.get("per_booked_appointment_max_usd") == constants.PER_BOOKED_APPOINTMENT_MAX_USD
    _check(r, "service_price matches locked CA-J terms", locked_ok)

    if env_example_text is not None:
        bad = [ln for ln in env_example_text.splitlines()
               if ln.strip() and not ln.lstrip().startswith("#") and not re.fullmatch(r"[A-Z0-9_]+=", ln.strip())]
        _check(r, ".env.example has names only (empty values)", not bad, f"offending={bad}" if bad else "")
    return r


def main() -> int:
    config = json.loads((BUILD_ROOT / "config" / "build_config.json").read_text(encoding="utf-8"))
    env_text = (BUILD_ROOT / ".env.example").read_text(encoding="utf-8")
    results = validate(config, C, env_text)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
    failed = [n for n, ok, _ in results if not ok]
    print(f"validate_config: {len(results) - len(failed)}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

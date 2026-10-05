"""Hard assertions on house facts, IDs, caps and forbidden values.

Run: python tools/validate_config.py   (exits non-zero on any failed check)
Prints one line per check.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402

REQUIRED_CONFIG_KEYS = [
    "build_mode", "business_name", "primary_location", "service_areas", "primary_service", "additional_services",
    "main_offer", "offer_expiration", "primary_cta", "phone", "avg_response_time", "est_service_time",
    "years_in_business", "customers_served", "review_rating", "review_count", "guarantee", "usp",
    "main_pain_points", "desired_outcomes", "brand_colors", "logo_path", "hero_image_path", "before_after_images",
    "landing_page_url", "facebook_page_id", "ad_account_id", "instagram_profile_id", "pixel_id", "dataset_id",
    "ghl_project_name", "ghl_form_name", "a2p_status", "privacy_policy_url",
]
# IDs that must never be guessed or committed: real values live in .env only.
ID_KEYS_ENV_ONLY = ["facebook_page_id", "ad_account_id", "instagram_profile_id", "pixel_id", "dataset_id"]
# Evidence-gated facts that must stay NEEDS_EVIDENCE until a human supplies proof.
EVIDENCE_GATED_KEYS = ["years_in_business", "customers_served", "review_rating", "review_count", "offer_expiration",
                       "guarantee"]


def load_config(root: Path = ROOT) -> dict:
    return json.loads((Path(root) / "config" / "build_config.json").read_text(encoding="utf-8"))


def run_checks(c=C, cfg: dict | None = None) -> list[tuple[str, bool, str]]:
    cfg = load_config() if cfg is None else cfg
    ne = C.NEEDS_EVIDENCE
    results: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        results.append((name, bool(ok), detail))

    check("ghl_location_id_exact_case", c.GHL_LOCATION_ID == "UWc5vKBgFVPdxNTRAy2s",
          f"GHL_LOCATION_ID={c.GHL_LOCATION_ID!r}")
    check("ad_spend_cap_zero_without_approval", c.APPROVAL_AD_SPEND or c.AD_SPEND_CAP_USD == 0,
          f"AD_SPEND_CAP_USD={c.AD_SPEND_CAP_USD!r} APPROVAL_AD_SPEND={c.APPROVAL_AD_SPEND!r}")
    check("daily_budget_needs_evidence_without_approval", c.APPROVAL_AD_SPEND or c.DAILY_BUDGET_USD == ne,
          f"DAILY_BUDGET_USD={c.DAILY_BUDGET_USD!r}")
    check("launch_authority_none_without_approval", c.APPROVAL_LAUNCH or c.LAUNCH_AUTHORITY == "none",
          f"LAUNCH_AUTHORITY={c.LAUNCH_AUTHORITY!r} APPROVAL_LAUNCH={c.APPROVAL_LAUNCH!r}")
    ref = str(getattr(c, "DOMAIN_PURCHASE_APPROVAL_REF", "") or "").strip()
    check("domain_purchase_requires_approval_ref", not c.DOMAIN_PURCHASE_APPROVED or (ref and ref != ne),
          f"DOMAIN_PURCHASE_APPROVED={c.DOMAIN_PURCHASE_APPROVED!r} ref={'set' if ref else 'empty'}")
    check("frozen_campaign_protected", c.FROZEN_CAMPAIGN_PROTECTED is True,
          f"FROZEN_CAMPAIGN_PROTECTED={c.FROZEN_CAMPAIGN_PROTECTED!r}")
    check("quote_price_in_message_false", c.QUOTE_PRICE_IN_MESSAGE is False,
          f"QUOTE_PRICE_IN_MESSAGE={c.QUOTE_PRICE_IN_MESSAGE!r}")
    check("locked_commercial_terms",
          (c.TECH_FEE_MONTHLY_USD, c.SETUP_FEE_USD, c.PER_BOOKED_APPOINTMENT_MIN_USD,
           c.PER_BOOKED_APPOINTMENT_MAX_USD) == (650, 0, 250, 300),
          "tech fee / setup fee / per booked appointment match the locked terms")
    check("booking_url_literal", c.BOOKING_URL == "https://ca-jenterprises.com/ai", f"BOOKING_URL={c.BOOKING_URL!r}")
    check("dry_run_default", c.DRY_RUN is True and c.NO_SPEND_DEFAULT is True, "DRY_RUN and NO_SPEND_DEFAULT true")
    check("new_campaign_pattern_is_draft", c.NEW_CAMPAIGN_NAME_PATTERN.endswith("-DRAFT")
          and C.FROZEN_CAMPAIGN_NAME not in c.NEW_CAMPAIGN_NAME_PATTERN, c.NEW_CAMPAIGN_NAME_PATTERN)

    cfg_text = json.dumps(cfg)
    check("config_has_exact_key_set", sorted(cfg) == sorted(REQUIRED_CONFIG_KEYS),
          f"missing={sorted(set(REQUIRED_CONFIG_KEYS) - set(cfg))} extra={sorted(set(cfg) - set(REQUIRED_CONFIG_KEYS))}")
    check("build_mode_caj_hvac", cfg.get("build_mode") == "CAJ_HVAC", f"build_mode={cfg.get('build_mode')!r}")
    guessed = [k for k in ID_KEYS_ENV_ONLY if cfg.get(k) != ne]
    check("no_guessed_ids_in_config", not guessed, f"non-NEEDS_EVIDENCE id keys: {guessed}")
    invented = [k for k in EVIDENCE_GATED_KEYS if cfg.get(k) != ne]
    check("no_invented_proof_facts", not invented, f"evidence-gated keys with values: {invented}")
    check("disallowed_location_id_absent_from_config", C.DISALLOWED_LOCATION_ID.lower() not in cfg_text.lower(),
          "unverified location ID not used")
    check("phone_is_public_contact", cfg.get("phone") in (ne, C.OWNER_PHONE), f"phone={cfg.get('phone')!r}")
    consumer = [b for b in C.CONSUMER_BRAND_BLOCKLIST if b.lower() in cfg_text.lower()]
    check("no_consumer_brand_in_config", not consumer, f"consumer brands: {consumer}")
    check("no_price_in_config_copy", not re.search(r"\$\s?\d", cfg_text), "no dollar figure in config values")
    return results


def main(argv=None) -> int:
    results = run_checks()
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}  ({detail})")
    failed = [r for r in results if not r[1]]
    print(f"{len(results) - len(failed)}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

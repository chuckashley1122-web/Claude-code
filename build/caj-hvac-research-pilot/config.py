"""Approval gates, locked CA&J facts, caps, and status enums for the HVAC research pilot.

Single source of truth for every stage of the pipeline. No secrets live here.

Absolute rules enforced by this project:
- This pilot performs zero GHL writes (and zero GHL reads), zero sends of any kind
  (email, SMS, DM, call), and zero retrieval over the network. Page content only
  enters through controlled fixtures or human-dropped files.
- GHL location IDs are case-sensitive literals. GHL_BUILD_LOCATION_ID is
  reference-only; nothing in this project calls GoHighLevel.
- No charges or purchases of any kind. SPEND_CAP_USD is 0.00.
- The live Meta campaign FROZEN_META_CAMPAIGN_ID is frozen; any action that
  targets it raises FrozenCampaignViolation (see src/guards.py).
- Pricing constants below are INTERNAL ONLY. Meeting-first: no price ever appears
  in generated output; pricing intent routes to BOOKING_URL.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- Project location -------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
WORKFLOW_VERSION = "0.1.0"

# --- Locked CA&J facts (verbatim from SPEC-06 step 2) -------------------------
OWNER_NAME = "Chuck Ashley"
OWNER_PHONE = "512-229-9199"
OWNER_EMAIL = "chuck@ca-jconsulting.com"
LEGAL_ENTITY = "CA&J Enterprises LLC"
BUSINESS_UNIT = "CA-J Enterprises"
GHL_AGENCY_URL = "https://app.gohighlevel.com"
GHL_BUILD_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"  # case-sensitive, reference-only
GHL_BUILD_LOCATION_NAME = "CA&J Enterprises"
BOOKING_URL = "https://ca-jenterprises.com/ai"

# Internal-only commercial terms. Never rendered into any output file.
TECH_FEE_MONTHLY_USD = 650
SETUP_FEE_USD = 0  # waived
PER_BOOKED_APPOINTMENT_MIN_USD = 250
PER_BOOKED_APPOINTMENT_MAX_USD = 300
MEETING_FIRST = True

# --- Approval gates -----------------------------------------------------------
DRY_RUN = True
ALLOW_LIVE = False
ALLOW_NETWORK_RETRIEVAL = False
HUMAN_APPROVAL_REQUIRED = True
SPEND_CAP_USD = 0.00
REQUIRE_HUMAN_APPROVAL_FOR_SEND = True
REQUIRE_HUMAN_APPROVAL_FOR_GHL = True
GHL_WRITES_ENABLED = False  # constant, not env-tunable
SEND_ENABLED = False  # constant, not env-tunable

# --- Caps -----------------------------------------------------------------------
MAX_COMPANIES_PER_RUN = 3
MAX_PAGES_PER_COMPANY = 3  # homepage + at most two same-domain pages
MAX_RETRIEVAL_RETRIES = 1
MISSING_LABEL = "Not found in reviewed pages"

RESULTS_CSV_HEADER = (
    "company_id,company_name,website_url,resolved_url,status,service_area,services,"
    "contact_method,observation,hypothesis,source_urls,checked_at_utc"
)
RESULTS_CSV_COLUMNS = tuple(RESULTS_CSV_HEADER.split(","))
INPUT_CSV_HEADER = ("company_id", "company_name", "website_url")
RUN_JSON_KEYS = (
    "run_id",
    "workflow_version",
    "input_path",
    "input_hash",
    "started_at_utc",
    "finished_at_utc",
    "record_count",
    "counts_by_status",
    "overall_status",
    "fixture_mode",
    "errors",
)

# --- Statuses -------------------------------------------------------------------
RUN_STATUSES = ("completed", "partial", "failed")
COMPANY_STATUSES = ("complete", "partial", "blocked")
INPUT_STATES = ("INPUT_REQUIRED", "INPUT_INVALID")
HANDOFF_STATUSES = (
    "SPECIFICATION_READY",
    "ENVIRONMENT_BLOCKED",
    "MVP_TESTED",
    "PILOT_IN_PROGRESS",
    "V1_READY",
    "USER_REVIEW_PENDING",
)

# --- Meta freeze ------------------------------------------------------------------
FROZEN_META_CAMPAIGN_ID = "CAJ_HVAC27_US_PURCHASE_TEST02"
FROZEN_META_CAMPAIGN_EDITABLE = False

# --- Extraction vocabulary ----------------------------------------------------------
AC_SERVICE_KEYWORDS = (
    "AC repair",
    "AC installation",
    "heating maintenance",
    "furnace repair",
    "heat pump",
    "duct cleaning",
    "HVAC installation",
    "emergency HVAC",
)

# Consumer brands that must never appear in CA-J B2B output (brand separation).
CONSUMER_BRAND_TERMS = (
    "Chuck's Daily Grind",
    "Daily Grind",
    "Etsy",
    "printables",
)

# --- Environment variables (names only; see .env.example) ---------------------------
ENV_VARS = (
    "DRY_RUN",
    "ALLOW_LIVE",
    "ALLOW_NETWORK_RETRIEVAL",
    "CAJ_RESEARCH_PROJECT_ROOT",
    "CAJ_RESEARCH_MAX_COMPANIES",
    "CAJ_RESEARCH_MAX_PAGES_PER_COMPANY",
    "CAJ_RESEARCH_MAX_RETRIES",
    "CAJ_RESEARCH_UI_WORK_ORDER_DIR",
    "CAJ_RESEARCH_FIXTURE_DIR",
)

_TRUE_VALUES = {"1", "true", "yes", "on"}


def env_flag(name: str, default: bool, environ: dict | None = None) -> bool:
    """Read a boolean gate from the environment. Unset or blank -> default."""
    env = os.environ if environ is None else environ
    raw = env.get(name, "")
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in _TRUE_VALUES


class CapRaiseRefused(ValueError):
    """Raised when an env var tries to raise a cap above its locked ceiling."""


def _capped_int(name: str, ceiling: int, minimum: int, environ: dict | None) -> int:
    env = os.environ if environ is None else environ
    raw = (env.get(name) or "").strip()
    if raw == "":
        return ceiling
    try:
        value = int(raw)
    except ValueError as exc:
        raise CapRaiseRefused(f"{name} must be an integer, got a non-integer value") from exc
    if value > ceiling:
        raise CapRaiseRefused(
            f"{name}={value} exceeds the locked cap of {ceiling}. Raising it is a scope "
            "change that needs a new spec and human approval, not a config tweak."
        )
    if value < minimum:
        raise CapRaiseRefused(f"{name}={value} is below the minimum of {minimum}")
    return value


def max_companies(environ: dict | None = None) -> int:
    return _capped_int("CAJ_RESEARCH_MAX_COMPANIES", MAX_COMPANIES_PER_RUN, 1, environ)


def max_pages(environ: dict | None = None) -> int:
    return _capped_int("CAJ_RESEARCH_MAX_PAGES_PER_COMPANY", MAX_PAGES_PER_COMPANY, 1, environ)


def max_retries(environ: dict | None = None) -> int:
    return _capped_int("CAJ_RESEARCH_MAX_RETRIES", MAX_RETRIEVAL_RETRIES, 0, environ)


def project_root(environ: dict | None = None) -> Path:
    env = os.environ if environ is None else environ
    raw = (env.get("CAJ_RESEARCH_PROJECT_ROOT") or "").strip()
    return Path(raw).resolve() if raw else PROJECT_ROOT


def fixture_dir(environ: dict | None = None) -> Path:
    env = os.environ if environ is None else environ
    raw = (env.get("CAJ_RESEARCH_FIXTURE_DIR") or "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else project_root(env) / p
    return project_root(env) / "tests" / "fixtures"


def ui_work_order_dir(environ: dict | None = None) -> Path:
    env = os.environ if environ is None else environ
    raw = (env.get("CAJ_RESEARCH_UI_WORK_ORDER_DIR") or "").strip()
    p = Path(raw) if raw else Path("..") / ".." / "ui-work-orders"
    return (p if p.is_absolute() else project_root(env) / p).resolve()

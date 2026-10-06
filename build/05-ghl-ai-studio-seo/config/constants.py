"""SPEC-05 house facts, IDs, guard flags, locked pricing and inquiry-contract bounds.

Every value here is either a locked house fact supplied by Chuck Ashley or the
literal marker NEEDS_EVIDENCE. Nothing in this file is a platform-verified ID
except where noted. Locked pricing is INTERNAL REFERENCE ONLY and must never be
emitted into customer-facing copy (meeting-first; pricing intent routes to
BOOKING_URL).
"""

NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
PROPOSED_NOT_APPROVED = "PROPOSED_NOT_APPROVED"

# --- house facts ---
OWNER_NAME = "Chuck Ashley"
OWNER_PHONE = "512-229-9199"
OWNER_EMAIL = "chuck@ca-jconsulting.com"
LEGAL_ENTITY = "CA&J Enterprises LLC"
BRAND_NAME = "CA-J Enterprises"
GHL_AGENCY_URL = "https://app.gohighlevel.com"
GHL_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"  # CASE-SENSITIVE. The ONLY build location. Reference only.
GHL_LOCATION_NAME = "CA&J Enterprises"
DISALLOWED_LOCATION_ID = "nuhFUYu0ZF9Eswiz9P79"  # named in the source as a different, unverified location
BOOKING_URL = "https://ca-jenterprises.com/ai"  # literal, verified destination. Never rewritten.
SITE_ORIGIN = NEEDS_EVIDENCE  # no domain is owned or confirmed for this build
PROPOSED_ROUTES = [
    "/",
    "/services/lead-generation",
    "/services/reputation-management",
    "/services/paid-advertising",
    "/locations/austin",
    "/locations/round-rock",
    "/about",
    "/contact",
]  # PROPOSED_NOT_APPROVED
BUILD_MODE = "draft_only"
DRY_RUN = True

# --- locked pricing (INTERNAL REFERENCE ONLY; must never appear in customer-facing copy) ---
TECH_FEE_MONTHLY_USD = 650
SETUP_FEE_USD = 0  # waived
PER_BOOKED_APPOINTMENT_MIN_USD = 250
PER_BOOKED_APPOINTMENT_MAX_USD = 300
QUOTE_PRICE_IN_MESSAGE = False  # MEETING-FIRST: no price in email, chat, page copy or AI reply

# --- guard flags ---
NO_SPEND_DEFAULT = True
AD_SPEND_CAP_USD = 0  # stays 0 until a human authorises an exact amount in writing
TOTAL_BUILD_SPEND_USD = 0  # this spec authorises zero spend
LOGO_NEVER_FIRST = True  # creatives lead with outcome/offer; logo = small footer disclaimer only
FROZEN_CAMPAIGN_NAME = "CAJ_HVAC27_US_PURCHASE_TEST02"
FROZEN_CAMPAIGN_PROTECTED = True  # never edited / paused / duplicated. Out of scope here.
PUBLISH_AUTHORITY = "none"
SITE_PUBLISH_APPROVED = False
SITE_PUBLISH_APPROVAL_REF = ""
DOMAIN_PURCHASE_APPROVED = False
DOMAIN_PURCHASE_APPROVAL_REF = ""
APPROVAL_DOMAIN_PURCHASE = False
ESTIMATOR_ENABLED = False  # phase 2; blocked until approved real pricing rules exist
THIN_CONTENT_SIMILARITY_MAX = 0.80  # above this, refuse to emit a near-duplicate page

# --- inquiry contract (authored guidance, not a platform contract) ---
INQUIRY_ALLOWED_FIELDS = [
    "submission_id", "name", "email", "phone", "service_interest", "service_area",
    "message", "source_page", "consent",
]
INQUIRY_REQUIRED_FIELDS = ["name", "submission_id"]
INQUIRY_PRIVILEGED_FIELDS_REJECTED = [
    "location_id", "pipeline_id", "stage_id", "tags", "assigned_user",
    "opportunity_id", "contact_id",
]
MAX_NAME_LEN = 120
MAX_MESSAGE_LEN = 2000
MAX_PAYLOAD_BYTES = 16384
UPSTREAM_TIMEOUT_S = 10
MAX_RETRIES = 2
IDEMPOTENCY_RETENTION_HOURS = 24
SERVICE_ALLOWLIST = NEEDS_EVIDENCE  # derived from verified services; empty allowlist => reject all
ALLOWED_SOURCE_ORIGINS = NEEDS_EVIDENCE
RATE_LIMIT_CONFIG = NEEDS_EVIDENCE  # no rate-limit capability verified on the platform
STATUS_SAVED = 201
STATUS_QUEUED = 202  # only if a real durable queue exists; UI text = "received for processing"
STATUS_INVALID = 422
STATUS_BAD_REQUEST = 400
STATUS_THROTTLED = 429
STATUS_UPSTREAM_BAD = 502
STATUS_UPSTREAM_FAIL = 503
TEST_TAG = "hermes_ai_studio_test"

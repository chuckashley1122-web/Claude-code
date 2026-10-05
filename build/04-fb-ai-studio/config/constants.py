"""House facts, IDs, guard flags and locked commercial terms for SPEC-04.

Single place for every fixed value the build relies on. Nothing in here is a
secret: real tokens, pixel IDs and dataset IDs live only in a local `.env`
(see `.env.example`), never in the repo.

The locked commercial terms below are INTERNAL ONLY. Meeting-first rule: no
price ever appears in prospect-facing copy; pricing intent routes to
BOOKING_URL.
"""

# --- Public contact (the only contact details any output may use) ---------
OWNER_NAME = "Chuck Ashley"
OWNER_PHONE = "512-229-9199"
OWNER_EMAIL = "chuck@ca-jconsulting.com"
LEGAL_ENTITY = "CA&J Enterprises LLC"
BUSINESS_DISPLAY_NAME = "CA-J Enterprises"

# --- GoHighLevel (reference only; this build never calls GHL) -------------
GHL_AGENCY_URL = "https://app.gohighlevel.com"
GHL_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"   # CASE-SENSITIVE. The ONLY build location.
GHL_PIPELINE_ID = "U95kdMryqjDqu7JeFrdw"    # existing "CA&J Demo - Lead Pipeline" - do not overwrite
GHL_PIPELINE_NAME = "CA&J Demo - Lead Pipeline"
GHL_PIPELINE_STAGES = ["New Lead", "Contacted", "Appointment Booked", "Quote Sent", "Job Won", "Lost / Not a Fit"]
GHL_FUNNEL_ID = "5WjNmZXpaD1tXVzvgRzn"    # CA-J Appointment Engine
GHL_OFFER_PAGE_ID = "3R0KG1iCnpPCBDwLTgTT"
NEW_PIPELINE_NAME = "Meta Ads Leads"          # separate from the existing pipeline
NEW_PIPELINE_STAGES = ["New Lead", "Hot Lead / Responded", "Closed (won)", "Lost"]
BOOKING_URL = "https://ca-jenterprises.com/ai"
DOMAIN_OFFER_SLUG = "offer"                 # offer.<domain>
DOMAIN_CALL_SLUG = "call"
DOMAIN_CONTACT_SLUG = "contact"
CNAME_VALUE = "NEEDS_EVIDENCE"          # source says vibe.cloud; unverified

# --- Locked CA-J commercial terms (INTERNAL ONLY, never in outbound copy) --
TECH_FEE_MONTHLY_USD = 650      # locked
SETUP_FEE_USD = 0               # locked: waived
PER_BOOKED_APPOINTMENT_MIN_USD = 250    # locked
PER_BOOKED_APPOINTMENT_MAX_USD = 300    # locked
QUOTE_PRICE_IN_MESSAGE = False   # MEETING-FIRST: no price in email, chat or AI reply

# --- Frozen live campaign tripwire ----------------------------------------
FROZEN_CAMPAIGN_NAME = "CAJ_HVAC27_US_PURCHASE_TEST02"
FROZEN_CAMPAIGN_PROTECTED = True  # never edit / pause / duplicate-in-place; new work = separate NEW draft
NEW_CAMPAIGN_NAME_PATTERN = "CAJ-FB-HVAC-Leads-{YYYYMMDD}-DRAFT"
NEW_CAMPAIGN_NAME_REGEX = r"^CAJ-FB-HVAC-Leads-\d{8}-DRAFT$"

# --- Creative rules ---------------------------------------------------------
LOGO_NEVER_FIRST = True     # creatives lead with pain or outcome; logo = small footer disclaimer only
ALLOWED_OPENING_ELEMENT_TYPES = ("pain", "outcome")
REQUIRED_IMAGE_DIMENSIONS = (1080, 1080)
ALTERNATE_IMAGE_DIMENSIONS = (1080, 1350)
MAX_VIDEO_SECONDS = 30
ABSOLUTE_MAX_VIDEO_SECONDS = 60

# --- Spend / launch gates ---------------------------------------------------
NO_SPEND_DEFAULT = True
DRY_RUN = True
AD_SPEND_CAP_USD = 0        # stays 0 until a human authorizes an exact amount in writing
DAILY_BUDGET_USD = "NEEDS_EVIDENCE"   # source's $70/day is instructor guidance, not authority
APPROVAL_AD_SPEND = False
APPROVAL_LAUNCH = False
APPROVAL_DOMAIN_PURCHASE = False
DOMAIN_PURCHASE_APPROVED = False
DOMAIN_PURCHASE_APPROVAL_REF = ""
LAUNCH_AUTHORITY = "none"
BUILD_MODE = "CAJ_HVAC"
NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
DISALLOWED_LOCATION_ID = "nuhFUYu0ZF9Eswiz9P79"

# --- CAPI ---------------------------------------------------------------------
CAPI_EVENT_TYPE = "Funnel Event"
CAPI_EVENT_TO_SEND = "Lead"
CAPI_CUSTOM_MAPPING = "OFF"
CAPI_CURRENCY = "USD"
PIXEL_ID_ENV = "META_PIXEL_ID"
DATASET_ID_ENV = "META_DATASET_ID"
CAPI_ACCESS_TOKEN_ENV = "META_CAPI_ACCESS_TOKEN"

# --- Brand separation ---------------------------------------------------------
B2B_BRANDS = (
    "CA-J Enterprises", "ca-jenterprises.com", "cajaimarketing.com",
    "CA-J Consulting", "ca-jconsulting.com",
)
# Consumer brands that must never appear in B2B output.
CONSUMER_BRAND_BLOCKLIST = ("Chuck's Daily Grind", "Daily Grind coffee", "Etsy")
# Built by concatenation so the forbidden number never appears literally.
FORBIDDEN_PHONE_NUMBERS = ("866" + "-566-" + "3445",)

# --- Paid services this build touches on (all blocked; approval required) ----
SPEND_ITEMS = [
    {"service": "Meta ad spend (campaign daily budget)", "purpose": "Delivering the NEW draft Leads campaign once approved",
     "approval": "approval required", "cost": "NEEDS_EVIDENCE"},
    {"service": "Meta ad account payment method", "purpose": "Required by Meta before any ad can deliver",
     "approval": "approval required", "cost": "NEEDS_EVIDENCE"},
    {"service": "Domain purchase (registrar)", "purpose": "Domain for the offer./call./contact. landing-page subdomain",
     "approval": "approval required", "cost": "NEEDS_EVIDENCE"},
    {"service": "GoHighLevel sub-account / AI Studio access", "purpose": "Hosting the landing page, form, pipeline and workflows",
     "approval": "approval required", "cost": "NEEDS_EVIDENCE"},
    {"service": "A2P 10DLC registration for the GHL number", "purpose": "Sending the speed-to-lead SMS sequence and owner SMS alerts",
     "approval": "approval required", "cost": "NEEDS_EVIDENCE"},
    {"service": "GHL SMS / email usage", "purpose": "Per-message sending for the follow-up sequence",
     "approval": "approval required", "cost": "NEEDS_EVIDENCE"},
    {"service": "AI image / video generation tool", "purpose": "Producing the 1080x1080 images and 30-second videos from the creative briefs",
     "approval": "approval required", "cost": "NEEDS_EVIDENCE"},
]

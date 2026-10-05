"""House facts, locked CA-J commercial terms, ID constants and guard flags.

Literals only. Every other module imports from here; nothing is looked up.
These values are INTERNAL. No price defined here may appear in prospect-facing
copy (meeting-first): pricing intent routes to BOOKING_URL.
"""

OWNER_NAME = "Chuck Ashley"
OWNER_PHONE = "512-229-9199"
OWNER_EMAIL = "chuck@ca-jconsulting.com"
LEGAL_ENTITY = "CA&J Enterprises LLC"
BRAND_NAME = "CA-J Enterprises"
GHL_AGENCY_URL = "https://app.gohighlevel.com"
GHL_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"   # CASE-SENSITIVE. The ONLY build location. Reference only.
GHL_PIPELINE_ID = "U95kdMryqjDqu7JeFrdw"    # "CA&J Demo - Lead Pipeline"
GHL_PIPELINE_NAME = "CA&J Demo - Lead Pipeline"
GHL_PIPELINE_STAGES = ["New Lead", "Contacted", "Appointment Booked", "Quote Sent", "Job Won", "Lost / Not a Fit"]
GHL_FUNNEL_ID = "5WjNmZXpaD1tXVzvgRzn"      # CA-J Appointment Engine
GHL_OFFER_PAGE_ID = "3R0KG1iCnpPCBDwLTgTT"
BOOKING_URL = "https://ca-jenterprises.com/ai"

# Locked CA-J commercial terms (internal only; presented on the call only).
TECH_FEE_MONTHLY_USD = 650
SETUP_FEE_USD = 0                       # waived
PER_BOOKED_APPOINTMENT_MIN_USD = 250
PER_BOOKED_APPOINTMENT_MAX_USD = 300

MEETING_FIRST = True                    # never quote price in email/chat/AI reply
QUOTE_PRICE_IN_MESSAGE = False
FROZEN_CAMPAIGN_NAME = "CAJ_HVAC27_US_PURCHASE_TEST02"
FROZEN_CAMPAIGN_PROTECTED = True        # never edit / pause / duplicate-in-place; new work = separate NEW draft
NEW_CAMPAIGN_NAME_PATTERN = "CAJ-HT-HVAC-Leads-{YYYYMMDD}"   # new draft only, never activated by this build
LOGO_NEVER_FIRST = True                 # creatives lead with outcome/offer; logo = small footer disclaimer only
NO_SPEND_DEFAULT = True
AD_SPEND_CAP_USD = 0                    # remains 0 until a human sets an authorized amount in writing
APPROVAL_AD_SPEND = False
APPROVAL_LAUNCH = False
LAUNCH_AUTHORITY = "none"
DRY_RUN_DEFAULT = True
BUILD_MODE = "CAJ_HVAC"                 # or SOURCE_REAL_ESTATE
OBJECT_PREFIX_MAP = {"CAJ_HVAC": "CAJ-HT-HVAC", "SOURCE_REAL_ESTATE": "CAJ-HT-RE"}
NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
DISALLOWED_LOCATION_ID = "nuhFUYu0ZF9Eswiz9P79"   # unverified; build must reject it

# House object IDs that must keep exact case wherever they appear.
HOUSE_IDS = {
    "GHL_LOCATION_ID": GHL_LOCATION_ID,
    "GHL_PIPELINE_ID": GHL_PIPELINE_ID,
    "GHL_FUNNEL_ID": GHL_FUNNEL_ID,
    "GHL_OFFER_PAGE_ID": GHL_OFFER_PAGE_ID,
}

# B2B brands this build may name. Consumer brands must never appear in B2B output.
B2B_BRANDS = ["CA-J Enterprises", "ca-jenterprises.com", "cajaimarketing.com", "CA-J Consulting", "ca-jconsulting.com"]
CONSUMER_BRANDS = ["Daily Grind", "Etsy"]

# Banned phrasing (built by concatenation so the literal never sits in a file).
BANNED_PHRASES = [
    "qualified" + " appointment",
    "shows" + " up",
    "10-25" + " leads/month",
    "10–25" + " leads/month",
]

# The only permitted public contact phone; this number is never used.
FORBIDDEN_PHONE = "866-566" + "-3445"

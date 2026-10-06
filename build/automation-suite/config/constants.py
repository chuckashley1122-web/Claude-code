"""Locked CA&J business facts and approval-gate constants for the automation suite.

GHL location IDs are case-sensitive. All GoHighLevel (GHL) work is UI-only: this
suite never calls a GHL API and the build location id below is reference-only.
No charges or purchases of any kind may be made without explicit human approval.

The commercial terms are INTERNAL ONLY. Meeting-first: no price ever appears in
outbound or prospect-facing copy; pricing intent is routed to BOOKING_URL.
"""

# --- Locked CA&J contact facts (public contact only) ---
OWNER_NAME = "Chuck Ashley"
OWNER_PHONE = "512-229-9199"
OWNER_EMAIL = "chuck@ca-jconsulting.com"
LEGAL_ENTITY = "CA&J Enterprises LLC"

# --- GoHighLevel (reference-only, UI-only) ---
GHL_AGENCY_URL = "https://app.gohighlevel.com"
GHL_BUILD_LOCATION_ID = "UWc5vKBgFVPdxNTRAy2s"
GHL_BUILD_LOCATION_NAME = "CA&J Enterprises"

# --- Meeting-first routing ---
BOOKING_URL = "https://ca-jenterprises.com/ai"
MEETING_FIRST = True

# --- Spend / run mode ---
SPEND_CAP_USD = 0.00
DRY_RUN = True

# --- Locked commercial terms (internal only, never in outbound copy) ---
TECH_FEE_MONTHLY_USD = 650
SETUP_FEE_USD = 0  # waived
PER_BOOKED_APPOINTMENT_MIN_USD = 250
PER_BOOKED_APPOINTMENT_MAX_USD = 300

# --- Approval gates (imported by every outbound node handler) ---
REQUIRE_HUMAN_APPROVAL_FOR_SPEND = True
REQUIRE_HUMAN_APPROVAL_FOR_OUTBOUND = True
REQUIRE_HUMAN_APPROVAL_FOR_PUBLISH = True
REQUIRE_HUMAN_APPROVAL_FOR_GHL = True

# --- Caps ---
# Source line 35; a training target, not a validated sending limit.
DAILY_EMAIL_CAP_PER_INBOX = 30
# Source line 36.
FOLLOWUP_SEQUENCE_MAX = 2
# Source claim (line 15), unverified -- do not treat as provisioned capacity.
VOICE_CONCURRENCY_REQUESTED = 10
SUPPRESSION_CHECK_REQUIRED = True
OPT_OUT_HONOR_REQUIRED = True


def workflow_vars() -> dict:
    """Values exposed to workflow expressions as ``$vars.<NAME>``.

    Commercial terms are deliberately excluded so no workflow can template a
    price into outbound copy.
    """
    return {
        "OWNER_NAME": OWNER_NAME,
        "OWNER_EMAIL": OWNER_EMAIL,
        "BOOKING_URL": BOOKING_URL,
        "MEETING_FIRST": MEETING_FIRST,
        "DAILY_EMAIL_CAP_PER_INBOX": DAILY_EMAIL_CAP_PER_INBOX,
        "FOLLOWUP_SEQUENCE_MAX": FOLLOWUP_SEQUENCE_MAX,
        "SENDER_FIRST_NAME": OWNER_NAME.split()[0],
    }

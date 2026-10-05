"""Pixel / CAPI spec -> out/pixel_capi_spec.md + out/capi_settings.json (SPEC-04 step 16).

Token and pixel/dataset IDs are referenced by env var NAME only.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.common import DRAFT_NOTICE, NE, md_table  # noqa: E402

SIGNALS = ["email", "phone", "first name", "last name", "city", "state", "zip", "country", "fbp", "fbc"]
EVENTS = ["Contact", "Lead"]
OPTIONAL_EVENTS = {"Schedule": "only if calendar booking is added to the page"}


def capi_settings() -> dict:
    return {
        "status": "Draft",
        "event_type": C.CAPI_EVENT_TYPE,
        "event_to_send": C.CAPI_EVENT_TO_SEND,
        "custom_mapping": C.CAPI_CUSTOM_MAPPING,
        "test_code": "",
        "ltv": NE,
        "currency": C.CAPI_CURRENCY,
        "pixel_id_env": C.PIXEL_ID_ENV,
        "dataset_id_env": C.DATASET_ID_ENV,
        "access_token_env": C.CAPI_ACCESS_TOKEN_ENV,
        "events_to_track": EVENTS,
        "optional_events": OPTIONAL_EVENTS,
        "identify_by": "Event ID",
        "signals": SIGNALS,
        "automatic_advanced_matching": True,
        "pixel_name": f"{NE} (format: '<BUSINESS> Pixel')",
    }


def render() -> str:
    s = capi_settings()
    steps_pixel = [
        "Business Settings (gear) > Data Sources > Datasets and Pixels > Add > Create Dataset/Pixel.",
        f"Name it `<BUSINESS> Pixel` (exact name {NE}). No category needed > Create.",
        "When prompted to connect it to the ad account, answer **Yes**. Then Connected Assets tab > confirm the ad account.",
        "Events Manager > Setup Meta Pixel > Install code manually > copy the base code. **Do not paste it into any "
        "repo file.** Install it via the AI Studio chat prompt: `Install this pixel code on this project: [PASTE CODE]`.",
        "Back in Events Manager > Continue > turn on **Automatic Advanced Matching** > Done.",
        "AI Studio > Publish > Publish Changes > Publish (deploys the pixel; PageView only, for future retargeting).",
    ]
    steps_capi = [
        "Events Manager > Setup Conversions API (new pixel) or Manage Integrations > Setup Conversions API (existing).",
        "Setup Manually > Next > **Conversions API and Meta Pixel** > Start CAPI Setup.",
        f"Business category: the closest match, or 'Other business category' ({NE} which).",
        "Events: **Contact** and **Lead** (add **Schedule** only if calendar booking is added).",
        "For each event: identify by **Event ID**; check every signal box: " + ", ".join(SIGNALS) + ".",
        "Continue to the Access Token screen > select the dataset > Generate. Store the token ONLY in the GHL action "
        f"field and a local `.env` as `{C.CAPI_ACCESS_TOKEN_ENV}`.",
        f"Finish > Settings > copy the Pixel/Dataset ID into a local `.env` as `{C.PIXEL_ID_ENV}` / `{C.DATASET_ID_ENV}`.",
    ]
    return "\n".join([
        "# Pixel / Dataset and Conversions API spec", "", DRAFT_NOTICE, "",
        "## Prerequisites (CAPI fails without both)",
        "1. A valid subdomain is connected to the AI Studio page (see `ui-tasks/DNS-CHECKLIST.md`).",
        "2. The form is natively connected to the GHL CRM (AI Studio prompt: 'Connect or integrate the form on the "
        "landing page to my CRM').",
        "**No valid connected subdomain + no native form-to-CRM connection = CAPI fails.**", "",
        "## Part 1 - Pixel / Dataset (human, Business Settings)", *[f"{i}. {t}" for i, t in enumerate(steps_pixel, 1)], "",
        "## Part 2 - Conversions API (human, Events Manager)", *[f"{i}. {t}" for i, t in enumerate(steps_capi, 1)], "",
        "## Settings carried into `capi_settings.json`",
        md_table(["Key", "Value"], [[k, v if not isinstance(v, (list, dict)) else str(v)] for k, v in s.items()]), "",
        "## Secrets policy",
        "The access token, pixel ID and dataset ID are referenced **by env var name only**. No value is written to any "
        "spec, config, output, log or HTML mock.", "",
        "## Unverified",
        "- The source's '100% lead tracking' is a marketing claim, not a verified result.",
        "- Available signal fields, matching settings and attribution windows in the live account are "
        f"`{NE}`; where a field is unavailable, record the limitation rather than inventing attribution.", "",
    ])


def build(ctx) -> list[Path]:
    ctx.state.record_blocker("pixel_id", f"Pixel/Dataset created in Business Settings (value kept in .env as {C.PIXEL_ID_ENV})",
                             "Workflow 03, campaign ad-set dataset field", "Human completes META-CHECKLIST Pixel section")
    return [ctx.write_asset("out/pixel_capi_spec.md", render(), "pixel_capi_spec", "src/pixel_capi_spec.py"),
            ctx.write_json("out/capi_settings.json", capi_settings(), "capi_settings", "src/pixel_capi_spec.py")]

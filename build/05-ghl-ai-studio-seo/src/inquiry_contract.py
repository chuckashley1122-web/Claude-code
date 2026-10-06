"""Inquiry contract as data -> out/inquiry_contract.json + out/inquiry_contract.md.

This is authored guidance, not a platform-supplied endpoint. ``POST /api/inquiries``
is a proposal; AI Studio may expose server functions only through a supported
equivalent path.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, emit  # noqa: E402

UI_TEXT = {
    "saved": "Thanks - your inquiry was saved.",
    "queued": "Your inquiry was received for processing.",
    "invalid": "Please check the highlighted fields and try again.",
    "throttled": "Too many attempts. Please wait a moment and try again.",
    "upstream": "We could not save your inquiry right now. Your entries are kept on this page; please try again.",
}


def _allowlist(value) -> list:
    return [] if value == C.NEEDS_EVIDENCE or not value else list(value)


def contract() -> dict:
    return {
        "nature": "Authored implementation guidance, not a platform contract or a video-supplied endpoint.",
        "proposed_operation": "POST /api/inquiries",
        "path_status": "PROPOSED - use the supported AI Studio server-function equivalent; the REST path is "
                       "not asserted to exist.",
        "fields": C.INQUIRY_ALLOWED_FIELDS,
        "required": {"all_of": ["submission_id", "name", "service_interest"],
                     "one_of_valid": ["email", "phone"]},
        "privileged_fields_rejected": C.INQUIRY_PRIVILEGED_FIELDS_REJECTED,
        "privileged_values_source": "server configuration only (environment variables by name)",
        "bounds": {"MAX_NAME_LEN": C.MAX_NAME_LEN, "MAX_MESSAGE_LEN": C.MAX_MESSAGE_LEN,
                   "MAX_SERVICE_AREA_LEN": C.MAX_NAME_LEN, "MAX_PAYLOAD_BYTES": C.MAX_PAYLOAD_BYTES},
        "service_allowlist": _allowlist(C.SERVICE_ALLOWLIST),
        "service_allowlist_status": "NEEDS_EVIDENCE - empty allowlist rejects every submission"
        if C.SERVICE_ALLOWLIST == C.NEEDS_EVIDENCE else "configured",
        "allowed_source_origins": _allowlist(C.ALLOWED_SOURCE_ORIGINS),
        "upstream_timeout_s": C.UPSTREAM_TIMEOUT_S,
        "retry_policy": {"max_retries": C.MAX_RETRIES, "backoff": "exponential (0.5 s, 1 s), at least any "
                         "upstream Retry-After", "same_submission_id": True,
                         "never_retry": ["validation errors", "permission/auth errors", "unconfigured integration"]},
        "idempotency": {"key": "submission_id", "retention_hours": C.IDEMPOTENCY_RETENTION_HOURS,
                        "replay": "a repeat request returns the prior outcome and never creates a second lead"},
        "rate_limit": C.RATE_LIMIT_CONFIG,
        "status_map": [
            {"status": C.STATUS_SAVED, "when": "only after the CRM save is confirmed", "body": "opaque inquiry "
             "reference only", "ui_text": UI_TEXT["saved"]},
            {"status": C.STATUS_QUEUED, "when": "only when a real durable queue accepted the request",
             "ui_text": UI_TEXT["queued"], "never": "saved to CRM"},
            {"status": C.STATUS_BAD_REQUEST, "when": "malformed JSON or payload over the byte cap",
             "ui_text": UI_TEXT["invalid"]},
            {"status": C.STATUS_INVALID, "when": "field validation failed", "ui_text": UI_TEXT["invalid"]},
            {"status": C.STATUS_THROTTLED, "when": "throttled by a configured rate limiter",
             "ui_text": UI_TEXT["throttled"]},
            {"status": C.STATUS_UPSTREAM_BAD, "when": "upstream rejected the request (auth/permission/bad "
             "response) or did not confirm the save", "ui_text": UI_TEXT["upstream"]},
            {"status": C.STATUS_UPSTREAM_FAIL, "when": "upstream timeout/unavailable after bounded retries, or "
             "integration not configured", "ui_text": UI_TEXT["upstream"]},
        ],
        "escalation_path": C.BOOKING_URL,
        "on_failure": "retain entered form values and show a useful retry message plus the booking link",
        "pii": "raw personal information never appears in logs or public responses",
    }


def render_markdown(c: dict) -> str:
    lines = ["# Inquiry contract (SPEC-05)", "", f"**{c['nature']}**", "",
             f"Proposed operation: `{c['proposed_operation']}` - {c['path_status']}", "",
             "## Fields", "", ", ".join(f"`{f}`" for f in c["fields"]), "",
             "Required: `submission_id`, `name`, a `service_interest` in the allowlist, and at least one valid "
             "contact method (`email` or `phone`); any contact method supplied must be valid.", "",
             "Rejected if supplied by the client (server configuration only): "
             + ", ".join(f"`{f}`" for f in c["privileged_fields_rejected"]), "",
             "## Bounds", ""]
    lines += [f"- `{k}` = {v}" for k, v in c["bounds"].items()]
    lines += ["", f"Service allowlist: {c['service_allowlist_status']}.",
              f"Allowed source origins: {c['allowed_source_origins'] or C.NEEDS_EVIDENCE}.",
              f"Rate limiting: {c['rate_limit']} (the public endpoint is not claimed to be protected).", "",
              "## Timeout, retry and idempotency", "",
              f"- Upstream timeout: {c['upstream_timeout_s']} s.",
              f"- Retries: at most {c['retry_policy']['max_retries']}, {c['retry_policy']['backoff']}, same "
              "`submission_id`; never retry validation, permission or unconfigured-integration errors.",
              f"- Idempotency: keyed on `submission_id`, retained {c['idempotency']['retention_hours']} h; "
              f"{c['idempotency']['replay']}.",
              "- Contact matching (CRM upsert) and submission idempotency solve different problems.", "",
              "## Status map", "", "| Status | When | UI text |", "|---|---|---|"]
    lines += [f"| {s['status']} | {s['when']} | {s['ui_text']} |" for s in c["status_map"]]
    lines += ["", f"202 UI text must read \"received for processing\", never \"saved to CRM\".", "",
              f"Escalation path on any failure: {c['escalation_path']}", ""]
    return "\n".join(lines)


def build(paths: Paths | None = None) -> dict:
    paths = paths or default_paths()
    c = contract()
    emit("inquiry_contract_json", paths.out / "inquiry_contract.json", c, STATUS.DRAFT, paths,
         source="src/inquiry_contract.py")
    emit("inquiry_contract_md", paths.out / "inquiry_contract.md", render_markdown(c), STATUS.DRAFT, paths,
         source="src/inquiry_contract.py")
    return c


if __name__ == "__main__":
    build()
    print("inquiry contract written")

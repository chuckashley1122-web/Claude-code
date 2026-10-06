"""Paste-ready AI Studio prompt pack -> out/ai_studio_prompt_pack.md.

Prompts 1-7, the master instruction and the required final-status format are
transcribed verbatim from the source playbook (docs/playbooks/05-ghl-ai-studio-seo.md).
The source's "20-prompt revised playbook" was never supplied and is not
reconstructed here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from tools import guardrails as G  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, emit  # noqa: E402

PROMPTS = [
    ("Prompt 1", "Project inspection",
     "Inspect this selected project before editing. Report its framework, routes, rendering behavior, server "
     "capabilities, secrets interface, integrations, and current errors. Identify the smallest reversible path to "
     "SEO-ready public pages plus a server-side inquiry flow. Preserve working code and existing conversion routes. "
     "List missing capabilities with evidence. Do not claim a migration has happened until verified."),
    ("Prompt 2", "Build the page foundation",
     "Use the approved business inputs and page map to implement responsive public pages in the supported project "
     "framework. Put substantive page content, titles, canonical URLs, H1s, and internal anchor links in initial "
     "HTML. Preserve existing functional routes and the approved conversion destination. Use unique intent-driven "
     "copy, accessible controls, and descriptive image text. Do not invent business facts or create thin location "
     "pages. Report every route added or changed."),
    ("Prompt 3", "Search verification",
     "Audit every public route using initial response HTML and browser rendering. Report HTTP status, title, H1, "
     "canonical, visible core copy, internal links, indexability, and hydration errors. Fix only confirmed "
     "failures, preserving working behavior. Verify sitemap and redirects against the route inventory. Distinguish "
     "missing content from rendering delays. Re-test changed routes and the main conversion path."),
    ("Prompt 4", "Implement the inquiry function",
     "Implement the specified inquiry contract using supported server-only functions. Add validation, field "
     "allowlisting, bounded execution, idempotency, and truthful success/failure states. Keep external credentials "
     "out of browser code. Connect only to verified server configuration. Use a mock adapter for draft testing when "
     "access is missing, label it clearly, and leave production integration BLOCKED until a real CRM record is "
     "verified."),
    ("Prompt 5", "Integration audit",
     "Trace a synthetic inquiry from browser to server to GHL. Show redacted request/response evidence and the "
     "persisted CRM record IDs. Verify destination, field mapping, retries, duplicates, and failure UI. Prove that "
     "no browser request carries a private API token. Mark any mocked or unverified step BLOCKED. Make minimal "
     "repairs and re-run this same trace."),
    ("Prompt 6", "Add the optional calculator",
     "Implement only the approved service calculation using the supplied versioned pricing rules. Validate and "
     "calculate on the server. Return an estimate with its currency, scope, exclusions, and rule version. Do not "
     "trust client totals or invent commercial rates. Keep the existing website and inquiry flow working. If rules "
     "are missing, report the missing inputs and keep this feature out of production."),
    ("Prompt 7", "Runtime quality check",
     "Inspect the application with available logs and testing tools. Exercise every route, form, server function, "
     "and API used in this scope. Find hangs, loops, timeouts, and incorrect responses. Repair only the demonstrated "
     "fault. After each edit confirm the app loads and the inquiry path still works. Return evidence and unresolved "
     "blockers; do not infer a pass from a successful build alone."),
]

MASTER_INSTRUCTION = (
    "Execute this GHL AI Studio SEO and Full Stack Implementation playbook for Chuck Ashley. Start by verifying the "
    "selected account, location, project, domain, and available capabilities. Use a reversible draft and preserve "
    "live conversion paths. Follow Steps 1–26, then Steps 32–36 as applicable. Treat Steps 27–31 as "
    "optional and blocked until real business pricing is supplied. Use the original prompts in this document, with "
    "the approved page map and business facts as inputs. Keep secrets server-side. Use synthetic test contacts and "
    "prevent accidental outbound messages. Verify actual CRM persistence and initial HTML rather than relying on a "
    "preview or build success. Continue independent work when blocked, and list the exact missing dependency. Do not "
    "claim the video supplied unpublished prompts or that mocks are live. Return the completed release package and "
    "execute production actions only within the authorization already provided."
)

FINAL_STATUS_FORMAT = (
    "Project and location verified: [IDs]. Draft/live URL: [URL]. Saved version and rollback target: [IDs]. "
    "Completed steps: [numbers]. Test results: [pass/fail/blocked counts and evidence]. CRM persistence: [redacted "
    "record references]. Outstanding inputs: [specific list]. Production status: [draft / published / rolled back]. "
    "Next executable action: [one concrete action]."
)

APPLICABILITY = {
    "Prompt 4": "INAPPLICABLE UNTIL BLOCKERS CLEAR: AI Studio server functions + secrets unverified for this "
                "project (work order 005-002); GHL API contract unverified (005-005).",
    "Prompt 6": "INAPPLICABLE: ESTIMATOR_ENABLED = False; no approved pricing rules exist (see out/estimator/BLOCKED.md).",
}


def placeholder_block(cfg: dict) -> list[tuple[str, str]]:
    return [
        ("Brand", C.BRAND_NAME),
        ("Approved public business name", cfg["business_name"]),
        ("Owner / public contact", f"{C.OWNER_NAME}, {C.OWNER_PHONE}, {C.OWNER_EMAIL}"),
        ("GHL location ID (case-sensitive)", C.GHL_LOCATION_ID),
        ("GHL project ID", cfg["ghl_project_id"]),
        ("Draft URL", cfg["ghl_draft_url"]),
        ("Live URL", cfg["ghl_live_url"]),
        ("Site origin (domain)", cfg["site_origin"]),
        ("Approved conversion destination", C.BOOKING_URL),
        ("Page map", "out/route_inventory.md (all routes PROPOSED_NOT_APPROVED)"),
        ("Page copy", "out/pages/*.md (drafts)"),
        ("Metadata", "out/metadata.md"),
        ("Structured data", "out/structured_data/*.json"),
        ("Verified services", cfg["services_verified"]),
        ("Service areas", cfg["service_areas"]),
        ("Inquiry contract", "out/inquiry_contract.md"),
        ("Server function source", "out/server_functions/inquiry.ts"),
        ("SSR supported on this project", cfg["ai_studio_ssr_supported"]),
        ("GHL API version / scopes", f"{cfg['ghl_api_version']} / {cfg['ghl_api_scopes']}"),
        ("Pipeline ID / stage ID", f"{cfg['ghl_pipeline_id']} / {cfg['ghl_stage_id']}"),
        ("Custom field IDs", cfg["ghl_custom_field_ids"]),
        ("Allowed source origins", str(C.ALLOWED_SOURCE_ORIGINS)),
        ("Service allowlist", str(C.SERVICE_ALLOWLIST)),
        ("Test tag", C.TEST_TAG),
    ]


def render(cfg: dict) -> str:
    lines = ["# AI Studio prompt pack (SPEC-05)", "",
             "Paste-ready. Prompts 1-7, the master instruction and the final-status format are transcribed "
             "verbatim from the source playbook. Fill every `NEEDS_EVIDENCE` value below before pasting. These "
             "prompts are authored guidance derived from a video transcript; exact AI Studio UI labels are "
             "`NEEDS_EVIDENCE`.", "",
             "> Note: the source's \"20-prompt revised playbook\" was never supplied. It must not be fetched, "
             "reconstructed or approximated. Use only the prompts below.", "",
             "## Placeholder-fill block", "", "| Input | Value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in placeholder_block(cfg)]
    lines.append("")
    for pid, title, text in PROMPTS:
        lines += [f"## {pid} — {title}", ""]
        if pid in APPLICABILITY:
            lines += [f"**{APPLICABILITY[pid]}**", ""]
        lines += ["```text", text, "```", ""]
    lines += ["## Master instruction (verbatim)", "", "```text", MASTER_INSTRUCTION, "```", "",
              "## Required final status format (verbatim)", "", "```text", FINAL_STATUS_FORMAT, "```", ""]
    return "\n".join(lines)


def build(paths: Paths | None = None) -> str:
    paths = paths or default_paths()
    cfg = json.loads(paths.build_config.read_text(encoding="utf-8"))
    text = render(cfg)
    G.assert_no_price_in_message(text)
    G.assert_no_consumer_brand(text)
    emit("ai_studio_prompt_pack", paths.out / "ai_studio_prompt_pack.md", text, STATUS.READY_FOR_HUMAN, paths,
         source="src/ai_studio_prompts.py")
    return text


if __name__ == "__main__":
    build()
    print("prompt pack written")

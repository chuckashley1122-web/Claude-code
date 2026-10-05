"""Launch review -> out/launch_review.md + out/asset_register.md (SPEC-04 step 22)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants as C  # noqa: E402
from src.common import DRAFT_NOTICE, md_table  # noqa: E402

UNAVAILABLE_CAPABILITIES = [
    "Meta Business Suite / Ads Manager / Events Manager / Ad Library (no browser, no login)",
    "Creating the Pixel/Dataset or generating a CAPI access token",
    "GoHighLevel sub-account, AI Studio, pipelines, workflows, A2P registration",
    "Publishing the AI Studio page, custom domain/subdomain, DNS CNAME records",
    "Buying a domain or adding a payment method (spend - approval required)",
    "Sending any SMS or email; verifying a sender",
    "Recording/editing video or generating images",
    "Reading Execution Logs, contact attribution or any logged-in dashboard",
    "Launching, pausing, resuming or editing any live Meta campaign",
]


def test_summary(root: Path) -> str:
    log = root / "out" / "tests"
    results = sorted(log.glob("T*.json")) if log.exists() else []
    if not results:
        return "Not yet run - run `tools/run_tests.py` (results land in `out/tests/test_log.md`)."
    counts: dict[str, int] = {}
    for p in results:
        v = json.loads(p.read_text(encoding="utf-8"))["verdict"]
        counts[v] = counts.get(v, 0) + 1
    return ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) + " (see `out/tests/test_log.md`)"


def render_register(assets: list[dict]) -> str:
    return "\n".join(["# Asset register", "", DRAFT_NOTICE, "",
                      md_table(["ID", "Path", "Status", "Owner"], [[a["id"], a["path"], a["status"], a["owner"]] for a in assets]),
                      ""])


def render_review(ctx, assets: list[dict], blockers: list[dict]) -> str:
    camp = json.loads((ctx.out / "campaign_config.json").read_text(encoding="utf-8"))
    capi = json.loads((ctx.out / "capi_settings.json").read_text(encoding="utf-8"))
    statuses = sorted({a["status"] for a in assets})
    return "\n".join([
        "# Launch review pack", "", DRAFT_NOTICE, "",
        "**Nothing was launched.** No Meta, GHL, domain, DNS or payment object was created, edited or touched.", "",
        "## Summary",
        md_table(["Item", "State"], [
            ["Draft campaign", f"{camp['campaign']['name']} - {camp['status']} (published_by_build={camp['published_by_build']})"],
            ["Budget exposure (USD)", f"{camp['budget_exposure_usd']} until approved in writing"],
            ["Daily budget", camp["ad_set"]["daily_budget"]],
            ["Campaign-level budget", camp["campaign"]["campaign_budget"]],
            ["Pixel / CAPI", f"spec only; event {capi['event_to_send']} / {capi['event_type']}; IDs via env "
                             f"`{capi['pixel_id_env']}`, token via env `{capi['access_token_env']}`; not verified live"],
            ["Workflows", "01 New Lead Automation, 02 Hot Lead - Replied, 03 Landing Page CAPI - Lead (specs only)"],
            ["Tests", test_summary(ctx.root)],
            ["Booking destination", C.BOOKING_URL],
            ["Asset statuses present", ", ".join(statuses)],
        ]), "",
        "## Campaign preview pack",
        "- `out/campaign_spec.md`, `out/campaign_config.json`", "- `out/ads/angles.md`, `out/ads/copy/A01..A04.md`, "
        "`out/ads/creative_specs.md`", "- `out/landing/index.html`, `out/landing/thank-you.html` (static mocks)",
        "- `out/test_urls.txt` (dummy tracking URLs, TEST DATA)", "",
        "## Open blockers", md_table(["Item", "Missing input", "Work affected", "Next action"],
                                     [[b["item"], b["missing_input"], b["work_affected"], b["next_action"]] for b in blockers]), "",
        "## Unavailable capabilities in this executor", *[f"- {u}" for u in UNAVAILABLE_CAPABILITIES], "",
        "## Assets", f"{len(assets)} assets - full list in `out/asset_register.md`.", "",
    ])


def build(ctx) -> list[Path]:
    blockers = ctx.state.load_blockers()
    p1 = ctx.write_asset("out/launch_review.md", "placeholder", "launch_review", "src/launch_review.py")
    p2 = ctx.write_asset("out/asset_register.md", "placeholder", "asset_register_md", "src/launch_review.py")
    assets = ctx.state.load_assets()
    p1.write_text(render_review(ctx, assets, blockers), encoding="utf-8", newline="\n")
    p2.write_text(render_register(assets), encoding="utf-8", newline="\n")
    return [p1, p2]

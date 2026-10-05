"""Launch review package -> out/launch_review.md + out/asset_register.md

Never marks anything Ready for launch or Live.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src.common import OFFER_VERSION, prefix  # noqa: E402

UNAVAILABLE = [
    "Operating GHL, Meta Ads Manager, Meta Business Suite, Whop, AI Studio or any logged-in UI (human checklists in ui-tasks/)",
    "Image generation (no image model in this executor; prompts are in out/creatives/)",
    "Payment-product creation (human-only, requires explicit approval)",
    "DNS, domains, Pixel/CAPI tokens, ad budgets (human-only, approval required)",
    "Live verification of any test case (every live-dependent case is BLOCKED)",
]


def test_summary(out_dir: Path) -> list[dict]:
    tests = []
    for p in sorted((out_dir / "tests").glob("T*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        tests.append({"test_id": d["test_id"], "verdict": d["verdict"], "logic": d.get("logic_simulation", "")})
    return tests


def render(state, assets: list[dict]) -> str:
    tests = test_summary(state.out_dir)
    counts = {v: sum(1 for t in tests if t["verdict"] == v) for v in ("PASS", "FAIL", "BLOCKED")}
    lines = ["# Launch review package", "",
             "**Overall status: Draft. Not ready for launch. Nothing was launched; no GHL, Meta or payment object was touched.**", "",
             f"- Build mode: `{state.config.get('build_mode')}`; object prefix `{prefix(state.config)}`; offer `{OFFER_VERSION}`",
             f"- Target GHL location: `{C.GHL_LOCATION_ID}` (reference only)",
             f"- Budget exposure: none authorized (AD_SPEND_CAP_USD = {C.AD_SPEND_CAP_USD}, APPROVAL_AD_SPEND = {C.APPROVAL_AD_SPEND})",
             f"- Launch authority: `{C.LAUNCH_AUTHORITY}`", "",
             "## Campaign preview (draft)", "",
             f"New draft campaign name pattern `{C.NEW_CAMPAIGN_NAME_PATTERN}` (PAUSED; created by a human only). Five concepts:", ""]
    for a in ("A01", "A02", "A03", "A04", "A05"):
        lines.append(f"- [{a} creative](creatives/{a}.md) / [{a} copy](copy/{a}.md)")
    lines += ["", "## Offer terms and payment", "", "- [Offer specification](offer_spec.md)", "- [Close and onboarding pack](close_pack.md)",
              "- [Risk reversal: no numerical guarantee](risk_reversal.md)", "- Payment setup: not created (human-only, approval required)", "",
              "## Workflows (all unpublished specs)", ""]
    lines += [f"- [{n}](workflows/{n}.md)" for n in ("01-intake", "02-unbooked", "03-booked", "04-outcome")]
    lines += ["", "## Tests", "", f"PASS {counts['PASS']} / FAIL {counts['FAIL']} / BLOCKED {counts['BLOCKED']} "
              "(see [test log](tests/test_log.md)). BLOCKED cases are not passing.", ""]
    lines += [f"- {t['test_id']}: {t['verdict']} (logic simulation: {t['logic']})" for t in tests]
    lines += ["", "## Onboarding", "", "- [Welcome page draft](welcome_page/index.html)", "- [Intake form spec](intake_form.json)", "",
              "## Unavailable capabilities", ""] + [f"- {u}" for u in UNAVAILABLE]
    lines += ["", "## Assets", "", "See [asset register](asset_register.md). Human tasks: [GHL](../ui-tasks/GHL-BUILD-CHECKLIST.md), "
              "[Meta](../ui-tasks/META-BUILD-CHECKLIST.md), [Decisions](../ui-tasks/HUMAN-DECISIONS.md).", ""]
    return "\n".join(lines)


def render_register(assets: list[dict]) -> str:
    lines = ["# Asset register", "", "| ID | Path | Status | Owner |", "|---|---|---|---|"]
    lines += [f"| {a['id']} | {a['path']} | {a['status']} | {a['owner']} |" for a in assets]
    lines.append("")
    return "\n".join(lines)


def build(state) -> list[Path]:
    # register both outputs first so they appear in the register they belong to
    state.mark_asset("LAUNCH-REVIEW", "out/launch_review.md", "Draft")
    state.mark_asset("ASSET-REGISTER-MD", "out/asset_register.md", "Draft")
    assets = state.load_assets()
    return [state.write("out/launch_review.md", render(state, assets), "LAUNCH-REVIEW", source="src/launch_review.py"),
            state.write("out/asset_register.md", render_register(assets), "ASSET-REGISTER-MD", source="src/launch_review.py")]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

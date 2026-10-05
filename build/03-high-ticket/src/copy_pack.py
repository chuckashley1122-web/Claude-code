"""Ad copy pack (playbook step 21) -> out/copy/A01..A05.md"""
from __future__ import annotations

from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src import creative_pack as CP  # noqa: E402
from tools import guardrails as G  # noqa: E402

SOURCE_EXAMPLE_COPY = (
    "HVAC owners in Austin and Round Rock: want a clearer process for bringing in inquiries and following up? "
    "CA-J Enterprises builds and manages the agreed advertising and follow-up system, so your team can focus on calls "
    "and estimates. Book a strategy session to review your market, capacity and budget."
)
ALLOWED_CTAS = {"Learn More", C.BOOKING_URL}


def copy_record(creative: dict) -> dict:
    rec = {"ad_id": creative["ad_id"], "primary_text": creative["primary_text"], "headline": creative["headline"],
           "cta": creative["cta"], "destination": C.BOOKING_URL, "offer_reference": creative["offer_reference"]}
    if rec["cta"] not in ALLOWED_CTAS:
        raise G.MeetingFirstViolation(f"CTA must be Learn More or the booking URL, got {rec['cta']!r}")
    for key in ("primary_text", "headline", "cta"):
        G.assert_meeting_first(rec[key])
        G.assert_prospect_copy(rec[key])
    return rec


def render(rec: dict) -> str:
    G.assert_prospect_copy(SOURCE_EXAMPLE_COPY)
    return "\n".join([
        f"# Ad copy {rec['ad_id']}", "", f"Status: Draft. Offer reference `{rec['offer_reference']}`.", "",
        f"- Primary text: {rec['primary_text']}", f"- Headline: {rec['headline']}", f"- CTA: {rec['cta']}",
        f"- Destination: lead form, qualified ending button links to {rec['destination']}", "",
        "## Source example copy (playbook step 21)", "",
        "> " + SOURCE_EXAMPLE_COPY, "",
        f"Headline: \"{CP.AD_HEADLINE}.\" CTA: Learn More. The market named in the source example is a proposal; "
        f"service_area is {C.NEEDS_EVIDENCE}.", "",
        "Rules: CTA is Learn More or the booking URL, never a price. Every string above passed assert_meeting_first().", "",
    ])


def build(state) -> list[Path]:
    paths = []
    if state.config.get("service_area", C.NEEDS_EVIDENCE) == C.NEEDS_EVIDENCE:
        state.needs("service_area", "out/copy/", "Confirm the market before naming it in ad copy")
    for creative in CP.concepts(state.config):
        rec = copy_record(creative)
        paths.append(state.write(f"out/copy/{rec['ad_id']}.md", render(rec), f"COPY-{rec['ad_id']}", source="src/copy_pack.py"))
    return paths


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

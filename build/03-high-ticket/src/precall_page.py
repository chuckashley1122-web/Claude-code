"""Pre-call page draft (playbook steps 37-38) -> out/precall_page/index.html

Self-contained static HTML, openable as file://. No scripts, no external resources.
"""
from __future__ import annotations

from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src.common import esc, html_page, ul  # noqa: E402
from tools import guardrails as G  # noqa: E402

SRC = "out/precall_page/index.html"
VIDEO_OUTLINE = (
    "Thanks for booking. We will first review your goals and current process. Our proposed system combines the agreed "
    "advertising work with follow-up and booking. Your team handles calls, estimates and sales. Results depend on the "
    "market, budget, capacity and conversion process. Bring your current spend and job economics so we can decide whether "
    "the numbers make sense. If we are a fit, we will review exact scope and pricing together."
)
SECTIONS = {
    "Who this is for": ["HVAC business owners or marketing decision makers",
                        "Teams with capacity to handle additional replacement or installation estimates"],
    "What we actually do": ["Plan and run the agreed advertising for your business",
                            "Qualify inquiries and follow up quickly", "Book estimates or calls onto your calendar",
                            "Report spend, inquiries, booked and held appointments, and completed sales you confirm"],
    "What your team does": ["Answer calls and attend estimates", "Supply brand assets and access through platform invitations",
                            "Report job outcomes so reporting stays accurate"],
    "Ad spend": ["Advertising media spend is separate from our service and is paid by your business to the ad platform."],
    "Implementation dependencies": ["Access to your ad accounts and calendar", "A verified routing plan for new inquiries",
                                    "Your approval of every ad before it runs", "Timing depends on access and capacity review"],
    "Call agenda": ["Your goals and current process", "Current spend, job economics and capacity",
                    "How the system would work for you", "Fit, scope and next steps"],
}


def render() -> str:
    for items in SECTIONS.values():
        for t in items:
            G.assert_prospect_copy(t)
    G.assert_prospect_copy(VIDEO_OUTLINE)
    sections = [(k, ul(v)) for k, v in SECTIONS.items()]
    sections.append(("Video", f"<div class=\"slot\">Video embed slot: {C.NEEDS_EVIDENCE} (short video from {esc(C.OWNER_NAME)} when recorded)</div>"))
    sections.append(("Video script (outline to record)", f"<blockquote>{esc(VIDEO_OUTLINE)}</blockquote>"))
    sections.append(("Need another time?", f"<p><a href=\"{esc(C.BOOKING_URL)}\">{esc(C.BOOKING_URL)}</a></p>"))
    return html_page("Before your strategy session", sections,
                     "DRAFT for content review. Private/unlisted. No case study, testimonial or outcome is shown because none is verified.")


def build(state) -> list[Path]:
    state.needs("pre-call video", SRC, "Record the outlined video; host it; replace the embed slot")
    state.needs("pre-call page hosting URL", SRC, "Publish as a private/unlisted GHL page; record the URL")
    return [state.write(SRC, render(), "PRECALL-PAGE", source="src/precall_page.py")]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

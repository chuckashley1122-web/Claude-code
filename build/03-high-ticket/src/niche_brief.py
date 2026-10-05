"""Niche brief (playbook steps 06-08) -> out/niche_brief.md + out/niche_brief.json"""
from __future__ import annotations

from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402
from src.common import md_table, niche_label, proof_block  # noqa: E402

SRC = "out/niche_brief.md"

FIELDS = [
    ("interest_or_experience", "Interest / experience in the niche"),
    ("addressable_buyer_count", "Addressable buyer count (business count, not employee count)"),
    ("value_per_customer", "Value per customer (client contribution, not revenue)"),
    ("seasonality", "Seasonality"),
]


def brief(config: dict) -> dict:
    fields = [{"field": key, "label": label, "value": C.NEEDS_EVIDENCE, "evidence": "", "date_observed": ""}
              for key, label in FIELDS]
    competitors = [{"slot": f"competitor_{i}", "agency_name": C.NEEDS_EVIDENCE, "evidence": "", "date_observed": "",
                    "ad_observed": C.NEEDS_EVIDENCE} for i in (1, 2, 3)]
    return {
        "build_mode": config.get("build_mode"),
        "niche": niche_label(config),
        "service_area": config.get("service_area", C.NEEDS_EVIDENCE),
        "buyer": ("HVAC owners or marketing decision makers who can handle additional replacement or installation "
                  "estimates (CA-J adaptation; not the instructor's example)"),
        "do_not_target": "Homeowners (this is an agency acquisition campaign aimed at businesses)",
        "channel": "Meta lead ads (demonstrated route), prepared as a draft only; validate the offer through authorized conversations first",
        "fields": fields,
        "competing_agencies": competitors,
        "corrections": [
            "Competitor ads indicate market activity; they do not establish profitability.",
            "Use business counts when selling to business owners; employee counts, business counts and licensed-agent counts are different units.",
            "The 50,000 population threshold is the instructor's heuristic, not a requirement.",
            "The source's market-share arithmetic at 4:42-5:23 is incorrect (5 of 100,000 is 0.005%).",
            "The video's cold SMS remarks do not establish permission to contact anyone; no purchased-list messaging.",
        ],
        "status": "Draft",
    }


def render(b: dict) -> str:
    lines = ["# Niche brief", "", f"Status: Draft. Build mode: `{b['build_mode']}`. Niche: {b['niche']}.", "",
             f"- Buyer: {b['buyer']}", f"- Do not target: {b['do_not_target']}",
             f"- Service area: {b['service_area']} (the playbook proposes Austin and Round Rock; not confirmed)",
             f"- Channel: {b['channel']}", "", "## Market fields", ""]
    lines += md_table(["Field", "Value", "Evidence (link)", "date_observed"],
                      [[f["label"], f["value"], f["evidence"], f["date_observed"]] for f in b["fields"]])
    lines += ["", "## Three competing agencies", ""]
    lines += md_table(["Slot", "Agency", "Ad observed", "Evidence (link)", "date_observed"],
                      [[c["slot"], c["agency_name"], c["ad_observed"], c["evidence"], c["date_observed"]] for c in b["competing_agencies"]])
    lines += ["", "## Source corrections (apply before using any number)", ""]
    lines += [f"- {c}" for c in b["corrections"]]
    lines += [""]
    lines += proof_block(["- The instructor's market counts and conversion claims are unverified and are not CA-J data."])
    lines += ["", "The brief is complete only after client break-even and agency margin are modeled with real inputs.", ""]
    return "\n".join(lines)


def build(state) -> list[Path]:
    b = brief(state.config)
    for f in b["fields"]:
        state.needs(f"niche: {f['field']}", SRC, "Research with dated, linked evidence (15-20 min initial choice)")
    state.needs("niche: three competing agencies", SRC, "Record three competitor agencies with ad links and dates")
    if b["service_area"] == C.NEEDS_EVIDENCE:
        state.needs("service_area", SRC, "Confirm the service area (playbook proposes Austin and Round Rock)")
    return [state.write(SRC, render(b), "NICHE-BRIEF-MD", source="src/niche_brief.py"),
            state.write_json("out/niche_brief.json", b, "NICHE-BRIEF-JSON", source="src/niche_brief.py")]


if __name__ == "__main__":
    from tools.state import run_standalone
    sys.exit(run_standalone(build))

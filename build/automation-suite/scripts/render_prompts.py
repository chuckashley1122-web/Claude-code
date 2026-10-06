"""Render prompts/*.txt by filling {{placeholders}}; hard-fail on anything unresolved.

Default run: renders all fifteen prompts with variables derived from
data/fixtures (plus BOOKING_URL from config/constants.py), writes them to
data/out/prompts/, and exits 0.

``--withhold NAME`` removes a variable before rendering to prove the renderer
fails closed (exit 1). ``--prompt ID`` limits the run to one prompt.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import constants  # noqa: E402

PROMPTS_DIR = ROOT / "prompts"
FIXTURES_DIR = ROOT / "data" / "fixtures"
PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
ANY_BRACES = re.compile(r"\{\{.*?\}\}", re.S)

# Synthetic brand brief used by the UGC workflow (B2B CA-J brand only).
BRAND_BRIEF = {
    "brand_desc": "CA-J Enterprises, which builds AI front desks for home service companies",
    "product": "an AI front desk that answers calls and books visits",
}
SERVICE_FOCUS = "answering and booking inbound calls"


class UnresolvedPlaceholder(ValueError):
    def __init__(self, prompt_id: str, names: list[str]):
        self.prompt_id = prompt_id
        self.names = names
        super().__init__(f"UNRESOLVED placeholders in {prompt_id}: {', '.join(names)}")


class PromptFormatError(ValueError):
    pass


@dataclass(frozen=True)
class Prompt:
    id: str
    version: str
    source: str
    body: str

    @property
    def placeholders(self) -> list[str]:
        seen: list[str] = []
        for name in PLACEHOLDER.findall(self.body):
            if name not in seen:
                seen.append(name)
        return seen


def parse_prompt(text: str, expected_id: str | None = None) -> Prompt:
    header, sep, body = text.partition("\n---\n")
    if not sep:
        raise PromptFormatError("prompt file needs a header terminated by a '---' line")
    meta = {}
    for line in header.splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    for key in ("id", "version", "source"):
        if not meta.get(key):
            raise PromptFormatError(f"prompt header missing {key!r}")
    if expected_id and meta["id"] != expected_id:
        raise PromptFormatError(f"prompt id {meta['id']!r} does not match file name {expected_id!r}")
    return Prompt(meta["id"], meta["version"], meta["source"], body.strip() + "\n")


def load_prompt(prompt_id: str, prompts_dir: Path = PROMPTS_DIR) -> Prompt:
    path = prompts_dir / f"{prompt_id}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"no prompt file {path}")
    return parse_prompt(path.read_text(encoding="utf-8"), prompt_id)


def list_prompt_ids(prompts_dir: Path = PROMPTS_DIR) -> list[str]:
    return sorted(p.stem for p in prompts_dir.glob("*.txt"))


def _to_text(value) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def render(prompt: Prompt | str, variables: dict) -> str:
    """Fill placeholders. Missing or empty (None) variables raise UnresolvedPlaceholder,
    as does any ``{{...}}`` left in the output."""
    if isinstance(prompt, str):
        prompt = load_prompt(prompt)
    missing = [n for n in prompt.placeholders if variables.get(n) is None]
    if missing:
        raise UnresolvedPlaceholder(prompt.id, missing)
    out = PLACEHOLDER.sub(lambda m: _to_text(variables[m.group(1)]), prompt.body)
    leftover = ANY_BRACES.findall(out)
    if leftover:
        raise UnresolvedPlaceholder(prompt.id, leftover)
    return out


def _load(name: str):
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def fixture_bindings() -> dict[str, dict]:
    """Variables for every prompt, derived only from fixtures and constants."""
    from adapters.mock_openai import CANNED, MockOpenAI

    lead = _load("leads.sample.json")["leads"][0]
    ad = _load("ad_transcript.sample.json")["ads"][0]
    videos = _load("youtube_top.sample.json")["items"]
    booking = constants.BOOKING_URL
    sender = constants.workflow_vars()["SENDER_FIRST_NAME"]

    enrich = json.loads(CANNED["02_lead_enrich"](lead))
    deconstruction = json.loads(CANNED["03_ad_deconstruction"](
        {"transcript": ad["transcript"], "frame_notes": ad["frames"]}))
    topics = json.loads(CANNED["04_trending_topics"]({"niche": "home services"}))["topics"]
    question = "How do I book an appointment?"
    chunks = MockOpenAI(fixtures_dir=FIXTURES_DIR).file_search(question, "faqs.sample.md", 2)
    analyses = [json.loads(CANNED["07_youtube_analysis"](v)) for v in videos]

    common = {"booking_url": booking}
    b = {
        "01_voice_receptionist_system": {"business_name": "Fixture Home Services (synthetic)",
                                         "caller_utterance": "I would like to book an appointment."},
        "02_lead_enrich": {k: lead[k] for k in ("website", "company", "niche", "website_text")},
        "02_cold_email": {"company": lead["company"], "icebreaker": enrich["icebreaker"],
                          "niche": lead["niche"], "service_focus": SERVICE_FOCUS,
                          "sender_first_name": sender},
        "02_followup": {"company": lead["company"], "followup_number": 1, "sender_first_name": sender},
        "03_ad_deconstruction": {"transcript": ad["transcript"], "frame_notes": ad["frames"]},
        "03_sora_prompt_format": {"hook_type": deconstruction["hook_type"],
                                  "ad_format": deconstruction["format"],
                                  "script_structure": deconstruction["script_structure"], **BRAND_BRIEF},
        "04_trending_topics": {"niche": "home services"},
        "04_faceless_script": {"trending_topic": topics[0], "niche": "home services"},
        "05_content_script": {"platform": "tiktok", "brand_tone": "plain and practical", "topic": topics[0]},
        "06_language_detect": {"user_message": "Hola, quiero una cita para el martes"},
        "06_faq_rag": {"retrieved_faq": "\n".join(c.as_text() for c in chunks), "user_msg": question},
        "06_translate": {"lang": "es", "text": chunks[0].answer if chunks else ""},
        "07_youtube_analysis": {k: videos[0][k] for k in ("title", "views", "description")},
        "07_youtube_ideas": {"analysis": analyses},
        "08_heygen_script": {"niche": "home services"},
    }
    return {pid: {**common, **vars_} for pid, vars_ in b.items()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prompt", help="render only this prompt id")
    ap.add_argument("--withhold", action="append", default=[], help="drop this variable (expect failure)")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "data" / "out")
    args = ap.parse_args(argv)

    bindings = fixture_bindings()
    ids = [args.prompt] if args.prompt else list_prompt_ids()
    missing_binding = [i for i in ids if i not in bindings]
    if missing_binding:
        print(f"FAIL: no fixture binding for {missing_binding}")
        return 1
    out = args.out_dir / "prompts"
    out.mkdir(parents=True, exist_ok=True)
    failures = 0
    for pid in ids:
        variables = {k: v for k, v in bindings[pid].items() if k not in args.withhold}
        try:
            text = render(load_prompt(pid), variables)
        except UnresolvedPlaceholder as exc:
            failures += 1
            print(f"FAIL  {exc}")
            continue
        (out / f"{pid}.rendered.txt").write_text(text, encoding="utf-8")
        print(f"OK    {pid}  ({len(text)} chars, 0 unresolved)")
    print(f"{len(ids) - failures}/{len(ids)} prompts rendered; {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

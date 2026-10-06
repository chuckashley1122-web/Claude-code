"""OpenAI interface: deterministic canned completions keyed by prompt id.

``MockOpenAI`` never calls a network. Each prompt id maps to a small,
deterministic function of the prompt variables (template filling, keyword
heuristics, fixture lookups). Outputs are labelled synthetic where they stand in
for model judgement, and never contain invented metrics or prices.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Protocol

from adapters.base import LiveAdapter, MockAdapter, load_json_fixture

STOPWORDS = {
    "a", "an", "the", "and", "or", "to", "of", "in", "on", "for", "is", "are", "my", "your",
    "i", "you", "we", "do", "does", "can", "how", "what", "when", "where", "why", "it", "be",
    "with", "at", "this", "that", "me", "our", "us", "will", "if", "from", "by", "as", "any",
    # Spanish / French / German function words, so cross-language retrieval scores fairly
    "hola", "quiero", "una", "un", "para", "mi", "el", "la", "de", "que", "por", "favor", "puedo",
    "como", "bonjour", "je", "voudrais", "mon", "pour", "le", "les", "hallo", "ich", "einen",
    "meinen", "bitte", "mein", "möchte",
}

# Tiny cross-language keyword map so non-English questions can hit the English FAQ.
CROSS_LANG = {
    "cita": "appointment", "citas": "appointment", "reservar": "book", "agendar": "schedule",
    "programar": "schedule", "reprogramar": "reschedule", "cancelar": "cancel",
    "horario": "hours", "horarios": "hours", "emergencia": "emergencies",
    "rendez": "appointment", "annuler": "cancel", "horaires": "hours",
    "termin": "appointment", "absagen": "cancel", "notfall": "emergencies",
}

_LANG_HINTS = {
    "es": {"hola", "quiero", "una", "cita", "para", "puedo", "gracias", "cuesta", "necesito", "el", "la", "por", "favor", "mi"},
    "fr": {"bonjour", "je", "voudrais", "un", "rendez", "vous", "merci", "est", "pour", "combien", "le", "les"},
    "de": {"hallo", "ich", "einen", "termin", "bitte", "danke", "ist", "und", "möchte", "kostet", "wie", "der", "die"},
    "pt": {"olá", "ola", "quero", "uma", "consulta", "obrigado", "você", "preço", "para", "não"},
    "hi": {"namaste", "mujhe", "kya", "hai", "aap", "kitna", "chahiye", "kab"},
}


def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zà-ÿ0-9]+", (text or "").lower()) if t not in STOPWORDS]


def detect_language(text: str) -> str:
    if re.search(r"[\u0900-\u097F]", text or ""):
        return "hi"
    words = set(re.findall(r"[a-zà-ÿ]+", (text or "").lower()))
    best, best_hits = "en", 0
    for code, hints in _LANG_HINTS.items():
        hits = len(words & hints)
        if hits > best_hits:
            best, best_hits = code, hits
    return best if best_hits >= 2 else "en"


@dataclass(frozen=True)
class FaqChunk:
    question: str
    answer: str
    score: float

    def as_text(self) -> str:
        return f"Q: {self.question}\nA: {self.answer}"


def parse_faq_markdown(text: str) -> list[tuple[str, str]]:
    entries, q, buf = [], None, []
    for line in text.splitlines():
        m = re.match(r"^##\s*Q:\s*(.+)$", line.strip())
        if m:
            if q:
                entries.append((q, " ".join(buf).strip()))
            q, buf = m.group(1).strip(), []
        elif q is not None and line.strip():
            buf.append(line.strip())
    if q:
        entries.append((q, " ".join(buf).strip()))
    return entries


def _first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return parts[0] if parts and parts[0] else ""


def _loads(value) -> object:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


# ---------------------------------------------------------------- canned completions

def _voice(v: dict) -> str:
    said = (v.get("caller_utterance") or "").lower()
    if re.search(r"\b(book|appointment|schedule|reschedule)\b", said):
        return "Happy to help you book. Let me check availability first."
    return f"Thanks for calling {v.get('business_name', 'us')}. How can I help today?"


def _fit_score(niche: str, text: str) -> int:
    niche, text = niche.lower(), text.lower()
    score = 3
    if re.search(r"hvac|plumb|electric|roof|home service", niche):
        score += 2
    if re.search(r"emergency|after-hours|24/7", text):
        score += 2
    if re.search(r"\bcall\b|\bphone\b", text):
        score += 2
    if re.search(r"\bbook|\bschedul", text):
        score += 1
    return max(1, min(10, score))


def _enrich(v: dict) -> str:
    text = v.get("website_text") or ""
    emergency = bool(re.search(r"emergency|after-hours|24/7", text, re.I))
    focus = "emergency service" if emergency else (v.get("niche") or "your services")
    return json.dumps({
        "what_they_do": _first_sentence(text) or "unknown",
        "pain_points": (["handling calls outside office hours (inferred from website text, unconfirmed)"]
                        if emergency else ["unknown"]),
        "decision_maker": "unknown",
        "fit_score": _fit_score(v.get("niche") or "", text),
        "icebreaker": (f"I was looking at {v.get('company')} and noticed the focus on {focus}. "
                       "I had a quick idea about how calls get handled when the team is busy."),
    })


_OPT_OUT = 'Reply "no thanks" and we will not email again.'


def _cold_email(v: dict) -> str:
    body = (f"{v['icebreaker']} We help {v['niche']} businesses with {v['service_focus']}. "
            f"Worth a quick chat? You can pick a time at {v['booking_url']}. - {v['sender_first_name']}"
            f"\n\n{_OPT_OUT}")
    return json.dumps({"subject": f"Quick idea for {v['company']}", "body": body})


def _followup(v: dict) -> str:
    n = v.get("followup_number")
    body = (f"Following up on my earlier note to {v['company']}. If a short conversation would help, "
            f"you can pick a time at {v['booking_url']}. - {v['sender_first_name']}\n\n{_OPT_OUT}")
    return json.dumps({"subject": f"Re: Quick idea for {v['company']} (follow-up {n})", "body": body})


def _deconstruct(v: dict) -> str:
    transcript = v.get("transcript") or ""
    frames = _loads(v.get("frame_notes"))
    frames = frames if isinstance(frames, list) else [str(frames)]
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", transcript.strip()) if s]
    hook = sentences[0] if sentences else ""
    last = sentences[-1].lower() if sentences else ""
    joined = " ".join(frames).lower()
    triggers = []
    if hook.endswith("?"):
        triggers.append("curiosity: opens with a question (mock heuristic)")
    if re.search(r"here is|check|first thing", transcript, re.I):
        triggers.append("problem-solution demonstration (mock heuristic)")
    fmt = "talking-head" if "talking-head" in joined else ("selfie UGC" if "selfie" in joined else "unknown")
    return json.dumps({
        "hook_text": hook,
        "hook_type": "question" if hook.endswith("?") else "statement",
        "full_script": transcript,
        "shot_list": frames,
        "psychological_triggers": triggers,
        "script_structure": ("hook -> demonstration -> call to action"
                             if re.search(r"\b(book|call|follow|visit)\b", last) else "hook -> demonstration"),
        "emotional_trigger": "recognition of a familiar problem (mock heuristic)" if triggers else "needs evidence",
        "format": fmt,
        "why_it_worked": "needs evidence (fixture has no engagement data)",
    })


_ACTORS = ("homeowner in a kitchen", "technician beside an outdoor unit", "office manager at a desk",
           "homeowner in a garage", "technician in a work van")


def _sora(v: dict) -> str:
    product = v.get("product") or "the product"
    lines = (
        f"Ever miss a call while you are on a job? This is {product}.",
        f"Here is what happens when a customer calls after hours with {product}.",
        f"I wanted every caller to get an answer, so we set up {product}.",
        f"Quick look at how {product} checks the calendar before booking.",
        f"If you run a busy team, here is one thing to look at: {product}.",
    )
    prompts = [
        (f"UGC style, {actor}, iPhone selfie, natural light, says: \"{line}\", product in hand, "
         f"TikTok style, 9:16, 8 seconds. Structure: {v.get('script_structure')}; hook type: {v.get('hook_type')}; "
         f"format: {v.get('ad_format')}; brand: {v.get('brand_desc')}")
        for actor, line in zip(_ACTORS, lines)
    ]
    return json.dumps({"prompts": prompts})


def _topics(v: dict) -> str:
    niche = v.get("niche") or "the niche"
    return json.dumps({"topics": [
        f"{niche}: seasonal maintenance questions (unverified, no live research in dry run)",
        f"{niche}: what to do before calling a technician (unverified, no live research in dry run)",
        f"{niche}: common noises and what they can mean (unverified, no live research in dry run)",
    ]})


def _faceless(v: dict) -> str:
    topic = re.sub(r"\s*\(unverified.*\)$", "", v.get("trending_topic") or "")
    return (f"Hook: Ever wondered about {topic}?\n"
            "1. Start with the basics you can safely check yourself.\n"
            "2. Write down what you notice and when it happens.\n"
            "3. When in doubt, ask a licensed professional.\n"
            "CTA: Follow for more practical tips.")


def _content(v: dict) -> str:
    topic = re.sub(r"\s*\(unverified.*\)$", "", v.get("topic") or "")
    return (f"[Platform: {v.get('platform')}] [Tone: {v.get('brand_tone')}]\n"
            f"Hook: A quick question about {topic}.\n"
            "Story: A common situation: the phone rings while the team is busy.\n"
            "Lesson: A clear process for answering and booking keeps things simple.\n"
            f"CTA: Book a short meeting at {v.get('booking_url')}.")


def _lang(v: dict) -> str:
    return detect_language(v.get("user_message") or "")


def _faq_rag(v: dict) -> str:
    context = v.get("retrieved_faq") or ""
    m = re.search(r"A:\s*(.+?)(?:\nQ:|$)", context, re.S)
    answer = m.group(1).strip() if m else ""
    if not answer:
        return "Thanks for asking. A team member will follow up with you."
    slots = re.search(r"Open times:\s*(.+)$", context)
    if slots and re.search(r"book|schedul|appointment|cita|termin|rendez", v.get("user_msg") or "", re.I):
        answer = answer.split(" Open times:")[0].strip()
        answer = f"{answer} Open times: {slots.group(1).strip()}"
    words = answer.split()
    return " ".join(words[:49])


def _translate(v: dict) -> str:
    lang = (v.get("lang") or "en").lower()
    text = v.get("text") or ""
    # The mock cannot translate; it tags the original text with the target language.
    return text if lang == "en" else f"[{lang}] {text}"


_KW_STOP = STOPWORDS | {"why", "never", "ignore", "should", "right", "way", "actually", "vs", "explained", "stop"}


def _yt_analysis(v: dict) -> str:
    title = v.get("title") or ""
    low = title.lower()
    if low.endswith("?"):
        pattern = "question"
    elif re.match(r"^\d", low):
        pattern = "number-led list"
    elif low.startswith("how to"):
        pattern = "how-to"
    elif " vs " in low or "explained" in low:
        pattern = "comparison / explainer"
    else:
        pattern = "statement"
    words = [w for w in re.findall(r"[a-z]+", low) if w not in _KW_STOP and len(w) > 2]
    return json.dumps({
        "title_pattern": pattern,
        "keywords": words[:4],
        "angle": _first_sentence(v.get("description") or "") or "unknown",
        "why_performed": "needs evidence (mock cannot attribute performance)",
    })


def _yt_ideas(v: dict) -> str:
    analyses = _loads(v.get("analysis"))
    analyses = analyses if isinstance(analyses, list) else []
    keywords, patterns = [], []
    for a in analyses:
        a = _loads(a)
        if isinstance(a, dict) and isinstance(a.get("analysis"), (dict, str)):
            a = _loads(a["analysis"])
        if isinstance(a, dict):
            keywords.extend(k for k in a.get("keywords", []) if k not in keywords)
            if a.get("title_pattern") and a["title_pattern"] not in patterns:
                patterns.append(a["title_pattern"])
    keywords = keywords or ["your niche"]
    patterns = patterns or ["statement"]
    ideas = []
    for i in range(10):
        kw = keywords[i % len(keywords)]
        pattern = patterns[i % len(patterns)]
        ideas.append({
            "titles": [f"What to check first: {kw}", f"{kw.capitalize()} questions answered",
                       f"Before you call about {kw}, watch this"],
            "angle": f"re-use the '{pattern}' title pattern with a new {kw} angle",
            "target_keyword": kw,
            "hook_script": f"Quick question about {kw}: do you know what to look at first?",
            "outline": ["hook", f"three practical points about {kw}", "call to action"],
        })
    return json.dumps({"ideas": ideas})


def _heygen(v: dict) -> str:
    return (f"[smile] Hook: Running a {v.get('niche')} company means the phone rings at busy moments. [pause]\n"
            "Problem: When nobody can answer, the caller has to try again later.\n"
            "Solution: An assistant that answers, checks the calendar, and books the visit.\n"
            f"[smile] CTA: Book a short meeting at {v.get('booking_url')}.")


CANNED: dict[str, Callable[[dict], str]] = {
    "01_voice_receptionist_system": _voice,
    "02_lead_enrich": _enrich,
    "02_cold_email": _cold_email,
    "02_followup": _followup,
    "03_ad_deconstruction": _deconstruct,
    "03_sora_prompt_format": _sora,
    "04_trending_topics": _topics,
    "04_faceless_script": _faceless,
    "05_content_script": _content,
    "06_language_detect": _lang,
    "06_faq_rag": _faq_rag,
    "06_translate": _translate,
    "07_youtube_analysis": _yt_analysis,
    "07_youtube_ideas": _yt_ideas,
    "08_heygen_script": _heygen,
}


class UnknownPrompt(KeyError):
    pass


class LLMClient(Protocol):
    def complete(self, prompt_id: str, prompt_text: str, variables: dict) -> str: ...
    def transcribe(self, media_ref: str) -> str: ...
    def file_search(self, query: str, knowledge_base: str, top_k: int = 3) -> list[FaqChunk]: ...


@dataclass
class MockOpenAI(MockAdapter):
    service: str = "openai"

    def complete(self, prompt_id: str, prompt_text: str, variables: dict) -> str:
        self._guard("complete", prompt_id=prompt_id, prompt_chars=len(prompt_text))
        if prompt_id not in CANNED:
            raise UnknownPrompt(prompt_id)
        if re.search(r"\{\{\s*\w+\s*\}\}", prompt_text):
            raise ValueError(f"prompt {prompt_id} reached the model with unresolved placeholders")
        return CANNED[prompt_id](dict(variables))

    def transcribe(self, media_ref: str) -> str:
        self._guard("transcribe", media_ref=media_ref)
        for ad in load_json_fixture("ad_transcript.sample.json", self.fixtures_dir)["ads"]:
            if media_ref in (ad["media_id"], ad["ad_url"]):
                return ad["transcript"]
        job = self.out_dir / "video_jobs" / f"{media_ref}.json"
        if job.is_file():
            record = json.loads(job.read_text(encoding="utf-8"))
            text = record.get("payload", {}).get("text") or record.get("payload", {}).get("script")
            if text:
                return text
        raise LookupError(f"no fixture or dry-run job found for media {media_ref!r}")

    def file_search(self, query: str, knowledge_base: str, top_k: int = 3) -> list[FaqChunk]:
        self._guard("file_search", knowledge_base=knowledge_base, top_k=top_k)
        path = (self.fixtures_dir / knowledge_base).resolve()
        if self.fixtures_dir.resolve() not in path.parents:
            raise ValueError("knowledge base must live in data/fixtures")
        entries = parse_faq_markdown(path.read_text(encoding="utf-8"))
        q = {CROSS_LANG.get(t, t) for t in tokens(query)}
        if not q:
            return []
        scored = []
        for question, answer in entries:
            qtok = {CROSS_LANG.get(t, t) for t in tokens(question)}
            doc = qtok | set(tokens(answer))
            hits = len(q & doc) + 0.5 * len(q & qtok)
            score = round(min(1.0, hits / len(q)), 3)
            if score > 0:
                scored.append(FaqChunk(question, answer, score))
        scored.sort(key=lambda c: (-c.score, c.question))
        return scored[:top_k]


class LiveOpenAI(LiveAdapter):
    service = "openai"
    credential_env = ("OPENAI_API_KEY",)

    def complete(self, prompt_id: str, prompt_text: str, variables: dict) -> str:
        self._refuse("complete")

    def transcribe(self, media_ref: str) -> str:
        self._refuse("transcribe")

    def file_search(self, query: str, knowledge_base: str, top_k: int = 3) -> list[FaqChunk]:
        self._refuse("file_search")

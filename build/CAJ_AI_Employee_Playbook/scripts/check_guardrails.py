"""Self-tests for the three guardrails (pricing, meeting-first, claims).

Usage (from the build root):  python3 scripts/check_guardrails.py
Exit 0 only when every forbidden sample is blocked, every clean sample passes,
and every outreach template renders clean. The literal source figures below are
denylist samples, used only to prove they are blocked.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardrails import claim_guard, meeting_first, pricing_guard  # noqa: E402
from scripts import render_templates  # noqa: E402

# (sample, must be blocked by pricing_guard in outbound email, must be blocked by claim_guard)
MUST_BLOCK: tuple[tuple[str, bool, bool], ...] = (
    ("$650 per month", True, False),
    ("$197", True, True),
    ("setup fee", True, False),
    ("$1,000 plus $2,000 setup", True, True),
    ("$9.99", True, True),
    ("we recovered $40k in missed calls", True, True),
    ("Our AI employee recovered 40 missed calls for every client last month.", False, True),
    ("CA-J clients booked 30% more jobs.", False, True),
    ("Normally $1,000 plus $2,000 setup, but not for you.", True, True),
    ("The trainer range is $97 to $297 a month.", True, True),
    ("It costs virtually nothing to run.", True, True),
    ("Unlimited calls included.", False, True),
    ("We have a low-churn client base and a strong valuation.", False, True),
    ("Send 30-90 emails a day across three domains.", False, True),
    ("Make 50 calls a day with the dialer.", False, True),
    ("Pricing is 650 USD.", True, False),
    # Consumer brand built at runtime so the literal never sits in a B2B file.
    ("Grab a coffee from Chuck's Daily " + "Grind while you wait.", False, True),
)

MUST_PASS: tuple[str, ...] = (
    "I can prepare a short AI demo using your business information so you can try it yourself.",
    "Open to a 15-minute walkthrough? You can pick a time here: https://ca-jenterprises.com/ai",
    "If this is not relevant, reply no and I will stop following up.",
    meeting_first.MEETING_REPLY,
)

PRICE_INTENT = (
    "How much does this cost?",
    "What do you charge per month?",
    "Is there a setup fee?",
    "Can you send me a quote?",
)
NO_PRICE_INTENT = ("Can you call me back tomorrow?", "Do you work with HVAC companies in Round Rock?")

OUTREACH_TEMPLATES = ("email-draft.txt", "email-post-demo.txt", "dm-draft.txt", "call-script.txt")
SAMPLE_VARS = {
    "business": "Example Heating and Air (synthetic)",
    "first_name": "Alex",
    "specific_available_time": "Tuesday at 10 a.m. Central",
    "sender_mailing_address": "Mailing address line (synthetic)",
    "demo_evidence_ref": "out/demo-test-log-synthetic.txt",
}


def run_checks() -> list[tuple[str, bool, str]]:
    """Return (check name, passed, detail) for every self-test."""
    results: list[tuple[str, bool, str]] = []
    for sample, want_price, want_claim in MUST_BLOCK:
        price_hit = not pricing_guard.is_clean(sample, "email")
        claim_hit = not claim_guard.is_clean(sample)
        ok = (price_hit or claim_hit) and (price_hit or not want_price) and (claim_hit or not want_claim)
        results.append((f"block {sample!r}", ok, f"pricing={price_hit} claim={claim_hit}"))
        try:
            pricing_guard.assert_clean(sample, "email")
            claim_guard.assert_clean(sample)
            raised = False
        except (pricing_guard.PricingViolation, claim_guard.ClaimViolation):
            raised = True
        results.append((f"assert raises {sample!r}", raised, ""))
    for sample in MUST_PASS:
        ok = all(pricing_guard.is_clean(sample, ch) for ch in pricing_guard.OUTBOUND_CHANNELS) and claim_guard.is_clean(sample)
        results.append((f"allow {sample[:50]!r}", ok, ""))
    for q in PRICE_INTENT:
        reply = meeting_first.respond(q)
        ok = reply is not None and pricing_guard.BOOKING_URL in reply and pricing_guard.is_clean(reply, "chat")
        results.append((f"meeting-first {q!r}", ok, ""))
    for q in NO_PRICE_INTENT:
        results.append((f"no price intent {q!r}", meeting_first.respond(q) is None, ""))
    rewritten, changed = meeting_first.enforce_outbound("It is $650 per month.", "email")
    results.append(("enforce_outbound rewrites priced draft", changed and pricing_guard.is_clean(rewritten, "email"), ""))
    for name in OUTREACH_TEMPLATES:
        raw = (ROOT / "outreach" / name).read_text(encoding="utf-8")
        try:
            render_templates.render_text(raw, SAMPLE_VARS)
            results.append((f"template {name} renders clean", True, ""))
        except render_templates.RenderError as exc:
            results.append((f"template {name} renders clean", False, str(exc)))
    return results


def main() -> int:
    results = run_checks()
    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name} {detail}".rstrip())
    print(f"{len(results) - len(failed)}/{len(results)} guardrail self-tests passed")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

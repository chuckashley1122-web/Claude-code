"""Self-test for guardrails/*: demonstrates every block the spec requires.

Default run:
- pricing_guard blocks "$650 per month", "setup fee", "$197", and
  "250 to 300 per booked appointment", and passes clean copy;
- meeting_first routes pricing intent to the booking URL with no number;
- claim_guard blocks source-author claims, consumer brands, and banned terms;
- assert_clean passes on all fifteen prompt files, and a re-injected price into a
  prompt is caught.

``--prompts-dir DIR`` scans another prompt directory (exit 1 if any is blocked).
``--inject-price`` copies the prompts to a temp dir, re-injects a price into one,
and scans it; this must exit non-zero.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.constants import BOOKING_URL  # noqa: E402
from guardrails import claim_guard, meeting_first, pricing_guard  # noqa: E402

MUST_BLOCK_PRICING = ("$650 per month", "setup fee", "$197", "250 to 300 per booked appointment")
MUST_PASS_PRICING = (
    "Worth a quick chat? You can pick a time at " + BOOKING_URL,
    "We help HVAC contractors businesses with answering and booking inbound calls.",
    "Keep answers <25 words.",
)
MUST_BLOCK_CLAIMS = (
    "Our agent answers 10 calls at a time.",
    "Unlimited calls per day.",
    "Make UGC 10x faster with us.",
    "It runs for $300-400/mo.",
    "Fresh from " + claim_guard.CONSUMER_BRANDS[0] + ".",
    "We deliver " + claim_guard.BANNED_TERMS[0] + "s.",
)
INJECTION = " Only $650 per month, setup fee waived."


def scan_prompts(prompts_dir: Path) -> list[str]:
    failures = []
    files = sorted(prompts_dir.glob("*.txt"))
    for path in files:
        text = path.read_text(encoding="utf-8")
        try:
            pricing_guard.assert_clean(text, path.name)
            claim_guard.assert_no_claims(text, path.name)
        except (pricing_guard.PricingViolation, claim_guard.ClaimViolation) as exc:
            failures.append(str(exc))
    return failures


def self_test() -> list[str]:
    problems: list[str] = []

    def expect(cond: bool, msg: str):
        print(f"{'PASS' if cond else 'FAIL'}  {msg}")
        if not cond:
            problems.append(msg)

    for text in MUST_BLOCK_PRICING:
        r = pricing_guard.check(text)
        spans = ", ".join(f"{f.rule}:{f.text!r}" for f in r.findings)
        expect(r.status == pricing_guard.BLOCKED, f"pricing_guard BLOCKED {text!r} [{spans}]")
    for text in MUST_PASS_PRICING:
        expect(pricing_guard.check(text).status == pricing_guard.CLEAN, f"pricing_guard CLEAN {text!r}")
    try:
        pricing_guard.assert_clean("The setup fee is waived.")
        expect(False, "assert_clean raises on a price")
    except pricing_guard.PricingViolation:
        expect(True, "assert_clean raises PricingViolation on a price")

    r = meeting_first.route("How much does it cost per month?")
    expect(r.pricing_intent and BOOKING_URL in (r.reply or "") and not re.search(r"\d", r.reply or ""),
           "meeting_first routes pricing intent to the booking URL with no number")
    expect(meeting_first.route("Cuanto cuesta?").pricing_intent, "meeting_first detects Spanish pricing intent")
    expect(not meeting_first.route("What are your office hours?").pricing_intent,
           "meeting_first leaves non-pricing questions alone")

    for text in MUST_BLOCK_CLAIMS:
        expect(claim_guard.check(text).blocked, f"claim_guard BLOCKED {text!r}")
    expect(not claim_guard.check("We build AI front desks for home service companies.").blocked,
           "claim_guard CLEAN on plain B2B copy")

    prompt_failures = scan_prompts(ROOT / "prompts")
    count = len(list((ROOT / "prompts").glob("*.txt")))
    expect(count == 15 and not prompt_failures,
           f"assert_clean + claim check pass on all {count} prompt files")
    for f in prompt_failures:
        print(f"      {f}")

    sample = (ROOT / "prompts" / "02_cold_email.txt").read_text(encoding="utf-8") + INJECTION
    try:
        pricing_guard.assert_clean(sample, "02_cold_email.txt + injected price")
        expect(False, "re-injected price into a prompt is blocked")
    except pricing_guard.PricingViolation:
        expect(True, "re-injected price into a prompt is blocked")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prompts-dir", type=Path, help="scan this prompt directory only")
    ap.add_argument("--inject-price", action="store_true",
                    help="re-inject a price into a temp copy of the prompts and scan it (must fail)")
    args = ap.parse_args(argv)

    if args.inject_price:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "prompts"
            shutil.copytree(ROOT / "prompts", target)
            victim = target / "02_cold_email.txt"
            victim.write_text(victim.read_text(encoding="utf-8") + INJECTION, encoding="utf-8")
            failures = scan_prompts(target)
        for f in failures:
            print(f"BLOCKED  {f}")
        print(f"{len(failures)} prompt file(s) blocked after re-injecting a price")
        return 1 if failures else 0

    if args.prompts_dir:
        failures = scan_prompts(args.prompts_dir)
        for f in failures:
            print(f"BLOCKED  {f}")
        print(f"{len(failures)} prompt file(s) blocked")
        return 1 if failures else 0

    problems = self_test()
    print(f"guardrail self-test: {len(problems)} failure(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

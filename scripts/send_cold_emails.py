#!/usr/bin/env python3
"""Render and send/preview cold emails to leads exported from Leads Gorilla.

Usage:
    python scripts/send_cold_emails.py data/leads/caj_leads.csv --dry-run
    python scripts/send_cold_emails.py data/leads/caj_leads.csv --variant ab --limit 50
    python scripts/send_cold_emails.py data/leads/caj_leads.csv --variant ab --send

Variants:
    a  = "8 seconds" cost-framing hook
    b  = "free mockup" offer hook
    ab = deterministic 50/50 split by hash(email)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import pathlib
import re
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sendiio import SendiioClient, SendiioError  # noqa: E402

TEMPLATE_DIR = REPO_ROOT / "sendiio" / "templates"
SENT_LOG = REPO_ROOT / "data" / "sent" / "sent_emails.txt"

# Leads Gorilla "Local Lead Generator" export columns -> canonical lead fields.
LEADS_GORILLA_MAP = {
    "Business Name": "business_name",
    "E-Mail": "email",
    "Phone Number": "business_phone",
    "Website": "website",
    "Address": "address",
    "Rating": "rating",
    "Total Review": "review_count",
    "Domain": "domain",
}


def load_env() -> dict[str, str]:
    env_path = REPO_ROOT / ".env"
    env: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    for k, v in os.environ.items():
        env.setdefault(k, v)
    return env


def parse_city_state(address: str) -> tuple[str, str]:
    # Leads Gorilla addresses look like:
    #   "Business Name, 123 Some St, City, ST 12345"
    # We want the last two comma-separated chunks.
    parts = [p.strip() for p in address.split(",") if p.strip()]
    if len(parts) < 2:
        return "", ""
    m = re.match(r"^([A-Za-z]{2})\s+\d", parts[-1])
    if not m:
        return "", ""
    return parts[-2], m.group(1)


def normalize_lead(row: dict[str, str], default_service: str) -> dict[str, str] | None:
    """Map a Leads Gorilla row into the canonical lead dict, or None to skip."""
    if "Business Name" in row and "E-Mail" in row:
        out: dict[str, str] = {}
        for src, dst in LEADS_GORILLA_MAP.items():
            v = (row.get(src) or "").strip()
            if v.upper() == "N/A":
                v = ""
            out[dst] = v
        city, state = parse_city_state(out.get("address", ""))
        out["city"] = city
        out["state"] = state
    else:
        # Already-canonical CSV (e.g. example_leads.csv)
        out = {k: (v or "").strip() for k, v in row.items()}

    email = out.get("email", "")
    if not email or "@" not in email:
        return None
    out["email"] = email.lower()
    out.setdefault("service", default_service)
    out.setdefault("first_name", "")
    out.setdefault("last_name", "")
    return out


def load_leads(csv_path: pathlib.Path, default_service: str, limit: int | None) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        raw_rows = list(csv.DictReader(f))
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for row in raw_rows:
        lead = normalize_lead(row, default_service)
        if lead is None:
            continue
        if lead["email"] in seen:
            continue
        seen.add(lead["email"])
        out.append(lead)
        if limit is not None and len(out) >= limit:
            break
    return out


def build_greeting(first_name: str) -> str:
    fn = first_name.strip()
    if not fn:
        return ""
    return f"<p>Hi {fn},</p>\n\n"


def render(template: str, lead: dict[str, str], env: dict[str, str]) -> str:
    fields = {
        "greeting": build_greeting(lead.get("first_name", "")),
        "first_name": lead.get("first_name") or "there",
        "last_name": lead.get("last_name", ""),
        "business_name": lead.get("business_name") or "your business",
        "city": lead.get("city") or "your area",
        "state": lead.get("state", ""),
        "service": lead.get("service") or "home services",
        "email": lead.get("email", ""),
        "booking_url": env.get("BOOKING_URL", ""),
        "phone": env.get("BUSINESS_PHONE", ""),
        "sender_name": env.get("SENDER_NAME", "Chuck"),
        "company_name": env.get("COMPANY_NAME", "CA&J Enterprises"),
        "company_address": env.get("COMPANY_ADDRESS", "[ADDRESS NOT SET]"),
        "unsubscribe_url": env.get("UNSUBSCRIBE_URL", ""),
    }
    try:
        return template.format(**fields)
    except KeyError as e:
        raise SystemExit(f"Template references unknown placeholder: {e}")


def variant_for(email: str, variant_flag: str) -> str:
    if variant_flag in ("a", "b"):
        return variant_flag
    digest = hashlib.sha256(email.lower().encode()).digest()
    return "a" if digest[0] % 2 == 0 else "b"


def load_templates() -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    for v in ("a", "b"):
        subj = (TEMPLATE_DIR / f"cold_email_{v}.subject.txt").read_text().strip()
        html = (TEMPLATE_DIR / f"cold_email_{v}.html").read_text()
        out[v] = (subj, html)
    return out


def load_sent_log() -> set[str]:
    if not SENT_LOG.exists():
        return set()
    return {line.strip().lower() for line in SENT_LOG.read_text().splitlines() if line.strip()}


def append_sent(email: str) -> None:
    SENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SENT_LOG.open("a") as f:
        f.write(email.lower() + "\n")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("csv", type=pathlib.Path, help="Path to leads CSV (Leads Gorilla export)")
    p.add_argument("--send", action="store_true", help="Actually send via SendIIO (default: dry-run)")
    p.add_argument("--dry-run", action="store_true", help="Render only, no API calls (default)")
    p.add_argument("--limit", type=int, default=None, help="Process at most N leads (after dedup)")
    p.add_argument("--variant", choices=["a", "b", "ab"], default="a",
                   help="Template variant: a, b, or ab (50/50 split)")
    p.add_argument("--service", default="HVAC",
                   help="Default service category when not in CSV (e.g. HVAC, Electrician)")
    p.add_argument("--skip-sent", action="store_true",
                   help="Skip emails already in data/sent/sent_emails.txt")
    args = p.parse_args()

    if not args.csv.exists():
        print(f"CSV not found: {args.csv}", file=sys.stderr)
        return 2
    if args.send and args.dry_run:
        print("Pick one: --send OR --dry-run, not both.", file=sys.stderr)
        return 2

    env = load_env()
    templates = load_templates()
    leads = load_leads(args.csv, args.service, limit=None)  # load all, filter below

    sent_log = load_sent_log() if args.skip_sent else set()
    if sent_log:
        leads = [l for l in leads if l["email"] not in sent_log]
    if args.limit is not None:
        leads = leads[: args.limit]
    if not leads:
        print("No leads to process after dedup/skip.", file=sys.stderr)
        return 1

    do_send = args.send and not args.dry_run

    client: SendiioClient | None = None
    if do_send:
        try:
            client = SendiioClient(
                token=env.get("SENDIIO_TOKEN", ""),
                secret=env.get("SENDIIO_SECRET", ""),
                base_url=env.get("SENDIIO_BASE_URL", "https://sendiio.com/api/v1"),
            )
            client.check_credentials()
        except SendiioError as e:
            print(f"SendIIO auth failed: {e}", file=sys.stderr)
            return 1
        if env.get("COMPANY_ADDRESS", "").strip() in ("", "[ADDRESS NOT SET]"):
            print("Refusing to send: COMPANY_ADDRESS not set. CAN-SPAM requires a real "
                  "postal address in every commercial email.", file=sys.stderr)
            return 1
        if not env.get("FROM_EMAIL"):
            print("Refusing to send: FROM_EMAIL not set.", file=sys.stderr)
            return 1

    counts = {"a": 0, "b": 0}
    for i, lead in enumerate(leads, 1):
        email = lead["email"]
        v = variant_for(email, args.variant)
        subject_tpl, html_tpl = templates[v]
        subject = render(subject_tpl, lead, env)
        html = render(html_tpl, lead, env)
        print(f"\n=== [{i}/{len(leads)}] [{v.upper()}] {email}  ({lead.get('business_name')})  ===")
        print(f"Subject: {subject}")
        if not do_send:
            print(html)
            counts[v] += 1
            continue
        assert client is not None
        list_id = env.get("SENDIIO_LIST_ID", "")
        if not list_id:
            print("SENDIIO_LIST_ID not set; cannot send.", file=sys.stderr)
            return 1
        try:
            client.subscribe_email(
                list_id=list_id,
                email=email,
                first_name=lead.get("first_name", ""),
                last_name=lead.get("last_name", ""),
            )
            resp: dict[str, Any] = client.send_broadcast(
                list_id=list_id,
                subject=subject,
                html_body=html,
                from_name=env.get("FROM_NAME", "CA&J Enterprises"),
                from_email=env.get("FROM_EMAIL", ""),
                reply_to=env.get("REPLY_TO_EMAIL") or None,
            )
            print(f"sent: {resp}")
            append_sent(email)
            counts[v] += 1
        except SendiioError as e:
            print(f"send failed: {e}", file=sys.stderr)

    verb = "Sent" if do_send else "Previewed"
    print(f"\nDone. {verb}: A={counts['a']}  B={counts['b']}  (total={counts['a']+counts['b']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

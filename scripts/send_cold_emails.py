#!/usr/bin/env python3
"""Render and send/preview cold emails to leads exported from Leads Gorilla.

Usage:
    python scripts/send_cold_emails.py data/leads/example_leads.csv --dry-run
    python scripts/send_cold_emails.py data/leads/austin_hvac.csv --limit 5
    python scripts/send_cold_emails.py data/leads/austin_hvac.csv --send
"""
from __future__ import annotations

import argparse
import csv
import os
import pathlib
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sendiio import SendiioClient, SendiioError  # noqa: E402

TEMPLATE_DIR = REPO_ROOT / "sendiio" / "templates"


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


def render(template: str, lead: dict[str, str], env: dict[str, str]) -> str:
    fields = {
        "first_name": lead.get("first_name") or "there",
        "last_name": lead.get("last_name", ""),
        "business_name": lead.get("business_name") or lead.get("company") or "your business",
        "city": lead.get("city", "your area"),
        "state": lead.get("state", ""),
        "service": lead.get("service") or lead.get("category") or "home services",
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


def load_leads(csv_path: pathlib.Path, limit: int | None) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if limit is not None:
        rows = rows[:limit]
    return rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("csv", type=pathlib.Path, help="Path to leads CSV (Leads Gorilla export)")
    p.add_argument("--send", action="store_true", help="Actually send via SendIIO (default: dry-run)")
    p.add_argument("--dry-run", action="store_true", help="Render only, no API calls (default)")
    p.add_argument("--limit", type=int, default=None, help="Process only first N leads")
    p.add_argument("--subject-template", default=str(TEMPLATE_DIR / "cold_email.subject.txt"))
    p.add_argument("--html-template", default=str(TEMPLATE_DIR / "cold_email.html"))
    args = p.parse_args()

    if not args.csv.exists():
        print(f"CSV not found: {args.csv}", file=sys.stderr)
        return 2

    env = load_env()
    subject_tpl = pathlib.Path(args.subject_template).read_text().strip()
    html_tpl = pathlib.Path(args.html_template).read_text()
    leads = load_leads(args.csv, args.limit)

    if not leads:
        print("No leads in CSV.", file=sys.stderr)
        return 1

    if args.send and args.dry_run:
        print("Pick one: --send OR --dry-run, not both.", file=sys.stderr)
        return 2

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

    sent = 0
    for i, lead in enumerate(leads, 1):
        email = (lead.get("email") or "").strip()
        if not email:
            print(f"[{i}] SKIP (no email): {lead.get('business_name', '?')}")
            continue
        subject = render(subject_tpl, lead, env)
        html = render(html_tpl, lead, env)
        print(f"\n=== [{i}/{len(leads)}] {email} ===")
        print(f"Subject: {subject}")
        if not do_send:
            print(html)
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
            sent += 1
        except SendiioError as e:
            print(f"send failed: {e}", file=sys.stderr)

    print(f"\nDone. {'Sent' if do_send else 'Previewed'} {sent if do_send else len(leads)} leads.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

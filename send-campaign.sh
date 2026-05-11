#!/usr/bin/env bash
set -euo pipefail

CSV="${1:-}"
if [[ -z "$CSV" || ! -f "$CSV" ]]; then
  echo "usage: $0 <leadsgorilla-export.csv>" >&2
  echo "env: DRY_RUN=1 (default) | SUBJECT=\"...\" | LOG=path" >&2
  exit 1
fi

DRY_RUN="${DRY_RUN:-1}"
SUBJECT="${SUBJECT:-Quick question about {{biz}}}"
LOG="${LOG:-campaign-$(date +%Y%m%d-%H%M%S).log}"

send_email() {
  local to="$1" name="$2" biz="$3"
  local subject="${SUBJECT//\{\{biz\}\}/${biz:-your business}}"
  local body="Hi ${name:-there},

I came across ${biz:-your business} and wanted to reach out.

[ ... your pitch ... ]

Best,
Charles"

  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[DRY-RUN] to=$to subject=\"$subject\""
    return 0
  fi

  # Wire up your provider here. Example for SendGrid:
  #
  # curl -sS -X POST https://api.sendgrid.com/v3/mail/send \
  #   -H "Authorization: Bearer $SENDGRID_API_KEY" \
  #   -H "Content-Type: application/json" \
  #   -d "$(jq -n --arg to "$to" --arg subject "$subject" --arg body "$body" \
  #     '{personalizations:[{to:[{email:$to}]}],
  #       from:{email:"you@yourdomain.com"},
  #       subject:$subject,
  #       content:[{type:"text/plain",value:$body}]}')"
  #
  # Example for Mailgun:
  # curl -sS -X POST "https://api.mailgun.net/v3/$MAILGUN_DOMAIN/messages" \
  #   --user "api:$MAILGUN_API_KEY" \
  #   -F from="you@yourdomain.com" -F to="$to" \
  #   -F subject="$subject" -F text="$body"

  echo "ERROR: DRY_RUN=0 but no provider wired in send_email()." >&2
  return 1
}

# Python's csv module handles quoted commas, newlines in fields, etc. correctly.
mapfile -t records < <(
  python3 - "$CSV" <<'PY'
import csv, sys, re
path = sys.argv[1]
EMAIL = re.compile(r'^(email|e-?mail|email address)$', re.I)
NAME  = re.compile(r'^(name|contact|contact name|first name|owner|owner name)$', re.I)
BIZ   = re.compile(r'^(business|business name|company|company name)$', re.I)
with open(path, newline='', encoding='utf-8-sig', errors='replace') as f:
    r = csv.reader(f)
    try:
        header = [h.strip() for h in next(r)]
    except StopIteration:
        sys.exit("empty csv")
    ec = nc = bc = None
    for i, h in enumerate(header):
        if ec is None and EMAIL.match(h): ec = i
        elif nc is None and NAME.match(h): nc = i
        elif bc is None and BIZ.match(h):  bc = i
    if ec is None:
        sys.exit("no email column found in header")
    for row in r:
        def g(i): return row[i].strip() if i is not None and i < len(row) else ''
        email = g(ec)
        if not email: continue
        print(f"{email}\t{g(nc)}\t{g(bc)}")
PY
)

declare -A seen
sent=0; dup=0; invalid=0; failed=0

for rec in "${records[@]}"; do
  IFS=$'\t' read -r email name biz <<< "$rec"
  if [[ ! "$email" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
    invalid=$((invalid+1)); printf 'invalid\t%s\n' "$email" >> "$LOG"; continue
  fi
  key="${email,,}"
  if [[ -n "${seen[$key]:-}" ]]; then
    dup=$((dup+1)); printf 'dup\t%s\n' "$email" >> "$LOG"; continue
  fi
  seen[$key]=1
  if send_email "$email" "$name" "$biz" >> "$LOG" 2>&1; then
    sent=$((sent+1))
  else
    failed=$((failed+1))
  fi
done

echo "sent=$sent dup=$dup invalid=$invalid failed=$failed log=$LOG"

#!/usr/bin/env bash
# Schedule daily_leads.py to run every morning at 08:00 local time.
#
#   ./install_schedule.sh            # install or update the cron entry
#   ./install_schedule.sh --remove   # take it back out
#   ./install_schedule.sh --time 07:30
#
# Re-running is safe: the existing entry is replaced, not duplicated.
# Failures inside the run are recorded in errors.log by daily_leads.py itself;
# cron's own stdout/stderr goes to cron.log next to this script.

set -euo pipefail

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
MARKER="# leadscraper-daily"
TIME="08:00"
REMOVE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remove) REMOVE=1; shift ;;
    --time) TIME="$2"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if ! command -v crontab >/dev/null 2>&1; then
  echo "crontab not found. See README.md for the systemd timer and Windows" >&2
  echo "Task Scheduler equivalents." >&2
  exit 1
fi

HOUR="${TIME%%:*}"
MINUTE="${TIME##*:}"
HOUR="$((10#$HOUR))"
MINUTE="$((10#$MINUTE))"

# Drop any previous entry, keeping the rest of the crontab intact.
EXISTING="$(crontab -l 2>/dev/null || true)"
CLEANED="$(printf '%s\n' "$EXISTING" | grep -vF "$MARKER" || true)"

if [[ "$REMOVE" == "1" ]]; then
  printf '%s\n' "$CLEANED" | crontab -
  echo "Removed the daily lead scrape from cron."
  exit 0
fi

if [[ ! -x "$PROJECT_DIR/.venv/bin/python" ]]; then
  echo "No .venv found. Run ./setup.sh first." >&2
  exit 1
fi

ENTRY="$MINUTE $HOUR * * * cd $PROJECT_DIR && $PROJECT_DIR/.venv/bin/python daily_leads.py >> $PROJECT_DIR/cron.log 2>&1 $MARKER"

printf '%s\n%s\n' "$CLEANED" "$ENTRY" | grep -v '^$' | crontab -

echo "Scheduled the daily lead scrape at ${TIME} local time:"
echo "  $ENTRY"
echo
echo "Check it with:  crontab -l"
echo "Run it now with:  .venv/bin/python daily_leads.py"

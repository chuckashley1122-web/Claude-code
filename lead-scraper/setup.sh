#!/usr/bin/env bash
# One-shot setup: virtual environment, Python packages, Chromium.
#
#   ./setup.sh
#
# Afterwards, start the local model and run the smoke test:
#
#   ollama serve &
#   ollama pull llama3.1
#   .venv/bin/python test_scrape.py

set -euo pipefail

cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

echo "==> Creating virtual environment in .venv"
"$PYTHON" -m venv .venv

echo "==> Installing Python packages"
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo "==> Installing the Chromium build Playwright expects"
.venv/bin/playwright install chromium

cat <<'EOF'

Setup complete.

Next steps:
  1. Install Ollama if you have not already:  https://ollama.com
  2. Start it and pull the model:
       ollama serve &
       ollama pull llama3.1
  3. Check the install end to end:
       .venv/bin/python test_scrape.py
  4. Verify the pipeline logic offline (no model needed):
       .venv/bin/python selftest.py
  5. Point config.yml at a real directory URL, then:
       .venv/bin/python lead_scraper.py --max-pages 2 --dry-run

EOF

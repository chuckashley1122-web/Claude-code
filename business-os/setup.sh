#!/usr/bin/env bash
# Create the data/ folder from templates. Safe to re-run — never overwrites a
# file that already has real business data in it.
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d templates/data ]; then
  echo "Error: templates/data/ not found. Run this script from inside the" >&2
  echo "business-os folder, with the templates/ directory intact." >&2
  exit 1
fi

mkdir -p data

created=0
skipped=0
for template in templates/data/*.md; do
  target="data/$(basename "$template")"
  if [ -e "$target" ]; then
    echo "  skip    $target (already exists)"
    skipped=$((skipped + 1))
  else
    cp "$template" "$target"
    echo "  create  $target"
    created=$((created + 1))
  fi
done

if [ ! -e .env ] && [ -e .env.example ]; then
  cp .env.example .env
  chmod 600 .env
  echo "  create  .env (from .env.example — fill in any keys you need)"
  created=$((created + 1))
fi

echo
echo "Done: $created created, $skipped left alone."

if [ -e .gitignore ] && grep -q '^/data/$' .gitignore && grep -q '^\.env$' .gitignore; then
  echo "data/ and .env are gitignored — your business data stays local."
else
  echo "WARNING: business-os/.gitignore is missing or incomplete. Add 'data/'" >&2
  echo "and '.env' to it before committing, or you will commit real business" >&2
  echo "data and API keys." >&2
fi
echo
echo "Next: fill in business.md, then run 'claude' here and try /run-all."

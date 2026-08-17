#!/usr/bin/env bash
# Create the data/ folder from templates. Safe to re-run — never overwrites a
# file that already has real business data in it.
set -euo pipefail

cd "$(dirname "$0")"

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
  echo "  create  .env (from .env.example — fill in any keys you need)"
fi

echo
echo "Done: $created created, $skipped left alone."
echo "data/ and .env are gitignored — your business data stays local."
echo
echo "Next: fill in business.md, then run 'claude' here and try /run-all."

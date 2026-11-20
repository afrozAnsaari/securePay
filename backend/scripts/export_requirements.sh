#!/usr/bin/env bash
# Regenerate the pip requirement files from uv.lock so uv and pip
# always install exactly the same versions.
# Run from anywhere:  ./scripts/export_requirements.sh
set -euo pipefail
cd "$(dirname "$0")/.."

uv export --frozen --no-hashes --no-dev --no-emit-project \
  --format requirements-txt -o requirements.txt >/dev/null

{
  echo "# Dev / notebook tools. Install with: pip install -r requirements-dev.txt"
  echo "-r requirements.txt"
  uv export --frozen --no-hashes --only-group dev --no-emit-project \
    --format requirements-txt
} > requirements-dev.txt

echo "requirements.txt and requirements-dev.txt updated from uv.lock"

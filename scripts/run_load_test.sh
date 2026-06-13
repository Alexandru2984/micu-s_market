#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${BASE_URL:-${APP_BASE_URL:-http://127.0.0.1:8000}}"

if ! command -v k6 >/dev/null 2>&1; then
  echo "k6 is not installed. Install it first: https://grafana.com/docs/k6/latest/set-up/install-k6/" >&2
  exit 127
fi

cd "$ROOT_DIR"
BASE_URL="$BASE_URL" k6 run scripts/load_test.js

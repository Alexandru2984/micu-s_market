#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-${APP_BASE_URL:-http://127.0.0.1:8000}}"
BASE_URL="${BASE_URL%/}"

check_url() {
  local label="$1"
  local url="$2"
  local expected="${3:-200}"
  local status

  status="$(curl -fsS -o /tmp/micu_smoke_response.txt -w '%{http_code}' "$url")"
  if [[ "$status" != "$expected" ]]; then
    echo "FAIL $label: expected $expected, got $status" >&2
    cat /tmp/micu_smoke_response.txt >&2 || true
    exit 1
  fi
  echo "OK $label $status"
}

check_url "health" "$BASE_URL/healthz"
check_url "home" "$BASE_URL/"
check_url "api-listings" "$BASE_URL/api/listings/"

echo "Smoke checks passed for $BASE_URL"

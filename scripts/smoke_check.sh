#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-${APP_BASE_URL:-http://127.0.0.1:8000}}"
BASE_URL="${BASE_URL%/}"
RESPONSE_FILE="$(mktemp)"
HEADER_FILE="$(mktemp)"
trap 'rm -f "$RESPONSE_FILE" "$HEADER_FILE"' EXIT

check_url() {
  local label="$1"
  local url="$2"
  local expected="${3:-200}"
  local status

  status="$(curl -sS -D "$HEADER_FILE" -o "$RESPONSE_FILE" -w '%{http_code}' "$url")"
  if [[ "$status" != "$expected" ]]; then
    echo "FAIL $label: expected $expected, got $status" >&2
    cat "$RESPONSE_FILE" >&2 || true
    exit 1
  fi
  echo "OK $label $status"
}

check_header() {
  local label="$1"
  local url="$2"
  local header="$3"
  local expected_fragment="$4"

  curl -sS -D "$HEADER_FILE" -o "$RESPONSE_FILE" "$url" >/dev/null
  if ! awk -v header="$header" -v expected="$expected_fragment" '
    BEGIN { found = 0 }
    {
      line = tolower($0)
      wanted = tolower(header) ":"
      if (index(line, wanted) == 1 && index(tolower($0), tolower(expected)) > 0) {
        found = 1
      }
    }
    END { exit found ? 0 : 1 }
  ' "$HEADER_FILE"; then
    echo "FAIL $label: missing $header containing '$expected_fragment'" >&2
    cat "$HEADER_FILE" >&2 || true
    exit 1
  fi
  echo "OK $label header $header"
}

check_url "health" "$BASE_URL/healthz"
check_url "home" "$BASE_URL/"
check_url "api-listings" "$BASE_URL/api/listings/"
check_url "private-chat-media-blocked" "$BASE_URL/media/chat/private/attachments/smoke.txt" 404

check_header "home" "$BASE_URL/" "X-Frame-Options" "DENY"
check_header "home" "$BASE_URL/" "X-Content-Type-Options" "nosniff"
check_header "home" "$BASE_URL/" "Permissions-Policy" "geolocation=()"
if [[ "$BASE_URL" == https://* ]]; then
  check_header "home" "$BASE_URL/" "Strict-Transport-Security" "max-age="
fi

echo "Smoke checks passed for $BASE_URL"

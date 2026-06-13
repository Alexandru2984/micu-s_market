#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /path/to/micu_market_YYYYmmddTHHMMSSZ.dump" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DUMP_FILE="$1"

cd "$ROOT_DIR"

if [[ ! -f "$DUMP_FILE" ]]; then
  echo "Backup dump not found: $DUMP_FILE" >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  echo ".env is missing in $ROOT_DIR" >&2
  exit 1
fi

set -a
source .env
set +a

: "${DB_USER:?DB_USER is required}"
: "${DB_PASS:?DB_PASS is required}"
: "${DB_HOST:?DB_HOST is required}"
: "${DB_PORT:=5432}"

restore_db="micu_market_restore_$(date -u +%Y%m%d%H%M%S)"

cleanup() {
  PGPASSWORD="$DB_PASS" dropdb \
    --if-exists \
    --host "$DB_HOST" \
    --port "$DB_PORT" \
    --username "$DB_USER" \
    "$restore_db" >/dev/null 2>&1 || true
}
trap cleanup EXIT

PGPASSWORD="$DB_PASS" createdb \
  --host "$DB_HOST" \
  --port "$DB_PORT" \
  --username "$DB_USER" \
  "$restore_db"

PGPASSWORD="$DB_PASS" pg_restore \
  --host "$DB_HOST" \
  --port "$DB_PORT" \
  --username "$DB_USER" \
  --dbname "$restore_db" \
  --no-owner \
  "$DUMP_FILE"

PGPASSWORD="$DB_PASS" psql \
  --host "$DB_HOST" \
  --port "$DB_PORT" \
  --username "$DB_USER" \
  --dbname "$restore_db" \
  --tuples-only \
  --command "SELECT COUNT(*) FROM django_migrations;" >/dev/null

echo "Backup restore verified in temporary database: $restore_db"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/micu_market}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

cd "$ROOT_DIR"
source scripts/lib_security.sh
check_env_file_permissions .env

if [[ ! -f .env ]]; then
  echo ".env is missing in $ROOT_DIR" >&2
  exit 1
fi

set -a
source .env
set +a

: "${DB_NAME:?DB_NAME is required}"
: "${DB_USER:?DB_USER is required}"
: "${DB_PASS:?DB_PASS is required}"
: "${DB_HOST:?DB_HOST is required}"
: "${DB_PORT:=5432}"

mkdir -p "$BACKUP_DIR"
chmod 750 "$BACKUP_DIR"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="$BACKUP_DIR/micu_market_${timestamp}.dump"

PGPASSWORD="$DB_PASS" pg_dump \
  --host "$DB_HOST" \
  --port "$DB_PORT" \
  --username "$DB_USER" \
  --format custom \
  --file "$out" \
  "$DB_NAME"

chmod 600 "$out"
find "$BACKUP_DIR" -type f -name 'micu_market_*.dump' -mtime +"$RETENTION_DAYS" -delete

echo "$out"

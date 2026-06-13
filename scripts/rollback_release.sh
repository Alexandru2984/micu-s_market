#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_REF="${1:-}"
SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-Micu_market.settings_production}"
SERVICE_NAME="${SERVICE_NAME:-micu-market}"
RUN_BACKUP="${RUN_BACKUP:-1}"
RUN_MIGRATE="${RUN_MIGRATE:-0}"
RUN_RESTART="${RUN_RESTART:-1}"
RUN_SMOKE="${RUN_SMOKE:-1}"

cd "$ROOT_DIR"
source scripts/lib_security.sh
check_env_file_permissions .env

if [[ -z "$TARGET_REF" ]]; then
  echo "Usage: ROLLBACK_CONFIRM=1 scripts/rollback_release.sh <git-ref>" >&2
  exit 2
fi

if [[ "${ROLLBACK_CONFIRM:-0}" != "1" ]]; then
  echo "Refusing rollback without ROLLBACK_CONFIRM=1." >&2
  exit 2
fi

if [[ -n "$(git status --short)" ]]; then
  echo "Worktree is dirty. Commit or stash changes before rollback." >&2
  git status --short >&2
  exit 1
fi

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

current_ref="$(git rev-parse --short HEAD)"
target_sha="$(git rev-parse --verify "$TARGET_REF")"
echo "Rolling back from $current_ref to $target_sha"

if [[ "$RUN_BACKUP" == "1" ]]; then
  backup_path="$(scripts/backup_postgres.sh)"
  echo "Backup created: $backup_path"
fi

git switch --detach "$target_sha"
venv/bin/python -m pip install -r requirements.txt
venv/bin/python manage.py check --deploy --settings="$SETTINGS_MODULE"

if [[ "$RUN_MIGRATE" == "1" ]]; then
  venv/bin/python manage.py migrate --noinput --settings="$SETTINGS_MODULE"
else
  echo "Skipping migrations during rollback. Set RUN_MIGRATE=1 only after checking migration compatibility."
fi

venv/bin/python manage.py collectstatic --noinput --settings="$SETTINGS_MODULE"

if [[ "$RUN_RESTART" == "1" ]]; then
  sudo systemctl restart "$SERVICE_NAME"
fi

if [[ "$RUN_SMOKE" == "1" ]]; then
  scripts/smoke_check.sh "${APP_BASE_URL:-http://127.0.0.1:8000}"
fi

echo "Rollback completed from $current_ref to $target_sha."

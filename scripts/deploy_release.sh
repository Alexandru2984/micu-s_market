#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-Micu_market.settings_production}"
SERVICE_NAME="${SERVICE_NAME:-micu-market}"
RUN_RESTART="${RUN_RESTART:-1}"
RUN_SMOKE="${RUN_SMOKE:-1}"

cd "$ROOT_DIR"
source scripts/lib_security.sh
check_env_file_permissions .env

if [[ -n "$(git status --short)" ]]; then
  echo "Worktree is dirty. Commit or stash changes before deploy." >&2
  git status --short >&2
  exit 1
fi

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

venv/bin/python -m pip install -r requirements.txt
venv/bin/python manage.py check --deploy --settings="$SETTINGS_MODULE"
venv/bin/python manage.py doctor --settings="$SETTINGS_MODULE"
venv/bin/python manage.py makemigrations --check --dry-run --settings="$SETTINGS_MODULE"
venv/bin/python manage.py migrate --noinput --settings="$SETTINGS_MODULE"
venv/bin/python manage.py collectstatic --noinput --settings="$SETTINGS_MODULE"

if [[ "$RUN_RESTART" == "1" ]]; then
  sudo systemctl restart "$SERVICE_NAME"
fi

if [[ "$RUN_SMOKE" == "1" ]]; then
  scripts/smoke_check.sh "${APP_BASE_URL:-http://127.0.0.1:8000}"
fi

echo "Deploy completed."

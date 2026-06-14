#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-Micu_market.settings_production}"
RUN_TESTS="${RUN_TESTS:-1}"
RUN_AUDIT="${RUN_AUDIT:-1}"
RUN_DOCTOR="${RUN_DOCTOR:-1}"

cd "$ROOT_DIR"
source scripts/lib_security.sh
check_env_file_permissions .env
check_sensitive_file_permissions

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

venv/bin/python -m pip check
venv/bin/python manage.py check --deploy --settings="$SETTINGS_MODULE"
venv/bin/python manage.py makemigrations --check --dry-run --settings="${TEST_SETTINGS_MODULE:-Micu_market.settings_test}"

if [[ "$RUN_DOCTOR" == "1" ]]; then
  venv/bin/python manage.py doctor --settings="$SETTINGS_MODULE"
fi

if [[ "$RUN_TESTS" == "1" ]]; then
  venv/bin/python manage.py test --settings="${TEST_SETTINGS_MODULE:-Micu_market.settings_test}"
fi

if [[ "$RUN_AUDIT" == "1" ]]; then
  if [[ -x venv/bin/pip-audit ]]; then
    venv/bin/pip-audit -r requirements.txt
  else
    echo "pip-audit is not installed in venv; skipping dependency audit." >&2
  fi
fi

echo "Preflight checks passed."

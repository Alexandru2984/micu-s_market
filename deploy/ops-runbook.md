# Operations runbook

## Healthcheck

The application exposes:

```text
GET /pages/healthz
```

Expected healthy response:

```json
{"status": "ok", "database": "ok"}
```

Use this endpoint from uptime monitoring and internal deployment checks. It verifies that Django can reach PostgreSQL.

## PostgreSQL backup

Create a backup directory owned by the deploy user:

```bash
sudo install -d -o micu -g micu -m 750 /var/backups/micu_market
```

Example daily backup script:

```bash
#!/usr/bin/env bash
set -euo pipefail

cd /home/micu/Micu_market
set -a
source .env
set +a

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="/var/backups/micu_market/micu_market_${timestamp}.dump"

PGPASSWORD="$DB_PASS" pg_dump \
  --host "$DB_HOST" \
  --port "$DB_PORT" \
  --username "$DB_USER" \
  --format custom \
  --file "$out" \
  "$DB_NAME"

chmod 600 "$out"
find /var/backups/micu_market -type f -name 'micu_market_*.dump' -mtime +14 -delete
```

Cron:

```cron
15 2 * * * /home/micu/Micu_market/scripts/backup_postgres.sh
```

Restore drill:

```bash
createdb micu_market_restore
pg_restore --dbname micu_market_restore /var/backups/micu_market/<backup>.dump
```

## Logs

Production settings log to stdout/stderr by default. Prefer `journalctl` for Gunicorn:

```bash
journalctl -u micu-market -f
journalctl -u micu-market --since "1 hour ago"
```

If file logging is enabled with `DJANGO_LOG_TO_FILE=True`, create the directory first and configure logrotate:

```bash
sudo install -d -o www-data -g adm -m 750 /var/log/micu_market
```

```text
/var/log/micu_market/*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
    copytruncate
}
```

## Deploy checklist

```bash
cd /home/micu/Micu_market
git pull --ff-only
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --settings=Micu_market.settings_production
python manage.py collectstatic --noinput --settings=Micu_market.settings_production
python manage.py check --deploy --settings=Micu_market.settings_production
sudo systemctl restart micu-market
curl -fsS https://market.micutu.com/pages/healthz
```

## Cloudflare/origin checks

- Cloudflare SSL/TLS mode: `Full (strict)`.
- Origin should not be reachable directly from the public internet except through Cloudflare, if possible.
- Nginx must return 404 for `/media/chat/private/`.
- The public Nginx listener must overwrite `X-Forwarded-Proto` with `$scheme`.
- `DJANGO_USE_X_FORWARDED_PROTO=True` and `DJANGO_TRUSTED_PROXY_CHAIN_CONFIGURED=True` should stay enabled only while the proxy chain is verified.

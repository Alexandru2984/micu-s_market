# Operations runbook

## Healthcheck

The application exposes:

```text
GET /healthz
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

Use the bundled script:

```bash
/home/micu/Micu_market/scripts/backup_postgres.sh
```

Cron:

```cron
15 2 * * * BACKUP_DIR=/var/backups/micu_market /home/micu/Micu_market/scripts/backup_postgres.sh >/var/log/micu_market/backup.log 2>&1
```

Restore drill:

```bash
scripts/verify_postgres_backup.sh /var/backups/micu_market/<backup>.dump
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
APP_BASE_URL=https://market.micutu.com scripts/deploy_release.sh
```

Smoke checks only:

```bash
APP_BASE_URL=https://market.micutu.com scripts/smoke_check.sh
```

Load test from a non-production shell:

```bash
BASE_URL=https://market.micutu.com SEARCH_TERM=telefon LISTING_SLUG=slug-real scripts/run_load_test.sh
```

Default thresholds fail the run if page p95 is above 800ms, API p95 is above 500ms, or the HTTP error rate reaches 1%.

External service checks only:

```bash
venv/bin/python manage.py doctor --settings=Micu_market.settings_production
```

To verify SMTP delivery explicitly, pass a real inbox:

```bash
venv/bin/python manage.py doctor --settings=Micu_market.settings_production --send-test-email you@example.com
```

## systemd service

Install or refresh the service unit:

```bash
sudo cp /home/micu/Micu_market/deploy/systemd/micu-market.service /etc/systemd/system/micu-market.service
sudo systemctl daemon-reload
sudo systemctl enable micu-market
sudo systemctl restart micu-market
sudo systemctl status micu-market --no-pager
```

The service reads `/home/micu/Micu_market/.env` and starts Gunicorn through the project virtualenv.

Install scheduled operations:

```bash
sudo cp /home/micu/Micu_market/deploy/systemd/micu-market-backup.* /etc/systemd/system/
sudo cp /home/micu/Micu_market/deploy/systemd/micu-market-notification-emails.* /etc/systemd/system/
sudo cp /home/micu/Micu_market/deploy/systemd/micu-market-media-cleanup.* /etc/systemd/system/
sudo cp /home/micu/Micu_market/deploy/systemd/micu-market-jobs.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now micu-market-backup.timer
sudo systemctl enable --now micu-market-notification-emails.timer
sudo systemctl enable --now micu-market-media-cleanup.timer
sudo systemctl enable --now micu-market-jobs.timer
systemctl list-timers 'micu-market-*'
```

Queue a background job manually:

```bash
venv/bin/python manage.py enqueue_periodic_jobs --settings=Micu_market.settings_production
venv/bin/python manage.py enqueue_job notifications.send_pending_emails --payload '{"limit": 200}' --settings=Micu_market.settings_production
venv/bin/python manage.py run_jobs --limit 10 --settings=Micu_market.settings_production
```

## Nginx vhost

Install or refresh the vhost after adjusting certificate paths in `deploy/nginx/micu-market.conf`:

```bash
sudo cp /home/micu/Micu_market/deploy/nginx/micu-market.conf /etc/nginx/sites-available/micu-market.conf
sudo ln -sfn /etc/nginx/sites-available/micu-market.conf /etc/nginx/sites-enabled/micu-market.conf
sudo nginx -t
sudo systemctl reload nginx
```

## Cloudflare/origin checks

- Cloudflare SSL/TLS mode: `Full (strict)`.
- Origin should not be reachable directly from the public internet except through Cloudflare, if possible.
- Nginx must return 404 for `/media/chat/private/`.
- The public Nginx listener must overwrite `X-Forwarded-Proto` with `$scheme`.
- `DJANGO_USE_X_FORWARDED_PROTO=True` and `DJANGO_TRUSTED_PROXY_CHAIN_CONFIGURED=True` should stay enabled only while the proxy chain is verified.

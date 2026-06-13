import os

os.environ.setdefault("SENTRY_ENVIRONMENT", "staging")

from .settings_production import *

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,staging.market.micutu.com").split(",")
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "300"))
EMAIL_SUBJECT_PREFIX = "[STAGING Micu's Market] "

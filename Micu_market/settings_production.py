# settings_production.py
from .settings import *

SENTRY_DSN = os.getenv('SENTRY_DSN', '')
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=False,
        traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.05')),
        profiles_sample_rate=float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.0')),
        environment=os.getenv('SENTRY_ENVIRONMENT', 'production'),
        release=os.getenv('SENTRY_RELEASE', ''),
    )

# Security settings pentru producție
DEBUG = False
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,market.micutu.com').split(',')

# HTTPS settings
SECURE_SSL_REDIRECT = True
if os.getenv('DJANGO_USE_X_FORWARDED_PROTO', 'False') == 'True':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Static files cu WhiteNoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Database production (din environment variables)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASS'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Logging
LOG_DIR = os.getenv('DJANGO_LOG_DIR', '/var/log/micu_market')
LOG_FILE = os.path.join(LOG_DIR, 'django.log')
LOG_TO_FILE = os.getenv('DJANGO_LOG_TO_FILE', 'False') == 'True'
LOG_LEVEL = os.getenv('DJANGO_LOG_LEVEL', 'INFO')
LOG_HANDLER = {
    'level': LOG_LEVEL,
    'class': 'logging.FileHandler',
    'filename': LOG_FILE,
    'formatter': 'production',
    'filters': ['request_id'],
} if LOG_TO_FILE else {
    'level': LOG_LEVEL,
    'class': 'logging.StreamHandler',
    'formatter': 'production',
    'filters': ['request_id'],
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {
            '()': 'Micu_market.observability.RequestIdFilter',
        },
    },
    'formatters': {
        'production': {
            'format': '%(asctime)s %(levelname)s [%(request_id)s] %(name)s %(message)s',
        },
    },
    'handlers': {
        'default': LOG_HANDLER,
    },
    'loggers': {
        'django': {
            'handlers': ['default'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'audit': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

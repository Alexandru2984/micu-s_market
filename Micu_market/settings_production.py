# settings_production.py
from .settings import *

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
LOG_HANDLER = {
    'level': 'ERROR',
    'class': 'logging.FileHandler',
    'filename': LOG_FILE,
} if LOG_TO_FILE else {
    'level': 'ERROR',
    'class': 'logging.StreamHandler',
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'default': LOG_HANDLER,
    },
    'loggers': {
        'django': {
            'handlers': ['default'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

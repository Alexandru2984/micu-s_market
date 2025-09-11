"""
Django settings for Micu_market project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# ======================
# BAZA
# ======================
BASE_DIR = Path(__file__).resolve().parent.parent

# încarcă variabile din .env (plasat lângă manage.py)
load_dotenv(BASE_DIR / ".env")

# ======================
# SECRET / DEBUG
# ======================
SECRET_KEY = os.getenv("SECRET_KEY", os.getenv("DJANGO_SECRET_KEY", "dev-secret-change-me"))
DEBUG = os.getenv("DEBUG", os.getenv("DJANGO_DEBUG", "1")) == "1"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")).split(",")

# ======================
# APPS
# ======================
INSTALLED_APPS = [
    # django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",  # necesar pentru allauth

    # allauth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    # "allauth.socialaccount.providers.google",  # dacă vrei Google login
    # "allauth.socialaccount.providers.facebook",  # dacă vrei Facebook login

    # apps proiect
    "pages",
    "accounts",
    "listings",
    "categories",
    "search",
    "chat",
    "reviews",
    "favorites",
    "notifications",
    "dashboard",
    "api",
    # "ws",  # doar dacă ai app ws
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # allauth middleware
]

ROOT_URLCONF = "Micu_market.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # PRIORITATE: template-uri globale
        "APP_DIRS": True,  # apoi template-urile din aplicații
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",  # necesar pentru allauth
            ],
        },
    },
]

WSGI_APPLICATION = "Micu_market.wsgi.application"
ASGI_APPLICATION = "Micu_market.asgi.application"

# ======================
# DATABASE (PostgreSQL)
# ======================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "micu_market"),
        "USER": os.getenv("DB_USER", "micu"),
        "PASSWORD": os.getenv("DB_PASS", ""),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}


# ======================
# AUTH / SECURITY
# ======================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"

# ======================
# LOCALE
# ======================
LANGUAGE_CODE = "ro-ro"
TIME_ZONE = "Europe/Bucharest"
USE_I18N = True
USE_TZ = True

# ======================
# STATIC / MEDIA
# ======================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATIC_ROOT = os.getenv("STATIC_ROOT", str(BASE_DIR / "staticfiles"))

MEDIA_URL = "/media/"
MEDIA_ROOT = os.getenv("MEDIA_ROOT", str(BASE_DIR / "media"))

# Security settings pentru producție
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True") == "True"
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "True") == "True"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "True") == "True"
    CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "True") == "True"
    SECURE_REFERRER_POLICY = "same-origin"

# ======================
# DEFAULT PK
# ======================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ======================
# DJANGO-ALLAUTH SETTINGS
# ======================
SITE_ID = 1

# Site name for emails
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[Micu\'s Market] '

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Custom adapter pentru username auto-generat
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'

# Allauth settings (sintaxa nouă)
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'
# ACCOUNT_USERNAME_REQUIRED = False  # DEPRECATED - folosim ACCOUNT_SIGNUP_FIELDS

# Signup fields (înlocuiește ACCOUNT_USERNAME_REQUIRED)
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']

# Auto-generate username from email
ACCOUNT_PRESERVE_USERNAME_CASING = False
ACCOUNT_SESSION_REMEMBER = True

# Rate limits
ACCOUNT_RATE_LIMITS = {
    'login_failed': '5/5m',  # 5 încercări la 5 minute
}

# Email confirmation settings
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_EMAIL_CONFIRMATION_HMAC = True

# Login/logout settings
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_SESSION_REMEMBER = True

# Password reset settings
ACCOUNT_PASSWORD_MIN_LENGTH = 8

# Redirect URLs
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

# ======================
# EMAIL SETTINGS
# ======================
# Email backend for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'micutu.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '465'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'market@micutu.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Micu\'s Market <market@micutu.com>')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', 'server@micutu.com')

# Email backend for development (decomentează pentru testare în consolă)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

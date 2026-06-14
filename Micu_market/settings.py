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
# IMPORTANT: SECRET_KEY sau DJANGO_SECRET_KEY trebuie setat în .env — aplicația va crăpa intenționat dacă lipsesc
SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY (sau DJANGO_SECRET_KEY) nu este setat în variabilele de mediu. "
        "Adaugă-l în fișierul .env."
    )
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")).split(",")


def _split_env(name, default=""):
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]

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
    "django.contrib.sitemaps",
    "django.contrib.postgres",

    # third-party
    "corsheaders",
    "storages",
    "channels",

    # allauth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    # "allauth.socialaccount.providers.google",  # dacă vrei Google login
    # "allauth.socialaccount.providers.facebook",  # dacă vrei Facebook login

    # apps proiect
    "pages.apps.PagesConfig",
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
    "audit.apps.AuditConfig",
    "billing.apps.BillingConfig",
    "jobs.apps.JobsConfig",
    # "ws",  # doar dacă ai app ws
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "Micu_market.observability.RequestIdMiddleware",
    "Micu_market.security.ClientIPMiddleware",
    "Micu_market.security.SecurityHeadersMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
                "django.template.context_processors.debug",
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

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
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

DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv("DATA_UPLOAD_MAX_MEMORY_SIZE", str(10 * 1024 * 1024)))
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv("FILE_UPLOAD_MAX_MEMORY_SIZE", str(5 * 1024 * 1024)))

CORS_ALLOWED_ORIGINS = _split_env("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = _split_env("CSRF_TRUSTED_ORIGINS")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "micu-market-local",
    }
}
RATELIMIT_USE_CACHE = os.getenv("RATELIMIT_USE_CACHE", "default")

# Channels (WebSocket) — layer Redis ca group_send să treacă între workerii uvicorn.
# DB Redis dedicat (/2) ca să nu se ciocnească cu cache/ratelimit. Pentru dev fără
# Redis se poate forța layerul in-memory cu CHANNELS_IN_MEMORY=1.
CHANNELS_REDIS_URL = os.getenv("CHANNELS_REDIS_URL", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/2"))
if os.getenv("CHANNELS_IN_MEMORY") == "1":
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [CHANNELS_REDIS_URL]},
        }
    }
API_READ_RATE = os.getenv("API_READ_RATE", "120/m")
API_WRITE_RATE = os.getenv("API_WRITE_RATE", "30/m")
AJAX_WRITE_RATE = os.getenv("AJAX_WRITE_RATE", "120/m")
REPORT_WRITE_RATE = os.getenv("REPORT_WRITE_RATE", "10/h")
SENSITIVE_READ_RATE = os.getenv("SENSITIVE_READ_RATE", "60/m")
CHAT_START_RATE = os.getenv("CHAT_START_RATE", "30/h")
AUTH_LOGIN_IP_RATE = os.getenv("AUTH_LOGIN_IP_RATE", "20/5m")
AUTH_LOGIN_USER_RATE = os.getenv("AUTH_LOGIN_USER_RATE", "10/15m")
AUTH_REGISTER_RATE = os.getenv("AUTH_REGISTER_RATE", "5/h")
BILLING_ORDER_RATE = os.getenv("BILLING_ORDER_RATE", "10/h")
HOMEPAGE_CACHE_SECONDS = int(os.getenv("HOMEPAGE_CACHE_SECONDS", "300"))
LISTING_AUTO_HIDE_REPORT_THRESHOLD = int(os.getenv("LISTING_AUTO_HIDE_REPORT_THRESHOLD", "3"))
LISTING_VIEW_COOLDOWN_SECONDS = int(os.getenv("LISTING_VIEW_COOLDOWN_SECONDS", "3600"))
LISTING_RISK_REVIEW_THRESHOLD = int(os.getenv("LISTING_RISK_REVIEW_THRESHOLD", "70"))
LISTING_RISK_TERMS = _split_env(
    "LISTING_RISK_TERMS",
    "whatsapp,telegram,avans,western union,crypto,bitcoin,revolut only,livrare doar cu plata in avans",
)
CHAT_MESSAGE_MAX_LENGTH = int(os.getenv("CHAT_MESSAGE_MAX_LENGTH", "5000"))

# Security settings pentru producție
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True") == "True"
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "True") == "True"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "True") == "True"
    CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "True") == "True"
    SECURE_REFERRER_POLICY = "same-origin"

# Security settings — active întotdeauna (nu doar în producție)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "Lax")
PERMISSIONS_POLICY = os.getenv("PERMISSIONS_POLICY", "geolocation=(), microphone=(), camera=()")
CROSS_ORIGIN_RESOURCE_POLICY = os.getenv("CROSS_ORIGIN_RESOURCE_POLICY", "same-site")
CROSS_ORIGIN_OPENER_POLICY = os.getenv("CROSS_ORIGIN_OPENER_POLICY", "same-origin")
# CSP enforced este servit de nginx (snippets/security-headers.conf) ca sursă
# unică pentru market. Aici definim doar o variantă strictă (script-src fără
# 'unsafe-inline', plus object-src/base-uri/form-action) rulată în report-only,
# ca să raporteze ce ar trebui curățat (handlerele onclick) înainte de lockdown.
DEFAULT_CONTENT_SECURITY_POLICY_REPORT_ONLY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob: https:;"
    "font-src 'self'; "
    "connect-src 'self'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'none'"
)
CONTENT_SECURITY_POLICY_REPORT_ONLY = os.getenv(
    "CONTENT_SECURITY_POLICY_REPORT_ONLY",
    DEFAULT_CONTENT_SECURITY_POLICY_REPORT_ONLY,
)

# Setări HTTPS active doar când nu suntem în dev local
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True") == "True"
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "True") == "True"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "True") == "True"
    CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "True") == "True"

# Sesiuni — expiră după 2 săptămâni (nu sesiuni permanente)
SESSION_COOKIE_AGE = 1209600  # 14 zile în secunde
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ======================
# DEFAULT PK
# ======================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ADMIN_URL = os.getenv("DJANGO_ADMIN_URL", "portal-secret-micu/").strip("/")
if not ADMIN_URL:
    raise RuntimeError("DJANGO_ADMIN_URL nu poate fi gol.")
ADMIN_URL = f"{ADMIN_URL}/"

PILLOW_MAX_IMAGE_PIXELS = int(os.getenv("PILLOW_MAX_IMAGE_PIXELS", "25000000"))
try:
    from PIL import Image as PilImage
    PilImage.MAX_IMAGE_PIXELS = PILLOW_MAX_IMAGE_PIXELS
except ImportError:
    pass

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
ACCOUNT_SESSION_REMEMBER = None  # None = întreabă utilizatorul ("ține-mă minte")

# Rate limits extinse
ACCOUNT_RATE_LIMITS = {
    'login_failed': '5/5m',       # 5 încercări eșuate la 5 minute
    'signup': '5/h',              # 5 înregistrări pe oră per IP
    'send_email': '3/5m',         # 3 emailuri (reset parolă) la 5 minute
    'confirm_email': '3/h',       # 3 confirmări email la oră
}

# Email confirmation settings
ACCOUNT_CONFIRM_EMAIL_ON_GET = os.getenv("ACCOUNT_CONFIRM_EMAIL_ON_GET", "False") == "True"
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_EMAIL_CONFIRMATION_HMAC = True

# Login/logout settings
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_LOGOUT_REDIRECT_URL = '/'


# Password reset settings
ACCOUNT_PASSWORD_MIN_LENGTH = 8

# Redirect URLs
LOGIN_URL = '/accounts/custom/login/'
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = '/'
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/'
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'

# ======================
# EMAIL SETTINGS
# ======================
# Email backend for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'micutu.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '465'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'True') == 'True'
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@micutu.com")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
SITE_URL = os.getenv("SITE_URL", "https://market.micutu.com").rstrip("/")

# Validare mutual-exclusion TLS/SSL
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ValueError(
        "EMAIL_USE_TLS și EMAIL_USE_SSL sunt mutual exclusive. "
        "Setează doar una din ele în .env (SSL=True pentru port 465, TLS=True pentru port 587)."
    )

if os.getenv("DJANGO_USE_X_FORWARDED_PROTO", "False") == "True":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
TRUSTED_PROXY_CHAIN_CONFIGURED = os.getenv("DJANGO_TRUSTED_PROXY_CHAIN_CONFIGURED", "False") == "True"

# allauth
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
# Email backend for development (decomentează pentru testare în consolă)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

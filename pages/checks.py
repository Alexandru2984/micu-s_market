import os
from urllib.parse import urlparse

from django.conf import settings
from django.core.checks import Error, Tags, Warning, register


@register(Tags.security, deploy=True)
def deployment_security_checks(app_configs, **kwargs):
    warnings = []

    if settings.ADMIN_URL == 'admin/':
        warnings.append(
            Warning(
                'Adminul este expus pe ruta implicită /admin/.',
                hint='Setează DJANGO_ADMIN_URL la o rută greu de ghicit și protejează staff login cu 2FA/IP allowlist.',
                id='micu.W001',
            )
        )

    if getattr(settings, 'SECURE_PROXY_SSL_HEADER', None):
        if not settings.TRUSTED_PROXY_CHAIN_CONFIGURED:
            warnings.append(
                Warning(
                    'SECURE_PROXY_SSL_HEADER este activ fără confirmarea lanțului de proxy.',
                    hint=(
                        'Setează DJANGO_TRUSTED_PROXY_CHAIN_CONFIGURED=True doar după ce ultimul proxy '
                        'din fața Gunicorn suprascrie X-Forwarded-Proto și originea nu poate fi accesată direct.'
                    ),
                    id='micu.W002',
                )
            )

        if not settings.CSRF_TRUSTED_ORIGINS:
            warnings.append(
                Warning(
                    'SECURE_PROXY_SSL_HEADER este activ, dar CSRF_TRUSTED_ORIGINS este gol.',
                    hint='Adaugă domeniile HTTPS publice în CSRF_TRUSTED_ORIGINS, separate prin virgulă.',
                    id='micu.W003',
                )
            )

    return warnings


@register(Tags.compatibility, deploy=True)
def production_environment_checks(app_configs, **kwargs):
    errors = []

    if settings.DEBUG:
        return errors

    required_database_keys = ("NAME", "USER", "PASSWORD", "HOST", "PORT")
    missing_db = [
        key for key in required_database_keys
        if not settings.DATABASES["default"].get(key)
    ]
    if missing_db:
        errors.append(
            Error(
                "Configurarea PostgreSQL de producție este incompletă.",
                hint=f"Setează variabilele DB lipsă: {', '.join(missing_db)}.",
                id="micu.E001",
            )
        )

    if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ["*"]:
        errors.append(
            Error(
                "ALLOWED_HOSTS nu este configurat strict pentru producție.",
                hint="Setează DJANGO_ALLOWED_HOSTS cu domeniile publice exacte.",
                id="micu.E002",
            )
        )

    if not os.getenv("DJANGO_ALLOWED_HOSTS"):
        errors.append(
            Error(
                "DJANGO_ALLOWED_HOSTS trebuie setat explicit în producție.",
                hint="Setează DJANGO_ALLOWED_HOSTS în .env cu domeniile publice exacte, separate prin virgulă.",
                id="micu.E005",
            )
        )

    if not getattr(settings, "DEFAULT_FROM_EMAIL", "") or "example.com" in settings.DEFAULT_FROM_EMAIL:
        errors.append(
            Error(
                "DEFAULT_FROM_EMAIL nu este configurat pentru producție.",
                hint="Setează DEFAULT_FROM_EMAIL la o adresă reală de pe domeniul aplicației.",
                id="micu.E003",
            )
        )

    site_url = getattr(settings, "SITE_URL", "")
    parsed_site_url = urlparse(site_url)
    if parsed_site_url.scheme != "https" or not parsed_site_url.netloc:
        errors.append(
            Error(
                "SITE_URL trebuie să fie un URL HTTPS complet în producție.",
                hint="Setează SITE_URL la domeniul public canonic, de exemplu https://market.micutu.com.",
                id="micu.E006",
            )
        )
    elif parsed_site_url.hostname not in settings.ALLOWED_HOSTS:
        errors.append(
            Error(
                "SITE_URL nu este inclus în ALLOWED_HOSTS.",
                hint="Adaugă hostul din SITE_URL în DJANGO_ALLOWED_HOSTS.",
                id="micu.E007",
            )
        )

    if getattr(settings, "MEDIA_STORAGE_BACKEND", "filesystem") == "s3":
        missing_s3 = [
            name for name in ("AWS_STORAGE_BUCKET_NAME", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")
            if not getattr(settings, name, "")
        ]
        if missing_s3:
            errors.append(
                Error(
                    "Storage-ul S3/R2 este activ, dar configurarea este incompletă.",
                    hint=f"Setează variabilele lipsă: {', '.join(missing_s3)}.",
                    id="micu.E004",
                )
            )

    if not getattr(settings, "REDIS_URL", ""):
        errors.append(
            Warning(
                "REDIS_URL nu este setat; cache-ul și rate-limit pot fi locale per proces.",
                hint="Setează REDIS_URL în producție pentru cache distribuit și rate-limit predictibil.",
                id="micu.W004",
            )
        )

    return errors

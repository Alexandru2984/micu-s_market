from django.conf import settings
from django.core.checks import Tags, Warning, register


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

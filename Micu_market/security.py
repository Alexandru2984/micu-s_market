from django.conf import settings


class ClientIPMiddleware:
    """Populate ``REMOTE_ADDR`` from the trusted reverse-proxy header.

    Under ASGI served over a Unix socket there is no peer IP address, so Django
    never sets ``REMOTE_ADDR``. Libraries that read ``request.META['REMOTE_ADDR']``
    directly (e.g. django-ratelimit) then crash with ``KeyError``. nginx sets
    ``X-Real-IP`` to the connecting address and overwrites any client-supplied
    value, which makes it the trustworthy source. Only honoured when the proxy
    chain is declared trusted, so it is a no-op in local development.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.trust_proxy = getattr(settings, "TRUSTED_PROXY_CHAIN_CONFIGURED", False)

    def __call__(self, request):
        if self.trust_proxy:
            real_ip = request.META.get("HTTP_X_REAL_IP")
            if real_ip:
                request.META["REMOTE_ADDR"] = real_ip.strip()
        return self.get_response(request)


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Permissions-Policy", getattr(settings, "PERMISSIONS_POLICY", "geolocation=(), microphone=(), camera=()"))
        response.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        response.setdefault("Cross-Origin-Resource-Policy", getattr(settings, "CROSS_ORIGIN_RESOURCE_POLICY", "same-site"))
        response.setdefault("Cross-Origin-Opener-Policy", getattr(settings, "CROSS_ORIGIN_OPENER_POLICY", "same-origin"))
        response.setdefault("X-Download-Options", "noopen")

        csp_report_only = getattr(settings, "CONTENT_SECURITY_POLICY_REPORT_ONLY", "")
        if csp_report_only:
            response.setdefault("Content-Security-Policy-Report-Only", csp_report_only)

        return response
